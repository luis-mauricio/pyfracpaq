"""Two-sided two-sample K-S with explicit MATLAB-compatible asymptotic method.

The empirical step functions include all ties. The p-value uses the public
Kolmogorov series with effective sample size and finite-sample correction;
no SciPy 'auto' choice or one-sample replacement is involved.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray


@dataclass(frozen=True, slots=True)
class KsResult:
    distance: float
    pvalue: float
    reject: bool
    alpha: float


def ks_probability(distance: ArrayLike, first_size: int, second_size: int) -> NDArray:
    if first_size < 1 or second_size < 1:
        raise ValueError('K-S requires two nonempty samples.')
    values = np.asarray(distance, dtype=np.float64)
    if not np.isfinite(values).all() or np.any((values < 0) | (values > 1)):
        raise ValueError('K-S distances must be finite and between zero and one.')
    effective = first_size * second_size / (first_size + second_size)
    correction = np.sqrt(effective) + .12 + .11 / np.sqrt(effective)
    result = np.empty(values.size, dtype=np.float64)
    terms = np.arange(1, 102, dtype=np.float64)
    signs = np.where(terms.astype(int) % 2, 1., -1.)
    for start in range(0, values.size, 4096):
        lam = values.ravel()[start:start + 4096] * correction
        series = np.exp(-2 * (lam[:, None] * terms) ** 2) @ signs
        result[start:start + len(lam)] = np.clip(2 * series, 0, 1)
    return result.reshape(values.shape)


def _sample(values: ArrayLike) -> NDArray[np.float64]:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1 or not len(array) or not np.isfinite(array).all():
        raise ValueError('K-S samples must be nonempty finite vectors.')
    return np.sort(array, kind='stable')


def ks_distance_sorted(first: NDArray, second: NDArray) -> float:
    """Supremum at both samples' steps; caller supplies sorted finite arrays."""
    n, m = len(first), len(second)
    difference_first = (np.searchsorted(first, first, side='right') / n
                         - np.searchsorted(second, first, side='right') / m)
    difference_second = (np.searchsorted(first, second, side='right') / n
                          - np.searchsorted(second, second, side='right') / m)
    return float(max(np.max(np.abs(difference_first)), np.max(np.abs(difference_second))))


def ks_two_sample(first: ArrayLike, second: ArrayLike, *, alpha: float = .05) -> KsResult:
    if not np.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError('K-S significance must be between zero and one.')
    left, right = _sample(first), _sample(second)
    distance = ks_distance_sorted(left, right)
    pvalue = float(ks_probability(distance, len(left), len(right)))
    return KsResult(distance, pvalue, bool(pvalue <= alpha), alpha)
