"""Fixed-factor CP ANOVA prototype (theory eq. 8); no structural claims.

Reference-state additive features plus rank-bounded distinct-site interactions.
Factors are seed-fixed Rademacher projections, not learned biological couplings.
Third-order means remain zero on HD<=2; Bayesian prior uncertainty remains nonzero.
"""
import numpy as np
from scipy.linalg import cho_factor, cho_solve

AA = 'ACDEFGHIKLMNPQRSTVWY'
WT = 'DEEEIRTTNPVATEQYGSVSTNLQRGNR'


class SparseEpistasisTensor:
    def __init__(self, reference=WT, rank=16, degree=3, seed=42):
        if degree not in (2, 3, 4) or rank < 1 or not reference or set(reference)-set(AA):
            raise ValueError('valid reference, positive rank, degree 2..4 required')
        self.reference, self.rank, self.degree = reference, rank, degree
        self.alternatives = [[a for a in AA if a != w] for w in reference]
        self.factors = np.random.default_rng(seed).choice([-1., 1.], (len(reference), 19, rank))
        self.epi_start = 1 + 19 * len(reference)

    def transform(self, sequences):
        n, length = len(sequences), len(self.reference)
        x = np.zeros((n, length, 19))
        for row, seq in enumerate(sequences):
            if len(seq) != length or set(seq)-set(AA):
                raise ValueError('invalid substitution sequence')
            for i, (a, w) in enumerate(zip(seq, self.reference)):
                if a != w:
                    x[row, i, self.alternatives[i].index(a)] = 1
        z = np.einsum('nla,lar->nlr', x, self.factors)
        e = np.zeros((n, self.degree + 1, self.rank)); e[:, 0] = 1
        for i in range(length):
            for k in range(self.degree, 0, -1):
                e[:, k] += z[:, i] * e[:, k-1]
        return np.column_stack([np.ones(n), x.reshape(n, -1)] +
                               [e[:, k] / np.sqrt(self.rank) for k in range(2, self.degree+1)])


class BayesianRidge:
    """Fixed alpha/noise Gaussian linear model; exact covariance in feature space.

    alpha=10, noise=1 are preregistered engineering choices, not calibrated assay
    noise. All parameters, including intercept, have the same proper prior.
    """
    def __init__(self, alpha=10., noise=1.):
        if alpha <= 0 or noise <= 0:
            raise ValueError('alpha and noise must be positive')
        self.alpha, self.noise = alpha, noise

    def fit(self, x, y):
        x, y = np.asarray(x, float), np.asarray(y, float)
        if x.ndim != 2 or y.shape != (len(x),) or not np.isfinite(x).all() or not np.isfinite(y).all():
            raise ValueError('finite aligned observations required')
        precision = x.T @ x / self.noise + self.alpha * np.eye(x.shape[1])
        factor = cho_factor(precision)
        self.covariance = cho_solve(factor, np.eye(x.shape[1]))
        self.coef = cho_solve(factor, x.T @ y / self.noise)
        return self

    def predict(self, x):
        return x @ self.coef, np.maximum(0, np.einsum('ij,ij->i', x @ self.covariance, x))
