"""Independent primitive scenes and contracts of the live sample renderer."""

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from pyfracpaq.plots.raster import SampleScene


def test_sample_lines_keep_coordinates_and_order_without_a_reference_image():
    figure=Figure(figsize=(.2,.2),dpi=600,facecolor='white')
    canvas=FigureCanvasAgg(figure);canvas.draw();renderer=canvas.get_renderer()
    scene=SampleScene(renderer,(0,0,120,120),[(0,0,1,1),(1,0,0,1)])
    start=np.array([10.,60.]);end=np.array([110.,60.])
    scene.line(start,end,6,(0,0,1,1))
    scene.line([60,10],[60,110],6,(1,0,0,1))
    np.testing.assert_array_equal(start,[10,60]);np.testing.assert_array_equal(end,[110,60])
    gc=renderer.new_gc()
    try:scene.draw(gc)
    finally:gc.restore()
    pixels=np.asarray(canvas.buffer_rgba())
    np.testing.assert_array_equal(pixels[60,30,:3],[0,0,255])
    np.testing.assert_array_equal(pixels[60,60,:3],[255,0,0])
    np.testing.assert_array_equal(pixels[10,10,:3],[255,255,255])
