"""Native helper arrays and explicit IO policies, independent of main GUI."""

import numpy as np
from PIL import Image
import pytest
from scipy.io import loadmat

from pyfracpaq.analysis.auxiliary import crack_tensor16, probe_plane
from pyfracpaq.analysis.palettes import cmocean
from pyfracpaq.analysis.preprocess import preprocess_image, sobel_edges
from pyfracpaq.analysis.roses import linear_rose, historical_rose
from pyfracpaq.geometry.primitives import Bounds
from pyfracpaq.io.move import convert_move
from pyfracpaq.io.nodes import read_txt
from pyfracpaq.io.text import readtext
from reference_common import REFERENCE


def test_six_preprocess_stages_equal_actual_matlab_arrays():
    folder = REFERENCE / 'sprint15/native'
    with Image.open(folder / 'MacduffColourCropped.jpg') as image:
        result = preprocess_image(np.asarray(image))
    native = loadmat(folder / 'preprocess_arrays.mat', simplify_cells=True)
    for name, key in [('grayscale', 'gray'), ('median', 'median'), ('difference', 'difference'),
                      ('edges', 'edges'), ('closed', 'closed'), ('processed', 'processed')]:
        np.testing.assert_array_equal(getattr(result, name), native[key])
        assert not getattr(result, name).flags.writeable
    details = loadmat(folder / 'details_arrays.mat', simplify_cells=True)
    for pixels, expected in zip(details['inputs'], details['edges']):
        np.testing.assert_array_equal(sobel_edges(pixels), expected)


def test_tensor16_probe_and_palette_against_native():
    native = loadmat(REFERENCE / 'sprint15/native/aux_arrays.mat', simplify_cells=True)
    tensor = crack_tensor16([2, 3], [30, 110], 20)
    assert tensor.components.shape == (2,) * 16
    np.testing.assert_allclose(tensor.components, native['tensor16'], atol=1e-13)
    np.testing.assert_allclose(tensor.polar, native['polar16'], atol=1e-12)
    probe = probe_plane(1, Bounds(0, 0, 10, 10), native['segments'], 8)
    np.testing.assert_allclose(probe.mq, native['probe_mq'], atol=1e-14)
    assert probe.m == pytest.approx(native['probe_m'], abs=1e-14)
    details = loadmat(REFERENCE / 'sprint15/native/details_arrays.mat', simplify_cells=True)
    np.testing.assert_allclose(cmocean('balance', pivot=1, limits=(-2, 5)), details['balance'], atol=1e-14)
    assert cmocean('balance', 7, pivot=1, limits=(-2, 5)).shape == (7, 3)
    # Historical probe origin does not add domain minima, and empty find counts 1.
    empty = probe_plane(1, Bounds(100, 100, 110, 110), np.empty((0, 4)), 8)
    np.testing.assert_allclose(empty.mq, np.full(8, 1 / 9.5))


def test_linear_and_historical_roses_native_data():
    native = loadmat(REFERENCE / 'sprint15/native/details_arrays.mat', simplify_cells=True)
    values = [0, 10, 20, 90, 180, 270, 350]
    linear = linear_rose(values, 30)
    np.testing.assert_allclose(linear.vertices[:, 0], native['linear_x'], atol=1e-13)
    np.testing.assert_allclose(linear.vertices[:, 1], native['linear_y'], atol=1e-13)
    np.testing.assert_array_equal(historical_rose(values, 12).counts, native['historical_counts'])


def test_generic_reader_native_masks_quotes_and_line_endings():
    native = loadmat(REFERENCE / 'sprint15/native/aux_arrays.mat', simplify_cells=True)
    table = readtext('1,,hello\r\n2,3,"a,b"\r\n', quotes='"', textsource=True)
    assert table.data.tolist() == [[1., None, 'hello'], [2., 3., '"a,b"']]
    assert (table.number, table.empty, table.string, table.quote_count) == (3, 1, 2, 1)
    for name in ('number_mask', 'empty_mask', 'string_mask'):
        key = name.replace('_mask', 'Mask')
        np.testing.assert_array_equal(getattr(table, name), native['readstats'][key])
    mixed = readtext('#comment\n1;2j;3+4i\n5;;text', '[;,]', '#', regex=True, textsource=True)
    assert mixed.data[0, 1] == 2j and mixed.data[0, 2] == 3+4j
    numeric = readtext('1,,word\r2,NaN,4', textsource=True, mode='numeric', empty='zero')
    assert numeric.data[0, 1] == 0 and np.isnan(numeric.data[0, 2])
    assert numeric.number == 4
    with pytest.raises(ValueError):
        readtext('"unmatched', quotes='"', textsource=True)


@pytest.mark.parametrize('trailing', ['', '\n', '\n\n'])
def test_move_keeps_last_object_and_explicit_header_columns(tmp_path, trailing):
    source = tmp_path / 'move.dat';output = tmp_path / 'nodes.txt'
    source.write_text('X Y Z\n1 2 3\n4 5 6\n\n7 8 9\n10 11 12' + trailing)
    dataset = convert_move(source, output, skip_header=1)
    result = read_txt(output)
    assert dataset.n_traces == result.n_traces == 2
    np.testing.assert_array_equal(result.traces[-1].nodes[-1].point, (10, 12))
    assert output.read_text().endswith('10.0000\t12.0000\t\n')
    original = output.read_bytes()
    with pytest.raises(ValueError):
        convert_move(source, output, skip_header=0)
    assert output.read_bytes() == original
    assert not list(tmp_path.glob('.pyfracpaq-*'))


def test_preprocess_invalid_and_cancelled():
    with pytest.raises(ValueError):
        preprocess_image(np.zeros((4, 4, 4), np.uint8))
    with pytest.raises(InterruptedError):
        preprocess_image(np.zeros((4, 4), np.uint8), interrupted=lambda: True)
