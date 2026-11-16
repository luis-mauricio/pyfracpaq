"""MLE and connectivity artists, including responsive shared colourbars."""

from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest
from matplotlib.backends.backend_agg import FigureCanvasAgg

from pyfracpaq.analysis.connectivity import classify_connectivity,connectivity_maps
from pyfracpaq.analysis.mle import fit_populations,survival
from pyfracpaq.domain import TraceInput,build_dataset
from pyfracpaq.geometry import Bounds
from pyfracpaq.plots.connectivity import render_connectivity,ternary_coordinates,CL2,CL357
from pyfracpaq.plots.mle import render_mle
from sprint3_reference import reference_config


def test_six_mle_figures_keep_source_names_scales_curves_and_cut_markers():
    result=fit_populations([1,2,3,4,6,10,18,40],[.5,1,1.5,2,3,5,9,20],seed=19,unit='metres')
    outputs=render_mle(SimpleNamespace(mle=result),reference_config())
    assert len(outputs)==6
    expected=('PowerLaw','Exponential','LogNormal')
    for index,output in enumerate(outputs):
        canvas=FigureCanvasAgg(output.figure);canvas.draw()
        population='trace' if index<3 else 'segment'
        assert output.basename==f'FracPaQ2D_{population}lengthsFitting{expected[index%3]}'
        record=(result.trace if index<3 else result.segment)[index%3]
        axes=output.figure.axes[0]
        assert (axes.get_xscale(),axes.get_yscale())==(
            ('linear','log') if index%3==1 else ('log','linear') if index%3==2 else ('log','log'))
        observed=np.unique(record.fit.sample.original)
        np.testing.assert_array_equal(axes.lines[0].get_xdata(),observed)
        np.testing.assert_array_equal(axes.lines[2].get_xdata(),[record.fit.sample.retained[-1]]*2)
        np.testing.assert_array_equal(axes.lines[3].get_xdata(),[record.fit.sample.retained[0]]*2)
        assert axes.get_xlabel()=='Length, metres'
        assert [t.get_text() for t in axes.get_legend().get_texts()]==[
            'Observed Data','Estimated Data','Upper cut-off','Lower cut-off']
        assert output.figure.texts and output.figure.texts[0].get_bbox_patch() is not None


@pytest.mark.parametrize('flip', [False,True])
def test_four_connectivity_outputs_share_counts_norm_and_responsive_bars(flip):
    data=build_dataset([TraceInput(((-2,0),(2,0))),TraceInput(((0,.1),(0,2)))],
                        source_bounds=Bounds(-3,-3,3,3))
    result=connectivity_maps(classify_connectivity(data,.2),3)
    cfg=replace(reference_config(),flip_x=flip,flip_y=flip)
    outputs=render_connectivity(result,cfg)
    assert [o.basename for o in outputs]==[
        'FracPaQ2D_IYXnodes_traces','FracPaQ2D_XYnodes_traces_heat',
        'FracPaQ2D_Inodes_traces_heat','FracPaQ2D_IYXtriangle']
    nodes=outputs[0].figure.axes[0]
    assert [line.get_label() for line in nodes.lines]==['I','Y']
    assert nodes.lines[0].get_color()=='blue' and nodes.lines[1].get_color()=='lime'
    assert 'n_I=3' in nodes.get_title() and 'n_Y=1' in nodes.get_title()
    for output in outputs[:3]:
        axes=output.figure.axes[0]
        assert axes.xaxis_inverted()==flip and axes.yaxis_inverted()==flip
    norms=[]
    for output,field in zip(outputs[1:3],(result.xy_heatmap,result.i_heatmap)):
        canvas=FigureCanvasAgg(output.figure)
        for size in ((6,6),(10,4),(3.4,2.8)):
            output.figure.set_size_inches(*size);canvas.draw()
            axes,scale=output.figure.axes
            np.testing.assert_array_equal(axes.images[0].get_array(),field.values)
            a,b=axes.get_window_extent(),scale.get_window_extent()
            np.testing.assert_allclose((a.x0,a.x1),(b.x0,b.x1),rtol=0,atol=1e-8)
            clearance=axes.xaxis.label.get_window_extent().y0-b.y1
            assert clearance/canvas.get_renderer().points_to_pixels(1)==pytest.approx(25,abs=1e-8)
        norms.append(output.figure.axes[1]._colorbar.norm)
    assert norms[0] is norms[1] and norms[0].vmax==result.maximum
    triangle=outputs[3].figure.axes[0];FigureCanvasAgg(outputs[3].figure).draw()
    assert not triangle.axison
    assert len(triangle.lines)==31 # Outline + 27 grid segments + 2 CL + point.


def test_ternary_vertices_cl_lines_and_total_zero_are_well_defined():
    got=ternary_coordinates([[100,0,0],[0,100,0],[0,0,100]])
    np.testing.assert_allclose(got,[[0,-1],[2/np.sqrt(3),-1],[1/np.sqrt(3),0]],atol=1e-12)
    assert CL2.shape==CL357.shape==(2,3)
    data=build_dataset([TraceInput(((-3,-3),(3,3)))])
    result=connectivity_maps(classify_connectivity(data,0),3)
    assert result.topology.counts==(0,0,0)
    outputs=render_connectivity(result,reference_config())
    for output in outputs:FigureCanvasAgg(output.figure).draw()
    assert any('No I/Y/X' in text.get_text() for text in outputs[-1].figure.axes[0].texts)
    assert 'total=0' in outputs[-1].figure.axes[0].get_title()
    assert len(outputs[-1].figure.axes[0].lines)==30
