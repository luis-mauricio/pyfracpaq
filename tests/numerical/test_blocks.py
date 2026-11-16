"""Native raster classification and approved Q-14 calibration."""

import numpy as np
from PIL import Image
import pytest
from scipy.io import loadmat

from pyfracpaq.analysis.blocks import compute_blocks, white_components
from pyfracpaq.analysis.lengths import compute_lengths
from pyfracpaq.domain import TraceInput, build_dataset
from pyfracpaq.domain.execution import RunContext
from pyfracpaq.io.block_raster import export_block_raster
from reference_common import REFERENCE
from sprint1213_reference import block_dataset, configuration


@pytest.mark.parametrize('case', ['separate', 'nested', 'oblique', 'scaled'])
def test_native_bmp_binarization_order_counts_and_centroids(case):
    folder = REFERENCE / 'sprint12/native' / case
    expected = loadmat(folder / 'raster_arrays.mat', simplify_cells=True)
    with Image.open(folder / 'FracPaQ2D_blocksize.bmp') as bitmap:
        result = white_components(np.asarray(bitmap))
    np.testing.assert_array_equal(result.binary, expected['binary'])
    np.testing.assert_array_equal(result.pixel_areas, expected['area'])
    np.testing.assert_allclose(result.pixel_centroids, expected['centroids'], atol=1e-12)
    np.testing.assert_array_equal(result.touches_border, expected['touches'])
    assert result.threshold == pytest.approx(expected['threshold'], abs=1e-15)


@pytest.mark.parametrize('scale,shift', [(None, (0, 0)), (10, (0, 0)), (None, (-200, 300))])
def test_approved_known_rectangles_scale_translation_and_constant_areas(scale, shift):
    result = compute_blocks(block_dataset(scale=scale, shift=shift), exclude_border=True)
    factor = scale or 1
    assert result.raster.shape == (60, 100)
    np.testing.assert_allclose(result.areas, np.array([1444, 1444]) / factor ** 2)
    np.testing.assert_allclose(result.centroids,
                              (np.array([[30, 30], [90, 50]]) + shift) / factor)
    assert result.histogram.frequencies.tolist() == [2]
    assert result.complementary.complementary.tolist() == [0]
    assert len(result.components.pixel_areas) == 3
    assert not result.centroids.flags.writeable


def test_white_8_connectivity_empty_solid_and_border_components():
    diagonal = np.array([[255, 0], [0, 255]], dtype=np.uint8)
    result = white_components(diagonal)
    assert result.pixel_areas.tolist() == [2] and result.touches_border.tolist() == [True]
    assert len(white_components(np.zeros((3, 3), np.uint8)).pixel_areas) == 0
    assert white_components(np.full((3, 3), 255, np.uint8)).pixel_areas.tolist() == [9]
    opened = build_dataset([TraceInput(((0, 0), (100, 50)))])
    result = compute_blocks(opened, exclude_border=True)
    assert result.areas.size == 0 and result.centroids.shape == (0, 2)


def test_raster_is_reversible_in_trace_direction_and_visible_bmp_has_fixed_name(tmp_path):
    dataset = block_dataset()
    reversed_dataset = build_dataset([TraceInput(tuple(reversed(t.points))) for t in dataset.source_traces])
    a = compute_blocks(dataset, exclude_border=True)
    b = compute_blocks(reversed_dataset, exclude_border=True)
    np.testing.assert_array_equal(a.raster, b.raster)
    sentinel = tmp_path / 'unrelated.bmp'
    sentinel.write_bytes(b'preserve')
    path = export_block_raster(a.raster, tmp_path)
    assert path.name == 'FracPaQ2D_blocksize.bmp'
    with Image.open(path) as image:
        assert image.mode == 'L' and image.size == (100, 60)
        np.testing.assert_array_equal(np.asarray(image), a.raster)
    export_block_raster(b.raster, tmp_path)
    assert sentinel.read_bytes() == b'preserve'
    assert not list(tmp_path.glob('.pyfracpaq-*'))


def test_invalid_domain_large_raster_and_cancellation():
    with pytest.raises(ValueError, match='two-dimensional'):
        compute_blocks(build_dataset([TraceInput(((0, 0), (10, 0)))]), exclude_border=True)
    with pytest.raises(MemoryError):
        compute_blocks(build_dataset([TraceInput(((0, 0), (1e6, 1e6)))]), exclude_border=True)
    with pytest.raises(InterruptedError):
        compute_blocks(block_dataset(), exclude_border=True, interrupted=lambda: True)


def test_complete_approved_lengths_pipeline_and_cancel_before_any_output(tmp_path):
    dataset = block_dataset(scale=10)
    cfg = configuration(('LEN-13', 'LEN-15'))
    context = RunContext(cfg, tmp_path, tmp_path, 'candidate')
    with pytest.raises(InterruptedError):
        compute_lengths(dataset, context, lambda *_: None, interrupted=lambda: True)
    assert not list(tmp_path.iterdir())
    result = compute_lengths(dataset, context, lambda *_: None)
    assert result.blocks is not None and result.variogram is not None
    assert len(list(tmp_path.glob('*.txt'))) == 3
    assert [p.name for p in tmp_path.glob('*.bmp')] == ['FracPaQ2D_blocksize.bmp']
    np.testing.assert_allclose(result.blocks.areas, [14.44, 14.44])


def test_approved_hough_uses_full_node_geometry_and_common_censor_mask(tmp_path):
    from pyfracpaq.analysis.hough import HoughParameters
    from pyfracpaq.io.images import read_image
    from reference_common import ROOT

    image = read_image(ROOT / 'tests/fixtures/images/tensor_network.tif', HoughParameters())
    cfg = configuration(('LEN-13', 'LEN-15'))
    context = RunContext(cfg, tmp_path, tmp_path, 'hough')
    result = compute_lengths(image.dataset, context, lambda *_: None)
    expected = image.dataset.as_arrays().segment_midpoints
    from pyfracpaq.analysis.variogram import experimental_variogram
    manual = experimental_variogram(expected, result.sample.segment_lengths, nrbins=30)
    np.testing.assert_allclose(result.variogram.values, manual.values, equal_nan=True)
    assert result.blocks.raster.ndim == 2
