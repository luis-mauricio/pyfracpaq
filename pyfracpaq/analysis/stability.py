"""Shared fracture stresses, stability fields and 10-degree equal-area roses.

Q-17 correction approved by the user on 2026-11-14: segment stresses define the common
normalizations; colour indices saturate to their palettes; CSF includes equality
in both maps and rose bins.
Equations derive from Healy/FracPaQ's tracemap, Mohr and tendency-rose routines.
"""

from collections.abc import Callable
from dataclasses import dataclass
import logging

import numpy as np
from numpy.typing import ArrayLike, NDArray

from pyfracpaq.analysis.angles import RoseData, equal_area_rose
from pyfracpaq.analysis.compatibility import (
    cosd, double_angles, matlab_round, readonly, sind, strike_indices,
)
from pyfracpaq.domain import Dataset
from pyfracpaq.domain.execution import AnalysisConfig, FieldError, RunContext
from pyfracpaq.geometry.primitives import DEFAULT_MEMORY_LIMIT

KINDS = {'MAP-11': 'slip', 'MAP-12': 'dilation', 'MAP-13': 'susceptibility', 'MAP-14': 'csf'}
LOG = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class StressParameters:
    sigma1: float
    sigma2: float
    theta: float
    cohesion: float
    pore_pressure: float
    friction: float

    def validate(self, kinds: tuple[str, ...]) -> None:
        for field, value in (('edit_sigma1', self.sigma1), ('edit_sigma2', self.sigma2)):
            if not np.isfinite(value) or value < 1e-8:
                raise FieldError(field, 'Use positive compressive principal stresses (at least 1e-8 MPa).')
        if self.sigma1 < self.sigma2:
            raise FieldError('edit_sigma2', 'Sigma 2 must be no greater than Sigma 1.')
        if not np.isfinite(self.theta) or not 0 <= self.theta <= 180:
            raise FieldError('edit_thetasigma1', 'The principal stress azimuth must be between 0 and 180 degrees.')
        for field, value in (('edit_C0', self.cohesion), ('edit_Pf', self.pore_pressure),
                             ('edit_mu', self.friction)):
            if not np.isfinite(value) or value < 0:
                raise FieldError(field, 'Use a finite nonnegative parameter.')
        if 'susceptibility' in kinds and self.friction == 0:
            raise FieldError('edit_mu', 'Fracture susceptibility requires a positive friction coefficient.')
        if 'dilation' in kinds and self.sigma1 == self.sigma2:
            raise FieldError('edit_sigma2', 'Dilation tendency is undefined when Sigma 1 equals Sigma 2.')


def parameters_from_config(config: AnalysisConfig) -> StressParameters:
    parameters = StressParameters(*(float(config.value(name)) for name in (
        'edit_sigma1', 'edit_sigma2', 'edit_thetasigma1', 'edit_C0', 'edit_Pf', 'edit_mu')))
    parameters.validate(tuple(KINDS[key] for key in KINDS if key in config.selected))
    return parameters


def normal_shear(strikes: ArrayLike, parameters: StressParameters) -> tuple[NDArray, NDArray]:
    pole = np.asarray(strikes, dtype=float) + 90 - parameters.theta
    mean = parameters.sigma1 / 2 + parameters.sigma2 / 2
    half = parameters.sigma1 / 2 - parameters.sigma2 / 2
    return (readonly(np.abs(mean + half * cosd(2 * pole))),
            readonly(np.abs(-half * sind(2 * pole))))


def colour_indices(normalized: ArrayLike, levels: int) -> NDArray[np.int64]:
    values = np.asarray(normalized, dtype=float)
    if not np.isfinite(values).all():
        raise ValueError('Stability colour values must be finite.')
    indices = np.clip(matlab_round(np.clip(values, 0, 1) * levels), 1, levels).astype(np.int64) - 1
    indices.setflags(write=False)
    return indices


@dataclass(frozen=True, slots=True)
class StabilityField:
    kind: str
    values: NDArray[np.float64]
    normalized: NDArray[np.float64]
    rose_values: NDArray[np.float64]
    rose_normalized: NDArray[np.float64]
    colour_range: tuple[float, float]
    map_indices: NDArray[np.int64]
    rose_indices: NDArray[np.int64]


@dataclass(frozen=True, slots=True)
class MohrData:
    normal: NDArray[np.float64]
    effective_normal: NDArray[np.float64]
    shear: NDArray[np.float64]


def mohr_circle(parameters: StressParameters) -> MohrData:
    theta = np.arange(361, dtype=float)
    half = parameters.sigma1 / 2 - parameters.sigma2 / 2
    normal = parameters.sigma1 / 2 + parameters.sigma2 / 2 + half * cosd(2 * theta)
    return MohrData(readonly(normal), readonly(normal - parameters.pore_pressure),
                     readonly(half * sind(2 * theta)))


@dataclass(frozen=True, slots=True)
class StabilityResult:
    dataset: Dataset
    parameters: StressParameters
    strikes: NDArray[np.float64]
    normal_stress: NDArray[np.float64]
    shear_stress: NDArray[np.float64]
    doubled_angles: NDArray[np.float64]
    rose: RoseData
    fields: tuple[StabilityField, ...]
    mohr: MohrData

    def field(self, kind: str) -> StabilityField:
        return next(field for field in self.fields if field.kind == kind)


def stability_fields(dataset: Dataset, parameters: StressParameters, *,
                      kinds: tuple[str, ...] = tuple(KINDS.values()), north: float = 0,
                      flip_x: bool = False, flip_y: bool = False,
                      progress: Callable[[int, str], None] = lambda *_: None,
                      interrupted: Callable[[], bool] = lambda: False) -> StabilityResult:
    if not kinds or len(set(kinds)) != len(kinds) or set(kinds) - set(KINDS.values()):
        raise ValueError('Select distinct known stability fields.')
    parameters.validate(kinds)
    if not np.isfinite(north) or not -360 <= north <= 360:
        raise FieldError('edit_degfromnorth', 'North correction must be between -360 and 360 degrees.')
    if dataset.n_segments * 512 > DEFAULT_MEMORY_LIMIT:
        raise MemoryError('Stability fields exceed the 256 MiB working memory budget.')
    if interrupted():
        raise InterruptedError('Stability cancelled.')
    arrays = dataset.as_arrays()
    strikes = readonly(strike_indices(arrays.raw_angles, north, flip_x, flip_y) + 1)
    sn, tau = normal_shear(strikes, parameters)
    doubled = double_angles(arrays.raw_angles, north, flip_x, flip_y)
    rose = equal_area_rose(doubled, np.ones(len(doubled)), 10)
    sn_mid, tau_mid = normal_shear(np.arange(5, 360, 10), parameters)
    fields = []
    for index, kind in enumerate(kinds):
        if interrupted():
            raise InterruptedError('Stability cancelled.')
        with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
            if kind == 'slip':
                values, mid = tau / sn, tau_mid / sn_mid
                maximum = float(values.max())
                normalized = values / maximum if maximum else np.zeros_like(values)
                mid_normalized = mid / maximum if maximum else np.zeros_like(mid)
                bounds = (0., 1.)
            elif kind == 'dilation':
                denominator = parameters.sigma1 - parameters.sigma2
                values = (parameters.sigma1 - sn) / denominator
                mid = (parameters.sigma1 - sn_mid) / denominator
                normalized, mid_normalized, bounds = values, mid, (0., 1.)
            elif kind == 'susceptibility':
                values = sn - parameters.pore_pressure - (tau - parameters.cohesion) / parameters.friction
                mid = sn_mid - parameters.pore_pressure - (tau_mid - parameters.cohesion) / parameters.friction
                low, high = float(values.min()), float(values.max())
                normalized = (values - low) / (high - low) if high > low else np.zeros_like(values)
                mid_normalized = (mid - low) / (high - low) if high > low else np.zeros_like(mid)
                bounds = (low, high)
            else:
                values = (tau >= parameters.friction * (sn - parameters.pore_pressure)
                          + parameters.cohesion).astype(float)
                mid = (tau_mid >= parameters.friction * (sn_mid - parameters.pore_pressure)
                       + parameters.cohesion).astype(float)
                normalized, mid_normalized, bounds = values, mid, (0., 1.)
        if not all(np.isfinite(v).all() for v in (values, normalized, mid, mid_normalized)):
            raise ValueError(f'{kind.capitalize()} values exceed float64 range.')
        # CSF uses the original low/high palette entries, now with one criterion.
        display = .1 + .8 * normalized if kind == 'csf' else normalized
        mid_display = .1 + .8 * mid_normalized if kind == 'csf' else mid_normalized
        fields.append(StabilityField(kind, readonly(values), readonly(normalized), readonly(mid),
                                      readonly(mid_normalized), bounds, colour_indices(display, 100),
                                      colour_indices(mid_display, 19)))
        progress(round(90 * (index + 1) / len(kinds)), f'Calculating {kind}...')
    if np.any((doubled < 0) | (doubled > 360)):
        LOG.warning('Q-10: legacy angular correction leaves values outside [0, 360]; rose excludes them.')
    return StabilityResult(dataset, parameters, strikes, sn, tau, doubled, rose,
                            tuple(fields), mohr_circle(parameters))


def compute_stability(dataset: Dataset, context: RunContext,
                       progress: Callable[[int, str], None], *,
                       interrupted: Callable[[], bool] = lambda: False) -> StabilityResult:
    config = context.config
    result = stability_fields(dataset, parameters_from_config(config),
        kinds=tuple(KINDS[key] for key in KINDS if key in config.selected),
        north=float(config.value('edit_degfromnorth')), flip_x=config.flip_x, flip_y=config.flip_y,
        progress=progress, interrupted=interrupted)
    if interrupted():
        raise InterruptedError('Stability cancelled before export.')
    if 'MAP-11' in config.selected:
        from pyfracpaq.io.stability import export_segmentdata
        export_segmentdata(dataset, config.tag, context.output_directory)
    for field in result.fields:
        LOG.info('%s: %d segments; raw range=[%g, %g]; colour range=%s',
                 field.kind, dataset.n_segments, field.values.min(), field.values.max(), field.colour_range)
    progress(100, 'Stability completed.')
    return result
