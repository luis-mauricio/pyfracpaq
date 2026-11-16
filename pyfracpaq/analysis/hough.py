"""Deterministic standard Hough transform with explicit MATLAB conventions.

Native MATLAB accumulator/peaks/endpoints are checked by the Sprint16 audit.
No random or probabilistic line detector is used. Internal pixels are zero-based; returned
endpoints are one-based (x, y), as MATLAB image coordinates.
"""

from collections.abc import Callable
from dataclasses import dataclass
from math import ceil, cos, hypot, isfinite, pi, sin

import numpy as np
from numpy.typing import NDArray
from scipy.ndimage import convolve

from pyfracpaq.analysis.compatibility import matlab_round, readonly
from pyfracpaq.domain.execution import FieldError
from pyfracpaq.geometry.primitives import DEFAULT_MEMORY_LIMIT

Progress = Callable[[int, str], None]


def freeze(values, dtype) -> NDArray:
    result = np.array(values, dtype=dtype, copy=True)
    result.setflags(write=False)
    return result


@dataclass(frozen=True, slots=True)
class HoughParameters:
    peaks: int = 1000
    threshold: float = .33
    fill_gap: float = 5.
    min_length: float = 3.

    def __post_init__(self) -> None:
        if isinstance(self.peaks, bool) or not isinstance(self.peaks, int) \
                or not 1 <= self.peaks <= 5000:
            raise FieldError('edit_houghpeaks', 'Hough peaks must be an integer from 1 to 5000.')
        if not isfinite(self.threshold) or not 0 < self.threshold <= 1:
            raise FieldError('edit_houghthreshold', 'Hough threshold must be > 0 and <= 1.')
        for name, value in (('edit_fillgap', self.fill_gap), ('edit_minlength', self.min_length)):
            if not isfinite(value) or value <= 1:
                raise FieldError(name, 'The distance must be a finite number greater than 1 pixel.')


def parameters_from_controls(values: tuple[tuple[str, str], ...]) -> HoughParameters:
    from pyfracpaq.analysis.registry import NUMERIC_TEXT

    fields = dict(values)
    numbers = {}
    for field in ('edit_houghpeaks', 'edit_houghthreshold', 'edit_fillgap', 'edit_minlength'):
        text = fields[field].strip()
        if NUMERIC_TEXT.fullmatch(text) is None:
            raise FieldError(field, 'Enter a valid finite numeric value.')
        value = float(text)
        if not isfinite(value):
            raise FieldError(field, 'Enter a valid finite numeric value.')
        numbers[field] = value
    peaks = numbers['edit_houghpeaks']
    if not peaks.is_integer() or not 100 <= peaks <= 5000:
        raise FieldError('edit_houghpeaks', 'Hough peaks must be a whole number, 100-5000.')
    return HoughParameters(int(peaks), numbers['edit_houghthreshold'],
                           numbers['edit_fillgap'], numbers['edit_minlength'])


def clean_complement(image: NDArray[np.uint8]) -> NDArray[np.bool_]:
    if image.ndim != 2 or image.dtype != np.uint8:
        raise ValueError('Hough input must be a 2-D uint8 grayscale image.')
    binary = image != 255  # imcomplement(uint8), followed by numeric-to-logical.
    neighbours = np.ones((3, 3), dtype=np.uint8)
    neighbours[1, 1] = 0
    adjacent = convolve(binary.astype(np.uint8), neighbours, mode='constant', cval=0)
    return freeze(binary & (adjacent > 0), bool)


def _check_cancel(interrupted: Callable[[], bool]) -> None:
    if interrupted():
        raise InterruptedError('Hough extraction interrupted.')


def hough_transform(binary: NDArray, *, progress: Progress = lambda *a: None,
                    interrupted: Callable[[], bool] = lambda: False,
                    max_bytes: int = DEFAULT_MEMORY_LIMIT
                    ) -> tuple[NDArray, NDArray, NDArray]:
    if binary.ndim != 2 or not all(binary.shape):
        raise ValueError('A nonempty 2-D image is required.')
    height, width = binary.shape
    diagonal = ceil(hypot(height - 1, width - 1))
    cells = (2 * diagonal + 1) * 360
    foreground = int(np.count_nonzero(binary))
    estimated = cells * 8 * 3 + foreground * 8 * 8 + binary.size * 3
    if estimated > max_bytes:
        raise MemoryError(f'Hough needs approximately {estimated} bytes; '
                          f'limit is {max_bytes}. Use a smaller input image.')
    theta = readonly(np.arange(-90, 90, .5))
    rho = readonly(np.arange(-diagonal, diagonal + 1, dtype=np.float64))
    accumulator = np.zeros((len(rho), len(theta)), dtype=np.int64, order='F')
    x, y = np.nonzero(binary.T)  # MATLAB find order: column, then row.
    for column, angle in enumerate(theta):
        _check_cancel(interrupted)
        # hough uses radians and rounds the positive, offset bin coordinate.
        # Rounding signed rho first changes half-bin votes on real rasters.
        radians = float(angle) * pi / 180
        projection = x * cos(radians) + y * sin(radians)
        bins = matlab_round(projection + diagonal).astype(np.int64)
        accumulator[:, column] = np.bincount(bins, minlength=len(rho))
        if column % 12 == 0:
            progress(10 + column * 50 // len(theta), 'Computing Hough accumulator...')
    accumulator.setflags(write=False)
    return accumulator, theta, rho


def suppression_size(shape: tuple[int, int]) -> tuple[int, int]:
    return tuple(max(1, 2 * ceil(size / 100) + 1) for size in shape)


def hough_peaks(accumulator: NDArray, count: int, threshold: int, *,
                neighbourhood: tuple[int, int] | None = None,
                interrupted: Callable[[], bool] = lambda: False) -> NDArray[np.int64]:
    if accumulator.ndim != 2 or not accumulator.size \
            or not np.isfinite(accumulator).all() or np.any(accumulator < 0):
        raise ValueError('A finite nonnegative Hough matrix is required.')
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise ValueError('Peak count must be a positive integer.')
    if not isfinite(threshold) or threshold < 0:
        raise ValueError('Peak threshold must be nonnegative.')
    hood = neighbourhood or suppression_size(accumulator.shape)
    if len(hood) != 2 or any(not isinstance(n, int) or n < 1 or n % 2 == 0 for n in hood):
        raise ValueError('Suppression dimensions must be positive odd integers.')
    working = np.array(accumulator, order='F', copy=True)
    flat = working.reshape(-1, order='F')
    height, width = working.shape
    half_r, half_c = (n // 2 for n in hood)
    peaks = []
    for _ in range(count):
        _check_cancel(interrupted)
        index = int(np.argmax(flat))
        value = flat[index]
        if value <= 0 or value < threshold:
            break
        row, column = index % height, index // height
        peaks.append((row, column))
        rows = np.arange(max(0, row - half_r), min(height, row + half_r + 1))
        for raw_column in range(column - half_c, column + half_c + 1):
            # Theta is a half-circle; crossing its seam reverses signed rho.
            selected_rows = height - 1 - rows if raw_column < 0 or raw_column >= width else rows
            working[selected_rows, raw_column % width] = 0
    return freeze(np.array(peaks, dtype=np.int64).reshape(-1, 2), np.int64)


def hough_lines(binary: NDArray, theta: NDArray, rho: NDArray, peaks: NDArray,
                fill_gap: float, min_length: float, *,
                progress: Progress = lambda *a: None,
                interrupted: Callable[[], bool] = lambda: False) -> NDArray[np.float64]:
    if not isfinite(fill_gap) or fill_gap <= 0 or not isfinite(min_length) or min_length <= 0:
        raise ValueError('Line gap and minimum length must be finite and positive.')
    x, y = np.nonzero(binary.T)
    points = np.column_stack((x, y))
    endpoints = []
    for index, (row, column) in enumerate(peaks):
        _check_cancel(interrupted)
        angle = theta[column]
        radians = float(angle) * pi / 180
        projection = x * cos(radians) + y * sin(radians)
        slope = (len(rho) - 1) / (rho[-1] - rho[0])
        membership = matlab_round(slope * (projection - rho[0]) + 1) == row + 1
        selected = points[membership]
        if len(selected) < 2:
            continue
        # MATLAB houghlines orders ascending by the axis of largest extent,
        # with the other axis breaking ties; it does not orient by signed theta.
        spans = np.ptp(selected, axis=0)
        primary, secondary = (1, 0) if spans[1] > spans[0] else (0, 1)
        selected = selected[np.lexsort((selected[:, secondary], selected[:, primary]))]
        gaps = np.hypot(*np.diff(selected, axis=0).T)
        cuts = np.flatnonzero(gaps > fill_gap) + 1
        for run in np.split(selected, cuts):
            if len(run) < 2:
                continue
            length = float(np.hypot(*(run[-1] - run[0])))
            if length >= min_length:
                endpoints.append((run[0] + 1, run[-1] + 1))
        if index % 10 == 0:
            progress(65 + index * 30 // max(1, len(peaks)), 'Extracting Hough line segments...')
    return readonly(np.array(endpoints, dtype=np.float64).reshape(-1, 2, 2))


@dataclass(frozen=True, slots=True)
class HoughResult:
    image: NDArray[np.uint8]
    binary: NDArray[np.bool_]
    accumulator: NDArray[np.int64]
    theta: NDArray[np.float64]
    rho: NDArray[np.float64]
    peaks: NDArray[np.int64]
    endpoints: NDArray[np.float64]
    threshold: int
    parameters: HoughParameters


def extract_hough(image: NDArray[np.uint8], parameters: HoughParameters, *,
                  progress: Progress = lambda *a: None,
                  interrupted: Callable[[], bool] = lambda: False) -> HoughResult:
    binary = clean_complement(image)
    accumulator, theta, rho = hough_transform(binary, progress=progress, interrupted=interrupted)
    threshold = ceil(parameters.threshold * int(accumulator.max()))
    progress(62, 'Selecting Hough peaks...')
    peaks = hough_peaks(accumulator, parameters.peaks, threshold, interrupted=interrupted)
    endpoints = hough_lines(binary, theta, rho, peaks, parameters.fill_gap,
                            parameters.min_length, progress=progress, interrupted=interrupted)
    return HoughResult(freeze(image, np.uint8), binary, accumulator, theta, rho,
                       peaks, endpoints, threshold, parameters)
