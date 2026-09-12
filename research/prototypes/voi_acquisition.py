"""Integer greedy marginal optimization of theory eq. 13, a VoI *proxy*.

Exact logdet and weighted epistasis trace-reduction marginal increments under a
Gaussian linear model. No oracle labels or within-batch feedback are consumed.
This is not Bellman-optimal VoI or a simple-regret guarantee.
"""
import numpy as np


def select_batch(mean, features, covariance, batch_size, *, noise=1.,
                 information_weight=0., epistasis_weight=0., epi_start=0,
                 remaining_rounds=1, total_rounds=1):
    mean, x, cov = np.asarray(mean, float), np.asarray(features, float), np.asarray(covariance, float).copy()
    if (x.ndim != 2 or mean.shape != (len(x),) or cov.shape != (x.shape[1], x.shape[1])
            or not 0 <= batch_size <= len(x) or noise <= 0
            or min(information_weight, epistasis_weight) < 0
            or not 1 <= remaining_rounds <= total_rounds or not 0 <= epi_start <= x.shape[1]
            or not all(np.isfinite(a).all() for a in (mean, x, cov))):
        raise ValueError('invalid acquisition inputs')
    if not np.allclose(cov, cov.T) or np.linalg.eigvalsh(cov).min() < -1e-9:
        raise ValueError('covariance must be positive semidefinite')
    anneal = (remaining_rounds-1)/(total_rounds-1) if total_rounds > 1 else 0.
    lam, nu = information_weight * anneal, epistasis_weight * anneal
    # Fixed W=identity on epistasis parameters, normalized by dimension.
    epi_dim = max(1, x.shape[1] - epi_start)
    cross = x @ cov
    available = np.ones(len(x), bool)
    picks, info, reduction = [], 0., 0.
    for _ in range(batch_size):
        variance = np.maximum(0, np.einsum('ij,ij->i', cross, x))
        ig = .5 * np.log1p(variance / noise)
        vr = np.sum(cross[:, epi_start:]**2, axis=1) / (noise+variance) / epi_dim
        score = mean + lam*ig + nu*vr
        score[~available] = -np.inf
        j = int(np.argmax(score))  # deterministic input-order ties
        picks.append(j); available[j] = False
        info += float(ig[j]); reduction += float(vr[j])
        direction = cross[j].copy()
        cross -= np.outer(x @ direction, direction) / (noise+variance[j])
    greedy = np.argsort(-mean, kind='stable')[:batch_size]
    return np.array(picks, int), dict(information_nats=info, epistasis_trace_reduction=reduction,
        mean_opportunity_cost=float(mean[greedy].sum()-mean[picks].sum()),
        non_greedy_slots=len(set(picks)-set(greedy.tolist())), anneal=anneal)
