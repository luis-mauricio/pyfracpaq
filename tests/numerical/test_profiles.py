"""Actual source arrays, geometric oracles and shared finite circle counts."""

from dataclasses import FrozenInstanceError, replace

import numpy as np
import pytest
from scipy.io import loadmat

from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.analysis.profiles import ALONG, FROM, along_profile, circular_profile, compute_graphs
from pyfracpaq.domain import TraceInput, build_dataset
from pyfracpaq.domain.execution import FieldError, RunContext
from pyfracpaq.geometry import GeometryError
from pyfracpaq.geometry.profiles import ProfileLine, signed_profile_distances
from reference_common import REFERENCE
from sprint1213_reference import configuration, graph_dataset


def test_along_and_from_match_executed_matlab_data(tmp_path):
    expected = loadmat(REFERENCE / 'sprint13/native/graph_arrays.mat', simplify_cells=True)['graphs']
    dataset = graph_dataset()
    config = configuration((*ALONG, *FROM))
    result = compute_graphs(dataset, RunContext(config, tmp_path, tmp_path, 'native'), lambda *_: None)
    for key, actual in (('trace_along', result.along.trace_lengths),
                        ('segment_along', result.along.segment_lengths),
                        ('angle_along', result.along.raw_angles)):
        np.testing.assert_allclose(result.along.distances, np.asarray(expected[key]['x'], dtype=float), atol=1e-12)
        np.testing.assert_allclose(actual, np.asarray(expected[key]['y'], dtype=float), atol=1e-12)
    for key, distances, values in (
        ('trace_from', result.trace_distances, dataset.as_arrays().trace_lengths),
        ('segment_from', result.segment_distances, dataset.as_arrays().segment_lengths),
        ('angle_from', result.segment_distances, dataset.as_arrays().raw_angles)):
        np.testing.assert_allclose(distances, np.asarray(expected[key]['x'], dtype=float), atol=1e-12)
        np.testing.assert_allclose(values, np.asarray(expected[key]['y'], dtype=float), atol=1e-12)
    assert result.along.trace_ids.tolist() == [0, 0, 1]
    assert not result.segment_distances.flags.writeable
    assert not list(tmp_path.iterdir())


def test_repeated_shared_vertex_noncoincident_hits_and_collinear_contacts():
    dataset = build_dataset([TraceInput(((-2, 1), (0, 0), (2, 1))),
                             TraceInput(((-3, 0), (-2, 0)))])
    result = along_profile(dataset, ProfileLine((-2, 0), (2, 0)))
    assert result.trace_ids.tolist() == [0, 0]
    assert result.distances.tolist() == [2, 2]
    assert result.segment_ids.tolist() == [[0, 0], [0, 1]]


def test_reverse_line_reverses_distance_origin_and_signed_from_support():
    dataset, line = graph_dataset(), ProfileLine((-6, 0), (6, 0))
    reverse = ProfileLine(line.end, line.start)
    a, b = along_profile(dataset, line), along_profile(dataset, reverse)
    np.testing.assert_allclose(b.distances, line.length - a.distances)
    np.testing.assert_array_equal(a.segment_ids, b.segment_ids)
    assert signed_profile_distances([[100, 2], [-100, -3]], line).tolist() == [-2, 3]
    np.testing.assert_allclose(signed_profile_distances([[100, 2]], reverse), [2])
    with pytest.raises(FrozenInstanceError):
        line.start = (0, 0)


@pytest.mark.parametrize('bad', [((0, 0), (0, 0)), ((0, 0), (np.inf, 0))])
def test_invalid_line_is_rejected(bad):
    with pytest.raises(GeometryError):
        ProfileLine(*bad)


def test_absent_selection_is_field_error_but_zero_coordinate_sum_is_valid(tmp_path):
    registry = AnalysisRegistry()
    with pytest.raises(FieldError, match='Select two distinct') as error:
        registry.validate(configuration(ALONG, line=None))
    assert error.value.field == 'pushbutton_selectgraphendpoints'
    registry.validate(configuration(ALONG))  # (-6,0)+(6,0) sums to zero.
    with pytest.raises(FieldError):
        compute_graphs(graph_dataset(), RunContext(configuration(ALONG, line=None), tmp_path, tmp_path, 'x'), lambda *_: None)


def test_no_intersections_and_cancelled_profiles():
    dataset = graph_dataset()
    empty = along_profile(dataset, ProfileLine((-6, 10), (6, 10)))
    assert empty.points.shape == (0, 2) and empty.segment_ids.shape == (0, 2)
    assert not len(empty.distances)
    with pytest.raises(InterruptedError):
        along_profile(dataset, ProfileLine((-6, 0), (6, 0)), interrupted=lambda: True)
    with pytest.raises(InterruptedError):
        circular_profile(dataset, ProfileLine((-6, 0), (6, 0)), 3, interrupted=lambda: True)


def test_approved_density_normalization_and_native_intensity():
    result = circular_profile(graph_dataset(), ProfileLine((-6, 0), (6, 0)), 3)
    assert result.radius == 2
    np.testing.assert_array_equal(result.centres, [[-4, 0], [0, 0], [4, 0]])
    assert result.distances.tolist() == [2, 6, 10]
    assert result.intersections.tolist() == [2, 0, 2]
    assert result.endpoints_inside.tolist() == [0, 2, 0]
    np.testing.assert_allclose(result.intensity, [.25, 0, .25])
    np.testing.assert_allclose(result.density, [0, 1 / (4 * np.pi), 0])
    assert not result.centres.flags.writeable


@pytest.mark.parametrize('count', [0, 1, 2.5, True, 100_000_000])
def test_invalid_or_unbounded_circle_count(count):
    with pytest.raises((GeometryError, MemoryError)):
        circular_profile(graph_dataset(), ProfileLine((-6, 0), (6, 0)), count)


def test_north_and_flips_do_not_transform_profile_data(tmp_path):
    config = configuration((*ALONG, *FROM))
    other = replace(configuration((*ALONG, *FROM), edit_degfromnorth='45'), flip_x=True, flip_y=True)
    results = [compute_graphs(graph_dataset(), RunContext(cfg, tmp_path, tmp_path, 'x'), lambda *_: None)
               for cfg in (config, other)]
    np.testing.assert_array_equal(results[0].along.raw_angles, results[1].along.raw_angles)
    np.testing.assert_array_equal(results[0].trace_distances, results[1].trace_distances)
    np.testing.assert_array_equal(results[0].segment_distances, results[1].segment_distances)


def test_hough_from_uses_actual_segment_midpoints(tmp_path):
    from pyfracpaq.analysis.hough import HoughParameters
    from pyfracpaq.io.images import read_image
    from reference_common import ROOT

    dataset = read_image(ROOT / 'tests/fixtures/images/tensor_network.tif', HoughParameters()).dataset
    cfg = configuration(FROM, line=ProfileLine((0, 10), (60, 10)))
    result = compute_graphs(dataset, RunContext(cfg, tmp_path, tmp_path, 'image'), lambda *_: None)
    coordinates = dataset.as_arrays().segment_coordinates
    expected_y = coordinates[:, 1] / 2 + coordinates[:, 3] / 2
    np.testing.assert_allclose(result.segment_distances, 10 - expected_y, atol=1e-12)
