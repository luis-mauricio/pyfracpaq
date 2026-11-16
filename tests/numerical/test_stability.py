"""Known stresses, approved Q-17 corrections, edge cases and source TXT format."""

from dataclasses import replace

import numpy as np
import pytest
from scipy.io import loadmat

from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.analysis.compatibility import double_angles, strike_indices
from pyfracpaq.analysis.palettes import matlab_jet
from pyfracpaq.analysis.stability import (
    StressParameters, colour_indices, mohr_circle, normal_shear, stability_fields,
)
from pyfracpaq.domain import TraceInput, build_dataset
from pyfracpaq.domain.execution import FieldError, RunContext
from pyfracpaq.io import read_txt
from pyfracpaq.io.stability import export_segmentdata
from reference_common import ROOT
from sprint3_reference import reference_config

PARAMETERS = StressParameters(100, 50, 30, 2, 10, .6)
ORTHOGONAL = build_dataset([TraceInput(((0, 0), (0, 2))), TraceInput(((0, 1), (2, 1)))])
NATIVE = loadmat(ROOT / 'tests/reference/sprint11/native/stability_arrays.mat', simplify_cells=True)


def test_rotated_orthogonal_stresses_and_raw_fields_match_native_formulas():
    expected = NATIVE['stability_refs']['rotated_orthogonal']
    result = stability_fields(ORTHOGONAL, PARAMETERS)
    np.testing.assert_allclose(result.normal_stress, expected['sn'], rtol=1e-8, atol=1e-12)
    np.testing.assert_allclose(result.shear_stress, expected['tau'], rtol=1e-8, atol=1e-12)
    for kind, name in (('slip', 'Ts'), ('dilation', 'Td'), ('susceptibility', 'Sf')):
        np.testing.assert_allclose(result.field(kind).values, expected[name], rtol=1e-8, atol=1e-12)
    # Source's preliminary normalizer is zero; the approved observed one is finite.
    assert expected['source_Tsmax'] == 0
    np.testing.assert_allclose(result.field('slip').normalized, [1, 5 / 7], rtol=0, atol=1e-12)
    np.testing.assert_array_equal(result.field('susceptibility').map_indices, [0, 99])
    assert result.field('susceptibility').colour_range == pytest.approx((19.748941508981723, 44.74894150898172))


def test_known_strikes_and_mohr_circle_include_effective_stress_without_extra_points():
    params = replace(PARAMETERS, theta=0)
    sn, tau = normal_shear([0, 45, 90], params)
    np.testing.assert_allclose(sn, [50, 75, 100], atol=1e-12)
    np.testing.assert_allclose(tau, [0, 25, 0], atol=1e-12)
    circle = mohr_circle(params)
    np.testing.assert_allclose((circle.normal - 75) ** 2 + circle.shear ** 2, 625, atol=1e-12)
    np.testing.assert_array_equal(circle.effective_normal, circle.normal - 10)
    assert circle.normal.shape == circle.shear.shape == (361,)


@pytest.mark.parametrize('flips', [(False, False), (True, False), (False, True), (True, True)])
def test_north_flips_use_shared_legacy_conventions_and_do_not_mutate_geometry(flips):
    data = read_txt(ROOT / 'tests/fixtures/nodes/mixed.txt')
    before = data.as_arrays().segment_coordinates.copy()
    result = stability_fields(data, PARAMETERS, north=12.5, flip_x=flips[0], flip_y=flips[1])
    raw = data.as_arrays().raw_angles
    np.testing.assert_array_equal(result.strikes, strike_indices(raw, 12.5, *flips) + 1)
    np.testing.assert_array_equal(result.doubled_angles, double_angles(raw, 12.5, *flips))
    np.testing.assert_array_equal(data.as_arrays().segment_coordinates, before)
    assert len(result.rose.edges) == 37 and np.diff(result.rose.edges).tolist() == [10] * 36
    assert result.rose.percentages.sum() == pytest.approx(100)


def test_csf_equality_is_inclusive_in_both_map_and_rose_without_tolerance():
    data = build_dataset([TraceInput(((0, 0), (2, 2)))])
    params = StressParameters(100, 50, 0, 25, 0, 0)
    result = stability_fields(data, params, kinds=('csf',))
    assert result.field('csf').values.tolist() == [1]
    assert result.field('csf').rose_values[4] == 1  # 45-degree bin midpoint.
    above = stability_fields(data, replace(params, cohesion=np.nextafter(25., np.inf)), kinds=('csf',))
    assert above.field('csf').values.tolist() == [0] and not np.any(above.field('csf').rose_values)
    native = NATIVE['stability_refs']['equality_csf']
    assert np.all(native['map_csf']) and not np.any(native['rose_csf'])


def test_constant_fields_are_finite_and_zero_friction_only_blocks_susceptibility():
    constant = replace(PARAMETERS, sigma2=100)
    result = stability_fields(ORTHOGONAL, constant, kinds=('slip', 'susceptibility', 'csf'))
    assert not np.any(result.field('slip').normalized)
    assert not np.any(result.field('susceptibility').normalized)
    assert not np.any(result.field('susceptibility').rose_normalized)
    assert result.field('susceptibility').colour_range[0] == result.field('susceptibility').colour_range[1]
    for field in result.fields:
        assert np.isfinite(field.values).all() and not field.values.flags.writeable
    free = stability_fields(ORTHOGONAL, replace(PARAMETERS, friction=0), kinds=('slip', 'dilation', 'csf'))
    assert len(free.fields) == 3


@pytest.mark.parametrize('changes,kinds,field', [
    ({'friction': 0}, ('susceptibility',), 'edit_mu'),
    ({'sigma2': 100}, ('dilation',), 'edit_sigma2'),
    ({'sigma1': -100}, ('slip',), 'edit_sigma1'),
    ({'sigma2': 150}, ('csf',), 'edit_sigma2'),
    ({'sigma2': 0}, ('slip',), 'edit_sigma2'),
    ({'theta': 181}, ('slip',), 'edit_thetasigma1'),
    ({'cohesion': -1}, ('slip',), 'edit_C0'),
    ({'pore_pressure': np.inf}, ('csf',), 'edit_Pf'),
])
def test_invalid_stress_combinations_have_field_context(changes, kinds, field):
    with pytest.raises(FieldError) as error:
        stability_fields(ORTHOGONAL, replace(PARAMETERS, **changes), kinds=kinds)
    assert error.value.field == field


@pytest.mark.parametrize('levels', [19, 100, 256])
def test_frozen_jet_is_exact_native_rgb_including_reversal(levels):
    np.testing.assert_array_equal(matlab_jet(levels), NATIVE[f'jet{levels}'])
    np.testing.assert_array_equal(matlab_jet(levels, reverse=True), NATIVE[f'jet{levels}'][::-1])
    assert not matlab_jet(levels).flags.writeable


def test_colour_rounding_is_linear_and_saturates_both_limits():
    np.testing.assert_array_equal(colour_indices([-1, 0, .1, .5, .75, 1, 2], 100),
                                   [0, 0, 9, 49, 74, 99, 99])
    result = stability_fields(ORTHOGONAL, PARAMETERS)
    for field in result.fields:
        assert 0 <= field.map_indices.min() <= field.map_indices.max() < 100
        assert 0 <= field.rose_indices.min() <= field.rose_indices.max() < 19
        assert not field.map_indices.flags.writeable


def test_segmentdata_has_native_order_precision_raw_angles_and_blank_tag(tmp_path):
    data = read_txt(ROOT / 'tests/fixtures/nodes/mixed.txt')
    target = export_segmentdata(data, '', tmp_path)
    assert target.name == 'FracPaQ2Dsegmentdata_.txt'
    assert target.read_bytes() == (
        b'   1\t  0.0000\t  0.0000\t  4.0000\t  0.0000\t90.0\n'
        b'   2\t  1.0000\t  2.0000\t  4.0000\t  2.0000\t90.0\n'
        b'   3\t  4.0000\t  2.0000\t  4.0000\t  6.0000\t0.0\n')
    other = tmp_path / 'unrelated.txt'
    other.write_text('keep')
    export_segmentdata(data, '', tmp_path)
    assert other.read_text() == 'keep'


def test_shared_stability_cache_and_slip_only_segmentdata_export(tmp_path):
    cfg = reference_config(('MAP-11', 'MAP-12', 'MAP-13', 'MAP-14'), edit_thetasigma1='30')
    results = AnalysisRegistry().execute(ORTHOGONAL, RunContext(cfg, tmp_path, tmp_path, 'stability'),
                                         lambda *_: None, lambda: False)
    assert len(results) == 4 and all(result.data is results[0].data for result in results)
    assert [p.name for p in tmp_path.iterdir()] == ['FracPaQ2Dsegmentdata_Run1.txt']
    assert len(results[0].data.fields) == 4


def test_invalid_selected_combinations_and_cancellation_export_nothing(tmp_path):
    registry = AnalysisRegistry()
    invalid = reference_config(('MAP-11', 'MAP-13'), edit_mu='0')
    with pytest.raises(FieldError, match='positive friction'):
        registry.execute(ORTHOGONAL, RunContext(invalid, tmp_path, tmp_path, 'bad'),
                          lambda *_: None, lambda: False)
    with pytest.raises(InterruptedError):
        stability_fields(ORTHOGONAL, PARAMETERS, interrupted=lambda: True)
    assert not list(tmp_path.iterdir())
