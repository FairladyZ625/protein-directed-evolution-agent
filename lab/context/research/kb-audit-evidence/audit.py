import json
from collections import Counter
from itertools import combinations
import pandas as pd
from knowledge.validators import load_rules, validate_candidate, _score
from agent.auto_researcher import _gate_variants
from evolution.datasets import AAV_WT
b = load_rules()['blosum62']; aa = 'ACDEFGHIKLMNPQRSTVWY'
def score(a, c): return 4 if a == c else b.get(a, {}).get(c, b.get(c, {}).get(a, 0))
def pairs(s): return list(combinations([(i, c) for i, (w, c) in enumerate(zip(AAV_WT, s)) if w != c], 2))
def emit(kind, **kw): print(json.dumps(dict(kind=kind, **kw), ensure_ascii=False))
raw = pd.read_csv('data/aav/full_data.csv', usecols=['mutated_region', 'number_of_mutations'])
s = raw.mutated_region.astype(str)
df = raw[s.str.len().eq(len(AAV_WT)) & s.str.match(r'^[A-Z]+$') & ~s.str.contains(r'\*')].drop_duplicates('mutated_region')
cold = df[df.number_of_mutations <= 2].mutated_region.tolist()
pool = df[df.number_of_mutations > 2].mutated_region.tolist()
gate, _ = _gate_variants(pool, wt=AAV_WT, max_hd=4, blosum_min=0., blosum_fn=score)
c = Counter(p for s in cold for p in pairs(s)); g = Counter(p for s in gate for p in pairs(s))
pos_c = {(p[0][0], p[1][0]) for p in c}; pos_g = {(p[0][0], p[1][0]) for p in g}
missing = set(g) - set(c)
emit('coverage', rows=len(df), cold=len(cold), pool=len(pool), gate=len(gate), cold_position_pairs=len(pos_c), gate_position_pairs=len(pos_g), unseen_position_pairs=len(pos_g-pos_c), gate_residue_pairs=len(g), unseen_residue_pairs=len(missing), gate_candidates_with_unseen_pair=sum(any(p in missing for p in pairs(s)) for s in gate), nonstandard_rows=sum(bool(set(s)-set(aa)) for s in df.mutated_region))
missing_b = [(a,c) for a,c in combinations(aa, 2) if c not in b.get(a,{}) and a not in b.get(c,{})]
zero_lost = [(a,c) for a in aa for c in aa if a!=c and b.get(a,{}).get(c)==0 and _score(a,c,b) is None]
emit('matrix', aa_entries=len(load_rules()['amino_acids']), unordered_pairs=190, missing_pairs=len(missing_b), zeros_lost=zero_lost, K_R_gate=score('K','R'), AAV_N8Q=validate_candidate(['N8Q']))
# Positive/negative controls exercise the same gate/validator path without labels.
allowed,rejected = _gate_variants([AAV_WT, AAV_WT[:-1], 'A'*28], wt=AAV_WT, max_hd=4, blosum_min=0., blosum_fn=score)
assert allowed == [AAV_WT] and len(rejected)==2
# Only `gate` rows may reject a candidate (rules.yaml: "every consumer filters on
# enforcement == \"gate\""). Asserting `all(...)` also demanded the advisory
# R-PRIORITIZE-HISTORICAL, whose `historical_good` argument validate_candidate never
# supplies, so `matched` is always empty and the row always reports pass=False: the
# assert could never hold and aborted the script before the `controls` emit below.
assert all(x['pass'] for x in validate_candidate(['V39I'])
           if x['enforcement'] == 'gate')
assert any(not x['pass'] for x in validate_candidate(['N8Q']))
assert c[((0,'A'),(1,'A'))] == sum(s[0]=='A' and s[1]=='A' for s in cold)
emit('controls', wt_pass=True, malformed_rejected=True, high_hd_rejected=True, GB1_V39I_pass=True, AAV_N8Q_fails=True, pair_counter_crosscheck=True, fitness_columns_read=False)
