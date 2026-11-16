"""Freeze nominal MATLAB hot/bone ramp equations; native RGB comparison pending."""

import json
from pathlib import Path

import numpy as np


def ramps(levels: int) -> dict:
    n = 3 * levels // 8
    hot = np.column_stack((
        np.r_[np.arange(1, n + 1) / n, np.ones(levels - n)],
        np.r_[np.zeros(n), np.arange(1, n + 1) / n, np.ones(levels - 2 * n)],
        np.r_[np.zeros(2 * n), np.arange(1, levels - 2 * n + 1) / (levels - 2 * n)],
    ))
    grey = np.tile(np.linspace(0, 1, levels)[:, None], (1, 3))
    return {'hot': hot, 'bone': (7 * grey + hot[:, ::-1]) / 8}


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    np.savez_compressed(root / 'pyfracpaq/resources/matlab_rgb.npz', **ramps(256))
    (root / 'pyfracpaq/resources/matlab_rgb.json').write_text(json.dumps({
        'levels': 256, 'method': 'Nominal piecewise hot ramp; bone=(7*gray+fliplr(hot))/8.',
        'scope': 'Independent equation reconstruction, not captured MATLAB RGB.',
        'native_comparison': 'pending',
        'sources': ['https://www.mathworks.com/help/matlab/ref/hot.html',
                    'https://www.mathworks.com/help/matlab/ref/bone.html'],
    }, indent=2) + '\n')
