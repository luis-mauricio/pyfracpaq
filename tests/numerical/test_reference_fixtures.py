"""Check analytical fixture consistency; the Python scientific port is future work."""

import json
import math

import numpy as np
import pytest
from PIL import Image

from reference_common import REFERENCE, ROOT, sha256

CASES = json.loads((ROOT / 'tests/fixtures/analytic_cases.json').read_text())['cases']


def test_fixture_inventory_and_inputs():
    assert len(CASES) == len({c['id'] for c in CASES}) == 46
    assert {'geometry', 'histograms', 'circles', 'topology', 'tensors', 'wavelets'} <= {
        c['family'] for c in CASES}
    for case in CASES:
        if 'file' in case['input']:
            assert (ROOT / case['input']['file']).is_file()
        assert 'não executado em MATLAB' in case['oracle']


@pytest.mark.parametrize('case', [c for c in CASES if c['family'] == 'geometry'],
                         ids=lambda c: c['id'])
def test_geometry_oracles_match_input(case):
    scale = case['input'].get('scale') or 1
    rows = (ROOT / case['input']['file']).read_text().splitlines()
    lengths = []
    for row in rows:
        values = [float(v) / scale for v in row.split('\t')]
        points = list(zip(values[::2], values[1::2]))
        points = [p for i, p in enumerate(points) if i == 0 or p != points[i - 1]]
        lengths.append([math.dist(a, b) for a, b in zip(points, points[1:])])
    expected = case['expected']
    if 'segment_lengths' in expected:
        np.testing.assert_allclose(lengths[0], expected['segment_lengths'], rtol=1e-10)
    if 'trace_length' in expected:
        assert sum(lengths[0]) == pytest.approx(expected['trace_length'], rel=1e-10)
    if 'trace_lengths' in expected:
        np.testing.assert_allclose(list(map(sum, lengths)), expected['trace_lengths'])


@pytest.mark.parametrize('case', [c for c in CASES if c['id'].endswith('_kernel')],
                         ids=lambda c: c['id'])
def test_kernel_oracles_at_known_points(case):
    e = case['expected']
    assert e['at_1_0_real'] == pytest.approx(math.exp(-.5))
    assert e['centre_real_imag'][1] == 0
    assert e['centre_real_imag'][0] == (1 if case['id'] == 'morlet_kernel' else 2)


def test_example_provenance_and_actual_formats():
    examples = json.loads((REFERENCE / 'examples.json').read_text())
    assert len(examples) == 10
    for entry in examples:
        assert sha256(ROOT / entry['path']) == entry['sha256']
    by_name = {entry['path'].split('/')[-1]: entry for entry in examples}
    assert by_name['Souter_Blue.txt']['direct_gui_txt']
    assert not by_name['souter_all_colour24378D.txt']['direct_gui_txt']
    for name in ('directional', 'rectangular', 'rgb_invalid'):
        with Image.open(ROOT / f'tests/fixtures/images/{name}.tif') as image:
            assert image.mode == ('RGB' if name == 'rgb_invalid' else 'L')
            extrema = ((0, 255),) * 3 if name == 'rgb_invalid' else (0, 255)
            assert image.getextrema() == extrema
