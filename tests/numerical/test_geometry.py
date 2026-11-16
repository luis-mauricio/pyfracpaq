"""Analytical and metamorphic checks of distances and segment relations."""

import numpy as np
import pytest

from pyfracpaq.geometry import (
    Bounds, GeometryError, IntersectionKind, distance_point_segment,
    distance_point_segments, distance_points, iter_segment_intersections,
    point_distance, segment_intersection,
)


@pytest.mark.parametrize('norm,expected', [(1, 7), (2, 5), (np.inf, 4)])
def test_point_distances_and_norms(norm, expected):
    matrix = distance_points([[0, 0], [3, 4]], [[3, 4]], norm=norm)
    np.testing.assert_allclose(matrix, [[expected], [0]], rtol=1e-10, atol=1e-12)
    paired = distance_points([[0, 0], [3, 4]], [[3, 4], [0, 0]],
                             norm=norm, diagonal=True)
    np.testing.assert_allclose(paired, [expected, expected], rtol=1e-10, atol=1e-12)


def test_norm_generalisation_empty_and_tiny_distances():
    np.testing.assert_allclose(distance_points([0, 0], [1, 1], norm=3),
                               [[2 ** (1 / 3)]], rtol=1e-10, atol=1e-12)
    assert distance_points([], [[0, 0]]).shape == (0, 1)
    assert distance_points([[0, 0]], []).shape == (1, 0)
    assert distance_points([], [], diagonal=True).shape == (0,)
    assert point_distance([0, 0], [3e-200, 4e-200]) == 5e-200
    assert distance_points([0, 0], [3e-200, 4e-200])[0, 0] == 5e-200


@pytest.mark.parametrize('point,expected_distance,parameter,closest', [
    ((3, 4), 4, .3, (3, 0)), ((-3, 4), 5, 0, (0, 0)),
    ((13, 4), 5, 1, (10, 0)), ((0, 0), 0, 0, (0, 0)),
])
def test_distance_to_finite_segment(point, expected_distance, parameter, closest):
    result = distance_point_segment(point, [0, 0], [10, 0])
    np.testing.assert_allclose(result.distance, expected_distance,
                               rtol=1e-10, atol=1e-12)
    np.testing.assert_allclose(result.parameter, parameter, rtol=1e-10, atol=1e-12)
    np.testing.assert_allclose(result.point, closest, rtol=1e-10, atol=1e-12)


def test_zero_length_and_very_small_edges():
    result = distance_point_segment([3, 4], [0, 0], [0, 0])
    assert result.distance == 5 and result.parameter == 0
    result = distance_point_segment([5e-200, 1e-200], [0, 0], [1e-199, 0])
    assert result.parameter == 0
    np.testing.assert_allclose(result.distance, np.hypot(5e-200, 1e-200),
                               rtol=1e-10, atol=0)
    # The cutoff is the original library's squared-length epsilon, not a
    # general policy that drops short segments from the imported dataset.
    result = distance_point_segment([.5e-7, 1e-7], [0, 0], [1e-7, 0])
    np.testing.assert_allclose(result.parameter, .5, rtol=1e-10, atol=0)


def test_point_segment_matrix_order_and_empty_shapes():
    distances, positions = distance_point_segments(
        [[3, 4], [-3, 4]], [[0, 0, 10, 0], [0, 0, 0, 0]],
    )
    np.testing.assert_allclose(distances, [[4, 5], [5, 5]], rtol=1e-10, atol=1e-12)
    np.testing.assert_allclose(positions, [[.3, 0], [0, 0]], rtol=1e-10, atol=1e-12)
    assert distance_point_segments([], [[0, 0, 1, 1]])[0].shape == (0, 1)


@pytest.mark.parametrize('first,second,kind,points,parallel,coincident', [
    ([0, 0, 4, 0], [2, -1, 2, 1], 'point', [(2, 0)], False, False),
    ([0, 0, 4, 0], [4, 0, 4, 2], 'point', [(4, 0)], False, False),
    ([0, 0, 1, 0], [2, -1, 2, 1], 'none', [], False, False),
    ([0, 0, 4, 0], [0, 1, 4, 1], 'none', [], True, False),
    ([0, 0, 4, 0], [2, 0, 6, 0], 'overlap', [(2, 0), (4, 0)], True, True),
    ([0, 0, 4, 0], [6, 0, 2, 0], 'overlap', [(2, 0), (4, 0)], True, True),
    ([0, 0, 4, 0], [5, 0, 6, 0], 'none', [], True, True),
    ([0, 0, 4, 0], [4, 0, 6, 0], 'point', [(4, 0)], True, True),
    ([0, -4, 0, -1], [0, -3, 0, 2], 'overlap', [(0, -3), (0, -1)], True, True),
    ([2, 0, 2, 0], [0, 0, 4, 0], 'point', [(2, 0)], False, False),
    ([0, 0, 4, 0], [2, 0, 2, 0], 'point', [(2, 0)], False, False),
    ([2, 1, 2, 1], [0, 0, 4, 0], 'none', [], False, False),
    ([2, 0, 2, 0], [2, 0, 2, 0], 'point', [(2, 0)], False, False),
    ([2, 0, 2, 0], [3, 0, 3, 0], 'none', [], False, False),
])
def test_segment_relations(first, second, kind, points, parallel, coincident):
    result = segment_intersection(first, second)
    assert result.kind == kind
    assert result.intersects == (kind != 'none')
    assert result.parallel == parallel and result.coincident == coincident
    np.testing.assert_allclose(result.points, points, rtol=1e-10, atol=1e-12)
    for t, u, point in zip(
        result.parameters_first, result.parameters_second, result.points,
    ):
        a = np.asarray(first).reshape(2, 2)
        b = np.asarray(second).reshape(2, 2)
        np.testing.assert_allclose((1 - t) * a[0] + t * a[1], point,
                                   rtol=1e-10, atol=1e-12)
        np.testing.assert_allclose((1 - u) * b[0] + u * b[1], point,
                                   rtol=1e-10, atol=1e-12)


def test_nearly_parallel_lines_are_not_snapped():
    result = segment_intersection([0, 0, 1, 1e-15], [0, 1e-15, 1, 0])
    assert result.kind is IntersectionKind.POINT
    assert not result.parallel
    np.testing.assert_allclose(result.points, [[.5, 5e-16]], rtol=1e-10, atol=0)
    gap = np.nextafter(0., 1.)
    result = segment_intersection([0, 0, 1, 0], [0, gap, 1, gap])
    assert result.parallel and not result.coincident and not result.intersects


def test_exact_predicates_survive_cross_product_cancellation():
    n = 2 ** 27
    result = segment_intersection(
        [0, 0, n, n - 1], [-.5, -.5, n + .5, n - .5],
    )
    assert result.kind is IntersectionKind.POINT
    assert not result.parallel
    np.testing.assert_allclose(result.points, [[n / 2, (n - 1) / 2]],
                               rtol=1e-10, atol=1e-12)


def test_translation_reversal_and_exchange_preserve_crossing():
    for offset in (np.array([0, 0]), np.array([-100, 40])):
        a = np.array([[0, 0], [4, 4]]) + offset
        b = np.array([[0, 4], [4, 0]]) + offset
        for left, right in [(a, b), (b, a), (a[::-1], b), (a, b[::-1])]:
            result = segment_intersection(left.ravel(), right.ravel())
            assert result.kind is IntersectionKind.POINT
            np.testing.assert_allclose(result.points[0], [2, 2] + offset,
                                       rtol=1e-10, atol=1e-12)


def test_pair_iterator_is_ordered_and_keeps_discrete_relations():
    left = [[0, 0, 4, 0], [0, 2, 4, 2]]
    right = [[1, -1, 1, 3], [8, -1, 8, 3]]
    hits = [(i, j) for i, j, _ in iter_segment_intersections(left, right)]
    assert hits == [(0, 0), (1, 0)]
    pairs = list(iter_segment_intersections(left, right, include_disjoint=True))
    assert [(i, j) for i, j, _ in pairs] == [(0, 0), (0, 1), (1, 0), (1, 1)]
    assert not list(iter_segment_intersections([], right))


def test_pairwise_memory_guards_precede_allocation():
    with pytest.raises(MemoryError, match='smaller batches'):
        distance_points(np.zeros((10, 2)), np.zeros((10, 2)), max_bytes=8)
    with pytest.raises(MemoryError):
        distance_point_segments([[0, 0]], [[0, 0, 1, 1]], max_bytes=8)


@pytest.mark.parametrize('bad', [[np.nan, 0], [0, np.inf], [1], [1, 2, 3], ['1', '2']])
def test_invalid_point_arrays_fail(bad):
    with pytest.raises(GeometryError):
        distance_points(bad, [0, 0])


def test_invalid_domains_and_numeric_overflow_fail_explicitly():
    with pytest.raises(GeometryError):
        Bounds(1, 0, 0, 1)
    with pytest.raises(GeometryError):
        Bounds(0, 0, 1e200, 1e200)
    with pytest.raises(GeometryError, match='underflows'):
        Bounds(0, 0, 1e-200, 1e-200)
    with pytest.raises(GeometryError):
        distance_points([-1e308, 0], [1e308, 0])
    with pytest.raises(GeometryError, match='Projection'):
        distance_point_segment([-1e308, -1e308], [1e308, 1e308], [0, 1.5e308])
    assert Bounds(0, 0, 4, 0).area == 0
