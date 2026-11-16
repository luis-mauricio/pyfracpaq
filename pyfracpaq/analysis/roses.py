"""Historical roseLinear and Middleton rosePlot data APIs, outside the GUI.

Historical histc's final singleton bin and dropped low angles are preserved.
The incomplete roseEqualArea2/experimental colour scripts remain references.
"""

from dataclasses import dataclass

import numpy as np

from pyfracpaq.analysis.compatibility import histcount_indices, readonly, sind, cosd


@dataclass(frozen=True, slots=True)
class HistoricalRose:
    edges: np.ndarray
    counts: np.ndarray
    radii: np.ndarray
    vertices: np.ndarray
    kind: str
    square_root: bool = False


def linear_rose(angles, delta: int = 10, *, lengths=None) -> HistoricalRose:
    angles = np.asarray(angles, float)
    if isinstance(delta, bool) or not isinstance(delta, int) or delta < 1 or 360 % delta \
            or angles.ndim != 1 or not len(angles) or not np.isfinite(angles).all():
        raise ValueError('Linear rose needs finite angles and a positive integer divisor of 360.')
    edges = np.arange(0, 361, delta, dtype=float)
    membership = histcount_indices(angles, edges)
    valid = membership >= 0
    weights = None if lengths is None else np.asarray(lengths, float)
    if weights is not None and (weights.shape != angles.shape or not np.isfinite(weights).all()
                                or np.any(weights <= 0)):
        raise ValueError('Rose lengths must be finite positive values matching the angles.')
    counts = np.bincount(membership[valid], minlength=len(edges) - 1).astype(float)
    values = counts if weights is None else np.bincount(membership[valid], weights=weights[valid],
                                                       minlength=len(edges) - 1)
    theta = np.r_[np.column_stack((edges[:-1], edges[1:])).ravel(), [0., 0.]]
    radii = np.r_[np.repeat(values, 2), [0., 0.]]
    vertices = np.column_stack((radii * sind(theta), radii * cosd(theta)))
    return HistoricalRose(readonly(edges), readonly(counts), readonly(radii), readonly(vertices), 'linear')


def historical_rose(angles, bins: int = 18, *, axial=False, square_root=False) -> HistoricalRose:
    values = np.asarray(angles, float)
    if values.ndim != 1 or not len(values) or not np.isfinite(values).all() \
            or isinstance(bins, bool) or not isinstance(bins, int) or bins < 2:
        raise ValueError('Historical rose needs finite angles and at least two classes.')
    if axial:
        values = np.where(values > 179.99, values - 180, values)
        values = np.r_[values, values + 180]
    centres = np.arange(bins) * 360 / bins + 180 / bins
    membership = np.searchsorted(centres, values, side='right') - 1
    valid = (membership >= 0) & ((values < centres[-1]) | (values == centres[-1]))
    counts = np.bincount(membership[valid], minlength=bins).astype(float)
    radii = np.sqrt(counts) if square_root else counts.copy()
    edges = np.linspace(0, 360, bins + 1)
    vertices = np.column_stack((np.repeat(radii, 2) * sind(np.column_stack((edges[:-1], edges[1:])).ravel()),
                                np.repeat(radii, 2) * cosd(np.column_stack((edges[:-1], edges[1:])).ravel())))
    return HistoricalRose(readonly(edges), readonly(counts), readonly(radii), readonly(vertices), 'historical', square_root)
