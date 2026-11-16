"""Analytical Lengths oracles and Q-03/05/08/10 integrity regressions."""

from dataclasses import replace
import itertools
import logging

import numpy as np
import pytest

from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.analysis.lengths import (
    complementary_distribution, length_histogram, length_statistics, select_lengths,
)
from pyfracpaq.domain import TraceInput, build_dataset
from pyfracpaq.domain.execution import FieldError, RunContext
from pyfracpaq.io.lengths import export_lengths
from sprint4_reference import edge_dataset, emulate_legacy_censor, length_config


def execute(dataset, cfg, tmp_path):
    return AnalysisRegistry().execute(dataset, RunContext(cfg, tmp_path, tmp_path, 'test'),
                                       lambda *args: None, lambda: False)


def test_statistics_and_censor_masks_cover_four_edges_and_preserve_ids():
    data = edge_dataset()
    before = data.as_arrays()
    sample = select_lengths(data, censor=True)
    assert (sample.excluded_traces, sample.excluded_segments) == (4, 4)
    assert sample.trace_keep.tolist() == [False] * 4 + [True, True]
    assert sample.segment_keep.tolist() == [False] * 4 + [True] * 3
    assert sample.trace_ids.tolist() == [4, 5]
    assert sample.segment_ids.tolist() == [[4, 0], [4, 1], [5, 0]]
    np.testing.assert_array_equal(sample.trace_lengths, [7, 5])
    np.testing.assert_array_equal(sample.segment_lengths, [3, 4, 5])
    np.testing.assert_allclose(sample.raw_angles, [90, 0, 36.86989764584402], atol=1e-12)
    assert length_statistics(sample.trace_lengths).mean == pytest.approx(6)
    stats = length_statistics(sample.segment_lengths)
    assert (stats.count, stats.minimum, stats.maximum, stats.mean) == (3, 3, 5, 4)
    np.testing.assert_array_equal(data.as_arrays().segment_lengths, before.segment_lengths)
    assert all(not getattr(sample, name).flags.writeable for name in (
        'trace_keep', 'segment_keep', 'trace_ids', 'segment_ids', 'trace_lengths',
        'segment_lengths', 'raw_angles'))
    unfiltered = select_lengths(data)
    assert (unfiltered.excluded_traces, unfiltered.excluded_segments) == (0, 0)
    assert length_statistics(unfiltered.trace_lengths).mean == pytest.approx(28 / 6)


def test_q05_static_reproduction_detects_missed_edges_and_angle_misalignment():
    original = emulate_legacy_censor(edge_dataset())
    assert original['trace_keep'] == [False, True, True, True, False, False]
    assert original['misaligned_angles'] != original['angles_with_common_mask']
    assert original['misaligned_angles'] == [90, 90, 0]
    assert original['angles_with_common_mask'] == [90, 0, 0]


@pytest.mark.parametrize('reverse', [False, True])
def test_censor_uses_first_and_actual_last_node_not_penultimate(reverse):
    traces = [TraceInput(((0, 0), (10, 10))),
              TraceInput(((2, 2), (3, 3), (10, 5))),
              TraceInput(((2, 4), (10, 4), (3, 5)))]
    if reverse:
        traces = [TraceInput(tuple(reversed(t.points))) for t in traces]
    sample = select_lengths(build_dataset(traces), censor=True)
    assert sample.trace_keep.tolist() == [False, False, True]
    # An intermediate vertex is not an endpoint: no broadened censoring rule.
    assert sample.segment_ids.tolist() == [[2, 0], [2, 1]]


@pytest.mark.parametrize('offset', [(0, 0), (-100, -100), (500, -800)])
def test_masks_statistics_and_diagonal_are_translation_invariant(tmp_path, offset):
    original = edge_dataset()
    dx, dy = offset
    shifted = build_dataset([TraceInput(tuple((n.x + dx, n.y + dy) for n in trace.nodes))
                             for trace in original.traces])
    cfg = length_config(('LEN-06',), checkbox_censor=True)
    result = execute(shifted, cfg, tmp_path)[0].data
    assert result.sample.trace_ids.tolist() == [4, 5]
    assert result.domain_diagonal == pytest.approx(np.sqrt(1300))
    assert result.maximum_possible_length == 37
    np.testing.assert_array_equal(result.sample.segment_lengths, [3, 4, 5])


@pytest.mark.parametrize('bins', [10, 20, 30, 50])
def test_histogram_centres_counts_and_lower_tie_rule(bins):
    histogram = length_histogram([1, 2, 3], bins)
    assert len(histogram.centres) == bins + 1
    assert histogram.centres[0] == 1 and histogram.centres[-1] == 3
    assert histogram.frequencies.sum() == 3
    assert histogram.frequencies[[0, bins // 2, bins]].tolist() == [1, 1, 1]
    assert histogram.bar_width == pytest.approx(2 / bins)
    tie = length_histogram([1, 1.1, 3], 10)
    assert tie.frequencies[0] == 2


def test_pixel_complementary_grid_includes_hist_tails_and_excludes_current_bin():
    data = complementary_distribution([1.2, 1.4, 2.1, 2.6, 3.9])
    np.testing.assert_allclose(data.centres, [1.2, 2.2, 3.2], atol=1e-14)
    assert data.frequencies.tolist() == [2, 2, 1]
    assert data.complementary.tolist() == [3, 1, 0]
    assert np.all(np.diff(data.complementary) <= 0)


def test_scaled_complementary_has_1001_centres_and_exact_population():
    data = complementary_distribution([1, 1.2, 1.5, 2], scaled=True)
    assert len(data.centres) == 1001
    assert data.centres[[0, -1]].tolist() == [1, 2]
    assert data.frequencies.sum() == 4
    assert data.complementary[[0, -1]].tolist() == [3, 0]
    assert not data.centres.flags.writeable


@pytest.mark.parametrize('values', [[2], [2, 2, 2], [1e-6, 1e-6]])
def test_constant_samples_keep_one_bin_without_jitter(values):
    histogram = length_histogram(values, 20)
    assert histogram.centres.tolist() == [values[0]]
    assert histogram.frequencies.tolist() == [len(values)]
    for scaled in (False, True):
        distribution = complementary_distribution(values, scaled=scaled)
        assert distribution.complementary.tolist() == [0]


@pytest.mark.parametrize('values', [[], [0], [-1], [float('nan')], [float('inf')]])
def test_invalid_or_empty_numeric_samples_are_explicit(values):
    for operation in (length_statistics, complementary_distribution):
        with pytest.raises(ValueError):
            operation(values)
    with pytest.raises(ValueError):
        length_histogram(values, 10)


def test_unrepresentable_bins_and_excessive_pixel_grid_are_rejected_without_resampling():
    with pytest.raises(ValueError, match='spacing'):
        length_histogram([1., np.nextafter(1., 2.)], 50)
    with pytest.raises(MemoryError, match='limit'):
        complementary_distribution([1, 1000000000])
    assert len(complementary_distribution([1, 1000000000], scaled=True).centres) == 1001


@pytest.mark.parametrize('selected', [('LEN-02',), ('LEN-03',), ('LEN-06',),
                                    ('LEN-02', 'LEN-03', 'LEN-06')])
def test_each_selection_triggers_three_txt_once_and_ignores_unused_parameters(
        tmp_path, monkeypatch, selected, caplog):
    import pyfracpaq.analysis.lengths as module
    cfg = length_config(selected, edit_sigma1='bad', edit_lc='bad')
    if selected == ('LEN-06',):
        cfg = length_config(selected, popupmenu_histolengthbins='bad')
    elif 'LEN-06' not in selected:
        cfg = length_config(selected, edit_degfromnorth='bad')
    actual, calls = module.export_lengths, []

    def record(*args):
        calls.append(args)
        return actual(*args)

    monkeypatch.setattr(module, 'export_lengths', record)
    with caplog.at_level(logging.INFO):
        results = execute(edge_dataset(), cfg, tmp_path)
    assert len(results) == len(selected) and len(calls) == 1
    assert all(r.data is results[0].data for r in results)
    assert len(list(tmp_path.glob('*.txt'))) == 3
    assert not list(tmp_path.glob('*EZROSE*'))
    assert 'Total number of traces found: 6' in caplog.text
    assert 'Total number of segments found: 7' in caplog.text
    assert 'Number of traces excluded (censored): 0' in caplog.text
    assert 'Average trace length:' in caplog.text


@pytest.mark.parametrize('flip_x,flip_y', tuple(itertools.product((False, True), repeat=2)))
def test_crossplot_uses_corrected_doubled_angles_but_txt_uses_raw_pairs(
        tmp_path, flip_x, flip_y):
    data = build_dataset([TraceInput(((0, 0), (1, 1)))])
    cfg = replace(length_config(('LEN-06',), edit_degfromnorth='10'),
                  flip_x=flip_x, flip_y=flip_y)
    result = execute(data, cfg, tmp_path)[0].data
    assert result.cross_angles.tolist() == ([145, 325] if flip_x != flip_y else [35, 215])
    np.testing.assert_allclose(result.cross_lengths, [np.sqrt(2), np.sqrt(2)], rtol=1e-10)
    assert (tmp_path / 'FracPaQ2Dsegmentangleslengths_Run1.txt').read_bytes() \
        == b' 45.00\t  1.41\n'


def test_all_censored_run_fails_before_writing_and_preserves_previous_files(tmp_path):
    data = build_dataset([TraceInput(((0, 0), (1, 0)))])
    old = tmp_path / 'FracPaQ2Dtracelengths_Run1.txt'
    old.write_text('previous\n')
    cfg = length_config(checkbox_censor=True)
    with pytest.raises(FieldError, match='excluded every') as error:
        execute(data, cfg, tmp_path)
    assert error.value.field == 'checkbox_censor'
    assert list(tmp_path.iterdir()) == [old]
    assert old.read_text() == 'previous\n'


def test_length_txt_exact_schema_sorting_and_common_mask(tmp_path):
    cfg = replace(length_config(('LEN-06',), checkbox_censor=True), tag='')
    execute(edge_dataset(), cfg, tmp_path)
    assert (tmp_path / 'FracPaQ2Dsegmentlengths_.txt').read_bytes() \
        == b'  3.00\n  4.00\n  5.00\n'
    assert (tmp_path / 'FracPaQ2Dtracelengths_.txt').read_bytes() == b'  5.00\n  7.00\n'
    assert (tmp_path / 'FracPaQ2Dsegmentangleslengths_.txt').read_bytes() \
        == b' 90.00\t  3.00\n  0.00\t  4.00\n 36.87\t  5.00\n'


def test_export_stage_failure_preserves_all_targets_and_unrelated_files(tmp_path, monkeypatch):
    targets = export_lengths([2], [1, 1], [0, 90], 'Run1', tmp_path)
    before = {p: p.read_bytes() for p in targets}
    other = tmp_path / 'foreign.txt'
    other.write_text('keep')
    actual = np.savetxt
    calls = []

    def fail_second(*args, **kwargs):
        calls.append(1)
        if len(calls) == 2:
            raise OSError('simulated write failure')
        return actual(*args, **kwargs)

    monkeypatch.setattr(np, 'savetxt', fail_second)
    with pytest.raises(OSError):
        export_lengths([3], [1, 2], [0, 90], 'Run1', tmp_path)
    assert all(p.read_bytes() == before[p] for p in targets)
    assert other.read_text() == 'keep'
    assert not list(tmp_path.glob('.pyfracpaq-*'))


def test_loglog_bins_validated_when_histogram_not_selected():
    with pytest.raises(FieldError) as error:
        AnalysisRegistry().validate(length_config(('LEN-03',), popupmenu_histolengthbins='12'))
    assert error.value.field == 'popupmenu_histolengthbins'


def test_nonfinite_plot_bounds_fail_before_export_with_scale_context(tmp_path):
    data = build_dataset([TraceInput(((0, 0), (1.7e308, 0)))])
    with pytest.raises(FieldError, match='plot limits') as error:
        execute(data, length_config(('LEN-06',)), tmp_path)
    assert error.value.field == 'edit_scaling'
    assert not list(tmp_path.iterdir())
