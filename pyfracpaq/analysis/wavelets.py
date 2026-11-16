"""Anisotropic 2-D CWT from Powell/Neupauer and Healy/Rizzo (FracPaQ MIT).

Preserves exact padding/crop, real Morlet response, non-centred self convolution,
Mexican Hat's 1/a prefactor, and the source's per-L then per-theta tie order.
"""

from dataclasses import dataclass
import logging
import re

import numpy as np
from scipy.fft import rfft2, irfft2

from pyfracpaq.analysis.compatibility import matlab_round, readonly, hist_auto
from pyfracpaq.domain.execution import FieldError

LOG = logging.getLogger(__name__)
MAX_WAVELET_BYTES = 2 * 1024 ** 3


@dataclass(frozen=True, slots=True)
class WaveletParameters:
    scales: tuple[int, ...]
    factors: tuple[int, ...]
    angular_step: int
    kernel: str

    def __post_init__(self):
        object.__setattr__(self, 'scales', tuple(self.scales))
        object.__setattr__(self, 'factors', tuple(self.factors))
        for name, values in (('a', self.scales), ('L', self.factors)):
            if not values or any(isinstance(v, bool) or not isinstance(v, int) or v < 1 for v in values):
                raise ValueError(f'{name} values must be positive whole numbers.')
        if self.kernel not in ('morlet', 'mexican'):
            raise ValueError('Choose Morlet or Mexican Hat.')
        if isinstance(self.angular_step, bool) or not isinstance(self.angular_step, int) \
                or not 1 <= self.angular_step <= 180 or 180 % self.angular_step:
            raise ValueError('Angular increment must be a positive whole-number divisor of 180 degrees.')

    @property
    def orientations(self):
        return np.deg2rad(np.arange(0, 180, self.angular_step, dtype=float))

    @property
    def ratios(self):
        return 1 / np.asarray(self.factors, dtype=float)


def parse_positive_integers(text: str) -> tuple[int, ...]:
    tokens = text.split()
    if not tokens or any(re.fullmatch(r'\+?[0-9]+', token) is None for token in tokens):
        raise ValueError('Enter a nonempty space-separated list of positive whole numbers.')
    values = tuple(int(token) for token in tokens)
    if any(value < 1 or value > 2_147_483_647 for value in values):
        raise ValueError('List values must be positive whole numbers at most 2147483647.')
    return values


def parameters_from_config(config) -> WaveletParameters:
    values = []
    for field in ('edit_aString', 'edit_LString', 'edit_DegString'):
        try:
            parsed = parse_positive_integers(str(config.value(field)))
            if field == 'edit_DegString' and (len(parsed) != 1 or parsed[0] > 180 or 180 % parsed[0]):
                raise ValueError('Angular increment must be a whole-number divisor of 180 degrees.')
            values.append(parsed)
        except ValueError as error:
            raise FieldError(field, str(error)) from error
    return WaveletParameters(values[0], values[1], values[2][0],
                             'morlet' if config.value('radiobutton_Morlet') else 'mexican')


def wavelet_kernel(x, y, scale: float, orientation: float, ratio: float, kind: str):
    if not np.isfinite([scale, orientation, ratio]).all() or scale <= 0 or ratio <= 0 \
            or kind not in ('morlet', 'mexican'):
        raise ValueError('Kernel needs finite orientation and positive scale/ratio.')
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.ndim != 1 or y.ndim != 1 or not len(x) or not len(y) \
            or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError('Kernel axes must be finite nonempty vectors.')
    if len(x) * len(y) * 96 > MAX_WAVELET_BYTES:
        raise MemoryError('Wavelet kernel exceeds its memory budget.')
    xf, yf = np.meshgrid(x, y)
    xx = np.cos(orientation) * xf + np.sin(orientation) * yf
    yy = -np.sin(orientation) * xf + np.cos(orientation) * yf
    squared = (ratio * xx) ** 2 + yy ** 2
    gaussian = np.exp(-squared / 2)
    if kind == 'morlet':
        return np.sqrt(ratio) / scale * np.exp(-2j * np.pi * yy) * gaussian
    return (2 - squared) * gaussian / scale


@dataclass(frozen=True, slots=True)
class CwtResponse:
    coefficients: np.ndarray
    eta: float
    self_coefficients: np.ndarray
    self_eta: float


def cwt2(data, scale: float, orientation: float, ratio: float, kind: str = 'morlet',
         *, x=None, y=None, max_bytes=MAX_WAVELET_BYTES) -> CwtResponse:
    data = np.asarray(data, float)
    if data.ndim != 2 or min(data.shape) < 2 or not np.isfinite(data).all():
        raise ValueError('CWT requires a finite image at least 2 by 2.')
    ny, nx = data.shape
    padded = (2 * ny - 1, 2 * nx - 1)
    if np.prod(padded, dtype=object) * 48 + data.size * 80 > max_bytes:
        raise MemoryError('Wavelet FFT working set exceeds its memory budget.')
    x = np.arange(1, nx + 1, dtype=float) if x is None else np.asarray(x, float)
    y = np.arange(1, ny + 1, dtype=float) if y is None else np.asarray(y, float)
    if x.shape != (nx,) or y.shape != (ny,) or not np.isfinite(x).all() or not np.isfinite(y).all() \
            or not np.allclose(np.diff(x), x[1] - x[0]) or not np.allclose(np.diff(y), y[1] - y[0]) \
            or x[1] == x[0] or y[1] == y[0]:
        raise ValueError('CWT axes must be finite regular vectors matching the image.')
    midx, midy = (nx - 1) // 2, (ny - 1) // 2
    kernel = wavelet_kernel(-(x - x[midx]) / scale, -(y - y[midy]) / scale,
                            scale, orientation, ratio, kind)
    spacing = abs(x[1] - x[0]) * abs(y[1] - y[0])
    crop = np.s_[midy:midy + ny, midx:midx + nx]
    ffft = rfft2(data - data.mean(), s=padded)
    gfft = rfft2(kernel.real, s=padded)
    product = ffft * gfft
    wc = irfft2(product, s=padded, overwrite_x=True)[crop].copy() * spacing
    del product, ffft
    # real((gr+i gi)*(gr+i gi)) = gr*gr - gi*gi; no loss of complex self term.
    gfft *= gfft
    self_wc = irfft2(gfft, s=padded, overwrite_x=True)[crop].copy()
    del gfft
    if kind == 'morlet':
        imaginary = rfft2(kernel.imag, s=padded)
        imaginary *= imaginary
        self_wc -= irfft2(imaginary, s=padded, overwrite_x=True)[crop]
    self_wc *= spacing
    if not np.isfinite(wc).all() or not np.isfinite(self_wc).all():
        raise ValueError('Wavelet response exceeds float64 range.')
    return CwtResponse(readonly(wc), float(np.sum(wc ** 2)), readonly(self_wc),
                        float(np.sum(self_wc ** 2)))


@dataclass(frozen=True, slots=True)
class WaveletScale:
    scale: int
    coefficients: np.ndarray
    optimum_theta: np.ndarray
    optimum_ratio: np.ndarray
    selected: np.ndarray
    doubled_degrees: np.ndarray
    histogram_centres: np.ndarray
    histogram_counts: np.ndarray
    eta: np.ndarray
    self_eta: np.ndarray
    threshold: float


@dataclass(frozen=True, slots=True)
class WaveletResult:
    image: np.ndarray
    parameters: WaveletParameters
    scales: tuple[WaveletScale, ...]
    colour: tuple[float, float, float] = (0., 0., 1.)


def analyse_wavelet_image(image, parameters: WaveletParameters, *, flip_x=False, flip_y=False,
                           progress=lambda *_: None, interrupted=lambda: False) -> WaveletResult:
    image = np.asarray(image, dtype=float)
    if image.ndim != 2 or min(image.shape) < 2 or not np.isfinite(image).all() \
            or np.any((image < 0) | (image > 1)):
        raise ValueError('Wavelet image must be finite and normalized to [0, 1].')
    ny, nx = image.shape
    estimate = (2 * ny - 1) * (2 * nx - 1) * 48 + image.size * (80 + 64 * len(parameters.scales))
    if estimate > MAX_WAVELET_BYTES:
        raise MemoryError('Wavelet scale results exceed the memory budget.')
    total = len(parameters.scales) * len(parameters.orientations) * len(parameters.factors)
    if total * 32 > MAX_WAVELET_BYTES:
        raise MemoryError('Wavelet orientation/anisotropy metadata exceed the memory budget.')
    results, completed = [], 0
    LOG.info('Started Wavelet analysis: image width=%d, height=%d; coordinates in pixels, no north correction.',
             image.shape[1], image.shape[0])
    for scale in parameters.scales:
        best = np.full(image.shape, -np.inf)
        best_theta, best_ratio = np.zeros(image.shape), np.zeros(image.shape)
        energies = np.zeros((len(parameters.orientations), len(parameters.factors)))
        self_energies = np.zeros_like(energies)
        for ti, theta in enumerate(parameters.orientations):
            for li, ratio in enumerate(parameters.ratios):
                if interrupted():
                    raise InterruptedError('Wavelet analysis cancelled.')
                response = cwt2(image, scale, theta, ratio, parameters.kernel)
                denominator = float(np.max(np.abs(response.self_coefficients)))
                if denominator == 0:
                    raise ValueError('Wavelet self response is zero at this scale; review a/L.')
                normalized = np.abs(response.coefficients / scale / denominator) * 2.5
                # theta outer/L inner matches max(L) followed by max(theta), first ties.
                # Q-12 approved: stable first-choice orientation for numerical
                # ties (notably isotropic L=1); retain the actual maximum WC.
                better = (normalized > best) & ~np.isclose(normalized, best, rtol=1e-12, atol=1e-14)
                best_theta[better], best_ratio[better] = theta, ratio
                np.maximum(best, normalized, out=best)
                energies[ti, li], self_energies[ti, li] = response.eta, response.self_eta
                completed += 1
                progress(round(completed / total * 100), f'Wavelet a={scale}, theta={np.rad2deg(theta):g}, L={1/ratio:g}...')
        threshold = float(best.max() * .5)
        selected = best > threshold
        angles = matlab_round(np.rad2deg(best_theta.ravel(order='F')[selected.ravel(order='F')]))
        doubled = np.r_[angles, angles + 180] - 90
        doubled[doubled < 0] += 360
        for flip in (flip_x, flip_y):
            if flip:
                doubled = 180 - doubled
                doubled[doubled < 0] += 360
        centres, counts = hist_auto(best.ravel(order='F'), 20)
        selected.setflags(write=False)
        results.append(WaveletScale(scale, readonly(best), readonly(best_theta), readonly(best_ratio),
            selected, readonly(doubled), readonly(centres), readonly(counts), readonly(energies),
            readonly(self_energies), threshold))
        LOG.info('Wavelet a=%s: maximum WC=%g, 50%% threshold=%g, selected=%d.',
                 scale, best.max(), threshold, int(selected.sum()))
    LOG.info('Finished Wavelet analysis.')
    return WaveletResult(readonly(image), parameters, tuple(results))


def compute_wavelets(dataset, context, progress, *, interrupted=lambda: False):
    from pyfracpaq.io.wavelets import rasterize_wavelets, normalize_raster, export_wavelets

    parameters = parameters_from_config(context.config)
    if interrupted():
        raise InterruptedError('Wavelet raster cancelled.')
    progress(0, 'Rasterizing traces at 72 dpi...')
    raster = rasterize_wavelets(dataset)
    result = analyse_wavelet_image(normalize_raster(raster), parameters,
        flip_x=context.config.flip_x, flip_y=context.config.flip_y,
        progress=progress, interrupted=interrupted)
    if interrupted():
        raise InterruptedError('Wavelets cancelled before export.')
    export_wavelets(result, context.config.tag, context.output_directory, raster=raster)
    return result
