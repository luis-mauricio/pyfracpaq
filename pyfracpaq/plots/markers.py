"""Native primitive materials for raster markers; scientific plots stay live.

The small atlas is generated independently from isolated graphics primitives,
never from scientific comparison figures. Unsupported API sizes use an
analytic fallback. No MATLAB runtime or scientific reference data is loaded.
"""

from contextlib import contextmanager
from functools import lru_cache
from math import ceil
from io import BytesIO

import numpy as np
from matplotlib.collections import PathCollection
from PIL import Image

from pyfracpaq.resources import resource_bytes

SAMPLES=np.array([[9,5],[7,11],[13,9],[5,3],[3,13],[1,7],[11,15],[15,1]],dtype=float)/16-.5


@lru_cache(maxsize=1)
def materials():
    with np.load(BytesIO(resource_bytes('matlab_markers.npz'))) as data:
        return {key:data[key] for key in data.files}


@lru_cache(maxsize=256)
def glyph(shape, extent, width, edge, face, dpi=600):
    """Tint a native primitive material, with analytic fallback for API sizes."""
    size=extent*72/dpi/(.8 if shape=='s' else 1)
    weight=width*72/dpi
    key=f'{shape}_{size:g}_{weight:g}_{int(face is not None)}'
    material=materials().get(key)
    if material is not None:
        pad=(material.shape[0]-1)//2
        if abs(dpi-600)>1e-9:
            pad=ceil(pad*dpi/600)
            # Resample the UI asset only when the canvas DPI changes. Scientific
            # figures/references are never resized by the comparison tools.
            channels=[np.asarray(Image.fromarray(material[:,:,i]).resize((pad*2+1,pad*2+1),Image.Resampling.LANCZOS)) for i in range(2)]
            material=np.stack(channels,axis=2)
        e=material[:,:,0].astype(float)/255;f=material[:,:,1].astype(float)/255
        edge=np.asarray(edge);face=np.asarray(face) if face is not None else np.zeros(4)
        alpha=np.clip(e*edge[3]+f*face[3],0,1)
        premul=e[...,None]*edge[:3]*edge[3]+f[...,None]*face[:3]*face[3]
        rgba=np.zeros((*alpha.shape,4),dtype=np.uint8)
        rgb=np.divide(premul,alpha[...,None],out=np.zeros_like(premul),where=alpha[...,None]>0)
        rgba[...,:3]=np.rint(np.clip(rgb,0,1)*255).astype(np.uint8)
        rgba[...,3]=np.rint(alpha*255).astype(np.uint8)
        return rgba,pad
    return analytic_glyph(shape,extent,width,edge,face)


def analytic_glyph(shape, extent, width, edge, face):
    """Fallback generated from geometry, independent of reference pixels."""
    radius=extent/2
    pad=ceil(radius+width+2)
    yy,xx=np.mgrid[-pad:pad+1,-pad:pad+1]
    x=xx[...,None]+SAMPLES[:,0];y=yy[...,None]+SAMPLES[:,1]
    if shape=='s':
        half=max(0,(extent-1)/2)
        stroke=max(.125,np.floor(width*8)/8)
        def box(r):return (x>=-r)&(x<r)&(y>=-r)&(y<r)
        outer=box(half+stroke/2);inner=box(max(0,half-stroke/2))
    else:
        sides=16 if extent<=50.00001 else 32
        angle=np.arctan2(y,x);step=2*np.pi/sides
        local=(angle+step) % step-step/2
        distance=np.hypot(x,y)*np.cos(local)/np.cos(step/2)
        stroke=width*.9
        outer=distance<=radius+stroke/2;inner=distance<max(0,radius-stroke/2)
    edge_coverage=(outer&~inner).mean(axis=2)
    face_coverage=inner.mean(axis=2) if face is not None else np.zeros_like(edge_coverage)
    edge=np.asarray(edge);face=np.asarray(face) if face is not None else np.zeros(4)
    alpha=edge_coverage*edge[3]+face_coverage*face[3]
    premul=edge_coverage[...,None]*edge[:3]*edge[3]+face_coverage[...,None]*face[:3]*face[3]
    rgba=np.zeros((*alpha.shape,4),dtype=np.uint8)
    rgb=np.divide(premul,alpha[...,None],out=np.zeros_like(premul),where=alpha[...,None]>0)
    rgba[...,:3]=np.rint(np.clip(rgb,0,1)*255).astype(np.uint8)
    rgba[...,3]=np.rint(np.clip(alpha,0,1)*255).astype(np.uint8)
    return rgba,pad


def paint(renderer,gc,point,shape,extent,width,edge,face):
    image,pad=glyph(shape,round(extent,6),round(width,6),tuple(edge),None if face is None else tuple(face),renderer.dpi)
    # Rasters use integer device-pixel centres; no scientific coordinate is
    # rounded or written back into an artist's data arrays.
    x=int(np.floor(point[0]+.5));y=int(np.ceil(point[1]-.5))
    renderer.draw_image(gc,int(x-pad),int(y-pad-1),image)


@contextmanager
def native_marker_renderer(renderer,dpi):
    """Override this raster renderer instance only, restoring it after drawing."""
    if type(renderer).__name__!='RendererAgg':
        yield
        return
    original=renderer.draw_markers
    def draw(gc,marker_path,marker_transform,path,transform,face=None):
        count=len(marker_path.vertices)
        shape='s' if count==5 else 'o' if count==26 else None
        if shape is None:return original(gc,marker_path,marker_transform,path,transform,face)
        extent=marker_path.get_extents(marker_transform).width
        # Non-marker geometric circles retain their vector drawing path.
        if extent<=0 or extent>dpi/72*24:
            return original(gc,marker_path,marker_transform,path,transform,face)
        points=transform.transform(path.vertices);clip=gc.get_clip_rectangle()
        fresh=renderer.new_gc();fresh.copy_properties(gc);fresh.set_clip_rectangle(None);fresh.set_clip_path(None)
        try:
            points=points[np.isfinite(points).all(axis=1)]
            if clip is not None:
                points=points[[clip.contains(*point) for point in points]]
            from pyfracpaq.plots.raster import draw_markers
            if draw_markers(renderer,fresh,points,shape,extent,gc.get_linewidth()*dpi/72,gc.get_rgb(),face):
                return
            for point in points:
                paint(renderer,fresh,point,shape,extent,gc.get_linewidth()*dpi/72,gc.get_rgb(),face)
        finally:fresh.restore()
    renderer.draw_markers=draw
    try:yield
    finally:renderer.draw_markers=original


class MatlabMarkers(PathCollection):
    """One ordered collection for mixed native node-marker glyphs."""

    _native_marker_atlas=True
    native_lines=None

    def draw(self,renderer):
        if self.native_lines is not None and type(renderer).__name__=='RendererAgg' and abs(renderer.dpi-600)<1e-8:
            return self.native_lines.draw_samples(renderer,self)
        if type(renderer).__name__!='RendererAgg':return super().draw(renderer)
        points=self.get_offset_transform().transform(self.get_offsets())
        sizes=np.sqrt(self.get_sizes())*self.figure.dpi/72
        paths=self.get_paths();edges=self.get_edgecolors();widths=self.get_linewidths()
        gc=renderer.new_gc()
        # Native multisampling resolves repeated opaque geometry once. Alpha
        # sprites otherwise darken shared endpoints on every duplicate draw.
        # Reuse a primitive only while no differently coloured glyph has
        # intervened in its bounding box, retaining the source painter order.
        previous={};buckets={};cell=max(1,16*self.figure.dpi/72)
        try:
            for i,point in enumerate(points):
                if not np.isfinite(point).all():continue
                shape='s' if len(paths[i%len(paths)].vertices)==5 else 'o'
                extent=sizes[i%len(sizes)]*(.8 if shape=='s' else 1)
                edge=edges[i%len(edges)]
                width=widths[i%len(widths)]*self.figure.dpi/72
                centre=(int(np.floor(point[0]+.5)),int(np.ceil(point[1]-.5)))
                key=(*centre,shape,float(extent),float(width),tuple(edge))
                if key in previous:
                    continue
                radius=extent/2+width+2
                box=(centre[0]-radius,centre[1]-radius,centre[0]+radius,centre[1]+radius)
                cells=[(x,y) for x in range(int(np.floor(box[0]/cell)),int(np.floor(box[2]/cell))+1)
                             for y in range(int(np.floor(box[1]/cell)),int(np.floor(box[3]/cell))+1)]
                nearby=set().union(*(buckets.get(c,()) for c in cells))
                for old in nearby:
                    bounds,colour,old_cells=previous[old]
                    if colour!=tuple(edge) and box[0]<=bounds[2] and box[2]>=bounds[0] and box[1]<=bounds[3] and box[3]>=bounds[1]:
                        del previous[old]
                        for c in old_cells:buckets[c].discard(old)
                previous[key]=(box,tuple(edge),cells)
                for c in cells:buckets.setdefault(c,set()).add(key)
                paint(renderer,gc,point,shape,extent,widths[i%len(widths)]*self.figure.dpi/72,
                      edge,None)
        finally:gc.restore()
        self.stale=False
