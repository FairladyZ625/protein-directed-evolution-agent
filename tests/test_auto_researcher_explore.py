"""Exploration, autonomy boundaries and withheld-label independence."""
from types import SimpleNamespace

import numpy as np
import pytest

from agent.auto_researcher import (
    _explore_batch_indices, _rounds_since_improvement, run_autoresearch,
)
from test_auto_researcher_gate import _big_gated_spec


@pytest.mark.parametrize('curve,count', [([], 0), ([1], 0), ([1,2,3,4], 0),
    ([1,2,2], 1), ([1,2,2,2], 2), ([1,1,1,2], 0)])
def test_stagnation_only_counts_non_improving_batches(curve, count):
    assert _rounds_since_improvement(curve) == count


@pytest.mark.parametrize('method', ['diverse', 'uncertainty', 'spread'])
def test_explore_can_reach_low_mean_rank_and_respects_eligibility(method):
    mean = np.arange(2000, 0, -1, dtype=float)
    var = np.zeros(2000)
    var[-1] = 1e8  # mean rank 2000, independently declared high uncertainty
    eligible = list(range(100, 2000))
    picks = _explore_batch_indices(mean, var, eligible_indices=eligible, n=48,
        rng=np.random.default_rng(42), method=method, seqs=['AAAA']*2000)
    assert 1999 in picks
    assert len(picks) == len(set(picks)) == 48
    assert set(picks) <= set(eligible)
    assert _explore_batch_indices(mean, var, eligible_indices=[], n=48,
        rng=np.random.default_rng(42), method=method) == []


def test_spread_prefers_sequence_distance_when_ucb_ties():
    picks = _explore_batch_indices(np.ones(3), np.ones(3), eligible_indices=range(3),
        n=2, rng=np.random.default_rng(0), method='spread',
        seqs=['AAAA', 'AAAS', 'SSSS'], anchors=['AAAA'])
    assert picks[0] == 2


def _fake_agent(monkeypatch, action):
    import pydantic_ai
    import agent.llm
    class FakeAgent:
        def __init__(self, *args, **kwargs):
            self.tools = {}
            self.round = 0
        def tool_plain(self, fn):
            self.tools[fn.__name__] = fn
        def run_sync(self, *args, **kwargs):
            self.round += 1
            action(self.tools, self.round)
            return SimpleNamespace(output='scripted test driver', all_messages=lambda: [])
    monkeypatch.setattr(pydantic_ai, 'Agent', FakeAgent)
    monkeypatch.setattr(agent.llm, 'llm_config', lambda: {
        'model':'test', 'api_key':'test-key', 'base_url':'https://example.invalid/v1'})


def test_semi_forces_exploration_and_blocks_direct_test_bypass(monkeypatch):
    states = []
    def action(t, rnd):
        status = t['analyze_measured']()
        states.append(status)
        if rnd == 4:
            assert status['exploration_required']
            assert t['test'](t['list_pool'](2))['status'] == 'exploration_required'
            # Even an explicit exploit request is redirected; the LLM picks how to explore.
            batch = t['compose_batch'](n=2, exploit_ratio=1.0, exploration='uncertainty')
            assert batch['method'] == 'uncertainty' and batch['forced']
        else:
            t['compose_batch'](n=2)
        assert t['test_composed_batch']()['n_measured_now'] == 2
        assert t['test'](t['list_pool'](2))['status'] == 'round_test_complete'
    _fake_agent(monkeypatch, action)
    spec = _big_gated_spec()
    # An enormous cold-start incumbent must not turn round 1 into stagnation.
    spec.df.loc[spec.df.hd <= 2, 'fitness'] = 1000
    spec.df.loc[spec.df.hd > 2, 'fitness'] = 2
    rep = run_autoresearch(spec, budget=2, n_rounds=4, guardrail=True, backtrack='semi')
    assert rep['budget_spent'] == 8
    assert [s['rounds_since_improvement'] for s in states] == [0,0,1,2]
    assert [s['exploration_required'] for s in states] == [False,False,False,True]
    assert rep['top10_max_history'] == [2]*4
    assert not [e for e in rep['tool_trace'] if e['event_type'].endswith('round_error')]


def test_full_retains_autonomy_after_stagnation_and_late_exploration(monkeypatch):
    allocations = []
    def action(t, rnd):
        s = t['analyze_measured']()
        assert not s['exploration_required']
        # FULL may keep exploiting a plateau or choose 100% exploration in the last round.
        batch = t['compose_batch'](n=2, exploit_ratio=0.0 if rnd == 4 else 1.0)
        allocations.append((batch['n_exploit'], batch['n_explore']))
        t['test_composed_batch']()
    _fake_agent(monkeypatch, action)
    spec = _big_gated_spec()
    spec.df.loc[spec.df.hd > 2, 'fitness'] = 2
    rep = run_autoresearch(spec, budget=2, n_rounds=4, backtrack='full', guardrail=True)
    assert allocations == [(2,0)]*3 + [(0,2)]
    assert rep['budget_spent'] == 8


@pytest.mark.parametrize('method', ['diverse', 'uncertainty', 'spread'])
def test_withheld_labels_cannot_change_first_exploration_batch(monkeypatch, method):
    def action(t, rnd):
        assert t['explore_batch'](n=999, method='invalid')['status'] == 'invalid_argument'
        batch = t['explore_batch'](n=999, method=method)
        assert batch['n'] == 4  # fixed per-round budget
        assert t['test_composed_batch']()['n_measured_now'] == 4
    _fake_agent(monkeypatch, action)
    original = _big_gated_spec()
    altered = _big_gated_spec()
    altered.df.loc[altered.df.hd > 2, 'fitness'] = np.arange((altered.df.hd > 2).sum())[::-1]*999
    reports = [run_autoresearch(s, budget=4, n_rounds=1, backtrack='full', guardrail=True)
               for s in (original, altered)]
    audit = [[e['payload']['candidates'] for e in r['tool_trace']
              if e['event_type']=='agent.acquisition'] for r in reports]
    assert audit[0] == audit[1]
    assert len(audit[0][0]) == 4
    assert all(c['mean_rank'] >= 1 for c in audit[0][0])
