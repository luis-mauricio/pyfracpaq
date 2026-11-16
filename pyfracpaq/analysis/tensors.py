"""Oda crack tensors and parallel-plate permeability in source pole conventions.

Derived from FracPaQ's getF2/4/8tensor and guiFracPaQ2Dtensor (Healy,
FracPaQ MIT). Computation is independent of graphics and never rewrites data.
"""

from collections.abc import Callable
from dataclasses import dataclass
import logging

import numpy as np
from numpy.typing import ArrayLike, NDArray

from pyfracpaq.analysis.compatibility import cosd, matlab_round, readonly, sind
from pyfracpaq.domain import Dataset
from pyfracpaq.domain.execution import FieldError, RunContext
from pyfracpaq.geometry import GeometryError
from pyfracpaq.geometry.primitives import DEFAULT_MEMORY_LIMIT

Progress = Callable[[int, str], None]
Interrupted = Callable[[], bool]
LOG = logging.getLogger(__name__)


def _inputs(lengths: ArrayLike, poles: ArrayLike, area: float) -> tuple:
    lengths, poles = np.asarray(lengths, dtype=float), np.asarray(poles, dtype=float)
    if lengths.ndim != 1 or not len(lengths) or poles.shape != lengths.shape \
            or not np.isfinite(lengths).all() or not np.isfinite(poles).all() \
            or np.any(lengths <= 0):
        raise ValueError('Tensors require matching finite poles and positive lengths.')
    if not np.isfinite(area) or area <= 0:
        raise GeometryError('Tensors require a positive two-dimensional trace envelope.')
    if len(lengths) * 128 > DEFAULT_MEMORY_LIMIT:
        raise MemoryError('Tensor inputs exceed the 256 MiB working memory budget.')
    return lengths, poles


def trace_envelope_area(dataset: Dataset) -> float:
    """getMapLimits' trace envelope, independently of a raster's canvas bounds."""
    if dataset.source_bounds is None:
        area = dataset.area
    else:
        width = max(n.x for n in dataset.nodes) - min(n.x for n in dataset.nodes)
        height = max(n.y for n in dataset.nodes) - min(n.y for n in dataset.nodes)
        area = width * height
    if not np.isfinite(area) or area <= 0:
        raise GeometryError('Tensors require a positive two-dimensional trace envelope.')
    return area


def _reverse(values: NDArray, flip_x: bool, flip_y: bool) -> NDArray:
    for flip in (flip_x, flip_y):
        if flip:
            values = 180 - values
            values = np.where(values < 0, values + 360, values)
    return values


def crack_poles(raw: ArrayLike, north: float, flip_x: bool, flip_y: bool) -> NDArray:
    # Crack tensors round the poles before applying the two reverseAxis calls.
    return readonly(_reverse(matlab_round(np.asarray(raw) + 90 - north), flip_x, flip_y))


def permeability_poles(raw: ArrayLike, north: float, flip_x: bool, flip_y: bool) -> NDArray:
    # Permeability reverses unrounded strikes first, then adds 90 - north.
    return readonly(_reverse(np.asarray(raw, dtype=float), flip_x, flip_y) + 90 - north)


@dataclass(frozen=True, slots=True)
class TensorRank:
    order: int
    components: NDArray[np.float64]
    polar: NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class CrackTensorResult:
    lengths: NDArray[np.float64]
    poles: NDArray[np.float64]
    area: float
    alpha: NDArray[np.float64]
    zero: NDArray[np.float64]
    ranks: tuple[TensorRank, ...]


def crack_tensors(lengths: ArrayLike, poles: ArrayLike, area: float, *,
                  progress: Progress = lambda *_: None,
                  interrupted: Interrupted = lambda: False) -> CrackTensorResult:
    lengths, poles = _inputs(lengths, poles, area)
    alpha = np.linspace(0, 2 * np.pi, 361)
    with np.errstate(over='ignore', invalid='ignore'):
        weights = (lengths / np.sqrt(area)) ** 2
    if not np.isfinite(weights).all() or not np.isfinite(weights.sum()):
        raise ValueError('Crack tensor weights exceed float64 range.')
    n = np.column_stack((cosd(poles), sind(poles)))
    directions = np.column_stack((np.cos(alpha), np.sin(alpha)))
    ranks = []
    for index, order in enumerate((2, 4, 8)):
        if interrupted():
            raise InterruptedError('Crack tensors cancelled.')
        # Only order+1 distinct moments are needed for the symmetric tensor;
        # no per-segment N x 2^order tensor is allocated.
        moments = np.array([np.sum(weights * n[:, 0] ** (order - k) * n[:, 1] ** k)
                            for k in range(order + 1)])
        components = np.empty((2,) * order)
        for indices in np.ndindex(components.shape):
            components[indices] = moments[sum(indices)]
        polar = np.zeros_like(alpha)
        for start in range(0, len(lengths), 1024):
            if interrupted():
                raise InterruptedError('Crack tensor projection cancelled.')
            stop = start + 1024
            polar += weights[start:stop] @ (n[start:stop] @ directions.T) ** order
            progress(round((index + min(stop, len(lengths)) / len(lengths)) / 3 * 100),
                     f'Projecting crack tensor of order {order}...')
        if not np.isfinite(components).all() or not np.isfinite(polar).all():
            raise ValueError('Crack tensor projection exceeds float64 range.')
        ranks.append(TensorRank(order, readonly(components), readonly(polar)))
    return CrackTensorResult(readonly(lengths), readonly(poles), float(area), readonly(alpha),
                             readonly(np.full(361, weights.sum())), tuple(ranks))


def compute_crack_tensor(dataset: Dataset, context: RunContext, progress: Progress, *,
                         interrupted: Interrupted = lambda: False) -> CrackTensorResult:
    if dataset.n_segments * 1024 > DEFAULT_MEMORY_LIMIT:
        raise MemoryError('Crack tensor working data exceed the 256 MiB memory budget.')
    config, arrays = context.config, dataset.as_arrays()
    result = crack_tensors(arrays.segment_lengths,
                           crack_poles(arrays.raw_angles, float(config.value('edit_degfromnorth')),
                                       config.flip_x, config.flip_y),
                           trace_envelope_area(dataset), progress=progress, interrupted=interrupted)
    LOG.info('Crack tensors 0/2/4/8: %d segments; trace-envelope area=%g %s; F0=%g',
             len(result.lengths), result.area, dataset.area_unit, result.zero[0])
    return result


@dataclass(frozen=True, slots=True)
class PermeabilityResult:
    lengths: NDArray[np.float64]
    poles: NDArray[np.float64]
    apertures: NDArray[np.float64]
    area: float
    lambda_factor: float
    p: NDArray[np.float64]
    k: NDArray[np.float64]
    eigenvalues: NDArray[np.float64]
    alpha: NDArray[np.float64]
    polar: NDArray[np.float64]
    unit: str


def permeability_tensor(lengths: ArrayLike, poles: ArrayLike, area: float,
                        apertures: ArrayLike, lambda_factor: float, *, unit: str = 'pixels^2',
                        interrupted: Interrupted = lambda: False) -> PermeabilityResult:
    lengths, poles = _inputs(lengths, poles, area)
    apertures = np.asarray(apertures, dtype=float)
    if apertures.shape != lengths.shape or not np.isfinite(apertures).all() \
            or np.any(apertures < 0):
        raise ValueError('Apertures must be matching finite nonnegative values.')
    if not np.isfinite(lambda_factor) or not 0 <= lambda_factor <= 1:
        raise ValueError('Lambda must be between zero and one.')
    n = np.column_stack((cosd(poles), sind(poles)))
    p = np.zeros((2, 2))
    for start in range(0, len(lengths), 4096):
        if interrupted():
            raise InterruptedError('Permeability tensor cancelled.')
        stop = start + 4096
        with np.errstate(over='ignore', invalid='ignore'):
            weights = apertures[start:stop] ** 3 * lengths[start:stop] / area
            p += n[start:stop].T @ (weights[:, None] * n[start:stop])
    # Independent reductions can differ by an ulp. Store an exactly symmetric P.
    p[1, 0] = p[0, 1]
    with np.errstate(over='ignore', invalid='ignore'):
        k = lambda_factor / 12 * (np.trace(p) * np.eye(2) - p)
    if not np.isfinite(p).all() or not np.isfinite(k).all():
        raise ValueError('Permeability tensor exceeds float64 range.')
    alpha = np.linspace(0, 2 * np.pi, 361)
    v = np.column_stack((np.cos(alpha), np.sin(alpha)))
    polar = np.einsum('ni,ij,nj->n', v, k, v)
    return PermeabilityResult(readonly(lengths), readonly(poles), readonly(apertures), float(area),
                              float(lambda_factor), readonly(p), readonly(k),
                              readonly(np.linalg.eigvalsh(k)), readonly(alpha), readonly(polar), unit)


def compute_permeability(dataset: Dataset, context: RunContext, progress: Progress, *,
                         interrupted: Interrupted = lambda: False) -> PermeabilityResult:
    if dataset.n_segments * 512 > DEFAULT_MEMORY_LIMIT:
        raise MemoryError('Permeability working data exceed the 256 MiB memory budget.')
    config, arrays = context.config, dataset.as_arrays()
    if config.value('radiobutton_fixedaperture'):
        field = 'edit_fixedaperture'
        apertures = np.full(dataset.n_segments, float(config.value(field)))
    else:
        field = 'edit_aperturefactor'
        with np.errstate(over='ignore', invalid='ignore'):
            apertures = float(config.value(field)) * arrays.segment_lengths ** float(
                config.value('edit_apertureexponent'))
    progress(10, 'Calculating parallel-plate permeability...')
    try:
        area = trace_envelope_area(dataset)
    except GeometryError as error:
        raise FieldError('checkbox_permellipse', str(error)) from error
    try:
        result = permeability_tensor(
            arrays.segment_lengths, permeability_poles(arrays.raw_angles,
                float(config.value('edit_degfromnorth')), config.flip_x, config.flip_y),
            area, apertures, float(config.value('edit_lambda')),
            unit=dataset.permeability_unit, interrupted=interrupted)
    except ValueError as error:
        raise FieldError(field, str(error)) from error
    LOG.info('Permeability trace-envelope area=%g %s; lambda=%g',
             result.area, dataset.area_unit, result.lambda_factor)
    LOG.info('Maximum permeability = %.5g %s', result.eigenvalues[-1], result.unit)
    LOG.info('Minimum permeability = %.5g %s', result.eigenvalues[0], result.unit)
    progress(100, 'Permeability completed.')
    return result
