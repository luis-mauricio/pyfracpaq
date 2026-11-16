"""Analytic circular estimators and approved finite-geometry Q-20 correction."""

from dataclasses import replace
import json
import logging
from math import pi

import numpy as np
import pytest

from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.analysis.circular import circle_grid, sample_circles
from pyfracpaq.domain import TraceInput, build_dataset
from pyfracpaq.domain.execution import FieldError, RunContext
from pyfracpaq.geometry import Bounds, GeometryError
from pyfracpaq.geometry.circles import circle_counts, _exact
from pyfracpaq.io.circular import export_circular
from reference_common import ROOT
from sprint3_reference import directional_dataset, reference_config


@pytest.mark.parametrize('segment,n,m', [
    ((-2, 0, 2, 0), 2, 0), ((0, -2, 0, 2), 2, 0),
    ((-2, .5, 2, .5), 2, 0), ((2, .5, 3, .5), 0, 0),
    ((-2, 1, 2, 1), 1, 0), ((2, 1, 3, 1), 0, 0),
    ((0, 0, .5, 0), 0, 2), ((0, 0, 2, 0), 1, 1),
    ((1, 0, 2, 0), 1, 0), ((-1, 0, 2, 0), 2, 0),
    ((-1, 0, 1, 0), 2, 0), ((0, 0, 1, 0), 1, 1),
    ((0, 1, 2, 1), 1, 0), ((1, 1, 2, 2), 0, 0),
])
@pytest.mark.parametrize('offset', [(0, 0), (-100, 75)])
def test_finite_intersections_tangencies_and_strict_endpoints(segment, n, m, offset):
    shifted = np.asarray(segment, dtype=float).reshape(2, 2) + offset
    for values in (shifted, shifted[::-1]):
        hits, ends = circle_counts(values.reshape(1, 4), offset, 1)
        assert (hits.tolist(), ends.tolist()) == ([n], [m])


def test_frozen_sprint_zero_circle_oracles():
    fixtures = json.loads((ROOT / 'tests/fixtures/analytic_cases.json').read_text())
    cases = fixtures['cases'] if isinstance(fixtures, dict) else fixtures
    for case in cases:
        if case['family'] != 'circles':
            continue
        data, expected = case['input'], case['expected']
        n, m = circle_counts(np.array(data['segment']).reshape(1, 4),
                             data['centre'], data['radius'])
        assert n[0] == expected.get('boundary_intersections', expected.get('unique_boundary_points'))
        assert m[0] == expected['endpoints_inside']


def test_near_tangent_no_epsilon_snapping_and_extreme_scales():
    ys = [np.nextafter(1., 0), 1., np.nextafter(1., 2)]
    segments = [[-2, y, 2, y] for y in ys]
    assert circle_counts(segments, (0, 0), 1)[0].tolist() == [2, 1, 0]
    for scale in (1e-200, 1e200):
        assert circle_counts(np.array(segments) * scale, (0, 0), scale)[0].tolist() == [2, 1, 0]


def test_vectorised_path_agrees_with_exact_rational_fallback():
    rng = np.random.default_rng(607)
    for offset in ((0, 0), (1e12, -1e12)):
        lines = rng.normal(size=(600, 4)) * 2 + np.tile(offset, 2)
        n, m = circle_counts(lines, offset, .99)
        expected = np.array([_exact(line, offset, .99) for line in lines])
        np.testing.assert_array_equal(n, expected[:, 0])
        np.testing.assert_array_equal(m, expected[:, 1])
    assert not n.flags.writeable and not m.flags.writeable


@pytest.mark.parametrize('bounds,shape,step', [
    (Bounds(0, 0, 6, 6), (2, 2), 2),
    (Bounds(-10, -20, 2, -14), (2, 5), 2),
    (Bounds(0, 0, 6, 12), (5, 2), 2),
])
def test_short_side_grid_source_arithmetic_and_column_major_order(bounds, shape, step):
    grid = circle_grid(bounds, 2)
    assert grid.shape == shape
    assert grid.dx == grid.dy == step
    assert grid.radius == .99
    np.testing.assert_array_equal(grid.centres[:shape[0], 0], np.repeat(grid.x[0], shape[0]))
    np.testing.assert_array_equal(grid.centres[:shape[0], 1], grid.y)
    np.testing.assert_allclose(grid.extent, (grid.x[0] - 1, grid.x[-1] + 1,
                                            grid.y[0] - 1, grid.y[-1] + 1))


@pytest.mark.parametrize('bounds,count', [
    (Bounds(0, 0, 0, 1), 2), (Bounds(0, 0, 1, 0), 2),
    (Bounds(0, 0, 1, 1), 1), (Bounds(0, 0, 1, 1), True),
    (Bounds(0, 0, 1, 1), 2.5), (Bounds(0, 0, 1, 1), 100000),
    (Bounds(0, 0, 1e20, 1), 2),
])
def test_empty_domains_and_resource_limits_rejected_before_allocation(bounds, count):
    with pytest.raises(GeometryError):
        circle_grid(bounds, count)


def test_estimators_count_segment_ends_not_deduplicated_vertices_and_global_separation():
    # Centres (2,2),(4,2),(2,4),(4,4), r=.99. First circle has one
    # interior segment, two incident segment endpoints at (2,2), and a secant.
    data = build_dataset([TraceInput(((2, 2), (2.5, 2))),
                          TraceInput(((0, 2), (2, 2), (6, 2))),
                          TraceInput(((0, 0), (6, 6)))])
    result = sample_circles(data, 2)
    assert result.intersections[0, 0] == 4
    assert result.endpoints_inside[0, 0] == 4
    assert result.intensity[0, 0] == pytest.approx(4 / (4 * .99))
    assert result.density[0, 0] == pytest.approx(4 / (2 * pi * .99 ** 2))
    assert result.global_intensity == data.total_length / 36
    assert result.global_density == 4 / 36
    assert result.global_density != result.density.mean()
    assert all(not getattr(result, a).flags.writeable for a in
               ('intersections', 'endpoints_inside', 'intensity', 'density'))
    scaled = sample_circles(data.with_scale(2), 2)
    np.testing.assert_array_equal(result.intersections, scaled.intersections)
    np.testing.assert_array_equal(result.endpoints_inside, scaled.endpoints_inside)
    np.testing.assert_allclose(scaled.intensity, result.intensity * 2, rtol=1e-10, atol=1e-12)
    np.testing.assert_allclose(scaled.density, result.density * 4, rtol=1e-10, atol=1e-12)
    assert scaled.global_intensity == result.global_intensity * 2
    assert scaled.global_density == result.global_density * 4


def test_translated_dataset_preserves_counts_rates_and_shifts_centres():
    data = directional_dataset()
    moved = build_dataset([TraceInput(tuple((n.x - 120, n.y + 32) for n in t.nodes))
                           for t in data.traces])
    a, b = sample_circles(data, 3), sample_circles(moved, 3)
    for name in ('intersections', 'endpoints_inside', 'intensity', 'density'):
        np.testing.assert_array_equal(getattr(a, name), getattr(b, name))
    np.testing.assert_array_equal(b.grid.centres, a.grid.centres + [-120, 32])


@pytest.mark.parametrize('selected', [('MAP-07',), ('MAP-08',), ('MAP-07', 'MAP-08')])
def test_coupled_exports_cached_once_source_format_and_selected_global_logs(selected, tmp_path, caplog):
    cfg = reference_config(selected, edit_numscancircles='2')
    with caplog.at_level(logging.INFO):
        results = AnalysisRegistry().execute(directional_dataset(),
            RunContext(cfg, tmp_path, tmp_path, 'circular'), lambda *a: None, lambda: False)
    assert len(list(tmp_path.glob('*.txt'))) == 2
    assert all(result.data is results[0].data for result in results)
    assert caplog.text.count('Saved circular TXT:') == 2
    assert ('Global intensity' in caplog.text) == ('MAP-07' in selected)
    assert ('Global density' in caplog.text) == ('MAP-08' in selected)
    r = results[0].data
    for kind in ('intensity', 'density'):
        expected = ''.join(f'{x:8.1f} {y:8.1f} {v:14.8f}\n' for (x, y), v in
                           zip(r.grid.centres, getattr(r, kind).ravel(order='F')))
        assert (tmp_path / f'FracPaQ2D{kind}_Run1.txt').read_text() == expected
    flipped = replace(cfg, flip_x=True, flip_y=True)
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    AnalysisRegistry().execute(directional_dataset(), RunContext(flipped, tmp_path, tmp_path, 'flip'),
                                lambda *a: None, lambda: False)
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before


def test_export_blank_tag_validation_staging_failure_preserves_targets(tmp_path, monkeypatch):
    paths = export_circular([[1, 2], [3, 4]], [0, 1], [2, 0], '', tmp_path)
    assert paths[0].name == 'FracPaQ2Dintensity_.txt'
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    real = np.savetxt
    calls = 0
    def failure(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError('disk full')
        return real(*args, **kwargs)
    monkeypatch.setattr(np, 'savetxt', failure)
    with pytest.raises(OSError, match='disk full'):
        export_circular([[1, 2]], [3], [4], '', tmp_path)
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before
    with pytest.raises(ValueError):
        export_circular([[1, 2]], [np.nan], [4], '', tmp_path)


def test_cancellation_between_circles_leaves_no_output_and_progress_is_monotonic(tmp_path):
    cfg = reference_config(('MAP-07', 'MAP-08'), edit_numscancircles='12')
    messages = []
    results = AnalysisRegistry().execute(directional_dataset(), RunContext(cfg, tmp_path, tmp_path, 'stop'),
        lambda p, text: messages.append((p, text)), lambda: len(messages) > 3)
    assert results == () and list(tmp_path.iterdir()) == []
    assert [p for p, _ in messages] == sorted(p for p, _ in messages)


def test_zero_area_error_is_contextual_no_export(tmp_path):
    cfg = reference_config(('MAP-08',))
    data = build_dataset([TraceInput(((0, 0), (5, 0)))])
    with pytest.raises(FieldError, match='positive width') as caught:
        AnalysisRegistry().execute(data, RunContext(cfg, tmp_path, tmp_path, 'zero'),
                                   lambda *a: None, lambda: False)
    assert caught.value.field == 'edit_numscancircles'
    assert list(tmp_path.iterdir()) == []
