"""Scalar-count HIST bins measured independently in MATLAB R2024b."""

import json

import numpy as np
import pytest

from pyfracpaq.analysis.compatibility import hist_auto
from reference_common import REFERENCE


@pytest.mark.parametrize('index',range(4))
def test_native_range_and_constant_centres(index):
    path=REFERENCE/'sprint16/final/native-graphics-details/hist-auto.json'
    native=json.loads(path.read_text())[index]
    centres,counts=hist_auto(native['values'],20)
    np.testing.assert_allclose(centres,native['centres'],rtol=0,atol=1e-14)
    np.testing.assert_array_equal(counts,native['counts'])
    assert not centres.flags.writeable


def test_histogram_finite_input_and_infinity_tails():
    with pytest.raises(ValueError):hist_auto([np.nan,np.inf])
    for bins in (True,1,2.5):
        with pytest.raises(ValueError):hist_auto([0,1],bins)
    _,counts=hist_auto([-np.inf,0,1,np.inf,np.nan],2)
    np.testing.assert_array_equal(counts,[2,2])
