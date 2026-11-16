"""Independent vote/endpoint oracles and deterministic Hough stage contracts."""

from dataclasses import replace
import logging
from math import ceil, cos, sin, radians, copysign, floor, hypot

import numpy as np
from PIL import Image
import pytest

from pyfracpaq.analysis.hough import (
    HoughParameters, clean_complement, extract_hough, hough_lines, hough_peaks,
    hough_transform, parameters_from_controls, suppression_size,
)
from pyfracpaq.domain.execution import FieldError
from pyfracpaq.io.images import ImageInputError, read_grayscale, read_image
from reference_common import ROOT


def test_accumulator_matches_independent_scalar_vote_oracle():
    binary = np.zeros((4, 7), dtype=bool)
    binary[0, 0] = binary[1, 4] = binary[3, 2] = True
    h, theta, rho = hough_transform(binary)
    diagonal = ceil(hypot(3, 6))
    assert h.shape == (2 * diagonal + 1, 360)
    assert theta[[0, -1]].tolist() == [-90, 89.5]
    expected = np.zeros_like(h)
    for y, x in np.argwhere(binary):
        for j, angle in enumerate(theta):
            if angle == -90:
                projection = -float(y)
            elif angle == 0:
                projection = float(x)
            else:
                projection = x * cos(radians(angle)) + y * sin(radians(angle))
            index = floor(projection + diagonal + .5)
            expected[index, j] += 1
    np.testing.assert_array_equal(h, expected)
    np.testing.assert_array_equal(h.sum(axis=0), np.full(360, 3))
    assert not h.flags.writeable


def test_preprocessing_uses_all_nonwhite_values_and_eight_neighbours_at_edges():
    image = np.full((6, 8), 255, dtype=np.uint8)
    image[0, 0] = 0
    image[1, 1] = 254  # diagonal neighbour survives; no intensity threshold.
    image[4, 4] = 128  # isolated nonwhite pixel is removed.
    clean = clean_complement(image)
    assert np.argwhere(clean).tolist() == [[0, 0], [1, 1]]
    assert not clean.flags.writeable


def test_peaks_include_threshold_ties_use_column_major_order_and_rho_wrap():
    h = np.zeros((9, 8), dtype=np.int64)
    h[6, 0] = h[0, 1] = 8
    h[2, 7] = 7  # seam equivalent of first peak; suppressed by reflected rho.
    h[7, 4] = 6
    peaks = hough_peaks(h, 10, 6, neighbourhood=(3, 3))
    assert peaks.tolist() == [[6, 0], [0, 1], [7, 4]]
    assert h[2, 7] == 7  # Original accumulator is not destroyed.
    assert suppression_size((723, 360)) == (17, 9)
    assert hough_peaks(np.zeros((5, 4)), 10, 0).shape == (0, 2)


def test_horizontal_endpoints_are_one_based_and_length_is_endpoint_distance():
    image = np.full((12, 20), 255, dtype=np.uint8)
    image[4, 2:18] = 0
    result = extract_hough(image, HoughParameters(peaks=1, threshold=1))
    assert result.threshold == 16
    row, col = result.peaks[0]
    assert result.theta[col] == -90 and result.rho[row] == -4
    assert result.endpoints.tolist() == [[[3, 5], [18, 5]]]
    assert not result.endpoints.flags.writeable


def test_gap_boundary_merges_and_min_length_is_inclusive():
    binary = np.zeros((10, 15), dtype=bool)
    binary[4, 1:5] = binary[4, 8:12] = True
    h, theta, rho = hough_transform(binary)
    peak = np.array([[np.flatnonzero(rho == -4)[0], 0]])
    separate = hough_lines(binary, theta, rho, peak, 3.99, 3)
    assert separate.tolist() == [[[2, 5], [5, 5]], [[9, 5], [12, 5]]]
    merged = hough_lines(binary, theta, rho, peak, 4, 3)
    assert merged.tolist() == [[[2, 5], [12, 5]]]
    assert not len(hough_lines(binary, theta, rho, peak, 3.99, 3.01))


def test_vertical_and_diagonal_lines_have_expected_vote_and_endpoint_membership():
    for points, angle, expected_rho in [
        ([(x, x) for x in range(2, 14)], -45, 0),
        ([(6, y) for y in range(2, 14)], 0, 6),
    ]:
        binary = np.zeros((18, 20), dtype=bool)
        for x, y in points:
            binary[y, x] = True
        h, theta, rho = hough_transform(binary)
        peak = np.array([[np.flatnonzero(rho == expected_rho)[0],
                          np.flatnonzero(theta == angle)[0]]])
        assert h[tuple(peak[0])] == len(points)
        lines = hough_lines(binary, theta, rho, peak, 2, 3)
        assert len(lines) == 1
        assert {tuple(p) for p in lines[0]} == {
            (points[0][0] + 1, points[0][1] + 1),
            (points[-1][0] + 1, points[-1][1] + 1)}


@pytest.mark.parametrize('mode', ['RGB', 'RGBA', 'P', '1', 'I;16'])
def test_image_modes_rejected_with_metadata_in_console(tmp_path, mode, caplog):
    path = tmp_path / 'wrong.tiff'
    Image.new(mode, (8, 8)).save(path)
    with caplog.at_level(logging.INFO), pytest.raises(ImageInputError) as error:
        read_grayscale(path)
    assert error.value.metadata.mode == mode
    assert 'Image metadata:' in caplog.text
    assert not list(tmp_path.glob('*.png'))


@pytest.mark.parametrize('extension,format', [('JPG', 'JPEG'), ('JPEG', 'JPEG'),
                                            ('TIF', 'TIFF'), ('TIFF', 'TIFF')])
def test_grayscale_formats_are_read_without_implicit_conversion(tmp_path, extension, format):
    path = tmp_path / ('input.' + extension)
    Image.new('L', (8, 6), 255).save(path, format=format)
    values, info = read_grayscale(path)
    assert info.mode == 'L' and info.bit_depth == 8 and info.format == format
    assert values.dtype == np.uint8 and values.shape == (6, 8)


def test_image_geometry_has_complete_fields_full_domain_and_idempotent_scale():
    result = read_image(ROOT / 'tests/fixtures/images/directional.tif',
                        HoughParameters(peaks=1), pixels_per_metre=2)
    data = result.dataset
    assert data.n_traces == data.n_segments == 1 and data.n_nodes == 2
    assert (data.bounds.x_min, data.bounds.y_min, data.bounds.x_max, data.bounds.y_max) \
        == (0, 0, 16, 16)
    trace = data.traces[0]
    segment = trace.segments[0]
    assert segment.end_length == trace.total_length == segment.length
    assert segment.midpoint == trace.midpoint
    assert trace.colour == (0, 0, 1)
    np.testing.assert_array_equal(data.with_scale(None).as_arrays().segment_coordinates,
                                  result.hough.endpoints.reshape(-1, 4))
    assert data.with_scale(None).bounds.x_max == 32
    np.testing.assert_array_equal(data.with_scale(2).as_arrays().node_coordinates,
                                  data.as_arrays().node_coordinates)


def test_no_line_and_resource_or_interruption_paths_are_explicit(tmp_path):
    path = tmp_path / 'empty.tif'
    Image.new('L', (16, 12), 255).save(path)
    result = read_image(path)
    assert result.dataset is None and not result.hough.accumulator.any()
    assert result.hough.peaks.shape == (0, 2)
    with pytest.raises(MemoryError):
        hough_transform(np.ones((10, 10), dtype=bool), max_bytes=1)
    with pytest.raises(InterruptedError):
        hough_transform(np.ones((10, 10), dtype=bool), interrupted=lambda: True)


@pytest.mark.parametrize('field,value', [('edit_houghpeaks', '100.5'),
                                       ('edit_houghpeaks', '99'),
                                       ('edit_houghthreshold', '0'),
                                       ('edit_houghthreshold', '1.1'),
                                       ('edit_fillgap', '1'),
                                       ('edit_minlength', 'nan')])
def test_gui_parameter_limits_are_applied_before_work(field, value):
    values = dict(edit_houghpeaks='100', edit_houghthreshold='0.33',
                  edit_fillgap='5', edit_minlength='3')
    values[field] = value
    with pytest.raises(FieldError) as error:
        parameters_from_controls(tuple(values.items()))
    assert error.value.field == field
