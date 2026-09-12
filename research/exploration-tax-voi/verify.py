"""Deterministic checks of report identities; not an AAV experiment."""
import itertools
import math
import pathlib
import re
from decimal import Decimal as D

root = pathlib.Path(__file__).parent
report = (root / 'exploration-tax-formalization.md').read_text()
cjk = len(re.findall(r'[\u4e00-\u9fff]', report))
assert cjk >= 3500, cjk
assert D('8.416') - D('7.829') == D('0.587')
assert D('8.416') - D('5.960') == D('2.456')
assert D('8.416') - D('7.530') == D('0.886')
# Enumerate the actual mixture experiment, independently of the closed form.
B, p, q, alpha = 4, .6, .15, .3
miss = 0.
for choices in itertools.product((0, 1), repeat=B):
    prob = math.prod(alpha if a else 1-alpha for a in choices)
    conditional_miss = math.prod(1-q if a else 1-p for a in choices)
    miss += prob * conditional_miss
assert abs(miss - (1-p+alpha*(p-q))**B) < 1e-12
for i in range(1, 100):
    a, h = i/100, 1e-4
    f = lambda z: (1-p+z*(p-q))**B-(1-p)**B
    assert f(a+h)-2*f(a)+f(a-h) >= -1e-12
# Finite Bellman tree: one branch of g has utility 2, other 4; pi differs.
vg1 = .5*2 + .5*4
jpi = .25*1 + .75*3
first_advantage = vg1 - (.25*2 + .75*4)
second_advantage = .25*(2-1) + .75*(4-3)
assert abs(vg1-jpi-first_advantage-second_advantage) < 1e-12
# Scalar Gaussian variance/information identity and finite-budget log inequality.
sigma2 = .4
for u in [0, .001, .2, .7, 1]:
    assert u <= math.log1p(u/sigma2)/math.log1p(1/sigma2)+1e-12
old, noise = 1.2, .4
new = 1/(1/old+1/noise)
info = .5*math.log1p(old/noise)
assert abs(old/new-math.exp(2*info)) < 1e-12
# Exact 2x2 inverse and determinant; test the continuous-design concavity.
def acq(w):
    a, b, c = 1+2*w, .2+.3*w, 1.5+.7*w
    det = a*c-b*b
    assert det>0
    return .6*w + .4*math.log(det) - .3*a/det
for i in range(1, 100):
    w, h = i/100, 1e-4
    assert acq(w+h)-2*acq(w)+acq(w-h) <= 1e-10
text = f'''# Verification record

Command: `python research/exploration-tax-voi/verify.py`

PASS: {cjk} CJK characters (minimum 3,500).
PASS: Decimal arithmetic for reported fitness contrasts.
PASS: Exhaustive four-slot randomized exploration enumeration matches equation (3).
PASS: Interior finite differences confirm convexity for that illustrative model.
PASS: Two-stage Bellman tree verifies telescoping exploration-tax identity.
PASS: Gaussian variance/information identity and variance-to-log inequality.
PASS: Two-dimensional positive-definite continuous design has concave objective along the checked affine path.

These checks supplement the written proofs; numerical checks are not general proofs.
No original AAV event replay, posterior calibration, or v0.5 experiment was performed.
Manual review separated recommendation from discovery regret, batch from sequential feedback,
and bounded-utility information bounds from unbounded Gaussian assumptions.
'''
(root / 'verification.md').write_text(text)
print(text)
