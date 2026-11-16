"""Unconverted 8-bit grayscale JPEG/TIFF inputs and complete image geometry."""

from collections.abc import Callable
from dataclasses import asdict, dataclass
import logging
from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError

from pyfracpaq.analysis.hough import HoughParameters, HoughResult, extract_hough
from pyfracpaq.domain import Dataset, InputMode, TraceInput, build_dataset
from pyfracpaq.geometry import Bounds
from pyfracpaq.io.colours import BLUE

LOG = logging.getLogger(__name__)
MAX_IMAGE_PIXELS = 16_777_216


@dataclass(frozen=True, slots=True)
class ImageMetadata:
    path: Path
    format: str
    mode: str
    width: int
    height: int
    bit_depth: int
    frames: int


class ImageInputError(ValueError):
    def __init__(self, message: str, metadata: ImageMetadata | None = None) -> None:
        self.metadata = metadata
        super().__init__(message)


def read_grayscale(path: Path | str) -> tuple[np.ndarray, ImageMetadata]:
    path = Path(path).expanduser().resolve()
    try:
        with Image.open(path) as source:
            width, height = source.size
            bits = source.tag_v2.get(258) if hasattr(source, 'tag_v2') else None
            bit_depth = (sum(bits) if isinstance(bits, tuple) else bits) if bits else (
                1 if source.mode == '1' else 16 if source.mode.startswith('I;16') else
                32 if source.mode in ('I', 'F') else 8 * len(source.getbands()))
            metadata = ImageMetadata(path, source.format or '', source.mode, width,
                                     height, int(bit_depth), getattr(source, 'n_frames', 1))
            LOG.info('Image metadata: %s', asdict(metadata))
            if metadata.format not in ('JPEG', 'TIFF') or source.mode != 'L' \
                    or metadata.bit_depth != 8 or metadata.frames != 1:
                raise ImageInputError('Selected image must be a single-frame, 8-bit '
                                      'grayscale JPEG/TIFF. Check console metadata; '
                                      'RGB, indexed and higher-depth images are not converted.', metadata)
            if width * height > MAX_IMAGE_PIXELS:
                raise ImageInputError('Image exceeds the 16 megapixel extraction limit.', metadata)
            return np.array(source, dtype=np.uint8), metadata
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as error:
        raise ImageInputError(f'Cannot read image {path}: {error}') from error


@dataclass(frozen=True, slots=True)
class ImageImport:
    dataset: Dataset | None
    metadata: ImageMetadata
    hough: HoughResult


def read_image(path: Path | str, parameters: HoughParameters = HoughParameters(), *,
               pixels_per_metre: float | None = None,
               progress: Callable[[int, str], None] = lambda *a: None,
               interrupted: Callable[[], bool] = lambda: False) -> ImageImport:
    progress(2, 'Reading grayscale image...')
    image, metadata = read_grayscale(path)
    result = extract_hough(image, parameters, progress=progress, interrupted=interrupted)
    dataset = None
    if len(result.endpoints):
        records = [TraceInput(tuple(map(tuple, pair)), BLUE) for pair in result.endpoints]
        dataset = build_dataset(records, source=metadata.path, input_mode=InputMode.IMAGE,
                                pixels_per_metre=pixels_per_metre,
                                source_bounds=Bounds(0, 0, metadata.width, metadata.height))
    LOG.info('Hough: theta -90:0.5:89.5; rho step 1; max(H)=%s; threshold=%s; '
             '%s peaks; %s lines; FillGap=%g; MinLength=%g',
             result.accumulator.max(), result.threshold, len(result.peaks),
             len(result.endpoints), parameters.fill_gap, parameters.min_length)
    return ImageImport(dataset, metadata, result)
