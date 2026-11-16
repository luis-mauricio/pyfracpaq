"""Lengths, censoring and legacy binned distributions without GUI dependencies."""

from collections.abc import Callable
from dataclasses import dataclass, replace
import logging
from math import ceil, floor, fsum
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import ArrayLike, NDArray

from pyfracpaq.analysis.compatibility import double_angles, hist_centres, readonly
from pyfracpaq.domain import Dataset
from pyfracpaq.domain.execution import FieldError, RunContext
from pyfracpaq.io.lengths import export_lengths

LOG = logging.getLogger(__name__)
if TYPE_CHECKING:
    from pyfracpaq.analysis.mle import MleResult
    from pyfracpaq.analysis.blocks import BlockResult
    from pyfracpaq.analysis.variogram import VariogramResult
MAX_CUMULATIVE_CENTRES = 1_000_001


def _frozen(values: ArrayLike, dtype) -> NDArray:
    result = np.array(values, dtype=dtype, copy=True)
    result.setflags(write=False)
    return result


@dataclass(frozen=True, slots=True)
class LengthStatistics:
    count: int
    minimum: float
    maximum: float
    mean: float


def length_statistics(values: ArrayLike) -> LengthStatistics:
    values = _positive_sample(values)
    maximum = float(values.max())
    try:
        mean = fsum(values) / len(values)
    except OverflowError:
        # The standalone API may receive a finite mean with an overflowing sum.
        mean = float(np.mean(values / maximum) * maximum)
    return LengthStatistics(len(values), float(values.min()), maximum, mean)


def _positive_sample(values: ArrayLike) -> NDArray[np.float64]:
    values = np.asarray(values, dtype=np.float64)
    if values.ndim != 1 or not len(values) or not np.isfinite(values).all() \
            or np.any(values <= 0):
        raise ValueError('Lengths require a nonempty sample of finite positive values.')
    return values


@dataclass(frozen=True, slots=True)
class LengthSample:
    trace_keep: NDArray[np.bool_]
    segment_keep: NDArray[np.bool_]
    trace_ids: NDArray[np.int64]
    segment_ids: NDArray[np.int64]
    trace_lengths: NDArray[np.float64]
    segment_lengths: NDArray[np.float64]
    raw_angles: NDArray[np.float64]
    excluded_traces: int
    excluded_segments: int


def select_lengths(dataset: Dataset, *, censor: bool = False) -> LengthSample:
    """Q-05: exclude a whole trace if its first/last node touches any map edge.

    Exact equality follows the source; no new spatial tolerance or snapping.
    The domain is fixed before filtering. All segment fields share one mask.
    """
    keep = np.ones(dataset.n_traces, dtype=bool)
    if censor:
        bounds = dataset.bounds
        for trace in dataset.traces:
            for node in (trace.nodes[0], trace.nodes[-1]):
                if (node.x in (bounds.x_min, bounds.x_max)
                        or node.y in (bounds.y_min, bounds.y_max)):
                    keep[trace.id] = False
                    break
    arrays = dataset.as_arrays()
    segment_keep = keep[arrays.segment_trace_ids]
    return LengthSample(
        _frozen(keep, bool), _frozen(segment_keep, bool),
        _frozen(np.flatnonzero(keep), np.int64),
        _frozen(arrays.segment_ids[segment_keep], np.int64),
        readonly(arrays.trace_lengths[keep]),
        readonly(arrays.segment_lengths[segment_keep]),
        readonly(arrays.raw_angles[segment_keep]),
        int(np.count_nonzero(~keep)), int(np.count_nonzero(~segment_keep)),
    )


@dataclass(frozen=True, slots=True)
class LengthHistogram:
    centres: NDArray[np.float64]
    frequencies: NDArray[np.int64]
    bar_width: float


def _interval_centres(low: float, high: float, intervals: int) -> NDArray:
    """Symmetric construction for min:(max-min)/intervals:max.

    Both endpoints are fixed; native MATLAB endpoint/tie parity is still pending.
    Adjacent centres that collapse in float64 are rejected, never deduplicated.
    """
    step = (high - low) / intervals
    index = np.arange(intervals + 1)
    centres = np.where(index <= intervals / 2, low + index * step,
                       high - (intervals - index) * step)
    if not np.all(np.diff(centres) > 0):
        raise ValueError('Length bin spacing cannot be represented in float64; '
                         'use fewer bins or review the input precision.')
    return centres


def _frequencies(values: NDArray, centres: NDArray) -> NDArray:
    if len(centres) == 1:
        return _frozen([len(values)], np.int64)
    return _frozen(hist_centres(values, centres), np.int64)


def length_histogram(values: ArrayLike, bins: int) -> LengthHistogram:
    values = _positive_sample(values)
    if isinstance(bins, bool) or bins not in (10, 20, 30, 50):
        raise ValueError('Length bins must be 10, 20, 30 or 50.')
    low, high = float(values.min()), float(values.max())
    if low == high:
        # The source's zero colon step is undefined. One populated class keeps
        # every observation without adding jitter or fabricating a range.
        centres = readonly([low])
        width = low * .1
        if width <= 0:
            raise ValueError('Length scale is too small to render a histogram.')
    else:
        centres = readonly(_interval_centres(low, high, bins))
        width = (high - low) / bins
    return LengthHistogram(centres, _frequencies(values, centres), width)


@dataclass(frozen=True, slots=True)
class ComplementaryDistribution:
    centres: NDArray[np.float64]
    frequencies: NDArray[np.int64]
    complementary: NDArray[np.int64]


def complementary_distribution(values: ArrayLike, *, scaled: bool = False,
                               max_centres: int = MAX_CUMULATIVE_CENTRES
                               ) -> ComplementaryDistribution:
    """Legacy N-cumsum(hist): unit pixel centres, or 1000 intervals in metres."""
    values = _positive_sample(values)
    if isinstance(max_centres, bool) or not isinstance(max_centres, int) or max_centres < 1:
        raise ValueError('The cumulative grid limit must be a positive integer.')
    low, high = float(values.min()), float(values.max())
    count = (1 if low == high else 1001 if scaled else floor(high - low) + 1)
    if count > max_centres:
        raise MemoryError(f'The cumulative length grid needs {count} centres; '
                          f'the limit is {max_centres}. Review the input scale.')
    if count == 1:
        centres = np.array([low])
    elif scaled:
        centres = _interval_centres(low, high, 1000)
    else:
        centres = low + np.arange(count, dtype=np.float64)
        if not np.all(np.diff(centres) > 0):
            raise ValueError('Unit pixel bins cannot be represented at this length scale.')
    frequencies = _frequencies(values, centres)
    cumulative = np.cumsum(frequencies, dtype=np.int64)
    return ComplementaryDistribution(readonly(centres), frequencies,
                                      _frozen(len(values) - cumulative, np.int64))


@dataclass(frozen=True, slots=True)
class LengthResult:
    sample: LengthSample
    trace_statistics: LengthStatistics
    segment_statistics: LengthStatistics
    unit: str
    domain_diagonal: float
    maximum_possible_length: float
    trace_histogram: LengthHistogram | None
    segment_histogram: LengthHistogram | None
    trace_complementary: ComplementaryDistribution | None
    segment_complementary: ComplementaryDistribution | None
    cross_angles: NDArray[np.float64] | None
    cross_lengths: NDArray[np.float64] | None
    colour: tuple[float, float, float]
    mle: 'MleResult | None' = None
    blocks: 'BlockResult | None' = None
    variogram: 'VariogramResult | None' = None


def _log_statistics(dataset: Dataset, sample: LengthSample,
                    trace: LengthStatistics, segment: LengthStatistics) -> None:
    LOG.info('Length stats...')
    LOG.info('Total number of traces found: %s', dataset.n_traces)
    LOG.info('Total number of segments found: %s', dataset.n_segments)
    LOG.info('Number of traces excluded (censored): %s', sample.excluded_traces)
    LOG.info('Number of segments excluded (censored): %s', sample.excluded_segments)
    LOG.info('Number of traces retained: %s; segments retained: %s',
             trace.count, segment.count)
    for subject, stats in (('trace', trace), ('segment', segment)):
        for label, value in (('Minimum', stats.minimum), ('Maximum', stats.maximum),
                             ('Average', stats.mean)):
            LOG.info('%s %s length: %8.2f %s', label, subject, value, dataset.length_unit)


def compute_lengths(dataset: Dataset, context: RunContext,
                    progress: Callable[[int, str], None], *,
                    interrupted: Callable[[], bool] = lambda: False,
                    mle_seed: int | None = None) -> LengthResult:
    config = context.config
    sample = select_lengths(dataset, censor=bool(config.value('checkbox_censor')))
    if not len(sample.trace_lengths):
        LOG.info('Length stats: %s traces and %s segments excluded; no retained sample.',
                 sample.excluded_traces, sample.excluded_segments)
        raise FieldError('checkbox_censor', 'Censoring excluded every trace and segment. '
                         'Disable edge censoring or choose a map with interior traces.')
    trace = length_statistics(sample.trace_lengths)
    segment = length_statistics(sample.segment_lengths)
    trace_histogram = segment_histogram = trace_cumulative = segment_cumulative = None
    if any(i in config.selected for i in ('LEN-02', 'LEN-03')):
        bins = int(config.value('popupmenu_histolengthbins'))
        trace_histogram = length_histogram(sample.trace_lengths, bins)
        segment_histogram = length_histogram(sample.segment_lengths, bins)
    if 'LEN-03' in config.selected:
        scaled = dataset.pixels_per_metre is not None
        trace_cumulative = complementary_distribution(sample.trace_lengths, scaled=scaled)
        segment_cumulative = complementary_distribution(sample.segment_lengths, scaled=scaled)
    cross_angles = cross_lengths = None
    if 'LEN-06' in config.selected:
        cross_angles = double_angles(sample.raw_angles,
                                     float(config.value('edit_degfromnorth')),
                                     config.flip_x, config.flip_y)
        cross_lengths = readonly(np.tile(sample.segment_lengths, 2))
        if np.any((cross_angles < 0) | (cross_angles > 360)):
            LOG.warning('Q-10: legacy cross-plot angles outside [0, 360] are preserved '
                        'in the result; the original x limits clip their display.')
    result = LengthResult(sample, trace, segment, dataset.length_unit,
                          dataset.bounds.diagonal, float(ceil(dataset.bounds.diagonal)),
                          trace_histogram, segment_histogram, trace_cumulative,
                          segment_cumulative, cross_angles, cross_lengths,
                          dataset.traces[0].colour)
    # Fail before any TXT if the requested drawing bounds cannot be finite and
    # positive. Never let Matplotlib silently substitute invalid log limits.
    for stats in (trace, segment):
        maximum = (max(stats.maximum, result.maximum_possible_length)
                   if 'LEN-03' in config.selected else stats.maximum)
        if not np.isfinite(maximum * 1.1) or (
                'LEN-03' in config.selected and stats.minimum * .9 <= 0):
            raise FieldError('edit_scaling', 'Length plot limits exceed the float64 '
                             'range. Review the coordinates or pixels/metre scale.')
    _log_statistics(dataset, sample, trace, segment)
    if 'LEN-07' in config.selected:
        from pyfracpaq.analysis.mle import fit_populations
        lower, upper = float(config.value('edit_lc')), float(config.value('edit_uc'))
        try:
            fitted = fit_populations(sample.trace_lengths, sample.segment_lengths,
                                     lower=lower, upper=upper, unit=dataset.length_unit,
                                     seed=mle_seed,
                                     colour=dataset.traces[0].colour,
                                     progress=progress, interrupted=interrupted)
        except ValueError as error:
            field = 'edit_lc' if lower else 'edit_uc' if upper else 'checkbox_mle'
            raise FieldError(field, str(error)) from error
        result = replace(result, mle=fitted)
    if 'LEN-15' in config.selected:
        from pyfracpaq.analysis.variogram import experimental_variogram
        midpoints = dataset.as_arrays().segment_midpoints[sample.segment_keep]
        variogram = experimental_variogram(midpoints, sample.segment_lengths,
            nrbins=30, progress=progress, interrupted=interrupted)
        result = replace(result, variogram=variogram)
        LOG.info('Semivariogram: %d segments, %d pairs, 30 distance classes.',
                 len(midpoints), variogram.pair_count)
    # Q-14 approved: fixed unscaled raster, enclosed components, calibrated areas.
    if 'LEN-13' in config.selected:
        from pyfracpaq.analysis.blocks import compute_blocks
        blocks = compute_blocks(dataset, exclude_border=True,
                                 progress=progress, interrupted=interrupted)
        result = replace(result, blocks=blocks)
        LOG.info('Blocks: %d enclosed components, area in %s.', len(blocks.areas), dataset.area_unit)
    if trace.minimum == trace.maximum or segment.minimum == segment.maximum:
        LOG.info('Constant length sample: using one populated histogram centre.')
    if interrupted():
        raise InterruptedError('Lengths cancelled before export.')
    if result.blocks is not None:
        from pyfracpaq.io.block_raster import export_block_raster
        path = export_block_raster(result.blocks.raster, context.output_directory)
        LOG.info('Saved block raster: %s', path)
    export_lengths(sample.trace_lengths, sample.segment_lengths, sample.raw_angles,
                   config.tag, context.output_directory)
    return result
