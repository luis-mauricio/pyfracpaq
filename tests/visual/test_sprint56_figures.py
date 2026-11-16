"""SVG colour artists, image-origin analyses and four-panel diagnostics."""

from dataclasses import replace

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from PIL import Image

from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.analysis.hough import HoughParameters
from pyfracpaq.domain.execution import RunContext
from pyfracpaq.io import read_txt
from pyfracpaq.io.images import read_image
from pyfracpaq.io.svg import read_svg
from pyfracpaq.plots.hough import render_hough
from pyfracpaq.plots.preview import draw_preview
from matplotlib.figure import Figure
from reference_common import ROOT
from sprint3_reference import reference_config


def test_multicolour_preview_and_additional_map_share_exact_per_trace_colours(tmp_path):
    dataset = read_svg(ROOT / 'tests/fixtures/svg/multicolour.svg').dataset
    figure = Figure()
    draw_preview(figure, dataset, flip_y=True)
    np.testing.assert_array_equal(figure.axes[0].collections[0].get_colors()[:, :3],
                                  dataset.as_arrays().trace_colours)
    assert figure.axes[0].yaxis_inverted()
    cfg = reference_config(('MAP-01', 'MAP-04', 'MAP-05', 'MAP-06'))
    registry = AnalysisRegistry()
    results = registry.execute(dataset, RunContext(cfg, tmp_path, tmp_path, 'multi'),
                               lambda *a: None, lambda: False)
    outputs = [output for result in results for output in
               next(s for s in registry.specs if s.id == result.analysis_id).render(result.data, cfg)]
    assert len(outputs) == 5
    extra = [o for o in outputs if o.basename == 'FracPaQ2D_tracemap_multicolour']
    assert len(extra) == 1
    np.testing.assert_array_equal(extra[0].figure.axes[0].collections[0].get_colors()[:, :3],
                                  dataset.as_arrays().trace_colours)
    assert extra[0].figure.axes[0].collections[0].get_zorder() \
        > extra[0].figure.axes[0].spines['bottom'].get_zorder()
    # It is coupled to the map family, not to selecting the basic trace map.
    cfg = reference_config(('MAP-06',))
    result = registry.execute(dataset, RunContext(cfg, tmp_path, tmp_path, 'strike'),
                              lambda *a: None, lambda: False)[0]
    outputs = next(s for s in registry.specs if s.id == 'MAP-06').render(result.data, cfg)
    assert [o.basename for o in outputs] == ['FracPaQ2D_tracemap_multicolour',
                                           'FracPaQ2D_segmentstrikemap']


def test_colour_txt_controls_histograms_and_plain_rose_fill(tmp_path):
    source = tmp_path / 'set_colourFF0000_converted.txt'
    source.write_text('0\t0\t3\t4\n0\t0\t2\t0\n')
    dataset = read_txt(source)
    cfg = reference_config(('MAP-01', 'LEN-02', 'ANG-01', 'ANG-02'), checkbox_rosecolour=False)
    registry = AnalysisRegistry()
    results = registry.execute(dataset, RunContext(cfg, tmp_path, tmp_path, 'colour'),
                               lambda *a: None, lambda: False)
    for result in results:
        outputs = next(s for s in registry.specs if s.id == result.analysis_id).render(result.data, cfg)
        for output in outputs:
            axes = output.figure.axes[0]
            if result.analysis_id == 'MAP-01':
                np.testing.assert_array_equal(axes.collections[0].get_colors()[0], [1, 0, 0, 1])
            else:
                assert axes.patches[0].get_facecolor() == (1, 0, 0, 1)


def test_four_panel_hough_raw_image_rho_orientation_and_threshold():
    result = read_image(ROOT / 'tests/fixtures/images/directional.tif',
                        HoughParameters(peaks=100)).hough
    output = render_hough(result)
    assert output.basename == 'FracPaQ2D_Houghstuff'
    figure = output.figure
    FigureCanvasAgg(figure).draw()
    assert len(figure.axes) == 4
    raw, side_rho, plan, side_theta = figure.axes
    np.testing.assert_array_equal(raw.images[0].get_array(), result.image)
    assert raw.images[0].origin == 'lower'
    assert plan.name == side_rho.name == side_theta.name == '3d'
    assert len(plan.collections) == 1
    assert plan.yaxis_inverted()
    assert len(side_rho.collections) == len(side_theta.collections) == 2
    assert side_rho.elev == 0 and side_rho.azim == 0
    assert side_theta.elev == 0 and side_theta.azim == -90
    assert plan.elev == 90
    assert raw.get_xlabel() == 'X, pixels'
    assert plan.get_xlabel() == r'$\theta$, degrees'


def test_existing_families_render_from_image_with_complete_geometry(tmp_path):
    result = read_image(ROOT / 'tests/fixtures/images/rectangular.tif',
                        HoughParameters(peaks=100), pixels_per_metre=2)
    dataset = result.dataset
    assert dataset is not None
    cfg = reference_config(('MAP-01', 'MAP-04', 'MAP-05', 'MAP-06',
                             'LEN-02', 'LEN-03', 'LEN-06', 'ANG-01', 'ANG-02'),
                            checkbox_shownodes=True)
    registry = AnalysisRegistry()
    results = registry.execute(dataset, RunContext(cfg, tmp_path, tmp_path, 'image'),
                               lambda *a: None, lambda: False)
    outputs = [o for result in results for o in
               next(s for s in registry.specs if s.id == result.analysis_id).render(result.data, cfg)]
    assert len(outputs) == 13
    for output in outputs:
        FigureCanvasAgg(output.figure).draw()
    assert len(list(tmp_path.glob('*.txt'))) == 4
    for trace in dataset.traces:
        assert trace.segments[0].midpoint == trace.midpoint
        assert trace.segments[0].end_length == trace.total_length


def test_hough_reconstructed_palettes_have_frozen_piecewise_anchors():
    from io import BytesIO
    from pyfracpaq.resources import resource_bytes
    with np.load(BytesIO(resource_bytes('matlab_rgb.npz'))) as archive:
        hot, bone = archive['hot'], archive['bone']
        assert hot.shape == bone.shape == (256, 3)
        np.testing.assert_array_equal(hot[95], [1, 0, 0])
        np.testing.assert_array_equal(hot[191], [1, 1, 0])
        np.testing.assert_array_equal(hot[-1], [1, 1, 1])
        np.testing.assert_allclose(bone[-1], [1, 1, 1], atol=1e-14)
