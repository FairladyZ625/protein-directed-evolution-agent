"""Package byte-identical research evidence; run explicitly, never from the UI."""
from pathlib import Path
import argparse
import csv
import hashlib
import itertools
import json
import shutil

WT = 'DEEEIRTTNPVATEQYGSVSTNLQRGNR'

def build(root: Path, v05: Path, v07: Path, out: Path):
    sources = {}
    def copy(source, destination):
        dest = out / destination
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
        sources[destination] = {'source': str(source.relative_to(root)),
                                'sha256': hashlib.sha256(dest.read_bytes()).hexdigest()}
    for version, origin in [('v0.1', root), ('v0.2', root), ('v0.4', root), ('v0.5', v05)]:
        for suffix in ['metrics.json', 'events.jsonl']:
            copy(origin / f'lab/reports/agentic-{version}/aav/agentic.{suffix}', f'{version}/agentic.{suffix}')
    for suffix in ['metrics.json', 'events.jsonl']:
        copy(v07 / f'lab/reports/agentic-v0.7/aav/alternating-seed42/{suffix}', f'v0.7/agentic.{suffix}')
    copy(root / 'lab/reports/agentic-v0.3/aav/surrogate_scan.json', 'v0.3/surrogate_scan.json')
    copy(root / 'lab/reports/agentic-v0.4/aav/deterministic.metrics.json', 'baseline.metrics.json')
    copy(root / 'reports/scientific_report_v1.0.md', 'scientific_report_v1.0.md')
    for p in sorted((root / 'reports/theoretical_foundations').glob('*.md')):
        copy(p, f'whitepapers/{p.name}')
    # Only measured single/double backgrounds needed for variants in the inspector.
    wanted = {WT}
    for p in out.glob('v*/agentic.metrics.json'):
        for row in json.loads(p.read_text())['rounds']:
            for seq, _ in row['top10']:
                wanted.add(seq)
                mutations = [(i, a) for i, a in enumerate(seq) if i < len(WT) and a != WT[i]]
                if len(seq) != len(WT):
                    continue
                for order in [1, 2]:
                    for subset in itertools.combinations(mutations, order):
                        s = list(WT)
                        for i, a in subset: s[i] = a
                        wanted.add(''.join(s))
    measured = {}
    source = root / 'data/aav/full_data.csv'
    with source.open() as f:
        for row in csv.DictReader(f):
            seq = row['mutated_region']
            if seq in wanted and seq not in measured:
                measured[seq] = float(row['score'])
    dest = out / 'measured_backgrounds.json'
    dest.write_text(json.dumps(measured, indent=2) + '\n')
    sources[dest.name] = {'source': 'data/aav/full_data.csv', 'transform': 'First occurrence per sequence, matching evolution.datasets.load_aav; selected WT, top10 sequences and single/double backgrounds only.', 'sha256': hashlib.sha256(dest.read_bytes()).hexdigest(), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest()}
    (out / 'provenance.json').write_text(json.dumps(sources, indent=2) + '\n')

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['root', 'v05', 'v07', 'out']: p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    build(a.root, a.v05, a.v07, a.out)
