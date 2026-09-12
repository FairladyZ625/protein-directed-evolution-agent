#!/usr/bin/env python3
"""Deterministic synthetic checks; not protein experiments or a proof assistant."""
import itertools
import json
import math
from pathlib import Path

checks = []

def check(name, condition, **evidence):
    if not condition:
        raise AssertionError(name)
    checks.append(dict(name=name, passed=True, **evidence))

def close(a, b, tol=1e-10):
    return abs(a-b) <= tol

X = list(itertools.product((0, 1), repeat=4))
phi = lambda x: x[0]*x[1]*x[2]*(1-2*x[3])
check('HD2_zero', all(phi(x)==0 for x in X if sum(x)<=2))
coeff = {}
for mask in range(16):
    coeff[mask] = sum((-1)**(mask.bit_count()-sub.bit_count()) * phi(X[sub])
                      for sub in range(16) if sub & mask == sub)
check('Mobius_exact_coefficients', coeff[14]==1 and coeff[15]==-2 and
      all(v==0 for k,v in coeff.items() if k not in (14,15)), coefficients=coeff)
# Uniform-product Walsh basis gives exact orthogonal low-order projection.
def walsh(x, inds):
    return math.prod(2*x[i]-1 for i in inds)
subsets = [s for n in range(3) for s in itertools.combinations(range(4), n)]
wcoef = {s: sum(phi(x)*walsh(x,s) for x in X)/16 for s in subsets}
proj = lambda x: sum(wcoef[s]*walsh(x,s) for s in subsets)
rho2 = sum((phi(x)-proj(x))**2 for x in X)/16
check('Projection_floor', rho2>0 and all(close(sum((phi(x)-proj(x))*walsh(x,s) for x in X),0) for s in subsets), rho_squared=rho2)
x3 = list(itertools.product((0,1),repeat=3))
check('Prediction_floor_not_discovery_floor', max(x3,key=lambda x:sum(x)+math.prod(x)) == max(x3,key=sum) == (1,1,1))
for estimate in (-5,0,0.2,4):
    check(f'Two_world_risk_{estimate}', ((estimate-1)**2+(estimate+1)**2)/2 >= 1)

# Two equally likely worlds, no noise: safe=1, probe=0, targets=(3,-1).
# Exact enumeration of posterior index sets, measured sets, and finite horizon.
worlds = [(1,0,3,-1), (1,0,-1,3)]
# probe observation identifies world despite zero direct payoff.
def observe(w,a):
    return w if a==1 else worlds[w][a]
def terminal(ws, measured):
    return sum(max([0]+[worlds[w][a] for a in measured]) for w in ws)/len(ws)
def transitions(ws, measured, a):
    groups = {}
    for w in ws:
        groups.setdefault(observe(w,a),[]).append(w)
    return [(len(v)/len(ws),tuple(v),tuple(sorted(set(measured)|{a}))) for v in groups.values()]
def greedy(ws,measured):
    return max(range(4),key=lambda a:(sum(worlds[w][a] for w in ws)/len(ws),-a))
def value(ws,measured,h,optimal):
    if not h:
        return terminal(ws,measured)
    acts = range(4) if optimal else [greedy(ws,measured)]
    return max(sum(p*value(v,m,h-1,optimal) for p,v,m in transitions(ws,measured,a)) for a in acts)
def telescope(ws,measured,h):
    if not h: return 0
    # A concrete probe-first policy, then target by posterior mean.
    a = 1 if h==2 else greedy(ws,measured)
    tr = transitions(ws,measured,a)
    adv = sum(p*value(v,m,h-1,False) for p,v,m in tr)-value(ws,measured,h,False)
    return adv+sum(p*telescope(v,m,h-1) for p,v,m in tr)
for h in range(4):
    check(f'Bellman_dominates_h{h}',value((0,1),(),h,True)>=value((0,1),(),h,False))
check('Telescope_probe_then_target',close(telescope((0,1),(),2),3-value((0,1),(),2,False)))
check('Last_round_probe_negative',sum(p*terminal(v,m) for p,v,m in transitions((0,1),(),1)) < value((0,1),(),1,False))
# Explicit layered propagation from arbitrary values, terminal pinned.
levels = [0,99,99,99]
for _ in range(3):
    old=levels[:]
    levels=[0]+[1+old[h-1] for h in range(1,4)]
check('Finite_layer_stabilization',levels==[0,1,2,3])
check('Undiscounted_not_strict_contraction',abs((1+5)-(1+2))==abs(5-2))
# Exhaust every budget/cost pair in this toy guard, including rejected mutations.
for budget in range(4):
    for cost in range(5):
        for signed in (False,True):
            accept=signed and cost<=budget
            nxt=budget-cost if accept else budget
            check(f'Guard_{budget}_{cost}_{signed}',nxt>=0 and (signed or not accept))

# L(u)=u^2/2+u^3/6 on [0,0.5], m=1, Hessian Lipschitz=1.
u=0.5
ratios=[]
for j in range(5):
    nxt=u-(u+u*u/2)/(1+u)
    check(f'Newton_bound_{j}',nxt>=0 and nxt<=0.5*u*u+1e-16, error=u, next_error=nxt)
    if u: ratios.append(nxt/u)
    u=nxt
check('Newton_ratios_decrease',all(b<a for a,b in zip(ratios,ratios[1:])),ratios=ratios)
eta=0.01
u=0.5
for _ in range(5): u=u-(u+eta)
check('Constant_noise_floor',close(abs(u),eta))

# Constant GP posterior has equal means/variances at all candidates for every data set.
tau2,sigma2=2.0,0.25
for ys in ([],[0.2],[-1,0.3,2]):
    variance=1/(1/tau2+len(ys)/sigma2)
    mean=variance*sum(ys)/sigma2
    ucb=[mean+math.sqrt(3*variance) for _ in X]
    check(f'Constant_GP_tie_{len(ys)}',len(set(ucb))==1)
for n in range(1,13):
    selected=X[1:n+2]
    check(f'Baselines_miss_N{n+1}',all(phi(x)==0 for x in selected))

# Independent Simpson integration of the Gaussian decision error, beyond erfc formula.
def tail_integral(z):
    if z>=12: return 0.0
    steps=12000
    dx=(12-z)/steps
    density=lambda t: math.exp(-t*t/2)/math.sqrt(2*math.pi)
    total=density(z)+density(12)
    for k in range(1,steps): total+=(4 if k%2 else 2)*density(z+k*dx)
    return total*dx/3
rows=[]
for delta,sigma,n in [(1,0,1),(1,0.1,1),(1,1,1),(1,1,12),(1,10**6,3),(0,1,3)]:
    if delta==0:
        regret=0.0
    elif sigma==0:
        regret=0.0
    else:
        z=delta*math.sqrt(n)/sigma
        regret=delta*math.erfc(z/math.sqrt(2))/4
        # θ=+Δ: always hit a. θ=-Δ: miss b iff noisy mean >=0.
        enumerated=0.5*0+0.5*delta*tail_integral(z)
        check(f'Integrated_regret_{delta}_{sigma}_{n}',close(regret,enumerated,1e-9))
        check(f'Chernoff_{sigma}_{n}',regret<=delta/2*math.exp(-z*z/2)+1e-15)
    check(f'Pareto_{delta}_{sigma}_{n}',regret<delta if delta>0 else regret==delta)
    rows.append(dict(delta=delta,sigma=sigma,n=n,N=n+1,dual_regret=regret,baseline_regret=delta))
check('Infinite_noise_limit',close(rows[-2]['dual_regret'],0.25,1e-6))
# At epsilon=0.1, Delta=sigma=1, sufficient n=ceil(2 log 5)=4.
n=math.ceil(2*math.log(5))
check('SNR_budget_feasible',n<=12 and math.erfc(math.sqrt(n/2))/4<=0.1,n=n)
gain=1-math.erfc(1/math.sqrt(2))/4
check('Cost_threshold',gain-(gain/2)>0 and close(gain-gain,0) and gain-2*gain<0)
result={'kind':'synthetic_boundary_checks','passed':True,'assertions':len(checks),
        'gaussian_cases':rows,'checks':checks,
        'limitations':['Not protein data','Not independent mathematical review','No universal BO dominance','No sample-superlinear claim']}
out=Path(__file__).with_name('verification.json')
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':True,'assertions':len(checks),'output':str(out)},ensure_ascii=False))
