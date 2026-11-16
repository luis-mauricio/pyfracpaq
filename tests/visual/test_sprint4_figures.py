"""Seven Lengths figure contracts and valid limits on degenerate populations."""

from dataclasses import replace

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.ticker import NullFormatter
import numpy as np
import pytest

from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.domain import TraceInput, build_dataset
from pyfracpaq.domain.execution import RunContext
from sprint4_reference import edge_dataset, length_config

NAMES = {
    'FracPaQ2D_histotracelength', 'FracPaQ2D_histosegmentlength',
    'FracPaQ2D_loglogplottracelengthdensity', 'FracPaQ2D_loglogplottracelength',
    'FracPaQ2D_loglogplotsegmentlengthdensity', 'FracPaQ2D_loglogplotsegmentlength',
    'FracPaQ2D_crossplotsegmentlengthangle',
}


def figures(tmp_path, dataset=None, config=None):
    dataset = dataset or edge_dataset()
    config = config or length_config(checkbox_censor=True)
    registry = AnalysisRegistry()
    results = registry.execute(dataset, RunContext(config, tmp_path, tmp_path, 'plot'),
                               lambda *args: None, lambda: False)
    outputs = {}
    for result in results:
        spec = next(s for s in registry.specs if s.id == result.analysis_id)
        for output in spec.render(result.data, config):
            FigureCanvasAgg(output.figure).draw()
            outputs[output.basename] = output.figure
    return results[0].data, outputs


def test_seven_names_square_axes_units_titles_and_hist_dual_axis(tmp_path):
    result, outputs = figures(tmp_path)
    assert set(outputs) == NAMES
    for name, figure in outputs.items():
        axes = figure.axes[0]
        assert axes.get_title().endswith('\n')
        assert axes.get_box_aspect() == 1
        assert figure.get_facecolor() == (1, 1, 1, 1)
        if 'histo' in name:
            subject = 'trace' if 'tracelength' in name else 'segment'
            histogram = getattr(result, subject + '_histogram')
            stats = getattr(result, subject + '_statistics')
            np.testing.assert_array_equal([p.get_height() for p in axes.patches],
                                          histogram.frequencies)
            assert len(axes.patches) == 21
            assert axes.get_xlabel() == f'{subject.capitalize()} length, pixels'
            assert axes.get_ylabel() == 'Frequency'
            right = figure.axes[1]
            assert right.get_ylabel() == 'Frequency, %'
            assert right.get_ylim()[1] == pytest.approx(axes.get_ylim()[1] / stats.count * 100)
            assert len(axes.lines) == 2
            assert [line.get_xdata()[0] for line in axes.lines] == [stats.minimum, stats.maximum]


def test_log_curves_retain_raw_zero_counts_and_render_only_positive_bins(tmp_path):
    result, outputs = figures(tmp_path)
    for subject in ('trace', 'segment'):
        for density in (True, False):
            suffix = 'density' if density else ''
            axes = outputs[f'FracPaQ2D_loglogplot{subject}length{suffix}'].axes[0]
            assert axes.get_xscale() == axes.get_yscale() == 'log'
            counts = (getattr(result, subject + '_histogram').frequencies if density else
                      getattr(result, subject + '_complementary').complementary)
            assert np.any(counts == 0)
            assert (axes.lines[0].get_ydata() > 0).all()
            assert len(axes.lines[0].get_ydata()) == np.count_nonzero(counts)
            assert axes.lines[0].get_marker() == 's'
            assert axes.lines[0].get_linestyle() == 'None'
            assert axes.get_ylim()[0] == .1
            assert isinstance(axes.xaxis.get_minor_formatter(), NullFormatter)
            assert isinstance(axes.yaxis.get_minor_formatter(), NullFormatter)
            if not density:
                assert axes.lines[-1].get_xdata().tolist() == [37, 37]
                assert axes.lines[-1].get_linestyle() == '--'


def test_crossplot_keeps_pairing_and_angular_display_without_reversing_axes(tmp_path):
    config = replace(length_config(('LEN-06',), checkbox_censor=True,
                                   edit_degfromnorth='10'), flip_x=True)
    result, outputs = figures(tmp_path, config=config)
    axes = next(iter(outputs.values())).axes[0]
    np.testing.assert_array_equal(axes.lines[0].get_xdata(), result.cross_angles)
    np.testing.assert_array_equal(axes.lines[0].get_ydata(), [3, 4, 5, 3, 4, 5])
    assert axes.lines[0].get_markersize() == 2
    assert axes.get_xlim() == (-10, 370)
    assert not axes.xaxis_inverted() and not axes.yaxis_inverted()
    assert axes.get_xticks().tolist() == [0, 60, 120, 180, 240, 300, 360]


@pytest.mark.parametrize('scale', [None, 2])
def test_all_repeated_lengths_render_valid_log_limits_and_no_fake_points(tmp_path, scale):
    dataset = build_dataset([TraceInput(((0, 0), (1, 0))),
                             TraceInput(((0, 1), (1, 1)))], pixels_per_metre=scale)
    result, outputs = figures(tmp_path, dataset, length_config())
    assert result.unit == ('metres' if scale else 'pixels')
    for name, figure in outputs.items():
        axes = figure.axes[0]
        for bounds in (axes.get_xlim(), axes.get_ylim()):
            assert np.isfinite(bounds).all() and bounds[0] < bounds[1]
        if name.endswith('length') and 'loglog' in name:
            assert len(axes.lines[0].get_xdata()) == 0
            assert any('No positive' in t.get_text() for t in axes.texts)
        if 'histo' in name:
            assert len(axes.patches) == 1 and axes.patches[0].get_height() == 2


def test_polyline_longer_than_domain_diagonal_remains_visible(tmp_path):
    points = ((0, 0), (1, 0), (0, 1), (1, 1), (0, 0))
    dataset = build_dataset([TraceInput(points)])
    result, outputs = figures(tmp_path, dataset, length_config(('LEN-03',)))
    axes = outputs['FracPaQ2D_loglogplottracelength'].axes[0]
    assert result.trace_statistics.maximum > result.maximum_possible_length
    assert axes.get_xlim()[1] > result.trace_statistics.maximum
    assert axes.get_xlim()[0] < result.maximum_possible_length
    assert axes.get_xlim()[0] < axes.get_xlim()[1]
