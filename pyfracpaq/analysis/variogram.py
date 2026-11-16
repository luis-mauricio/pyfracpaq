"""Streaming port of Schwanghart's supplied experimental variogram equations.

The source has size-dependent self pairs: n<1000 includes the diagonal; n>=1000
does not. This observable convention is retained, including native cloud order,
empty-bin NaNs, doubled directional closure and unhalved cloud differences.
No fit of a theoretical variogram is introduced.
"""

from collections.abc import Callable
from dataclasses import dataclass
from math import floor, hypot, isfinite
import warnings

import numpy as np
from numpy.typing import ArrayLike, NDArray

from pyfracpaq.analysis.compatibility import readonly
from pyfracpaq.geometry.primitives import DEFAULT_MEMORY_LIMIT


def _indices(values) -> NDArray[np.int64]:
    result = np.array(values, dtype=np.int64, copy=True)
    result.setflags(write=False)
    return result


@dataclass(frozen=True, slots=True)
class VariogramResult:
    distance: NDArray[np.float64]
    values: NDArray[np.float64]
    counts: NDArray[np.float64] | None
    theta: NDArray[np.float64] | None
    pair_indices: NDArray[np.int64] | None
    pair_count: int
    sample_indices: NDArray[np.int64]
    maximum_distance: float
    bins: int
    kind: str
    includes_self: bool
    dimensions: int
    seed: int | None


def experimental_variogram(coordinates: ArrayLike, values: ArrayLike, *,
                            nrbins: int = 20, maxdist: float | None = None,
                            kind: str = 'gamma', anisotropy: bool = False,
                            thetastep: float = 30, subsample: int | float = np.inf,
                            seed: int | None = None, subsample_indices: ArrayLike | None = None,
                            progress: Callable[[int, str], None] = lambda *_: None,
                            interrupted: Callable[[], bool] = lambda: False) -> VariogramResult:
    x, y = np.asarray(coordinates, dtype=float), np.asarray(values, dtype=float)
    if x.ndim == 1:
        x = x[:, None]
    if y.ndim == 2 and y.shape[1] == 1:
        y = y[:, 0]
    if x.ndim != 2 or not x.shape[1] or y.ndim != 1 or len(x) != len(y):
        raise ValueError('Variogram requires N by D coordinates and N scalar observations.')
    keep = ~(np.isnan(x).any(axis=1) | np.isnan(y))
    original_ids = np.flatnonzero(keep)
    x, y = x[keep], y[keep]
    if np.isinf(x).any() or np.isinf(y).any():
        raise ValueError('Retained variogram inputs cannot contain infinity.')
    if not len(y):
        raise ValueError('Variogram requires at least one finite observation.')
    if isinstance(nrbins, bool) or not isinstance(nrbins, int) or nrbins < 1:
        raise ValueError('Variogram bin count must be a positive integer.')
    if kind not in ('default', 'gamma', 'cloud1', 'cloud2'):
        raise ValueError('Variogram kind must be gamma, cloud1 or cloud2.')
    if not np.isfinite(thetastep) or not 0 < thetastep <= 180:
        raise ValueError('Directional width must be between zero and 180 degrees.')
    if anisotropy and x.shape[1] != 2:
        warnings.warn('Anisotropy is supported only for 2-D coordinates; using isotropic bins.',
                      RuntimeWarning, stacklevel=2)
        anisotropy = False
    angular_bins = floor(180 / thetastep) if anisotropy else 1
    cells = nrbins * (angular_bins + 1 if anisotropy else 1)
    if len(y) * max(128, x.shape[1] * 64) + cells * 32 > DEFAULT_MEMORY_LIMIT:
        raise MemoryError('Variogram working data exceed the 256 MiB memory budget.')
    # Source extent and default maxdist are measured before optional subsampling.
    with np.errstate(over='ignore', invalid='ignore'):
        spans = x.max(axis=0) - x.min(axis=0)
    extent = hypot(*spans)
    maximum = extent / 2 if maxdist is None else float(maxdist)
    if not isfinite(extent) or not isfinite(maximum) or maximum < 0:
        raise ValueError('Variogram maximum distance must be finite and nonnegative.')
    if maximum > extent:
        warnings.warn('Maximum variogram distance exceeds the coordinate extent; clamping it.',
                      RuntimeWarning, stacklevel=2)
        maximum = extent
    if not (subsample == np.inf or (not isinstance(subsample, bool)
            and isinstance(subsample, (int, np.integer)) and subsample >= 1)):
        raise ValueError('Subsample must be a positive integer or infinity.')
    if subsample_indices is not None:
        selected = np.asarray(subsample_indices)
        if selected.ndim != 1 or not len(selected) or selected.dtype.kind not in 'iu' \
                or len(np.unique(selected)) != len(selected) \
                or np.any((selected < 0) | (selected >= len(y))):
            raise ValueError('Shared subsample indices must be distinct valid filtered-row indices.')
        x, y, original_ids = x[selected], y[selected], original_ids[selected]
    elif subsample < len(y):
        sequence = np.random.SeedSequence(seed)
        seed = int(sequence.entropy)
        selected = np.random.Generator(np.random.PCG64(sequence)).choice(
            len(y), int(subsample), replace=False)
        x, y, original_ids = x[selected], y[selected], original_ids[selected]
    n = len(y)
    includes_self = n < 1000
    edges = np.linspace(0, maximum, nrbins + 1)
    edges[-1] = np.inf
    distance_centres = edges[:-1] + maximum / nrbins / 2
    theta_centres = theta_edges = None
    if anisotropy:
        step = np.deg2rad(thetastep)
        theta_edges = np.linspace(-step / 2, np.pi - step / 2, angular_bins + 1)
        theta_centres = theta_edges + step / 2
        theta_centres[-1] = np.pi
    shape = (nrbins, angular_bins + 1) if anisotropy else (nrbins,)
    counts, totals = np.zeros(shape, dtype=np.int64), np.zeros(shape)
    distances, differences, directions, pairs = [], [], [], []
    pair_count = 0
    for outer in range(n):
        if interrupted():
            raise InterruptedError('Variogram cancelled.')
        if includes_self:
            left, right = np.arange(outer + 1), np.full(outer + 1, outer)
        else:
            right = np.arange(outer + 1, n)
            left = np.full(len(right), outer)
        delta = x[right] - x[left]
        with np.errstate(over='ignore', invalid='ignore'):
            if includes_self and x.shape[1] == 2:
                distance = np.hypot(delta[:, 0], delta[:, 1])
            elif x.shape[1] == 1:
                distance = np.abs(delta[:, 0])
            else:
                distance = np.sqrt(np.sum(delta ** 2, axis=1))
        eligible = distance <= maximum
        left, right, delta, distance = left[eligible], right[eligible], delta[eligible], distance[eligible]
        if len(left):
            with np.errstate(over='ignore', invalid='ignore'):
                squared = (y[left] - y[right]) ** 2
            if not np.isfinite(squared).all():
                raise ValueError('Variogram squared differences exceed float64 range.')
            radial = np.searchsorted(edges, distance, side='right') - 1
            angular = None
            if anisotropy:
                theta = np.arctan2(delta[:, 0], delta[:, 1])
                theta = np.where(theta < 0, theta + np.pi, theta)
                theta = np.where(theta >= np.pi - np.deg2rad(thetastep) / 2, 0, theta)
                angular = np.searchsorted(theta_edges, theta, side='right') - 1
            pair_count += len(left)
            if kind in ('default', 'gamma'):
                membership = (radial, angular) if anisotropy else radial
                np.add.at(counts, membership, 1)
                np.add.at(totals, membership, squared)
            else:
                if pair_count * 128 + n * max(128, x.shape[1] * 64) > DEFAULT_MEMORY_LIMIT:
                    raise MemoryError('Variogram cloud exceeds the 256 MiB memory budget.')
                distances.append(distance_centres[radial] if kind == 'cloud1' else distance)
                differences.append(squared)
                pairs.append(np.column_stack((original_ids[left], original_ids[right])))
                if anisotropy:
                    directions.append(theta_centres[angular])
        if outer % max(1, n // 100) == 0 or outer + 1 == n:
            progress(round(100 * (outer + 1) / n), 'Accumulating variogram pairs...')
    if kind in ('default', 'gamma'):
        if not np.isfinite(totals).all():
            raise ValueError('Variogram accumulated differences exceed float64 range.')
        gamma = np.full(shape, np.nan)
        np.divide(totals, 2 * counts, out=gamma, where=counts != 0)
        population = counts.astype(float)
        population[counts == 0] = np.nan
        if anisotropy:
            gamma[:, -1], population[:, -1] = gamma[:, 0], population[:, 0]
        return VariogramResult(readonly(distance_centres), readonly(gamma), readonly(population),
            None if theta_centres is None else readonly(theta_centres), None, pair_count,
            _indices(original_ids), maximum, nrbins, kind, includes_self, x.shape[1], seed)
    cloud_distance = np.concatenate(distances) if distances else np.empty(0)
    cloud_values = np.concatenate(differences) if differences else np.empty(0)
    cloud_pairs = np.vstack(pairs) if pairs else np.empty((0, 2), dtype=np.int64)
    cloud_theta = (np.concatenate(directions) if directions else np.empty(0)) if anisotropy else None
    return VariogramResult(readonly(cloud_distance), readonly(cloud_values), None,
        None if cloud_theta is None else readonly(cloud_theta), _indices(cloud_pairs), pair_count,
        _indices(original_ids), maximum, nrbins, kind, includes_self, x.shape[1], seed)
