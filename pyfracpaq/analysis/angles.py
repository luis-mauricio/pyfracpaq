"""Source-compatible Angles calculations, independent of Qt and Matplotlib."""

from dataclasses import dataclass
from collections.abc import Callable
import logging
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import ArrayLike, NDArray

from pyfracpaq.analysis.compatibility import (
    cosd, double_angles, hist_centres, histcount_indices, readonly, sind,
)
from pyfracpaq.domain import Dataset
from pyfracpaq.domain.execution import RunContext
from pyfracpaq.io.angles import export_ezrose
from pyfracpaq.geometry.primitives import DEFAULT_MEMORY_LIMIT

if TYPE_CHECKING:
    from pyfracpaq.analysis.tensors import CrackTensorResult


@dataclass(frozen=True, slots=True)
class AxialStatistics:
    mean: float
    standard_deviation: float
    resultant: float
    mean_defined: bool


def axial_statistics(angles: ArrayLike) -> AxialStatistics:
    """circStat.m: unweighted first axial half, sqrt(2*(1-R)) deviation."""
    values = np.asarray(angles, dtype=np.float64)
    if values.ndim != 1 or not len(values) or len(values) % 2 \
            or not np.isfinite(values).all():
        raise ValueError('Circular statistics require finite doubled axial angles.')
    values = values[:len(values) // 2]
    v, w = float(cosd(2 * values).sum()), float(sind(2 * values).sum())
    mean = float(np.rad2deg(np.arctan2(w, v)) / 2)
    if mean < 0:
        mean += 180
    resultant = float(np.hypot(v, w) / len(values))
    # Sums of unit vectors can exceed 1 by a rounding ulp, never physically.
    resultant = min(1., resultant)
    return AxialStatistics(mean, float(np.rad2deg(np.sqrt(2 * (1 - resultant)))),
                           resultant, resultant > 0)


@dataclass(frozen=True, slots=True)
class RoseData:
    edges: NDArray[np.float64]
    raw_counts: NDArray[np.float64]
    counts: NDArray[np.float64]
    length_sums: NDArray[np.float64]
    percentages: NDArray[np.float64]
    radii: NDArray[np.float64]
    vertices: NDArray[np.float64]
    limit: float
    weighted: bool


def equal_area_rose(angles: ArrayLike, lengths: ArrayLike, delta: int,
                    *, weighted: bool = False) -> RoseData:
    values, lengths = np.asarray(angles), np.asarray(lengths)
    if delta not in (5, 10, 20, 30):
        raise ValueError('Rose bins must be 5, 10, 20 or 30 degrees.')
    if values.ndim != 1 or not len(values) or lengths.shape != values.shape \
            or not np.isfinite(values).all() or not np.isfinite(lengths).all() \
            or np.any(lengths <= 0):
        raise ValueError('Rose requires matching finite angles and positive lengths.')
    edges = np.arange(0, 361, delta, dtype=np.float64)
    membership = histcount_indices(values, edges)
    valid = membership >= 0
    bins = len(edges) - 1
    raw = np.bincount(membership[valid], minlength=bins).astype(np.float64)
    counts = raw.copy()
    half = bins // 2
    counts[[0, half]] = (raw[0] + raw[half]) / 2
    counts[[half - 1, -1]] = (raw[half - 1] + raw[-1]) / 2
    sums = np.bincount(membership[valid], weights=lengths[valid], minlength=bins)
    # Normalise weights before summing to avoid overflow for valid large lengths.
    scaled = lengths / lengths.max()
    weight_percent = np.bincount(membership[valid], weights=scaled[valid],
                                minlength=bins) / scaled.sum() * 100
    percentages = weight_percent if weighted else counts / len(values) * 100
    # Two trailing zero entries reproduce the source's allocation and closure.
    theta = np.zeros(2 * len(edges))
    theta[:-2:2], theta[1:-2:2] = edges[:-1], edges[1:]
    radii = np.zeros_like(theta)
    radii[:-2] = 50 * np.sqrt(np.repeat(percentages, 2))
    vertices = np.column_stack((radii * sind(theta), radii * cosd(theta)))
    extent = float(vertices.max())
    contours = 50 * np.sqrt([1, 5, 10, 20, 30, 50])
    larger = contours[contours > extent]
    # The original returns an empty limit at an exact 50% cardinal peak.
    limit = float(larger[0] if len(larger) else max(contours[-1], extent))
    return RoseData(*(readonly(v) for v in (edges, raw, counts, sums, percentages,
                                          radii, vertices)), limit, weighted)


@dataclass(frozen=True, slots=True)
class AngularResult:
    angles: NDArray[np.float64]
    lengths: NDArray[np.float64]
    centres: NDArray[np.float64] | None
    frequencies: NDArray[np.float64] | None
    rose: RoseData | None
    statistics: AxialStatistics
    colour: tuple[float, float, float] = (0., 0., 1.)
    crack: 'CrackTensorResult | None' = None


def compute_angles(dataset: Dataset, context: RunContext,
                   progress: Callable[[int, str], None], *,
                   interrupted: Callable[[], bool] = lambda: False) -> AngularResult:
    config = context.config
    if 'FLO-08' in config.selected and dataset.n_segments * 1024 > DEFAULT_MEMORY_LIMIT:
        raise MemoryError('Crack tensor working data exceed the 256 MiB memory budget.')
    arrays = dataset.as_arrays()
    angles = double_angles(arrays.raw_angles, float(config.value('edit_degfromnorth')),
                           config.flip_x, config.flip_y)
    lengths = readonly(np.tile(arrays.segment_lengths, 2))
    centres = frequencies = rose = None
    if 'ANG-01' in config.selected:
        bins = int(config.value('popupmenu_histoanglebins'))
        centres = readonly(np.linspace(0, 360, bins + 1))
        frequencies = readonly(hist_centres(angles, centres))
    if 'ANG-02' in config.selected:
        rose = equal_area_rose(angles, lengths, int(config.value('popupmenu_rosebins')),
                               weighted=bool(config.value('checkbox_roselengthweighted')))
    statistics = axial_statistics(angles)
    logger = logging.getLogger(__name__)
    if np.any((angles < 0) | (angles > 360)):
        logger.warning('Q-10: legacy angular correction leaves values outside '
                       '[0, 360]; histogram includes tails, rose excludes them.')
    if 'ANG-02' in config.selected and config.value('checkbox_showrosemean'):
        logger.info('Circular statistics: mean=%g degrees from North; '
                    'standard deviation=%g degrees; resultant=%g; mean defined=%s',
                    statistics.mean, statistics.standard_deviation,
                    statistics.resultant, statistics.mean_defined)
    crack = None
    if 'FLO-08' in config.selected:
        from pyfracpaq.analysis.tensors import compute_crack_tensor
        crack = compute_crack_tensor(dataset, context, progress, interrupted=interrupted)
    if interrupted():
        raise InterruptedError('Angles cancelled before EZROSE export.')
    export_ezrose(angles, config.tag, context.output_directory)
    return AngularResult(angles, lengths, centres, frequencies, rose, statistics,
                          dataset.traces[0].colour, crack)
