"""Analytical checks of the actual TXT importer and immutable domain model."""

from dataclasses import FrozenInstanceError, fields
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from pyfracpaq.domain import (
    InputMode, Node, Segment, Trace, TraceGeometryError, TraceInput, build_dataset,
)
from pyfracpaq.geometry import GeometryError
from pyfracpaq.io import NodeFileError, read_txt
from reference_common import REFERENCE, ROOT

CASES = json.loads((ROOT / 'tests/fixtures/analytic_cases.json').read_text())['cases']
GEOMETRY = [case for case in CASES if case['family'] == 'geometry']


def close(actual, expected, scale=1):
    np.testing.assert_allclose(actual, expected, rtol=1e-10,
                               atol=1e-12 * max(1, scale))


@pytest.mark.parametrize('case', GEOMETRY, ids=lambda case: case['id'])
def test_importer_against_frozen_analytical_oracles(case):
    dataset = read_txt(ROOT / case['input']['file'],
                       pixels_per_metre=case['input'].get('scale'))
    expected = case['expected']
    arrays = dataset.as_arrays()
    for field, actual in [('traces', dataset.n_traces),
                          ('segments', dataset.n_segments),
                          ('nodes', dataset.n_nodes)]:
        if field in expected:
            assert actual == expected[field]
    comparisons = {
        'segment_lengths': arrays.segment_lengths,
        'raw_angles_degrees': arrays.raw_angles,
        'segment_midpoints': arrays.segment_midpoints,
        'trace_lengths': arrays.trace_lengths,
        'bounds_xyxy': [dataset.bounds.x_min, dataset.bounds.y_min,
                        dataset.bounds.x_max, dataset.bounds.y_max],
        'area': dataset.area,
    }
    for field, actual in comparisons.items():
        if field in expected:
            length_scale = max(dataset.bounds.width, dataset.bounds.height)
            characteristic = (360 if 'angles' in field else
                              length_scale ** 2 if field == 'area'
                              else length_scale)
            close(actual, expected[field], characteristic)
    if 'trace_length' in expected:
        close(dataset.traces[0].total_length, expected['trace_length'])
    if 'trace_halfway_point' in expected:
        close(dataset.traces[0].midpoint, expected['trace_halfway_point'])


def test_duplicate_provenance_segment_links_and_array_order(tmp_path):
    path = tmp_path / 'nodes.txt'
    path.write_text('0\t0\t0\t0\t3\t0\t3\t0\t3\t4\n0\t0\t0\t2\n')
    dataset = read_txt(path)
    trace = dataset.traces[0]
    assert [node.id for node in trace.nodes] == [(0, 0), (0, 2), (0, 4)]
    assert [d.source_node_index for d in dataset.diagnostics] == [1, 3]
    assert [d.retained_node_id for d in dataset.diagnostics] == [(0, 0), (0, 2)]
    assert all(d.source_line == 1 for d in dataset.diagnostics)
    assert dataset.traces[1].nodes[0] != trace.nodes[0]
    arrays = dataset.as_arrays()
    close(arrays.segment_lengths, [3, 4, 2])
    close(arrays.start_lengths, [0, 3, 0])
    close(arrays.end_lengths, [3, 7, 2])
    assert arrays.segment_trace_ids.tolist() == [0, 0, 1]
    for segment in dataset.segments:
        assert segment.start is dataset.traces[segment.trace_id].nodes[segment.id[1]]
        assert segment.end is dataset.traces[segment.trace_id].nodes[segment.id[1] + 1]
        assert segment.length > 0
    assert arrays.segment_node_ids.tolist()[0] == [[0, 0], [0, 2]]


def test_closed_trace_is_not_merged_or_rejected():
    dataset = build_dataset([TraceInput(((0, 0), (3, 0), (0, 0)))])
    assert dataset.n_nodes == 3
    close(dataset.traces[0].total_length, 6)
    close(dataset.traces[0].euclidean_length, 0)
    close(dataset.traces[0].midpoint, [3, 0])
    assert not dataset.diagnostics


@pytest.mark.parametrize('end,angle', [((3, 4), 36.86989764584402),
                                      ((-3, -4), 36.86989764584402),
                                      ((3, -4), 143.13010235415598),
                                      ((-3, 4), 143.13010235415598),
                                      ((0, -4), 0), ((-3, 0), 90)])
def test_raw_angles_and_midpoints_in_all_quadrants(end, angle):
    trace = build_dataset([TraceInput(((0, 0), end))]).traces[0]
    close(trace.segments[0].raw_angle, angle, 360)
    close(trace.midpoint, np.asarray(end) / 2)
    close(trace.euclidean_length, np.hypot(*end))


def test_scale_is_rebuilt_from_original_and_has_derived_units():
    original = read_txt(ROOT / 'tests/fixtures/nodes/mixed.txt')
    scaled = original.with_scale(2)
    repeated = scaled.with_scale(2)
    restored = repeated.with_scale(None)
    close(scaled.as_arrays().node_coordinates,
          original.as_arrays().node_coordinates / 2)
    close(repeated.as_arrays().node_coordinates, scaled.as_arrays().node_coordinates)
    close(restored.as_arrays().node_coordinates, original.as_arrays().node_coordinates)
    close(scaled.total_length, original.total_length / 2)
    close(scaled.area, original.area / 4)
    assert original.source_traces == scaled.source_traces == restored.source_traces
    assert (scaled.as_arrays().node_ids.tolist()
            == original.as_arrays().node_ids.tolist())
    assert original.length_unit == 'pixels'
    assert scaled.length_unit == 'metres'
    assert scaled.area_unit == scaled.permeability_unit == 'metres^2'
    assert scaled.intensity_unit == 'metres^-1'
    assert scaled.density_unit == 'metres^-2'
    assert scaled.source == original.source


@pytest.mark.parametrize('scale', [0, -1, float('inf'), float('nan'), True, '2'])
def test_invalid_scale_is_rejected(scale):
    with pytest.raises(GeometryError):
        read_txt(ROOT / 'tests/fixtures/nodes/mixed.txt', pixels_per_metre=scale)


def test_translation_preserves_lengths_area_and_diagonal():
    raw = TraceInput(((0, 0), (3, 0), (3, 4)))
    shifted = TraceInput(((-100, -200), (-97, -200), (-97, -196)))
    a, b = build_dataset([raw]), build_dataset([shifted])
    close(a.area, b.area)
    close(a.bounds.diagonal, 5)
    close(b.bounds.diagonal, 5)
    close(a.as_arrays().segment_lengths, b.as_arrays().segment_lengths)
    assert b.bounds.x_max == -97 and b.bounds.y_max == -196


def test_model_and_array_snapshots_do_not_mutate_source():
    dataset = read_txt(ROOT / 'tests/fixtures/nodes/mixed.txt')
    with pytest.raises(FrozenInstanceError):
        dataset.nodes[0].x = 9
    arrays = dataset.as_arrays()
    for field in fields(arrays):
        array = getattr(arrays, field.name)
        assert not array.flags.writeable
        assert array.dtype == (np.int64 if 'ids' in field.name else np.float64)
    with pytest.raises(ValueError):
        arrays.segment_lengths[0] = 99
    arrays.segment_lengths.setflags(write=True)
    arrays.segment_lengths[0] = 99
    assert dataset.segments[0].length == 4
    assert dataset.as_arrays().segment_lengths[0] == 4


@pytest.mark.parametrize('mode', list(InputMode))
def test_common_constructor_has_complete_fields_for_every_origin(mode):
    dataset = build_dataset([
        TraceInput(((0, 0), (3, 4)), (1, 0, 0)),
        TraceInput(((0, 0), (0, 4)), (0, 0, 1)),
    ], input_mode=mode, source='source')
    assert dataset.input_mode is mode
    assert dataset.colours == ((1., 0., 0.), (0., 0., 1.))
    assert dataset.n_traces == 2
    assert dataset.n_segments == 2
    assert dataset.n_nodes == 4
    close(dataset.as_arrays().segment_midpoints, [[1.5, 2], [0, 2]])
    assert all(t.colour for t in dataset.traces)


def test_bom_crlf_blank_lines_trailing_tabs_and_physical_lines(tmp_path):
    path = tmp_path / 'nós com espaços.TXT'
    path.write_bytes(b'\xef\xbb\xbf\r\n0\t0\t3\t4\t \t\r\n\r\n1\t2\t4\t2\t4\t6\r\n')
    dataset = read_txt(path)
    assert [t.source_line for t in dataset.traces] == [2, 4]
    assert [t.id for t in dataset.traces] == [0, 1]
    assert dataset.source == path.resolve()
    close(dataset.as_arrays().trace_lengths, [5, 7])


@pytest.mark.parametrize('text,code,column', [
    ('0\t0\t1', 'incomplete_pair', 3),
    ('0\t0', 'too_few_nodes', None),
    ('0\t\t1\t2', 'empty_coordinate', 2),
    ('\t0\t1\t2', 'empty_coordinate', 1),
    ('0,0,1,2', 'incomplete_pair', 1),
    ('0\t0\tNaN\t2', 'nonfinite_coordinate', 3),
    ('0\t0\t1e999\t2', 'nonfinite_coordinate', 3),
    ('0\t0\t1_0\t2', 'invalid_number', 3),
    ('0\t0\t1+2\t2', 'invalid_number', 3),
    ('0\t0\t1\t# comment', 'invalid_number', 4),
    ('0\t0\t0\t0', 'degenerate_trace', None),
])
def test_bad_rows_have_line_column_and_no_partial_result(tmp_path, text, code, column):
    path = tmp_path / 'bad.txt'
    path.write_text('0\t0\t3\t4\n\n' + text + '\n')
    with pytest.raises(NodeFileError) as raised:
        read_txt(path)
    error = raised.value
    assert error.path == path.resolve()
    issue, = error.issues
    assert (issue.line, issue.column, issue.code) == (3, column, code)
    assert f'{path}:3' in str(error)


def test_all_invalid_lines_are_reported(tmp_path):
    path = tmp_path / 'bad.txt'
    path.write_text('0\t0\t1\n1\t1\t1\t1\n\n0\t0\tinf\t1\n')
    with pytest.raises(NodeFileError) as raised:
        read_txt(path)
    assert [issue.line for issue in raised.value.issues] == [1, 2, 4]


@pytest.mark.parametrize('name', [
    'empty', 'incomplete', 'degenerate', 'nonfinite', 'comma',
])
def test_frozen_invalid_fixtures(name):
    with pytest.raises(NodeFileError):
        read_txt(ROOT / f'tests/fixtures/nodes/{name}.txt')


def test_missing_directory_and_bad_encoding_have_context(tmp_path):
    invalid = tmp_path / 'encoding.txt'
    invalid.write_bytes(b'\xff\xfe')
    for path, code in [
        (tmp_path / 'missing', 'io'), (tmp_path, 'io'), (invalid, 'encoding'),
    ]:
        with pytest.raises(NodeFileError) as raised:
            read_txt(path)
        assert raised.value.issues[0].code == code
        assert str(path) in str(raised.value)


def test_current_directory_does_not_change_absolute_source(tmp_path, monkeypatch):
    path = ROOT / 'tests/fixtures/nodes/mixed.txt'
    monkeypatch.chdir(tmp_path)
    assert read_txt(path).source == path
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('name', [
    'IYXtest1_converted.txt', 'IYXtest2_converted.txt',
    'Souter_Blue.txt',
])
def test_selected_real_tabulated_examples(name):
    examples = json.loads((REFERENCE / 'examples.json').read_text())
    entry = next(e for e in examples if Path(e['path']).name == name)
    dataset = read_txt(ROOT / entry['path'])
    assert dataset.n_traces == entry['records']
    assert dataset.n_nodes == dataset.n_segments + dataset.n_traces
    assert np.isfinite(dataset.as_arrays().segment_lengths).all()
    assert all(segment.length > 0 for segment in dataset.segments)


@pytest.mark.parametrize('name,excluded', [
    ('map1_edit_converted.txt', [1589, 1595, 1604]),
    ('map7_edit_converted.txt', [2496, 3242]),
])
def test_real_degenerate_traces_are_reported_and_excluded_explicitly(
    tmp_path, name, excluded,
):
    source = ROOT / 'fracpaq-matlab' / name
    with pytest.raises(NodeFileError) as raised:
        read_txt(source)
    assert [issue.line for issue in raised.value.issues] == excluded
    assert all(issue.code == 'degenerate_trace' for issue in raised.value.issues)
    lines = source.read_text().splitlines()
    prepared = tmp_path / name
    prepared.write_text('\n'.join(
        '' if line in excluded else text
        for line, text in enumerate(lines, 1)
    ) + '\n')
    dataset = read_txt(prepared)
    assert dataset.n_traces == len(lines) - len(excluded)
    assert dataset.n_nodes == dataset.n_segments + dataset.n_traces
    assert all(t.source_line not in excluded for t in dataset.traces)
    assert all(segment.length > 0 for segment in dataset.segments)


def test_scientific_core_imports_without_gui_modules():
    script = (
        'import sys; from pyfracpaq.io import read_txt; '
        'from pyfracpaq.geometry import segment_intersection; '
        'assert not any(k.startswith(("PySide6", "matplotlib")) for k in sys.modules)'
    )
    subprocess.run([sys.executable, '-c', script], check=True, cwd=ROOT)


def test_invalid_domain_records_cannot_create_partial_datasets():
    with pytest.raises(GeometryError, match='empty dataset'):
        build_dataset([])
    with pytest.raises(TraceGeometryError) as raised:
        build_dataset([TraceInput(((1, 1), (1, 1)), source_line=4)])
    assert raised.value.source_line == 4
    for points in [((0, 0), (float('nan'), 1)), ((0, 0), (1, float('inf')))]:
        with pytest.raises(GeometryError):
            TraceInput(points)
    for colour in [(2, 0, 0), (0, 0), (0, float('nan'), 0)]:
        with pytest.raises(GeometryError):
            TraceInput(((0, 0), (1, 1)), colour)
    with pytest.raises(GeometryError):
        Segment((0, 0), 0, Node((0, 0), 0, 0), Node((1, 0), 1, 1))
    with pytest.raises(GeometryError):
        Trace(0, (Node((0, 0), 1, 1),))
    with pytest.raises(GeometryError, match='Dataset length'):
        build_dataset([TraceInput(((0, 0), (1e308, 0)))] * 2)


@pytest.mark.parametrize('points,scale', [
    (((0, 0), (1e-300, 0)), 1e300),
    (((0, 0), (1e300, 0)), 1e-300),
])
def test_scaling_outside_float64_range_is_rejected_with_line(points, scale):
    with pytest.raises(TraceGeometryError) as raised:
        build_dataset([TraceInput(points, source_line=5)], pixels_per_metre=scale)
    assert raised.value.source_line == 5
