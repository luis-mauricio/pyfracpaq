"""Actual MATLAB arrays, source pair conventions and numerical invariances."""

import numpy as np
import pytest
from scipy.io import loadmat

from pyfracpaq.analysis.variogram import experimental_variogram as variogram
from reference_common import REFERENCE


NATIVE = loadmat(REFERENCE / 'sprint12/native/variogram_arrays.mat', simplify_cells=True)


@pytest.mark.parametrize('name,options', [
    ('default', {'nrbins': 30}), ('gamma', {'nrbins': 4, 'maxdist': 3}),
    ('cloud1', {'nrbins': 4, 'maxdist': 3, 'kind': 'cloud1'}),
    ('cloud2', {'nrbins': 4, 'maxdist': 3, 'kind': 'cloud2'}),
    ('anisotropic', {'nrbins': 4, 'maxdist': 3, 'anisotropy': True}),
    ('anisotropic40', {'nrbins': 4, 'maxdist': 3, 'anisotropy': True, 'thetastep': 40}),
])
def test_actual_native_arrays(name, options):
    expected = NATIVE['variograms'][name]
    result = variogram(NATIVE['x'], NATIVE['values'], **options)
    np.testing.assert_allclose(result.distance, expected['distance'], rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(result.values, expected['val'], rtol=1e-12, atol=1e-12, equal_nan=True)
    if result.counts is not None:
        np.testing.assert_array_equal(result.counts, expected['num'])
    if result.theta is not None:
        np.testing.assert_allclose(result.theta, expected['theta'], atol=1e-12)
    assert not result.values.flags.writeable


@pytest.mark.parametrize('n', [999, 1000])
def test_source_size_switch_and_streaming_pairs(n):
    x = np.arange(n, dtype=float)
    result = variogram(x, np.ones(n), nrbins=3, maxdist=0)
    assert result.includes_self == (n < 1000)
    assert result.pair_count == (n if n < 1000 else 0)
    assert np.isnan(result.values[:-1]).all()
    assert result.values[-1] == 0 if n < 1000 else np.isnan(result.values).all()


def test_pair_order_cloud_squared_differences_maximum_and_duplicate_positions():
    result = variogram([0, 1, 1], [1, 3, 4], kind='cloud2', maxdist=1, nrbins=2)
    assert result.pair_indices.tolist() == [[0, 0], [0, 1], [1, 1], [0, 2], [1, 2], [2, 2]]
    assert result.values.tolist() == [0, 4, 0, 9, 1, 0]
    assert result.distance.tolist() == [0, 1, 0, 1, 0, 0]
    assert result.pair_count == 6
    zero = variogram([[1, 1]] * 3, [2, 2, 2], nrbins=30)
    assert zero.pair_count == 6 and zero.counts[-1] == 6 and zero.values[-1] == 0


def test_translation_scale_and_nan_filtered_identity():
    x, y = NATIVE['x'].astype(float), NATIVE['values'].astype(float)
    # Keep pairs away from a maxdist/bin boundary: source uses exact <= and
    # decimal scaling can change a last-bit boundary decision (no new epsilon).
    original = variogram(x, y, nrbins=7, maxdist=2.5)
    shifted = variogram(x + [30, -50], y, nrbins=7, maxdist=2.5)
    scaled = variogram(x / 10, y / 10, nrbins=7, maxdist=.25)
    np.testing.assert_allclose(shifted.values, original.values, equal_nan=True)
    np.testing.assert_allclose(scaled.distance, original.distance / 10)
    np.testing.assert_allclose(scaled.values, original.values / 100, equal_nan=True)
    filtered = variogram([[0, 0], [np.nan, np.inf], [1, 0]], [1, 5, 3], kind='cloud2')
    assert filtered.sample_indices.tolist() == [0, 2]


def test_local_subsampling_reproducibility_shared_indices_and_rng_isolation():
    np.random.seed(100)
    before = np.random.get_state()
    a = variogram(np.arange(30), np.arange(30), subsample=6, seed=12)
    b = variogram(np.arange(30), np.arange(30), subsample=6, seed=12)
    c = variogram(np.arange(30), np.arange(30), subsample_indices=a.sample_indices)
    np.testing.assert_array_equal(a.sample_indices, b.sample_indices)
    np.testing.assert_allclose(a.values, c.values, equal_nan=True)
    assert a.maximum_distance == 14.5
    after = np.random.get_state()
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]


@pytest.mark.parametrize('options', [{'nrbins': 0}, {'kind': 'bad'}, {'thetastep': 0},
    {'subsample': 1.5}, {'subsample_indices': [0, 0]}, {'maxdist': -1}])
def test_invalid_options_fail_without_outputs(options):
    with pytest.raises(ValueError):
        variogram([0, 1], [1, 2], **options)


def test_cancellation_memory_and_non2d_anisotropy():
    with pytest.raises(InterruptedError):
        variogram([0, 1], [1, 2], interrupted=lambda: True)
    with pytest.raises(MemoryError):
        variogram([0, 1], [1, 2], nrbins=100_000_000)
    with pytest.warns(RuntimeWarning, match='only for 2-D'):
        result = variogram([0, 1], [1, 2], anisotropy=True)
    assert result.theta is None
