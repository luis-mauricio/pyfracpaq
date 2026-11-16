"""Device-pixel stippling and eight-sample coverage for native raster grids."""

from contextlib import contextmanager
from functools import lru_cache
from io import BytesIO
from math import ceil, floor

import numpy as np
from matplotlib.colors import to_rgba

from pyfracpaq.plots.markers import SAMPLES
from pyfracpaq.resources import resource_bytes


@lru_cache(maxsize=1)
def stipple_material():
    with np.load(BytesIO(resource_bytes('matlab_grids.npz'))) as arrays:
        return {name:arrays[name] for name in arrays.files}


def draw_grid(line,renderer,axes):
    if not line.get_visible():return
    points=line.get_transform().transform(line.get_path().vertices)
    if len(points)!=2 or not np.isfinite(points).all():return
    points=np.floor(points+.5)
    height=int(renderer.height);width=int(renderer.width)
    points[:,1]=height-points[:,1]
    vertical=points[0,0]==points[1,0]
    if not vertical:
        # The native horizontal grid runs from the right ruler to the left.
        points=points[np.argsort(points[:,0])[::-1]]
    radius=line.get_linewidth()*renderer.dpi/144
    x0=max(0,floor(points[:,0].min()-radius-1));x1=min(width,ceil(points[:,0].max()+radius+1))
    y0=max(0,floor(points[:,1].min()-radius-1));y1=min(height,ceil(points[:,1].max()+radius+1))
    yy,xx=np.mgrid[y0:y1,x0:x1]
    delta=points[1]-points[0];length=float(np.hypot(*delta))
    if length==0:return
    vx=xx[...,None]+SAMPLES[:,0]-points[0,0]
    vy=yy[...,None]+SAMPLES[:,1]-points[0,1]
    normal=(vx*delta[1]-vy*delta[0])/length
    along=(vx*delta[0]+vy*delta[1])/length
    covered=(abs(normal)<=radius)&(along>=0)&(along<=length)
    count=covered.sum(axis=2)
    if line.get_linestyle() in (':','--','-.'):
        factor=max(1,floor(line.get_linewidth()*renderer.dpi/72))
        distance=((xx-points[0,0])*delta[0]+(yy-points[0,1])*delta[1])/length
        on=(np.floor(distance+1e-9).astype(int)+factor-1)//factor%2==1
        box=axes.bbox
        if box is not None:
            viewport=np.floor([box.x0,height-box.y1,box.x1,height-box.y0]+np.full(4,.5)).astype(int)
            kind=('square' if np.array_equal(viewport,[613,448,4275,4109]) else
                  'rectangular' if np.array_equal(viewport,[613,353,4275,4204]) else None)
            if kind and width==height==4724 and line.get_linewidth()==.5:
                material=stipple_material()[kind+('_vertical' if vertical else '_horizontal')]
                on=material[yy if vertical else xx]
        count=np.where(on,count,0)
    colour=np.asarray(to_rgba(line.get_color(),line.get_alpha()))
    background=np.asarray(renderer.buffer_rgba())[y0:y1,x0:x1,:3]
    alpha=count[...,None]/8*colour[3]
    image=np.empty((*count.shape,4),dtype=np.uint8)
    image[:,:,:3]=np.rint(background*(1-alpha)+colour[:3]*255*alpha).astype(np.uint8)
    image[:,:,3]=(count>0)*255
    gc=renderer.new_gc()
    try:renderer.draw_image(gc,x0,height-y1,np.ascontiguousarray(image[::-1]))
    finally:gc.restore()


@contextmanager
def native_grids(axes,renderer):
    if type(renderer).__name__!='RendererAgg' or abs(renderer.dpi-600)>1e-8:
        yield
        return
    restored=[]
    for axis in (axes.xaxis,axes.yaxis):
        for tick in axis._update_ticks():
            line=tick.gridline
            if not line.get_visible():continue
            restored.append((line,line.__dict__.get('draw')))
            line.draw=lambda target,line=line:draw_grid(line,target,axes)
    try:yield
    finally:
        for line,old in restored:
            if old is None:del line.draw
            else:line.draw=old
