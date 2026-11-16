"""Genuine MATLAB kernels, GUI maps/exports and approved Q-12 decisions."""

from dataclasses import replace

import numpy as np
from PIL import Image
import pytest
from scipy.io import loadmat

from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.analysis.wavelets import (cwt2, analyse_wavelet_image, WaveletParameters,
                                         parse_positive_integers, parameters_from_config)
from pyfracpaq.domain.execution import FieldError
from pyfracpaq.io.wavelets import normalize_raster, export_wavelets
from reference_common import REFERENCE
from sprint3_reference import reference_config


@pytest.mark.parametrize('kind,w,s,e,se', [('morlet', 'wm', 'sm', 'em', 'esm'),
                                         ('mexican', 'wh', 'sh', 'eh', 'esh')])
def test_rectangular_native_cwt_self_and_energy(kind, w, s, e, se):
    native = loadmat(REFERENCE / 'sprint14/native/cwt_arrays.mat', simplify_cells=True)
    for ai, a in enumerate(native['a']):
        for ti, theta in enumerate(native['theta']):
            for li, ratio in enumerate(native['L']):
                result = cwt2(native['data'], a, theta, ratio, kind)
                np.testing.assert_allclose(result.coefficients, native[w][:, :, ai, ti, li], atol=1e-13)
                np.testing.assert_allclose(result.self_coefficients, native[s][:, :, ai, ti, li], atol=1e-13)
                assert result.eta == pytest.approx(native[e][ai, ti, li], rel=1e-12, abs=1e-13)
                assert result.self_eta == pytest.approx(native[se][ai, ti, li], rel=1e-12, abs=1e-13)
                assert result.coefficients.shape == (5, 8) and not result.coefficients.flags.writeable


@pytest.mark.parametrize('kind', ['morlet', 'mexican'])
def test_actual_native_gui_map_and_strict_half_max_selection(kind):
    native = loadmat(REFERENCE / 'sprint14/native/gui_arrays.mat', simplify_cells=True)['details'][kind]
    result = analyse_wavelet_image(native['binary'], WaveletParameters((2,), (2, 1), 45, kind)).scales[0]
    np.testing.assert_allclose(result.coefficients, native['wc'], atol=1e-13)
    np.testing.assert_array_equal(result.selected, native['wc'] > native['wc'].max() * .5)
    assert result.selected.dtype == bool
    expected = np.loadtxt(REFERENCE / f'sprint14/native/{kind}/FracPaQ2Dwavelet_theta_a2.txt')
    if kind == 'morlet':
        np.testing.assert_array_equal(result.doubled_degrees, expected)
    else:
        # Q-12 explicitly approves stable orientation of isotropic/numerical ties.
        assert np.count_nonzero(result.doubled_degrees != expected) == 8


@pytest.mark.parametrize('text', ['', '1 0', '-1', '1.5', '2:2:8', '[2 4]', '__import__("os")', 'Inf'])
def test_lists_reject_invalid_values_without_evaluation(text):
    with pytest.raises(ValueError):
        parse_positive_integers(text)


@pytest.mark.parametrize('step', [0, 7, 40, 120, 181, 270, 360])
def test_angular_step_rejects_incoherent_axial_classes(step):
    with pytest.raises(ValueError):
        WaveletParameters((2,), (2,), step, 'morlet')


def test_contextual_validation_no_north_correction_and_flips():
    registry = AnalysisRegistry()
    cfg = reference_config(('WAV-01',), edit_aString='2 4', edit_LString='2 1',
                           edit_DegString='45', edit_degfromnorth='not used')
    registry.validate(cfg)
    parameters = parameters_from_config(cfg)
    assert parameters.ratios.tolist() == [.5, 1]
    bad = reference_config(('WAV-01',), edit_aString='2 4', edit_LString='0')
    with pytest.raises(FieldError) as error:
        registry.validate(bad)
    assert error.value.field == 'edit_LString'
    image = np.eye(8)
    original = analyse_wavelet_image(image, parameters).scales[0]
    once = analyse_wavelet_image(image, parameters, flip_x=True).scales[0]
    both = analyse_wavelet_image(image, parameters, flip_x=True, flip_y=True).scales[0]
    np.testing.assert_array_equal(original.coefficients, once.coefficients)
    np.testing.assert_array_equal(original.doubled_degrees, both.doubled_degrees)
    assert not np.array_equal(original.doubled_degrees, once.doubled_degrees)


def test_empty_white_raster_multi_scale_histogram_cancel_and_memory(tmp_path):
    parameters = WaveletParameters((2, 3), (2,), 45, 'morlet')
    result = analyse_wavelet_image(np.zeros((6, 8)), parameters)
    assert len(result.scales) == 2
    for scale in result.scales:
        assert not scale.selected.any() and not scale.doubled_degrees.size
        assert scale.histogram_counts.sum() == 48
        assert np.all(scale.coefficients == 0)
    paths = export_wavelets(result, '', tmp_path, raster=np.full((6, 8), 255, np.uint8))
    assert {p.name for p in paths} == {'FracPaQ2D_wavelet_traces.png',
        'FracPaQ2Dwavelet_theta_a2_.txt', 'FracPaQ2Dwavelet_theta_a3_.txt'}
    assert paths[1].read_text() == '' and not list(tmp_path.glob('.pyfracpaq-*'))
    with pytest.raises(InterruptedError):
        analyse_wavelet_image(np.eye(8), parameters, interrupted=lambda: True)
    with pytest.raises(MemoryError):
        cwt2(np.eye(8), 2, 0, .5, max_bytes=10)
    with pytest.raises(ValueError):
        normalize_raster(np.zeros((3, 3), np.uint8))
