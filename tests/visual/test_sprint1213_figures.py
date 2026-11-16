"""Source names, axes, styles, coupling and controlled empty visualizations."""

from dataclasses import replace

from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np
import pytest
from scipy.io import loadmat

from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.analysis.blocks import compute_blocks
from pyfracpaq.analysis.lengths import compute_lengths
from pyfracpaq.analysis.profiles import ALONG, CIRCULAR, FROM, compute_graphs
from pyfracpaq.domain.execution import RunContext
from pyfracpaq.geometry.profiles import ProfileLine
from pyfracpaq.plots.blocks import render_blocks
from pyfracpaq.plots.profiles import render_graph
from pyfracpaq.plots.variogram import render_variogram, variogram
from reference_common import REFERENCE
from sprint1213_reference import block_dataset, configuration, graph_dataset


def test_all_nine_graph_names_coupling_native_labels_limits_and_colours(tmp_path):
    config = configuration((*ALONG, *CIRCULAR, *FROM))
    result = compute_graphs(graph_dataset(), RunContext(config, tmp_path, tmp_path, 'x'), lambda *_: None)
    figures = [figure for key in config.selected for figure in render_graph(result, config, key)]
    names = ['tracelengthalonggraph', 'segmentlengthalonggraph', 'segmentanglealonggraph',
             'graphtracemap', 'intensityalonggraph', 'densityalonggraph',
             'tracelengthfromgraph', 'segmentlengthfromgraph', 'segmentanglefromgraph']
    assert [f.basename for f in figures] == ['guiFracPaQ2D_' + name for name in names]
    native = loadmat(REFERENCE / 'sprint13/native/graph_arrays.mat', simplify_cells=True)['graphs']
    keys = ['trace_along', 'segment_along', 'angle_along', 'map', 'intensity', 'density',
            'trace_from', 'segment_from', 'angle_from']
    for output, key in zip(figures, keys):
        FigureCanvasAgg(output.figure).draw()
        axes = output.figure.axes[0]
        assert len(output.figure.axes) == 1
        if key not in ('map', 'intensity', 'density'):
            assert axes.get_title() == native[key]['title']
            assert axes.get_xlabel() == native[key]['xlabel']
            assert axes.get_ylabel() == native[key]['ylabel']
            np.testing.assert_allclose(axes.get_xlim(), native[key]['xlim'], atol=1e-12)
            np.testing.assert_allclose(axes.get_ylim(), native[key]['ylim'], atol=1e-12)
            assert axes.lines[0].get_color() == 'blue'
        if key == 'map':
            assert [text.get_text() for text in axes.get_legend().get_texts()] == ['Point 1', 'Point 2']
            assert len(axes.patches) == 3
            assert all(patch.get_edgecolor() == (1, 0, 0, 1) for patch in axes.patches)
        output.figure.clear()
    cfg = replace(config, selected=('GRA-07',))
    assert len(render_graph(result, cfg, 'GRA-07')) == 3


def test_no_hits_has_empty_artists_and_explicit_annotation(tmp_path):
    cfg = configuration(ALONG, line=ProfileLine((-6, 10), (6, 10)))
    result = compute_graphs(graph_dataset(), RunContext(cfg, tmp_path, tmp_path, 'x'), lambda *_: None)
    for key in ALONG:
        figure = render_graph(result, cfg, key)[0].figure
        FigureCanvasAgg(figure).draw()
        assert len(figure.axes[0].lines[0].get_xdata()) == 0
        assert 'No noncoincident' in figure.axes[0].texts[0].get_text()
        figure.clear()


def test_three_block_figures_constant_ccdf_and_semivariogram(tmp_path):
    cfg = configuration(('LEN-15',))
    lengths = compute_lengths(block_dataset(), RunContext(cfg, tmp_path, tmp_path, 'x'), lambda *_: None)
    result = replace(lengths, blocks=compute_blocks(block_dataset(), exclude_border=True))
    figures = (*render_blocks(result, cfg), *render_variogram(result, cfg))
    assert [f.basename for f in figures] == ['FracPaQ2D_blocksizecentroidmap',
        'FracPaQ2D_blocksizeloglog', 'FracPaQ2D_blocksizehisto', 'FracPaQ2D_segmentlength_variogram']
    for output in figures:
        FigureCanvasAgg(output.figure).draw()
    centroid_axes = figures[0].figure.axes[0]
    assert centroid_axes.lines[0].get_marker() == 'o'
    np.testing.assert_allclose(centroid_axes.lines[0].get_xdata(), [30, 90])
    assert 'constant block area' in figures[1].figure.axes[0].texts[0].get_text()
    assert sum(bar.get_height() for bar in figures[2].figure.axes[0].patches) == 100
    assert figures[3].figure.axes[0].lines[0].get_marker() == 's'
    assert figures[3].figure.axes[0].lines[0].get_color() == 'r'
    for output in figures:
        output.figure.clear()


@pytest.mark.parametrize('options', [{}, {'kind': 'cloud2'}, {'anisotropy': True},
                                  {'anisotropy': True, 'kind': 'cloud2'}])
def test_advanced_plotit_is_api_only_and_has_no_new_gui_parameters(options):
    args = ([[0, 0], [1, 0], [0, 1]], [1, 2, 3])
    result, absent = variogram(*args, plotit=False, **options)
    assert absent is None
    same, output = variogram(*args, plotit=True, **options)
    np.testing.assert_allclose(result.values, same.values, equal_nan=True)
    FigureCanvasAgg(output.figure).draw()
    output.figure.clear()
    spec = next(s for s in AnalysisRegistry().specs if s.id == 'LEN-15')
    assert spec.parameters == ()
