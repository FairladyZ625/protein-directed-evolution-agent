"""Deterministic independent algebra checks; no AAV performance claims."""
import itertools as it
import json
import math
import random
import re
from pathlib import Path

rng = random.Random(5099)
rows = [{"order": k, "site_sets": math.comb(28, k),
         "reference_parameters": math.comb(28, k)*19**k,
         "one_hot_columns": math.comb(28, k)*20**k} for k in range(1, 5)]
max_error = 0.0
for _ in range(100):
    u = [rng.uniform(-2, 2) for _ in range(8)]
    e = [1., 0., 0., 0., 0.]
    for z in u:
        for k in range(4, 0, -1):
            e[k] += z * e[k-1]
    for k in range(1, 5):
        explicit = sum(math.prod(c) for c in it.combinations(u, k))
        max_error = max(max_error, abs(explicit-e[k]))
assert max_error < 1e-10

def pairwise(bits):
    return 0.7 + sum((i+1)*b for i,b in enumerate(bits)) + sum(
        (i+j+0.25)*bits[i]*bits[j] for i,j in it.combinations(range(3),2))

def difference(fn):
    return sum((-1)**(3-sum(b))*fn(b) for b in it.product((0,1),repeat=3))
assert abs(difference(pairwise)) < 1e-12
assert abs(difference(lambda b:pairwise(b)+2.5*math.prod(b))-2.5) < 1e-12
for bits in it.product((0,1),repeat=6):
    if sum(bits)<=2:
        for k in (3,4):
            assert all(math.prod(bits[i] for i in s)==0 for s in it.combinations(range(6),k))
# Full categorical contraction versus low-rank projection, orders 3 and 4.
tucker_error = 0.0
for k in (3,4):
    q,r=3,2
    U=[[[rng.uniform(-1,1) for _ in range(r)] for _ in range(q)] for _ in range(k)]
    x=[[rng.uniform(-1,1) for _ in range(q)] for _ in range(k)]
    G={b:rng.uniform(-1,1) for b in it.product(range(r),repeat=k)}
    z=[[sum(U[i][a][b]*x[i][a] for a in range(q)) for b in range(r)] for i in range(k)]
    projected=sum(g*math.prod(z[i][b[i]] for i in range(k)) for b,g in G.items())
    full=0.
    for a in it.product(range(q),repeat=k):
        coefficient=sum(g*math.prod(U[i][a[i]][b[i]] for i in range(k)) for b,g in G.items())
        full+=coefficient*math.prod(x[i][a[i]] for i in range(k))
    tucker_error=max(tucker_error,abs(full-projected))
assert tucker_error<1e-10
root=Path(__file__).parent
report=(root/'higher-order-epistasis-theory.md').read_text()
han=len(re.findall(r'[\u4e00-\u9fff]', report))
assert han>=3500
counts={"L4":1+532+136458,"L4_Tucker3":1+532+136458+532*4+64*4**3,
        "L4_Tucker34":1+532+136458+532*4+64*4**3+32*4**4,
        "CP234":1+532+532*16+3*16,"L4_CP34":1+532+136458+532*16+2*16}
result={"status":"passed","seed":5099,"han_characters":han,"dimensions":rows,
        "parameter_counts":counts,"dense_float32_GB":{"order3":10433*rows[2]['reference_parameters']*4/1e9,
        "order4":10433*rows[3]['reference_parameters']*4/1e9},
        "dp_max_abs_error":max_error,"tucker_max_abs_error":tucker_error,
        "pairwise_third_difference":difference(pairwise),
        "injected_third_difference":difference(lambda b:pairwise(b)+2.5*math.prod(b)),
        "hd_le_2_high_order_zero":True,"scope":"Algebra and document checks only; no AAV model fit."}
(root/'verification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(result,ensure_ascii=False))
