"""Deterministic, project-authored tensor/stability fixtures (project MIT)."""

from pathlib import Path

import numpy as np
from PIL import Image

from pyfracpaq.analysis.compatibility import cosd, sind
from pyfracpaq.domain import TraceInput, build_dataset


def uniform_dataset():
    """Same nominal nodes/angles as capture_native_s1011.m make_traces."""
    traces = []
    for k, angle in enumerate(range(0, 180, 5), 1):
        start = np.array([k / 4, k / 8])
        finish = start + 2 * np.array([sind(angle), cosd(angle)])
        traces.append(TraceInput((tuple(start), tuple(finish))))
    return build_dataset(traces)


def network_image(path: Path) -> Path:
    """64x48 L/uint8: two horizontal lines and a crossing vertical line."""
    pixels = np.full((48, 64), 255, dtype=np.uint8)
    pixels[12, 5:59] = 0
    pixels[34, 5:59] = 0
    pixels[4:44, 44] = 0
    Image.fromarray(pixels).save(path)
    return path


if __name__ == '__main__':
    from reference_common import ROOT, sha256, write_json
    target = ROOT / 'tests/fixtures/images/tensor_network.tif'
    network_image(target)
    write_json(target.with_suffix('.json'), {
        'origin': 'Project-authored analytical raster, created for Sprints 10/11.',
        'license': 'MIT (LICENSE at project root)',
        'generator': 'scripts/sprint1011_reference.py:network_image',
        'path': str(target.relative_to(ROOT)), 'sha256': sha256(target),
        'shape_yx': [48, 64], 'dtype': 'uint8', 'mode': 'L',
        'black_pixels_zero_based': ['row 12, columns 5..58', 'row 34, columns 5..58',
                                    'column 44, rows 4..43'],
        'role': 'Nonzero trace-envelope area after Hough, unlike single-row fixtures.',
    })
