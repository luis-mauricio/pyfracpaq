"""Circular artists, physical extents, palettes and all three input modes."""

from dataclasses import replace

import numpy as np
import pytest
from matplotlib.backends.backend_agg import FigureCanvasAgg

from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.analysis.circular import sample_circles
from pyfracpaq.analysis.hough import HoughParameters
from pyfracpaq.analysis.palettes import matlab_rgb
from pyfracpaq.domain import TraceInput, build_dataset
from pyfracpaq.domain.execution import RunContext
from pyfracpaq.geometry import Bounds
from pyfracpaq.io import read_txt
from pyfracpaq.io.images import read_image
from pyfracpaq.io.svg import read_svg
from pyfracpaq.plots.circular import render_circular
from reference_common import ROOT
from sprint3_reference import reference_config


@pytest.mark.parametrize('mode', ['txt', 'svg', 'image'])
def test_circular_run_all_input_modes_shared_results_colours_units_and_extents(mode, tmp_path):
    if mode == 'txt':
        dataset = read_txt(ROOT / 'tests/fixtures/nodes/mixed.txt')
    elif mode == 'svg':
        dataset = read_svg(ROOT / 'tests/fixtures/svg/multicolour.svg').dataset
    else:
        dataset = read_image(ROOT / 'tests/fixtures/images/rectangular.tif',
                             HoughParameters(peaks=100), pixels_per_metre=2).dataset
    cfg = reference_config(('MAP-07', 'MAP-08'), edit_numscancircles='3', checkbox_showcircles=True)
    registry = AnalysisRegistry()
    results = registry.execute(dataset, RunContext(cfg, tmp_path, tmp_path, mode),
                               lambda *a: None, lambda: False)
    assert len(results) == 2 and results[0].data is results[1].data
    data = results[0].data
    outputs = [o for r in results for o in
               next(s for s in registry.specs if s.id == r.analysis_id).render(r.data, cfg)]
    assert [o.basename for o in outputs] == ['FracPaQ2D_scancircle',
                                           'FracPaQ2D_intensityP21', 'FracPaQ2D_densityP20']
    assert len(list(tmp_path.glob('*.txt'))) == 2
    scan = outputs[0].figure.axes[0]
    assert scan.get_title() == f'Mapped trace segments, n={dataset.n_segments}\n'
    np.testing.assert_array_equal(scan.collections[0].get_colors()[0, :3], dataset.traces[0].colour)
    np.testing.assert_array_equal(scan.collections[1].get_offsets(), data.grid.centres)
    np.testing.assert_allclose(scan.collections[1].get_edgecolors()[0], [1, 0, 0, 1])
    assert scan.collections[1].get_linewidths()[0] == .25
    # EllipseCollection retains data-space radii without one Python patch per circle.
    np.testing.assert_allclose(scan.collections[1]._widths, data.grid.radius)
    for output, values in zip(outputs[1:], (data.intensity, data.density)):
        axes, bar = output.figure.axes
        FigureCanvasAgg(output.figure).draw()
        image = axes.images[0]
        np.testing.assert_array_equal(image.get_array(), values)
        np.testing.assert_array_equal(image.get_extent(), data.grid.extent)
        np.testing.assert_array_equal(image.cmap.colors, matlab_rgb('hot')[::-1])
        assert image.origin == 'lower' and image.get_interpolation() == 'nearest'
        assert image.norm.vmin == 0
        assert image.norm.vmax == (values.max() or 1)
        assert axes.get_xlim() == (dataset.bounds.x_min, dataset.bounds.x_max)
        assert axes.get_ylim() == (dataset.bounds.y_min, dataset.bounds.y_max)
        assert axes.get_xlabel() == f'X, {dataset.length_unit}'
        assert (bar.get_position().x0, bar.get_position().x1) == pytest.approx(
            (axes.get_position().x0, axes.get_position().x1))
        assert bar.get_position().y1 < axes.get_position().y0
        assert ('metre' in bar.get_xlabel()) == (mode == 'image')
        assert axes.get_aspect() == 1


@pytest.mark.parametrize('kind,selected', [('intensity', ('MAP-07',)), ('density', ('MAP-08',))])
def test_single_map_show_circles_flips_display_only(kind, selected):
    dataset = build_dataset([TraceInput(((0, 0), (6, 6)))])
    data = sample_circles(dataset, 2)
    cfg = reference_config(selected, checkbox_showcircles=True)
    cfg = replace(cfg, flip_x=True, flip_y=True)
    outputs = render_circular(data, cfg, kind)
    assert len(outputs) == 2
    for output in outputs:
        axes = output.figure.axes[0]
        assert axes.xaxis_inverted() and axes.yaxis_inverted()
    np.testing.assert_array_equal(outputs[1].figure.axes[0].images[0].get_array(), getattr(data, kind))


def test_empty_windows_render_zero_arrays_with_only_zero_bar_tick():
    dataset = build_dataset([TraceInput(((0, 0), (6, 0)))], source_bounds=Bounds(0, 0, 6, 6))
    result = sample_circles(dataset, 2)
    assert not result.intensity.any() and not result.density.any()
    outputs = render_circular(result, reference_config(('MAP-08',)), 'density')
    assert len(outputs) == 1
    FigureCanvasAgg(outputs[0].figure).draw()
    axes, bar = outputs[0].figure.axes
    np.testing.assert_array_equal(axes.images[0].get_array(), np.zeros((2, 2)))
    np.testing.assert_array_equal(bar.get_xticks(), [0])
    assert result.global_intensity > 0 and result.global_density > 0
