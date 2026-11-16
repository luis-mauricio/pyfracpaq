"""Rendered colourbar endpoints follow the live axes box on every backend draw."""

import ast
from dataclasses import replace

import numpy as np
import pytest
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.colors import Normalize
from matplotlib.figure import Figure
from matplotlib.transforms import Bbox
from PIL import Image

from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.domain import TraceInput, build_dataset
from pyfracpaq.domain.execution import RunContext
from pyfracpaq.io.figures import export_png
from pyfracpaq.plots.colourbars import colourbar
from reference_common import ROOT
from sprint3_reference import directional_dataset, reference_config


def endpoints(host, bar, renderer):
    plot = host.get_window_extent(renderer)
    scale = bar.ax.get_window_extent(renderer)
    if bar.orientation == 'horizontal':
        return (plot.x0, plot.x1), (scale.x0, scale.x1)
    return (plot.y0, plot.y1), (scale.y0, scale.y1)


def label_clearance_points(host, bar, renderer, location):
    plot, scale = host.get_window_extent(renderer), bar.ax.get_window_extent(renderer)
    axis = host.xaxis if bar.orientation == 'horizontal' else host.yaxis
    text = axis.get_tightbbox(renderer) if host.axison else None
    facing = Bbox.union([plot, text]) if text is not None else plot
    gap = {'bottom': facing.y0 - scale.y1, 'top': scale.y0 - facing.y1,
           'left': facing.x0 - scale.x1, 'right': scale.x0 - facing.x1}[location]
    return gap / renderer.points_to_pixels(1)


@pytest.mark.parametrize('location', ['bottom', 'top', 'left', 'right'])
@pytest.mark.parametrize('kind', ['equal', 'box', 'automatic', 'polar'])
def test_horizontal_and_vertical_bars_follow_aspect_and_resizing(location, kind):
    figure = Figure()
    host = figure.add_axes((.2, .25, .55, .5), projection='polar' if kind == 'polar' else None)
    if kind == 'equal':
        host.set(xlim=(0, 3), ylim=(0, 1), aspect='equal')
    elif kind == 'box':
        host.set_box_aspect(1)
    bar = colourbar(host, location=location, norm=Normalize(0, 8))
    canvas = FigureCanvasAgg(figure)
    original = host.get_position(original=True).frozen()
    for size in ((6, 6), (12, 3.5), (3.5, 10), (7, 7)):
        figure.set_size_inches(*size)
        canvas.draw()  # No second draw or explicit resize callback allowed.
        expected, actual = endpoints(host, bar, canvas.get_renderer())
        np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-9)
        np.testing.assert_array_equal(host.get_position(original=True).bounds, original.bounds)
        plot, scale = host.get_position(), bar.ax.get_position()
        if location == 'bottom':
            assert scale.y1 < plot.y0
        elif location == 'top':
            assert scale.y0 > plot.y1
        elif location == 'left':
            assert scale.x1 < plot.x0
        else:
            assert scale.x0 > plot.x1


@pytest.mark.parametrize('identifier', ['MAP-04', 'MAP-05', 'MAP-06', 'ANG-02', 'MAP-07', 'MAP-08'])
@pytest.mark.parametrize('stretch', [(1, 1), (4, 1), (1, 4)])
def test_every_existing_coloured_output_matches_actual_plot_box(identifier, stretch, tmp_path):
    data = directional_dataset()
    data = build_dataset([TraceInput(tuple((n.x * stretch[0], n.y * stretch[1]) for n in t.nodes))
                          for t in data.traces])
    cfg = replace(reference_config((identifier,), checkbox_rosecolour=True,
                                    edit_numscancircles='3'), flip_x=True, flip_y=True)
    registry = AnalysisRegistry()
    result = registry.execute(data, RunContext(cfg, tmp_path, tmp_path, identifier),
                              lambda *a: None, lambda: False)[0]
    spec = next(s for s in registry.specs if s.id == identifier)
    figure = spec.render(result.data, cfg)[0].figure
    host, bar_axes = figure.axes
    bar = bar_axes._colorbar
    canvas = FigureCanvasAgg(figure)
    norm = bar.norm.vmin, bar.norm.vmax
    palette = bar.cmap(np.arange(bar.cmap.N))
    for size in ((6, 6), (12, 4), (4, 10), (7, 7)):
        figure.set_size_inches(*size)
        canvas.draw()
        expected, actual = endpoints(host, bar, canvas.get_renderer())
        np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-9)
        assert label_clearance_points(host, bar, canvas.get_renderer(), 'bottom') == pytest.approx(25, abs=1e-8)
        assert (bar.norm.vmin, bar.norm.vmax) == norm
        np.testing.assert_array_equal(bar.cmap(np.arange(bar.cmap.N)), palette)


def test_alignment_updates_after_limits_change_and_with_a_renderer_dependent_host_locator():
    figure = Figure()
    host = figure.add_axes((.2, .25, .55, .5))
    host.set(aspect='equal', xlim=(0, 1), ylim=(0, 1))
    def host_locator(axes, renderer):
        assert renderer is not None
        return Bbox.from_bounds(.2, .25, .55, .5)
    host.set_axes_locator(host_locator)
    bar = colourbar(host)
    canvas = FigureCanvasAgg(figure)
    for limits in ((0, 1), (0, 4), (0, .25)):
        host.set_xlim(*limits)
        canvas.draw()
        expected, actual = endpoints(host, bar, canvas.get_renderer())
        np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-9)


def test_mathtext_scale_label_stays_inside_short_wide_figures_on_first_draw():
    figure = Figure(figsize=(10, 4))
    host = figure.add_axes((.13, .22, .74, .64))
    host.set(aspect='equal', xlim=(0, 2), ylim=(0, 1))
    bar = colourbar(host, norm=Normalize(0, 1))
    bar.set_label('Intensity of segments (P21), pixel$^{-1}$')
    canvas = FigureCanvasAgg(figure)
    for size in ((10, 4), (10, 3.5), (6, 6)):
        figure.set_size_inches(*size)
        canvas.draw()
        assert bar.ax.xaxis.get_tightbbox(canvas.get_renderer()).y0 >= 0
        expected, actual = endpoints(host, bar, canvas.get_renderer())
        np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-9)


@pytest.mark.parametrize('location', ['bottom', 'top', 'left', 'right'])
@pytest.mark.parametrize('pad', [None, 12.])
def test_clearance_from_axis_labels_is_fixed_and_small_windows_reserve_space(location, pad):
    figure = Figure()
    host = figure.add_axes((.2, .25, .55, .5))
    host.set_box_aspect(1)
    host.set_xlabel('X coordinate, metres')
    host.set_ylabel('Y coordinate, metres')
    if location == 'top':
        host.xaxis.set_label_position('top')
        host.xaxis.tick_top()
    elif location == 'right':
        host.yaxis.set_label_position('right')
        host.yaxis.tick_right()
    bar = colourbar(host, location=location, pad=pad)
    bar.set_label('Estimated quantity, metre$^{-1}$')
    canvas = FigureCanvasAgg(figure)
    original = host.get_position(original=True).bounds
    first = None
    for size in ((6, 6), (16, 10), (3.2, 2.5), (10, 3.5), (6, 6)):
        figure.set_size_inches(*size)
        canvas.draw()
        renderer = canvas.get_renderer()
        assert label_clearance_points(host, bar, renderer, location) == pytest.approx(
            25 if pad is None else pad, abs=1e-8)
        label = host.xaxis.label if bar.orientation == 'horizontal' else host.yaxis.label
        text, scale = label.get_window_extent(renderer), bar.ax.get_window_extent(renderer)
        direct_gap = {'bottom': text.y0 - scale.y1, 'top': scale.y0 - text.y1,
                      'left': text.x0 - scale.x1, 'right': scale.x0 - text.x1}[location]
        assert direct_gap / renderer.points_to_pixels(1) == pytest.approx(
            25 if pad is None else pad, abs=1e-8)
        expected, actual = endpoints(host, bar, renderer)
        np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-8)
        text_axis = bar.ax.xaxis if bar.orientation == 'horizontal' else bar.ax.yaxis
        tight = text_axis.get_tightbbox(renderer)
        assert tight.x0 >= -1e-5 and tight.x1 <= figure.bbox.x1 + 1e-5
        assert tight.y0 >= -1e-5 and tight.y1 <= figure.bbox.y1 + 1e-5
        np.testing.assert_array_equal(host.get_position(original=True).bounds, original)
        if first is None:
            first = host.get_position().bounds
    # Growing the window restores the initial plot size, without cumulative shrinkage.
    np.testing.assert_allclose(host.get_position().bounds, first, rtol=0, atol=1e-9)


@pytest.mark.parametrize('location', ['bottom', 'right'])
def test_png_export_and_restored_screen_size_keep_bar_aligned(location, tmp_path):
    figure = Figure(figsize=(10, 4))
    host = figure.add_axes((.2, .25, .55, .5))
    host.set_box_aspect(1)
    host.set_xlabel('X, metres')
    host.set_ylabel('Y, metres')
    bar = colourbar(host, location=location)
    bar.set_label('Estimated quantity, metre$^{-1}$')
    canvas = FigureCanvasAgg(figure)
    observed = []
    gaps = []
    canvas.mpl_connect('draw_event', lambda event: observed.append(endpoints(host, bar, event.renderer)))
    canvas.mpl_connect('draw_event', lambda event: gaps.append(
        label_clearance_points(host, bar, event.renderer, location)))
    old_size = figure.get_size_inches().copy()
    target = export_png(figure, 'aligned', location, tmp_path)
    assert observed
    for expected, actual in observed:
        np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-8)
    np.testing.assert_allclose(gaps, 25, rtol=0, atol=1e-8)
    np.testing.assert_array_equal(figure.get_size_inches(), old_size)
    canvas.draw()
    expected, actual = endpoints(host, bar, canvas.get_renderer())
    np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-9)
    with Image.open(target) as image:
        assert image.size == (4724, 4724)
        assert abs(image.info['dpi'][0] - 600) < .01


def test_future_renderers_cannot_bypass_the_shared_colourbar_factory():
    for source in (ROOT / 'pyfracpaq/plots').rglob('*.py'):
        if source.name == 'colourbars.py':
            continue
        for node in ast.walk(ast.parse(source.read_text())):
            if isinstance(node, ast.ImportFrom) and node.module == 'matplotlib.colorbar':
                pytest.fail(f'{source.name}: use plots.colourbars.colourbar for all colourbars.')
            if isinstance(node, ast.Call):
                name = node.func.attr if isinstance(node.func, ast.Attribute) else (
                    node.func.id if isinstance(node.func, ast.Name) else '')
                assert name not in ('colorbar', 'Colorbar', 'ColorbarBase'), source.name
