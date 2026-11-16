"""Depth, fallback and state contracts of the native-style raster renderer."""

from dataclasses import replace

import numpy as np
import pytest
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties

from pyfracpaq.plots.raster import SampleScene
from pyfracpaq.plots.tex import native_mathtext,runs


def test_nearest_stroke_wins_independently_of_painter_order():
    figure=Figure(figsize=(.2,.2),dpi=600)
    canvas=FigureCanvasAgg(figure);canvas.draw();renderer=canvas.get_renderer()
    blue=(0,0,1,1);red=(1,0,0,1)
    scene=SampleScene(renderer,(0,0,120,120),[blue,red],depth=True)
    scene.line([10,60],[110,60],8,red,depth=(2,2))
    scene.line([60,10],[60,110],8,blue,depth=(1,1))
    gc=renderer.new_gc()
    try:scene.draw(gc)
    finally:gc.restore()
    pixels=np.asarray(canvas.buffer_rgba())
    np.testing.assert_array_equal(pixels[60,60,:3],[255,0,0])
    np.testing.assert_array_equal(pixels[30,60,:3],[0,0,255])


def test_opaque_face_occludes_deeper_strokes_and_preserves_vertices():
    figure=Figure(figsize=(.2,.2),dpi=600)
    canvas=FigureCanvasAgg(figure);canvas.draw();renderer=canvas.get_renderer()
    blue=(0,0,1,1);white=(1,1,1,1)
    scene=SampleScene(renderer,(0,0,120,120),[blue,white],depth=True)
    vertices=np.array([[10.,10.],[110.,10.],[60.,110.]])
    original=vertices.copy()
    scene.line([10,60],[110,60],8,blue,depth=(1,1))
    scene.triangle(vertices,white,depth=(2,2,2))
    scene.line([60,10],[60,110],4,blue,depth=(3,3))
    gc=renderer.new_gc()
    try:scene.draw(gc)
    finally:gc.restore()
    pixels=np.asarray(canvas.buffer_rgba())
    np.testing.assert_array_equal(pixels[60,50,:3],[255,255,255])
    np.testing.assert_array_equal(pixels[60,60,:3],[0,0,255])
    np.testing.assert_array_equal(vertices,original)


def test_tex_operators_and_scripts_keep_native_font_sizes():
    result=runs(r'$\log_{10}$(frequency)',FontProperties(family='Arial',size=10))
    assert result is not None
    assert ''.join(piece[0] for piece in result)=='log10(frequency)'
    assert next(font.get_size_in_points() for literal,font,_ in result if literal=='10')==8
    assert runs(r'$\unsupported{x}$',FontProperties(size=10)) is None


def test_renderer_methods_are_restored_after_failure():
    figure=Figure(figsize=(1,1));canvas=FigureCanvasAgg(figure);canvas.draw()
    renderer=canvas.get_renderer()
    before=(renderer.draw_text,renderer.draw_mathtext,renderer.get_text_width_height_descent)
    with pytest.raises(RuntimeError):
        with native_mathtext(renderer):raise RuntimeError('drawing interrupted')
    assert (renderer.draw_text,renderer.draw_mathtext,renderer.get_text_width_height_descent)==before


def test_hough_canonical_draw_keeps_live_surfaces_and_rotation():
    from pyfracpaq.io.images import read_image
    from pyfracpaq.plots.hough import render_hough
    from reference_common import ROOT
    source=read_image(ROOT/'tests/fixtures/images/tensor_network.tif').hough
    result=replace(source,accumulator=np.array([[0,1],[1,0]]),
                   theta=np.array([-1.,1.]),rho=np.array([-1.,1.]),threshold=1)
    figure=render_hough(result).figure;figure.set_size_inches(1,1);figure.set_dpi(600)
    plan=figure.axes[2];original=plan.viewLim.frozen();collections=list(plan.collections)
    canvas=FigureCanvasAgg(figure);canvas.draw()
    np.testing.assert_array_equal(plan.viewLim.extents,original.extents)
    assert plan._axis3don and plan.title.get_visible() and plan.patch.get_visible()
    plan.view_init(elev=25,azim=30);canvas.draw()
    assert list(plan.collections)==collections and plan.elev==25 and plan.azim==30
    np.testing.assert_array_equal(result.accumulator,[[0,1],[1,0]])
