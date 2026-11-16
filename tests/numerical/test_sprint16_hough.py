"""Ordered native oracles, including half-bin votes and real-raster peaks."""

import numpy as np
import pytest
from scipy.io import loadmat

from pyfracpaq.analysis.hough import HoughParameters, extract_hough
from pyfracpaq.io.images import read_grayscale
from reference_common import REFERENCE, ROOT


@pytest.mark.parametrize('case', ['directional', 'rectangular', 'tensor_network',
                                 'MacduffBinary', 'Orkney1aBinary'])
def test_all_hough_stages_match_actual_matlab_in_source_order(case):
    real = case.endswith('Binary')
    folder = REFERENCE / 'sprint16/native'
    source = (ROOT / 'fracpaq-matlab' / f'{case}.tif' if real
              else ROOT / 'tests/fixtures/images' / f'{case}.tif')
    native = loadmat(folder / ('details/hough_real.mat' if real else 'hough_arrays.mat'),
                     simplify_cells=True)['hough_real' if real else 'hough_refs'][case]
    actual = extract_hough(read_grayscale(source)[0], HoughParameters())
    for field, expected in [('binary', 'binary'), ('accumulator', 'H'),
                            ('theta', 'theta'), ('rho', 'rho'),
                            ('endpoints', 'endpoints')]:
        np.testing.assert_array_equal(getattr(actual, field), native[expected])
    np.testing.assert_array_equal(actual.peaks + 1, native['peaks'])
    assert actual.threshold == native['threshold']
