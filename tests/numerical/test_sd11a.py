"""Regression cases from the real TXT selected by the maintainer."""

import hashlib

import numpy as np

from pyfracpaq.analysis.compatibility import double_angles
from pyfracpaq.io import read_txt
from pyfracpaq.io.angles import export_ezrose
from reference_common import ROOT, REFERENCE


def test_sd11a_original_geometry_and_ezrose_match_native(tmp_path):
    path = ROOT / 'fracpaq-matlab/SD11A.txt'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == (
        '96bafa56537444279a748c3f4b7a4300f7e73341a04d2ba4ff8cf1299ad74688')
    dataset = read_txt(path)
    assert (dataset.n_traces, dataset.n_segments, dataset.n_nodes) == (445, 1076, 1521)
    assert not dataset.diagnostics
    # Record 397 is a downward vertical segment. Its halfway point must be
    # inside the segment; the native reader incorrectly returns y=690.65.
    np.testing.assert_allclose(dataset.traces[396].midpoint, (1605.9, 644.75),
                               rtol=0, atol=1e-10)
    # Record 389 reaches its halfway point on a downward vertical subsegment.
    np.testing.assert_allclose(dataset.traces[388].midpoint,
                               (1699.4, 754.6698428056986), rtol=0, atol=1e-10)
    angles = double_angles(dataset.as_arrays().raw_angles, 0)
    actual = export_ezrose(angles, 'SD11A', tmp_path)
    native = REFERENCE / 'sprint16/sd11a/native/FracPaQ2DEZROSE_SD11A.txt'
    assert actual.read_bytes() == native.read_bytes()
