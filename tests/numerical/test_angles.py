"""Independent directional oracles for the ported MATLAB angular conventions."""

import itertools
import json
import subprocess
import sys

import numpy as np
import pytest

from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.analysis.angles import axial_statistics, equal_area_rose
from pyfracpaq.analysis.compatibility import (
    double_angles, hist_centres, histcount_indices, matlab_round, strike_indices,
)
from pyfracpaq.analysis.maps import length_indices
from pyfracpaq.analysis.palettes import cmocean
from pyfracpaq.domain import TraceInput
from pyfracpaq.domain.construction import build_dataset
from pyfracpaq.domain.execution import RunContext
from pyfracpaq.io.angles import export_ezrose
from pyfracpaq.resources import resource_bytes, resource_text
from reference_common import ROOT, sha256
from freeze_cmocean import extract
from test_execution_contract import config


def test_round_half_away_from_zero_and_degree_boundaries():
    np.testing.assert_array_equal(matlab_round([-2.5, -1.5, -.5, 0, .5, 1.5, 2.5]),
                                  [-3, -2, -1, 0, 1, 2, 3])
    np.testing.assert_array_equal(double_angles([.5, 179.5], 0), [1, 180, 181, 360])


@pytest.mark.parametrize('flip_x,flip_y', tuple(itertools.product((False, True), repeat=2)))
def test_north_and_all_flip_combinations(flip_x, flip_y):
    expected = [160, 340] if flip_x != flip_y else [20, 200]
    result = double_angles([30], 10, flip_x, flip_y)
    np.testing.assert_array_equal(result, expected)
    assert not result.flags.writeable
    strike = strike_indices([30], 10, flip_x, flip_y)
    assert strike.tolist() == ([159] if flip_x != flip_y else [19])


@pytest.mark.parametrize('north,expected', [
    (-360, [390, 570]), (360, [30, 210]), (180, [210, 30]),
    (-.5, [31, 211]), (.5, [30, 210]),
])
def test_q10_preserves_single_adjustment_instead_of_modulo(north, expected):
    np.testing.assert_array_equal(double_angles([30], north), expected)
    assert np.all((strike_indices([0, 180], north) >= 0)
                  & (strike_indices([0, 180], north) < 180))


def test_hist_uses_centres_lower_ties_tails_and_ignores_nan():
    counts = hist_centres([-np.inf, -100, 0, 45, 45.001, 90, 135, 180, np.inf,
                           np.nan], [0, 90, 180])
    assert counts.tolist() == [4, 3, 2]
    assert histcount_indices([-1, 0, 10, 359, 360, 361], [0, 10, 360]).tolist() \
        == [-1, 0, 1, 1, 1, -1]


@pytest.mark.parametrize('bins', [10, 20, 30, 50])
def test_angular_histogram_has_n_plus_one_centres(bins):
    centres = np.linspace(0, 360, bins + 1)
    counts = hist_centres([0, 90, 180, 270, 360], centres)
    assert len(counts) == bins + 1 and counts.sum() == 5
    assert counts[0] == counts[-1] == 1
    assert counts[bins // 2] == 1


@pytest.mark.parametrize('delta', (5, 10, 20, 30))
@pytest.mark.parametrize('weighted', (False, True))
def test_rose_analytical_bin_counts_lengths_and_equal_area(delta, weighted):
    angles = np.array([0, 45, 90, 135, 180, 225, 270, 315])
    lengths = np.array([1, 2, 3, 4, 1, 2, 3, 4])
    rose = equal_area_rose(angles, lengths, delta, weighted=weighted)
    expected = np.zeros(360 // delta)
    for a, length in zip(angles, lengths):
        expected[a // delta] += length if weighted else 1
    expected = expected / (20 if weighted else 8) * 100
    np.testing.assert_allclose(rose.percentages, expected, rtol=1e-12)
    np.testing.assert_allclose(rose.radii[:-2:2] ** 2, 2500 * expected, atol=1e-10)
    np.testing.assert_array_equal(rose.vertices[-2:], [[0, 0], [0, 0]])
    assert not rose.vertices.flags.writeable
    assert np.isfinite(rose.limit) and rose.limit > 0


def test_rose_boundary_patch_applies_to_counts_but_not_lengths():
    # 360 belongs to the last bin, whereas 0 and 180 start their bins.
    rose = equal_area_rose([0, 180, 360], [1, 2, 3], 30)
    assert rose.raw_counts[[0, 5, 6, 11]].tolist() == [1, 0, 1, 1]
    assert rose.counts[[0, 5, 6, 11]].tolist() == [1, .5, 1, .5]
    assert rose.length_sums[[0, 5, 6, 11]].tolist() == [1, 0, 2, 3]
    weighted = equal_area_rose([0, 180, 360], [1, 2, 3], 30, weighted=True)
    np.testing.assert_allclose(weighted.percentages[[0, 5, 6, 11]],
                               np.array([1, 0, 2, 3]) / 6 * 100)
    outside = equal_area_rose([390, 570], [1, 1], 10)
    assert not outside.counts.any()
    assert outside.limit == 50


def test_circular_statistics_use_axial_first_half_and_original_std_formula():
    directed = axial_statistics([30, 30, 210, 210])
    assert directed.mean == pytest.approx(30)
    assert directed.resultant == pytest.approx(1)
    assert directed.standard_deviation == pytest.approx(0, abs=1e-6)
    mixed = axial_statistics([0, 45, 180, 225])
    assert mixed.mean == pytest.approx(22.5)
    assert mixed.resultant == pytest.approx(np.sqrt(.5))
    assert mixed.standard_deviation == pytest.approx(
        180 / np.pi * np.sqrt(2 * (1 - np.sqrt(.5))))
    isotropic = axial_statistics([0, 90, 180, 270])
    assert isotropic.resultant == 0 and not isotropic.mean_defined
    assert isotropic.mean == 0  # atan2(0,0) legacy convention, flagged undefined.
    assert isotropic.standard_deviation == pytest.approx(180 / np.pi * np.sqrt(2))


def test_length_and_strike_colour_indices_preserve_q17_and_seam():
    assert length_indices([1, 2, 256]).tolist() == [0, 1, 255]
    assert length_indices([.5, 1, 2]).tolist() == [63, 127, 255]
    assert strike_indices([0, 1, 90, 179, 180], 0).tolist() == [179, 0, 89, 178, 179]
    # Negative and positive half ties differ before the axial colour reduction.
    assert strike_indices([0, 180], .5).tolist() == [178, 179]


def test_all_frozen_rgb_tables_match_original_decimal_tokens():
    manifest = json.loads(resource_text('cmocean_manifest.json'))
    source = ROOT / manifest['source']
    assert sha256(source) == manifest['source_sha256']
    tables = extract(source.read_text())
    from io import BytesIO
    with np.load(BytesIO(resource_bytes('cmocean_rgb.npz'))) as frozen:
        assert len(frozen.files) == 18
        for key in tables:
            np.testing.assert_array_equal(frozen[key], tables[key])
    for name, key in manifest['names'].items():
        np.testing.assert_array_equal(cmocean(name, len(tables[key])), tables[key])
        np.testing.assert_array_equal(cmocean(name, 2), tables[key][[0, -1]])
        np.testing.assert_array_equal(cmocean(name, 180, reverse=True),
                                      cmocean(name, 180)[::-1])
    # An independent midpoint oracle for MATLAB's channel interpolation.
    table = tables['pha']
    np.testing.assert_allclose(cmocean('phase', 3)[1],
                               (table[127] + table[128]) / 2, rtol=1e-14)


def test_ezrose_keeps_signed_zero_tie_order(tmp_path):
    # SD11A exposed this distinction: the numeric angles are equal, but the
    # original TXT retains the input order of +0/-0 after sorting.
    output = export_ezrose([180., 0., 0., -0., -0., 0., 0., 90.], 'zero', tmp_path)
    assert output.read_bytes() == (
        b'  0.00\n  0.00\n -0.00\n -0.00\n  0.00\n  0.00\n 90.00\n180.00\n')


def test_ezrose_order_exact_precision_empty_tag_and_atomic_failure(tmp_path, monkeypatch):
    output = export_ezrose([200, 20, 160, 340], '', tmp_path)
    assert output.name == 'FracPaQ2DEZROSE_.txt'
    assert output.read_bytes() == b' 20.00\n160.00\n200.00\n340.00\n'
    import pyfracpaq.io.angles as module
    monkeypatch.setattr(module.os, 'replace', lambda *args: (_ for _ in ()).throw(
        OSError('simulated replacement failure')))
    with pytest.raises(OSError):
        export_ezrose([1], '', tmp_path)
    assert output.read_bytes().startswith(b' 20.00')
    assert not list(tmp_path.glob('.pyfracpaq-*'))


@pytest.mark.parametrize('selected', [('ANG-01',), ('ANG-02',), ('ANG-01', 'ANG-02')])
def test_registry_angular_dispatch_export_once_and_selected_parameters_only(
        tmp_path, monkeypatch, selected):
    import pyfracpaq.analysis.angles as module
    dataset = build_dataset([TraceInput(((0, 0), (1, 1)))])
    cfg = config(selected)
    if selected == ('ANG-01',):
        cfg = config(selected, popupmenu_rosebins='invalid')
    if selected == ('ANG-02',):
        cfg = config(selected, popupmenu_histoanglebins='invalid')
    context = RunContext(cfg, tmp_path, tmp_path, 'test')
    calls = []
    actual_export = module.export_ezrose

    def record(*args):
        calls.append(args)
        return actual_export(*args)

    monkeypatch.setattr(module, 'export_ezrose', record)
    results = AnalysisRegistry().execute(dataset, context, lambda *a: None, lambda: False)
    assert len(results) == len(selected) and len(calls) == 1
    if len(results) == 2:
        assert results[0].data is results[1].data
    assert (tmp_path / 'FracPaQ2DEZROSE_Run1.txt').read_bytes() == b' 45.00\n225.00\n'
    if selected == ('ANG-01',):
        assert len(results[0].data.centres) == 21
        assert results[0].data.frequencies.sum() == 2


def test_scientific_core_does_not_import_qt_or_matplotlib():
    script = ('import sys; from pyfracpaq.analysis import AnalysisRegistry; '
              'AnalysisRegistry(); '
              'assert not any(n.startswith(("PySide6", "matplotlib")) for n in sys.modules)')
    subprocess.run([sys.executable, '-c', script], check=True, cwd=ROOT)
