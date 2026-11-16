"""Strict SVG geometry, colour sets and conversion side-effect contracts."""

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.domain.execution import RunContext
from pyfracpaq.io import NodeFileError, read_txt
from pyfracpaq.io.colours import filename_colour, hex_rgb, normalise_hex
from pyfracpaq.io.svg import SvgInputError, convert_svg, read_svg, write_conversion
from reference_common import ROOT
from sprint3_reference import reference_config


def svg(tmp_path, body, *, attributes=''):
    path = tmp_path / 'map.SVG'
    path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" {attributes}>'
                    + body + '</svg>')
    return path


def test_plain_namespace_group_style_order_and_source_relative_outputs(tmp_path):
    path = svg(tmp_path, '<g stroke="#aBc" opacity="1e0" style="stroke: #F00; fill: none">'
               '<line y2="4" x2="3" y1="0" x1="0"/>'
               '<polyline points="0,0 0,2 2,2"/>'
               '<path id="poly" d="M 1e0,1 L2,1 2,3"/></g>')
    result = read_svg(path, pixels_per_metre=2)
    assert not list(tmp_path.glob('*.txt'))  # Preparation has no writes.
    assert result.dataset.n_traces == 3 and result.dataset.n_segments == 5
    assert result.dataset.colours == ((1, 0, 0),)
    assert [e.kind for e in result.tables[0].elements] == ['path', 'polyline', 'line']
    targets = write_conversion(result)
    assert targets == (path.with_name('map_converted.txt'),)
    raw = targets[0].read_bytes()
    assert raw.startswith(b'  1.00000000\t  1.00000000')
    assert b'\t\r\n' in raw and not raw.endswith(b'\n')
    reloaded = read_txt(targets[0], pixels_per_metre=2, colour=(1, 0, 0))
    np.testing.assert_array_equal(result.dataset.as_arrays().node_coordinates,
                                  reloaded.as_arrays().node_coordinates)
    np.testing.assert_array_equal(result.dataset.with_scale(None).as_arrays().node_coordinates,
                                  read_svg(path).dataset.as_arrays().node_coordinates)
    # A child cannot erase an ancestor's composited transparency.
    path = svg(tmp_path, '<g opacity="0.5"><line opacity="1" x2="3"/></g>')
    with pytest.raises(SvgInputError, match='Transparent'):
        read_svg(path)


def test_multicolour_sorted_groups_individual_reimport_and_unrelated_files(tmp_path):
    source = ROOT / 'tests/fixtures/svg/multicolour.svg'
    path = tmp_path / 'colors.with.dots.SVG'
    path.write_bytes(source.read_bytes())
    sentinel = tmp_path / 'foreign_converted.txt'
    sentinel.write_bytes(b'')
    old = tmp_path / 'colors.with.dots_colourFFFFFF_converted.txt'
    old.write_text('unrelated previous set')
    result = convert_svg(path)
    assert [t.path.name for t in result.tables] == [
        'colors.with.dots_colour0000FF_converted.txt',
        'colors.with.dots_colourFF0000_converted.txt']
    assert (result.dataset.n_traces, result.dataset.n_segments, result.dataset.n_nodes) == (2, 3, 5)
    assert result.dataset.colours == ((0, 0, 1), (1, 0, 0))
    red = read_txt(result.tables[1].path)
    assert red.colours == ((1, 0, 0),) and red.n_segments == 1
    assert sentinel.exists() and sentinel.stat().st_size == 0
    assert old.read_text() == 'unrelated previous set'
    assert not list(tmp_path.glob('.pyfracpaq-*'))


@pytest.mark.parametrize('body', [
    '<path d="M0 0 C1 1 2 2 3 3"/>', '<path d="m0 0 l2 3"/>',
    '<path d="M0 0 H4"/>', '<path d="M0 0 L1 1 Z"/>',
    '<path d="M0 0 M1 1 L2 2"/>', '<path d="M0 0 L1 1 L"/>',
    '<path d="M0 0 L L1 1"/>', '<path d="M0 0 L1"/>',
    '<polygon points="0,0 1,1 2,0"/>', '<line x2="3" transform="translate(1,2)"/>',
    '<g transform="scale(2)"><line x2="3"/></g>',
    '<line x2="3px"/>', '<line x2="3" stroke="url(#gradient)"/>',
    '<line x2="3" stroke="none"/>', '<line x2="3" stroke="##FF0000"/>',
    '<line x2="3" class="st0"/>', '<use href="#line"/>',
    '<style>.st0{stroke:#ff0000}</style><line x2="3"/>',
    '<line x2="3" style="transform:translate(1px)"/>',
    '<line x2="NaN"/>', '<line x2="1e999"/>', '<line x2="0"/>',
    '<polyline points="0,,0 1,1"/>', '<path d="M0 0 L1 1,"/>',
])
def test_unsupported_or_degenerate_geometry_rejects_whole_conversion(tmp_path, body):
    path = svg(tmp_path, '<line x2="4"/>' + body)
    sentinel = tmp_path / 'map_converted.txt'
    sentinel.write_text('previous')
    with pytest.raises(SvgInputError):
        convert_svg(path)
    assert sentinel.read_text() == 'previous'
    assert not list(tmp_path.glob('.pyfracpaq-*'))


def test_external_entities_rejected_without_replacement(tmp_path):
    path = tmp_path / 'unsafe.svg'
    path.write_text('<!DOCTYPE svg [<!ENTITY x SYSTEM "file:///not-read">]>'
                    '<svg>&x;<line x2="4"/></svg>')
    with pytest.raises(SvgInputError, match='parse SVG'):
        read_svg(path)
    assert not list(tmp_path.glob('*.txt'))


def test_conversion_precision_is_the_dataset_source_and_normalises_duplicates(tmp_path):
    path = svg(tmp_path, '<polyline points="0,0 0,0 3.123456789,4"/>')
    result = convert_svg(path)
    assert result.dataset.n_nodes == 2
    assert result.dataset.traces[0].nodes[-1].x == 3.12345679
    assert result.dataset.diagnostics[0].code == 'consecutive_duplicate'
    assert read_txt(result.tables[0].path).n_nodes == result.dataset.n_nodes


@pytest.mark.parametrize('value,expected', [('#a0b1c2', 'A0B1C2'), ('#f00', 'FF0000'),
                                           ('00ff00', '00FF00')])
def test_hex_normalisation_and_individual_file_detection(value, expected):
    assert normalise_hex(value) == expected
    np.testing.assert_allclose(hex_rgb(value), [int(expected[i:i+2], 16) / 255
                                               for i in (0, 2, 4)])
    assert filename_colour(f'map_colour{expected.lower()}_converted.TXT') == hex_rgb(expected)


def test_conversion_failure_staging_preserves_every_old_target(tmp_path, monkeypatch):
    path = tmp_path / 'multicolour.svg'
    path.write_bytes((ROOT / 'tests/fixtures/svg/multicolour.svg').read_bytes())
    result = convert_svg(path)
    before = {t.path: t.path.read_bytes() for t in result.tables}
    import pyfracpaq.io.svg as module
    actual = module.tempfile.NamedTemporaryFile
    calls = []

    def fail_second(*args, **kwargs):
        calls.append(1)
        if len(calls) == 2:
            raise OSError('simulated staging failure')
        return actual(*args, **kwargs)

    monkeypatch.setattr(module.tempfile, 'NamedTemporaryFile', fail_second)
    with pytest.raises(OSError):
        write_conversion(result)
    assert all(path.read_bytes() == data for path, data in before.items())
    assert not list(tmp_path.glob('.pyfracpaq-*'))


def test_individual_colour_drives_lengths_and_angular_outputs(tmp_path):
    path = tmp_path / 'single_colourA020F0_converted.txt'
    path.write_text('0\t0\t3\t4\n')
    dataset = read_txt(path)
    cfg = reference_config(('LEN-02', 'ANG-01'))
    registry = AnalysisRegistry()
    results = registry.execute(dataset, RunContext(cfg, tmp_path, tmp_path, 'colour'),
                               lambda *a: None, lambda: False)
    assert all(r.data.colour == hex_rgb('A020F0') for r in results)


def test_supplied_malformed_examples_are_explicit(tmp_path):
    with pytest.raises(NodeFileError, match='tab-delimited'):
        read_txt(ROOT / 'fracpaq-matlab/souter_all_colour24378D.txt')
    # Read-only check: the original SVG has known wholly degenerate traces.
    with pytest.raises(SvgInputError, match='eight decimal'):
        read_svg(ROOT / 'fracpaq-matlab/map1_edit.svg')
