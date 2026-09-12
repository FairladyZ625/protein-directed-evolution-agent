"""Snapshot original metrics with source paths and SHA-256 provenance."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    args = parser.parse_args()
    sources = {
        'gb1_llm': 'harness/reports/workflow-v1.0/gb1/campaign_llm.metrics.json',
        'gb1_easy': 'harness/reports/workflow-v1.0/gb1/campaign_easy.metrics.json',
        **{f'aav_v0{v}': f'harness/reports/agentic-v0.{v}/aav/agentic.metrics.json' for v in (1, 2, 4)},
        'aav_greedy': 'harness/reports/agentic-v0.4/aav/deterministic.metrics.json',
        'aav_v05': '.worktrees/t-v05/harness/reports/agentic-v0.5/aav/agentic.metrics.json',
        **{f'aav_{mode}_{seed}': f'.worktrees/t-v07/harness/reports/agentic-v0.7/aav/{mode}-seed{seed}/metrics.json'
           for mode in ('mean', 'alternating') for seed in (0, 7, 42)},
    }
    out = ROOT / 'artifacts/figures_data'
    out.mkdir(parents=True, exist_ok=True)
    index = {}
    for key, relative in sources.items():
        raw = (args.source_root / relative).read_bytes()
        data = json.loads(raw)
        # Keep only machine metrics; LLM narrative is not measurement evidence.
        kept = {k: data[k] for k in ('schema_version', 'dataset', 'candidate_space_size',
                'cold_start', 'llm', 'budget_per_round', 'budget_spent', 'seed', 'summary') if k in data}
        def rounds(rows):
            spent = 0
            result = []
            for row in rows:
                spent += row['n_nominated']
                assert row.get('spent_after', spent) == spent
                result.append({k: row[k] for k in ('round', 'n_nominated', 'cum_top10_max', 'cum_n_strong')})
                result[-1]['spent_after'] = spent
            return result
        if 'strategies' in data:
            kept['strategies'] = {k: {'seed': v['seed'], 'rounds': rounds(v['rounds'])} for k,v in data['strategies'].items()}
        else:
            kept['rounds'] = rounds(data['rounds'])
        kept['provenance'] = {'source': relative, 'sha256': hashlib.sha256(raw).hexdigest(),
                              'fields': 'rounds.{round,n_nominated,cum_top10_max,cum_n_strong}; summary',
                              'metric': 'cumulative maximum among newly queried variants; excludes cold start'}
        text = json.dumps(kept, indent=2) + '\n'
        (out / f'{key}.json').write_text(text)
        index[key] = {**kept['provenance'], 'snapshot_sha256': hashlib.sha256(text.encode()).hexdigest()}
    (out / 'provenance.json').write_text(json.dumps(index, indent=2) + '\n')
    print(f'Extracted {len(index)} provenance-pinned metric snapshots')

if __name__ == '__main__':
    main()
