"""Numerical conventions of the supplied MATLAB sources (not NumPy defaults)."""

import numpy as np
from numpy.typing import ArrayLike, NDArray


def readonly(values: ArrayLike) -> NDArray[np.float64]:
    result = np.array(values, dtype=np.float64, copy=True)
    result.setflags(write=False)
    return result


def matlab_round(values: ArrayLike) -> NDArray[np.float64]:
    values = np.asarray(values, dtype=np.float64)
    return np.copysign(np.floor(np.abs(values) + .5), values)


def sind(values: ArrayLike) -> NDArray[np.float64]:
    values = np.asarray(values, dtype=np.float64)
    result = np.sin(np.deg2rad(values))
    # MATLAB degree trigonometry returns exact zeros at multiples of 180.
    return np.where(np.remainder(values, 180) == 0, 0., result)


def cosd(values: ArrayLike) -> NDArray[np.float64]:
    return sind(np.asarray(values, dtype=np.float64) + 90)


def double_angles(raw: ArrayLike, north: float, flip_x: bool = False,
                  flip_y: bool = False) -> NDArray[np.float64]:
    axial = matlab_round(np.asarray(raw) - north)
    angles = np.concatenate((axial, axial + 180))
    angles = np.where(angles < 0, angles + 360, angles)
    for flip in (flip_x, flip_y):
        if flip:
            angles = 180 - angles
            angles = np.where(angles < 0, angles + 360, angles)
    return readonly(angles)


def strike_indices(raw: ArrayLike, north: float, flip_x: bool = False,
                   flip_y: bool = False) -> NDArray[np.int64]:
    angles = matlab_round(np.asarray(raw) - north)
    for flip in (flip_y, flip_x):
        if flip:
            angles = 180 - angles
    angles = np.where(angles < 0, angles + 360, angles)
    angles = np.where(angles > 180, angles - 180, angles)
    angles = np.where(angles > 180, angles - 180, angles)
    angles = np.where(angles < 1, 180, angles)
    result = angles.astype(np.int64) - 1
    result.setflags(write=False)
    return result


def hist_centres(samples: ArrayLike, centres: ArrayLike) -> NDArray[np.int64]:
    """MATLAB hist: tails included, midpoint ties assigned to the lower bin."""
    centres = np.asarray(centres, dtype=np.float64)
    if centres.ndim != 1 or len(centres) < 2 or not np.isfinite(centres).all() \
            or not np.all(np.diff(centres) > 0):
        raise ValueError('Histogram centres must be finite and increasing.')
    samples = np.asarray(samples, dtype=np.float64).ravel()
    samples = samples[~np.isnan(samples)]
    middle = centres[:-1] / 2 + centres[1:] / 2
    return np.bincount(np.searchsorted(middle, samples, side='left'),
                       minlength=len(centres))


def hist_auto(samples: ArrayLike, bins: int = 20):
    """MATLAB ``hist(values, bins)`` centres and counts, including constants.

    Scalar bin counts divide the observed range into equal intervals; they
    do not put the first and last centres on the observed extrema.
    """
    values=np.asarray(samples,dtype=np.float64).ravel()
    if isinstance(bins,bool) or not isinstance(bins,(int,np.integer)) or bins<2:
        raise ValueError('Histogram bin count must be an integer of at least two.')
    finite=values[np.isfinite(values)]
    if not finite.size:
        raise ValueError('Automatic histogram needs at least one finite value.')
    low,high=float(finite.min()),float(finite.max())
    if low==high:
        centres=low+np.arange(bins)-bins//2
    else:
        step=(high-low)/bins
        centres=low+step*(np.arange(bins)+.5)
    return readonly(centres),hist_centres(values,centres)


def histcount_indices(samples: ArrayLike, edges: ArrayLike) -> NDArray[np.int64]:
    """Zero-based histcounts membership; -1 outside, last edge included."""
    samples, edges = np.asarray(samples), np.asarray(edges)
    bins = np.searchsorted(edges, samples, side='right') - 1
    bins = np.where(samples == edges[-1], len(edges) - 2, bins)
    return np.where((samples < edges[0]) | (samples > edges[-1])
                    | ~np.isfinite(samples), -1, bins)
