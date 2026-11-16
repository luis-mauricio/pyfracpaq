"""Figure primitives and deterministic exports; no claim of MATLAB execution."""

from dataclasses import replace

from matplotlib import rcParams
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.colors import LogNorm
from matplotlib.patches import Polygon
import numpy as np
import pytest

from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.analysis.palettes import cmocean
from pyfracpaq.domain.execution import RunContext
from pyfracpaq.plots.style import legend, matlab_style
from sprint3_reference import directional_dataset, reference_config


def execute(tmp_path, cfg=None):
    cfg = cfg or reference_config(checkbox_shownodes=True, checkbox_rosecolour=False,
                                  checkbox_showrosemean=True)
    dataset = directional_dataset()
    registry = AnalysisRegistry()
    results = registry.execute(dataset, RunContext(cfg, tmp_path, tmp_path, 'plot'),
                               lambda *a: None, lambda: False)
    outputs = {result.analysis_id: next(s for s in registry.specs
                                       if s.id == result.analysis_id).render(
                                           result.data, cfg)[0] for result in results}
    for output in outputs.values():
        FigureCanvasAgg(output.figure).draw()
    return cfg, dataset, results, outputs


def test_map_artists_nodes_centres_and_q17_colourbar(tmp_path):
    cfg, dataset, results, outputs = execute(tmp_path)
    axes = outputs['MAP-01'].figure.axes[0]
    assert len(axes.collections[0].get_segments()) == dataset.n_traces
    markers = axes.collections[1]
    assert len(markers.get_offsets()) == 3 * dataset.n_segments + dataset.n_traces
    expected = []
    for trace in dataset.traces:
        for segment in trace.segments:
            expected.extend((segment.start.point, segment.end.point, segment.midpoint))
        expected.append(trace.midpoint)
    np.testing.assert_array_equal(markers.get_offsets(), expected)
    np.testing.assert_array_equal(markers.get_sizes()[:4], [16, 16, 36, 36])
    assert axes.get_xlabel() == 'X, pixels'
    for identifier in ('MAP-04', 'MAP-05'):
        figure = outputs[identifier].figure
        result = next(r.data for r in results if r.analysis_id == identifier)
        expected = cmocean('haline')[result.colour_indices]
        np.testing.assert_array_equal(figure.axes[0].collections[0].get_colors()[:, :3],
                                      expected)
        assert isinstance(figure.axes[1]._colorbar.norm, LogNorm)
        assert figure.axes[1]._colorbar.orientation == 'horizontal'
        assert figure.axes[1].get_position().y1 < figure.axes[0].get_position().y0
    strike = outputs['MAP-06'].figure
    assert strike.axes[1].get_xlabel() == 'Segment strike, degrees'
    assert strike.axes[1]._colorbar.norm.vmax == 180


@pytest.mark.parametrize('flip_x,flip_y', [(False, False), (True, False),
                                         (False, True), (True, True)])
def test_map_display_flips_and_scaled_units_preserve_geometry(tmp_path, flip_x, flip_y):
    dataset = directional_dataset().with_scale(2)
    original = dataset.as_arrays().node_coordinates.copy()
    cfg = replace(reference_config(('MAP-06',), edit_degfromnorth='10'),
                  flip_x=flip_x, flip_y=flip_y)
    registry = AnalysisRegistry()
    result = registry.execute(dataset, RunContext(cfg, tmp_path, tmp_path, 'flip'),
                               lambda *a: None, lambda: False)[0]
    figure = registry.specs[3].render(result.data, cfg)[0].figure
    axes = figure.axes[0]
    assert axes.xaxis_inverted() == flip_x
    assert axes.yaxis_inverted() == flip_y
    assert axes.get_xlabel() == 'X, metres'
    assert axes.get_aspect() == 1
    np.testing.assert_array_equal(dataset.as_arrays().node_coordinates, original)
    assert not list(tmp_path.iterdir())  # Maps alone never trigger EZROSE.


def test_histogram_dual_frequency_axes_and_rose_mean_geometry(tmp_path):
    cfg, dataset, results, outputs = execute(tmp_path)
    histogram = next(r.data for r in results if r.analysis_id == 'ANG-01')
    axes, right = outputs['ANG-01'].figure.axes
    assert len(axes.patches) == 21
    np.testing.assert_array_equal([p.get_height() for p in axes.patches],
                                  histogram.frequencies)
    assert axes.get_ylabel() == 'Frequency'
    assert right.get_ylabel() == 'Frequency, %'
    assert right.get_ylim()[1] == pytest.approx(axes.get_ylim()[1] / 12 * 100)
    rose = outputs['ANG-02'].figure.axes[0]
    polygon = next(p for p in rose.patches if isinstance(p, Polygon))
    np.testing.assert_array_equal(polygon.get_xy()[:-1], histogram.rose.vertices)
    assert rose.lines[-1].get_label() == 'Axial mean'
    mean_line = rose.lines[-1].get_xydata()
    np.testing.assert_allclose(mean_line[0], -mean_line[1])
    assert not rose.axison


def test_coloured_weighted_rose_repeats_phase_table_per_axial_half(tmp_path):
    cfg = reference_config(('ANG-02',), checkbox_rosecolour=True,
                            checkbox_roselengthweighted=True)
    _, _, results, outputs = execute(tmp_path, cfg)
    figure = outputs['ANG-02'].figure
    polygons = [p for p in figure.axes[0].patches if isinstance(p, Polygon)]
    bins = len(results[0].data.rose.edges) - 1
    assert len(polygons) == bins
    for a, b in zip(polygons[:bins // 2], polygons[bins // 2:]):
        assert a.get_facecolor() == b.get_facecolor()
        assert a.get_edgecolor() == a.get_facecolor()
    assert figure.axes[1]._colorbar.cmap.N == bins // 2 + 1
    assert 'length weighted' in figure.axes[0].get_title()


def test_style_scope_axes_and_legend_helpers_are_isolated():
    from matplotlib import get_backend
    get_backend()  # Resolve Matplotlib's lazy backend sentinel before snapshot.
    before = rcParams.copy()
    from pyfracpaq.plots.style import figure_axes
    with matlab_style():
        figure, axes = figure_axes()
        axes.plot([0, 1], [0, 1], label='Reference')
        item = legend(axes)
        assert item.get_frame_on()
        assert type(item.get_frame().get_boxstyle()).__name__ == 'Square'
        assert axes.spines['left'].get_linewidth() == .5
        assert figure.get_facecolor() == (1, 1, 1, 1)
    assert rcParams == before
