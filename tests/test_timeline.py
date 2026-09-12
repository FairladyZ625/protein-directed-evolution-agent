"""Evidence integrity and user-visible timeline behavior."""
import hashlib
import json
from pathlib import Path
import sys

import pytest
from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.timeline_data import EVIDENCE, VERSIONS, indicators, load_version, mutations, pairwise_effects, parse_events, read_json


def test_snapshot_hashes_and_metrics_reconcile():
    for name, provenance in read_json(EVIDENCE / 'provenance.json').items():
        assert hashlib.sha256((EVIDENCE / name).read_bytes()).hexdigest() == provenance['sha256']
    for version in VERSIONS:
        data = load_version(version)
        if version == 'v0.3':
            assert data['metrics'] is None and not data['events']
            continue
        m = data['metrics']
        assert sum(r['n_nominated'] for r in m['rounds']) == m['budget_spent']
        assert max(score for r in m['rounds'] for _, score in r['top10']) == m['summary']['final_cum_top10_max']
        assert sum(r['n_hit_strong'] for r in m['rounds']) == m['summary']['final_cum_n_strong']
    assert load_version('v0.7')['metrics']['llm_used'] is False
    assert load_version('v0.5')['metrics']['summary']['final_cum_n_strong'] == 163
    assert indicators(load_version('v0.7')['metrics'], 8.4162)['peak_round'] == 4


def test_corrupt_stream_rejected(tmp_path):
    events = (EVIDENCE / 'v0.4/agentic.events.jsonl').read_text()
    rows = events.splitlines()
    event = json.loads(rows[3]); event['payload']['n'] = 999
    rows[3] = json.dumps(event)
    path = tmp_path / 'bad.jsonl'; path.write_text('\n'.join(rows))
    with pytest.raises(ValueError, match='line 4'): parse_events(path)
    path.write_text(events + '{incomplete')
    with pytest.raises(ValueError): parse_events(path)


def test_missing_pair_not_zero_and_indel_not_substitution():
    rows = pairwise_effects('CC', 'AA', {'AA': 1, 'CA': 2, 'AC': 3, 'CC': 7})
    assert rows[0]['epsilon'] == 3
    assert pairwise_effects('CC', 'AA', {'AA': 1})[0]['epsilon'] is None
    with pytest.raises(ValueError): mutations('AAA', 'AA')


def test_every_version_and_replay_controls():
    at = AppTest.from_file(str(Path(__file__).parents[1] / 'app' / 'timeline.py'), default_timeout=30).run()
    for version in VERSIONS:
        at.radio(key='version').set_value(version).run()
        assert not at.exception, [e.value for e in at.exception]
        if version == 'v0.3':
            assert not at.metric
            continue
        best = load_version(version)['metrics']['summary']['final_cum_top10_max']
        assert at.metric[0].value == f'{best:.4f}'
        at.button(key=f'{version}_step_全部_next').click().run()
        assert at.select_slider[0].value == 1
        at.selectbox(key=f'{version}_round').set_value(1).run()
        at.selectbox(key=f'{version}_variant').select_index(1).run()
        assert not at.exception
    at.radio(key='version').set_value('💡 科研认知结晶与未来蓝图').run()
    assert not at.exception
