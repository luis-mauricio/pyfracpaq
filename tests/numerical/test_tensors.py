"""Native tensors/projections, physical symmetries, aperture law and dispatch."""

from dataclasses import replace

import numpy as np
import pytest
from scipy.io import loadmat

from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.analysis.tensors import (
    crack_poles, crack_tensors, permeability_poles, permeability_tensor,
    trace_envelope_area,
)
from pyfracpaq.domain import TraceInput, build_dataset
from pyfracpaq.domain.execution import FieldError, RunContext
from pyfracpaq.geometry import Bounds, GeometryError
from reference_common import ROOT
from sprint3_reference import reference_config

NATIVE = loadmat(ROOT / 'tests/reference/sprint10/native/tensor_arrays.mat', simplify_cells=True)


@pytest.mark.parametrize('case', ['directional', 'isotropic', 'oblique'])
def test_all_tensor_components_and_361_polar_values_match_native(case):
    native = NATIVE['tensor_refs'][case]
    result = crack_tensors(native['lengths'], native['angles'], native['area'])
    np.testing.assert_allclose(result.zero, native['F0'], rtol=1e-8, atol=1e-12)
    for rank in result.ranks:
        np.testing.assert_allclose(rank.components, native[f'F{rank.order}'], rtol=1e-8, atol=1e-12)
        np.testing.assert_allclose(rank.polar, native[f'polar{rank.order}'], rtol=1e-8, atol=1e-12)
        np.testing.assert_array_equal(rank.components, np.swapaxes(rank.components, 0, -1))
        assert not rank.components.flags.writeable and not rank.polar.flags.writeable
    assert result.alpha.shape == (361,) and result.alpha[-1] == 2 * np.pi


def test_directional_and_isotropic_patterns_have_known_projections():
    directional = crack_tensors([2, 3, 4], [90, 90, 90], 16)
    for rank in directional.ranks:
        assert rank.polar[0] == pytest.approx(0, abs=1e-12)
        assert rank.polar[90] == pytest.approx(29 / 16)
        assert np.count_nonzero(rank.components) == 1
    isotropic = crack_tensors(np.ones(36), np.arange(0, 180, 5), 100)
    for rank, factor in zip(isotropic.ranks, (.5, 3 / 8, 35 / 128)):
        np.testing.assert_allclose(rank.polar, .36 * factor, rtol=0, atol=1e-12)


@pytest.mark.parametrize('flip_x,flip_y', [(False, False), (True, False), (False, True), (True, True)])
def test_crack_and_permeability_keep_distinct_rounding_and_flip_order(flip_x, flip_y):
    raw = np.array([0, 30.25, 90, 179])
    crack_expected = np.array([78, 108, 168, 257.])
    perme_expected = raw.copy()
    for flip in (flip_x, flip_y):
        if flip:
            crack_expected = 180 - crack_expected
            crack_expected[crack_expected < 0] += 360
            perme_expected = 180 - perme_expected
            perme_expected[perme_expected < 0] += 360
    np.testing.assert_array_equal(crack_poles(raw, 12.5, flip_x, flip_y), crack_expected)
    np.testing.assert_array_equal(permeability_poles(raw, 12.5, flip_x, flip_y), perme_expected + 77.5)


@pytest.mark.parametrize('mode', ['fixed', 'scaled', 'zero_aperture', 'zero_lambda'])
def test_native_permeability_matrix_eigenvalues_and_projection(mode):
    native = NATIVE['permeability_refs'][mode]
    result = permeability_tensor(native['lengths'], native['poles'], native['area'],
                                 native['apertures'], native['lambda'])
    for actual, name in ((result.p, 'P'), (result.k, 'K'), (result.eigenvalues, 'eigenvalues'),
                          (result.polar, 'polar')):
        scale = float(np.max(np.abs(native[name])))
        np.testing.assert_allclose(actual, native[name], rtol=1e-8, atol=1e-12 * scale)
        assert not actual.flags.writeable
    np.testing.assert_array_equal(result.k, result.k.T)
    assert result.eigenvalues[0] >= -1e-24


def test_aperture_is_cubic_lambda_linear_and_geometry_scales_as_area():
    lengths, poles, apertures = np.array([2, 3, 4]), [90, 120, 155], np.array([.001, .002, .003])
    base = permeability_tensor(lengths, poles, 24, apertures, .5)
    triple = permeability_tensor(lengths, poles, 24, apertures * 3, .5)
    full = permeability_tensor(lengths, poles, 24, apertures, 1)
    physical_scale = permeability_tensor(lengths / 2, poles, 24 / 4, apertures / 2, .5, unit='metres^2')
    np.testing.assert_allclose(triple.k, base.k * 27, rtol=1e-12, atol=1e-24)
    np.testing.assert_allclose(full.k, base.k * 2, rtol=1e-12, atol=1e-24)
    np.testing.assert_allclose(physical_scale.k, base.k / 4, rtol=1e-12, atol=1e-24)
    assert physical_scale.unit == 'metres^2'
    original = crack_tensors(lengths, poles, 24)
    scaled = crack_tensors(lengths / 2, poles, 24 / 4)
    for a, b in zip(original.ranks, scaled.ranks):
        np.testing.assert_array_equal(a.components, b.components)


def test_permeability_flows_along_fractures_not_their_poles_and_uses_linear_storage():
    result = permeability_tensor(np.ones(10000), np.full(10000, 90.), 10000,
                                 np.ones(10000) * .001, 1)
    assert result.k[0, 0] == pytest.approx(1e-9 / 12)
    assert result.k[1, 1] == 0 and result.polar.shape == (361,)
    assert result.polar[0] == pytest.approx(result.k[0, 0])
    assert result.polar[90] == pytest.approx(0, abs=1e-24)


def test_trace_envelope_area_is_distinct_from_raster_canvas_and_translation_invariant():
    data = build_dataset([TraceInput(((2, 3), (4, 5)))], source_bounds=Bounds(0, 0, 10, 10))
    assert trace_envelope_area(data) == 4 and data.area == 100
    translated = build_dataset([TraceInput(((-98, -97), (-96, -95)))])
    assert trace_envelope_area(translated) == 4
    assert trace_envelope_area(data.with_scale(2)) == 1


@pytest.mark.parametrize('area', [0, -1, np.inf, np.nan])
def test_invalid_area_is_rejected(area):
    with pytest.raises(GeometryError):
        crack_tensors([1], [90], area)


def test_tensor_cancellation_and_invalid_apertures_do_not_produce_partial_results():
    with pytest.raises(InterruptedError):
        crack_tensors([1], [90], 1, interrupted=lambda: True)
    with pytest.raises(InterruptedError):
        permeability_tensor([1], [90], 1, [.1], 1, interrupted=lambda: True)
    with pytest.raises(ValueError):
        permeability_tensor([1], [90], 1, [-.1], 1)
    with pytest.raises(ValueError):
        permeability_tensor([1], [90], 1, [.1], 1.01)


def test_angular_dispatch_caches_crack_tensor_and_ezrose_once(tmp_path, monkeypatch):
    import pyfracpaq.analysis.angles as angles_module
    data = build_dataset([TraceInput(((0, 0), (0, 2))), TraceInput(((0, 0), (2, 0)))])
    cfg = reference_config(('ANG-01', 'ANG-02', 'FLO-08'))
    calls = []
    original = angles_module.export_ezrose
    def export(*args):
        calls.append(args)
        return original(*args)
    monkeypatch.setattr(angles_module, 'export_ezrose', export)
    results = AnalysisRegistry().execute(data, RunContext(cfg, tmp_path, tmp_path, 'tensor'),
                                          lambda *_: None, lambda: False)
    assert len(calls) == 1 and len(results) == 3
    assert results[0].data is results[1].data is results[2].data
    assert results[0].data.crack is not None
    assert list(tmp_path.glob('*.txt')) == [tmp_path / 'FracPaQ2DEZROSE_Run1.txt']


@pytest.mark.parametrize('fixed', [True, False])
def test_zero_aperture_mode_and_inactive_parameters_are_contextual(tmp_path, fixed):
    data = build_dataset([TraceInput(((0, 0), (2, 2)))])
    cfg = reference_config(('FLO-09',), radiobutton_fixedaperture=fixed,
                           edit_fixedaperture='0' if fixed else 'unused invalid',
                           edit_aperturefactor='unused invalid' if fixed else '0',
                           edit_apertureexponent='unused invalid' if fixed else '.75')
    result, = AnalysisRegistry().execute(data, RunContext(cfg, tmp_path, tmp_path, 'zero'),
                                         lambda *_: None, lambda: False)
    assert not np.any(result.data.k) and not np.any(result.data.apertures)
    assert not list(tmp_path.iterdir())


def test_zero_area_crack_does_not_export_ezrose(tmp_path):
    data = build_dataset([TraceInput(((0, 0), (2, 0)))])
    cfg = reference_config(('FLO-08',))
    with pytest.raises(FieldError, match='trace envelope'):
        AnalysisRegistry().execute(data, RunContext(cfg, tmp_path, tmp_path, 'invalid'),
                                   lambda *_: None, lambda: False)
    assert not list(tmp_path.iterdir())


def test_permeability_console_matches_native_printed_values(tmp_path, caplog):
    from sprint1011_reference import uniform_dataset
    cfg = reference_config(('FLO-09',), edit_degfromnorth='12', edit_lambda='.7',
                           radiobutton_fixedaperture=True, edit_fixedaperture='.001')
    cfg = replace(cfg, flip_x=True)
    with caplog.at_level('INFO'):
        AnalysisRegistry().execute(uniform_dataset(), RunContext(cfg, tmp_path, tmp_path, 'native'),
                                   lambda *_: None, lambda: False)
    assert 'Maximum permeability = 5.3786e-11 pixels^2' in caplog.text
    assert 'Minimum permeability = 5.3786e-11 pixels^2' in caplog.text
