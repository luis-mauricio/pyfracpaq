"""Ordinary marker geometry in the GUI and high-resolution exports."""

import numpy as np
import pytest
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.markers import MarkerStyle
from matplotlib.transforms import Affine2D

from pyfracpaq.plots.style import MatlabFigure,figure_axes,legend,matlab_style,square_marker


@pytest.mark.parametrize('dpi',[100,200,600])
@pytest.mark.parametrize('shape',['s','o'])
@pytest.mark.parametrize('filled',[False,True])
def test_markers_match_standard_geometric_paths(dpi,shape,filled):
    """The theme must not replace paths with atlas pixels or polygons."""
    buffers=[]
    for cls in (MatlabFigure,Figure):
        with matlab_style():
            figure=cls(figsize=(1,1),dpi=dpi,facecolor='white')
            marker=(square_marker() if cls is MatlabFigure else
                    MarkerStyle('s',transform=Affine2D().scale(.8))) if shape=='s' else 'o'
            line=Line2D([.3,.7],[.4,.6],transform=figure.transFigure,linestyle='none',
                        marker=marker,markersize=12,markeredgewidth=.5,
                        markeredgecolor='blue',markerfacecolor='blue' if filled else 'none')
            figure.add_artist(line)
            canvas=FigureCanvasAgg(figure);canvas.draw()
            buffers.append(np.asarray(canvas.buffer_rgba()).copy())
            np.testing.assert_array_equal(line.get_xdata(),[.3,.7])
            np.testing.assert_array_equal(line.get_ydata(),[.4,.6])
    np.testing.assert_array_equal(*buffers)


def test_legend_preserves_marker_outline_size_and_colour():
    with matlab_style():
        figure,axes=figure_axes()
        line,=axes.plot([0],[0],marker='o',markersize=3,markeredgewidth=.5,
                        color='lime',markerfacecolor='lime',label='Y',linestyle='none')
        proxy=legend(axes).get_lines()[0]
        assert proxy.get_markersize()==line.get_markersize()
        assert proxy.get_markeredgewidth()==line.get_markeredgewidth()
        assert proxy.get_markerfacecolor()==line.get_markerfacecolor()
        figure.clear()
