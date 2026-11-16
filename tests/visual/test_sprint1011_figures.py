"""Tensor orientation, source output contracts, field colours and bar geometry."""

from dataclasses import replace
from types import SimpleNamespace

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.colors import to_rgb
from matplotlib.text import Text
import numpy as np
import pytest

from pyfracpaq.analysis.palettes import matlab_jet
from pyfracpaq.analysis.stability import KINDS, StressParameters, stability_fields
from pyfracpaq.analysis.tensors import crack_tensors, permeability_tensor
from pyfracpaq.domain import TraceInput, build_dataset
from pyfracpaq.plots.stability import render_stability
from pyfracpaq.plots.tensors import render_crack_tensor, render_permeability
from sprint3_reference import reference_config

DATA = build_dataset([TraceInput(((0, 0), (0, 2))), TraceInput(((0, 1), (2, 1)))])
PARAMS = StressParameters(100, 50, 30, 2, 10, .6)


def test_vertical_stress_azimuth_annotation_does_not_overlap_rose_title():
    result=stability_fields(DATA,replace(PARAMS,theta=0))
    output=render_stability(result,reference_config(('MAP-12',)),'dilation')[-1]
    canvas=FigureCanvasAgg(output.figure);canvas.draw();axes=output.figure.axes[0]
    annotation=next(text for text in axes.texts if text.get_text().startswith('Azimuth'))
    # The source's intentional blank second title line reserves annotation
    # space. Compare its visible first line, not the entire multiline box.
    heading=Text(0,0,axes.title.get_text().rstrip(),
                 fontproperties=axes.title.get_fontproperties())
    heading.set_figure(output.figure)
    renderer=canvas.get_renderer()
    first_line_bottom=(axes.title.get_window_extent(renderer).y1
                       - heading.get_window_extent(renderer).height)
    assert first_line_bottom > annotation.get_window_extent(renderer).y1 + 1


def test_tensor_figures_have_north_clockwise_native_colours_and_correct_curves():
    cfg = reference_config()
    result = crack_tensors([2, 3, 4], [90, 90, 90], 16)
    output, = render_crack_tensor(SimpleNamespace(crack=result), cfg)
    assert output.basename == 'FracPaQ2D_cracktensor'
    canvas = FigureCanvasAgg(output.figure)
    canvas.draw()
    axes = output.figure.axes[0]
    assert axes.name == 'polar' and axes.get_theta_direction() == -1
    assert axes.get_theta_offset() == pytest.approx(np.pi / 2)
    assert [to_rgb(line.get_color()) for line in axes.lines] == [
        (1, 0, 1), (0, 0, 1), (1, 0, 0), (0, 1, 0)]
    for line, curve in zip(axes.lines, (result.zero,) + tuple(r.polar for r in result.ranks)):
        np.testing.assert_array_equal(line.get_ydata(), curve)
        assert line.get_linewidth() == 1.5
    assert len(axes.get_legend().texts) == 4
    for lam in (0, 1):
        permeability = permeability_tensor([2], [90], 4, [.001], lam, unit='metres^2')
        output, = render_permeability(permeability, cfg)
        FigureCanvasAgg(output.figure).draw()
        assert output.basename == 'FracPaQ2D_permeability_polar'
        axes = output.figure.axes[0]
        assert len(axes.lines) == 1  # No source's 360 spurious zero columns.
        np.testing.assert_array_equal(axes.lines[0].get_ydata(), permeability.polar)
        assert 'metres' in axes.get_title() and axes.get_theta_direction() == -1


def test_all_stability_outputs_have_one_mohr_and_consistent_native_rgb():
    result = stability_fields(DATA, PARAMS)
    cfg = reference_config(tuple(KINDS))
    outputs = tuple(o for kind in KINDS.values() for o in render_stability(result, cfg, kind))
    assert [o.basename for o in outputs] == [
        'FracPaQ2D_Mohrplot', 'FracPaQ2D_sliptendencymap', 'FracPaQ2D_sliptendencyrose',
        'FracPaQ2D_dilationtendencymap', 'FracPaQ2D_dilationtendencyrose',
        'FracPaQ2D_fracsuscepmap', 'FracPaQ2D_fracsusceprose',
        'FracPaQ2D_CSFmap', 'FracPaQ2D_CSFrose']
    for output in outputs:
        FigureCanvasAgg(output.figure).draw()
    mohr = outputs[0].figure.axes[0]
    assert [line.get_label() for line in mohr.lines] == ['Stress', 'Effective stress', 'Sliding or Failure']
    np.testing.assert_array_equal(mohr.lines[0].get_xdata(), result.mohr.normal)
    np.testing.assert_array_equal(mohr.lines[1].get_xdata(), result.mohr.effective_normal)
    assert not mohr.collections  # Source accepts sn/tau but does not draw their points.
    for index, kind in enumerate(KINDS.values()):
        field = result.field(kind)
        map_axes = outputs[1 + 2 * index].figure.axes[0]
        rose_axes = outputs[2 + 2 * index].figure.axes[0]
        np.testing.assert_array_equal(map_axes.collections[0].get_colors()[:, :3],
                                       matlab_jet(100, reverse=kind == 'susceptibility')[field.map_indices])
        assert len(rose_axes.patches) >= 36 and not rose_axes.axison
        for petal, rgb in zip(rose_axes.patches[:36],
                              matlab_jet(19, reverse=kind == 'susceptibility')[field.rose_indices]):
            np.testing.assert_array_equal(petal.get_facecolor()[:3], rgb)
        line = rose_axes.lines[-1]
        assert line.get_color() == 'red' and line.get_linewidth() == 1.5
        assert len(result.rose.edges) == 37
        assert len(map_axes.figure.axes) == len(rose_axes.figure.axes) == 2
        if kind == 'csf':
            for axes in (map_axes, rose_axes):
                assert [t.get_text() for t in axes.figure.axes[1].get_xticklabels()] == ['Non-CSF', 'CSF']


@pytest.mark.parametrize('flip', [False, True])
@pytest.mark.parametrize('identifier,kind', list(KINDS.items()))
def test_new_map_and_rose_bars_keep_edges_and_fixed_clearance_at_all_sizes(flip, identifier, kind):
    result = stability_fields(DATA, PARAMS)
    cfg = replace(reference_config((identifier,)), flip_x=flip, flip_y=flip)
    for output in render_stability(result, cfg, kind)[1:]:
        figure = output.figure
        canvas = FigureCanvasAgg(figure)
        for size in ((6, 6), (10, 4), (3.4, 2.8), (6, 6)):
            figure.set_size_inches(*size)
            canvas.draw()
            axes, scale = figure.axes
            plot, bar = axes.get_window_extent(), scale.get_window_extent()
            np.testing.assert_allclose((plot.x0, plot.x1), (bar.x0, bar.x1), atol=1e-8, rtol=0)
            bottom = axes.xaxis.label.get_window_extent().y0 if axes.axison else plot.y0
            gap = (bottom - bar.y1) / canvas.get_renderer().points_to_pixels(1)
            assert gap == pytest.approx(25, abs=1e-8)
            if axes.axison:
                assert axes.xaxis_inverted() == axes.yaxis_inverted() == flip


def test_constant_susceptibility_has_one_tick_and_the_same_colour_in_plot_and_bar():
    result = stability_fields(DATA, replace(PARAMS, sigma2=100), kinds=('susceptibility',))
    outputs = render_stability(result, reference_config(('MAP-13',)), 'susceptibility')
    value = result.field('susceptibility').colour_range[0]
    for output, levels in zip(outputs[1:], (100, 19)):
        FigureCanvasAgg(output.figure).draw()
        axes, scale = output.figure.axes
        bar = scale._colorbar
        np.testing.assert_array_equal(bar.get_ticks(), [value])
        rgb = axes.collections[0].get_colors()[0, :3] if axes.axison else axes.patches[0].get_facecolor()[:3]
        np.testing.assert_array_equal(bar.cmap(bar.norm(value))[:3], rgb)


def test_no_pore_pressure_omits_effective_mohr_and_multicolour_map_is_coupled_once():
    data = build_dataset([TraceInput(((0, 0), (0, 2)), (1, 0, 0)),
                          TraceInput(((0, 1), (2, 1)), (0, 0, 1))])
    result = stability_fields(data, replace(PARAMS, pore_pressure=0))
    cfg = reference_config(tuple(KINDS))
    outputs = tuple(o for kind in KINDS.values() for o in render_stability(result, cfg, kind))
    assert len(outputs) == 10
    assert sum(o.basename == 'FracPaQ2D_tracemap_multicolour' for o in outputs) == 1
    mohr = next(o for o in outputs if o.basename == 'FracPaQ2D_Mohrplot')
    assert len(mohr.figure.axes[0].lines) == 2
