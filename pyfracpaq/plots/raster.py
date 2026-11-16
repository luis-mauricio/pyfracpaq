"""Eight-sample opaque primitives for native-style scientific raster plots.

Samples are composited before resolving the image. This matters for repeated
endpoints and overlapping markers: repeatedly blending already resolved alpha
sprites darkens edges. All coordinates come from live Matplotlib transforms;
no scientific reference image or MATLAB runtime is read here.
"""

from functools import lru_cache
from math import ceil, floor

import numpy as np
from matplotlib.collections import LineCollection

from pyfracpaq.plots.markers import SAMPLES, materials


@lru_cache(maxsize=64)
def primitive_samples(key):
    """Preserve measured coverage, ordering subsamples by primitive geometry."""
    material=materials()[key]
    pad=(material.shape[0]-1)//2
    yy,xx=np.mgrid[-pad:pad+1,-pad:pad+1]
    x=xx[...,None]+SAMPLES[:,0];y=yy[...,None]+SAMPLES[:,1]
    shape,size,_,_=key.split('_')
    extent=float(size)*600/72*(.8 if shape=='s' else 1)
    radius=(extent-1)/2 if shape=='s' else extent/2
    distance=np.maximum(abs(x),abs(y)) if shape=='s' else np.hypot(x,y)
    edge_count=np.rint(material[:,:,0].astype(float)*8/255).astype(int)
    face_count=np.rint(material[:,:,1].astype(float)*8/255).astype(int)
    # Assign face samples first, followed by the measured number of edge
    # samples nearest the hollow primitive's stroke. Exact coverage is retained
    # for every pixel; sample ownership at intersections is geometric.
    rank=np.argsort(np.argsort(distance,axis=2),axis=2)
    face=rank<face_count[...,None]
    score=np.where(face,np.inf,abs(distance-radius))
    rank=np.argsort(np.argsort(score,axis=2),axis=2)
    edge=rank<edge_count[...,None]
    return edge,face,pad


class SampleScene:
    """A bounded palette-indexed sample buffer; blank pixels stay transparent."""

    def __init__(self,renderer,bounds,colours,*,depth=False):
        self.renderer=renderer
        height=int(renderer.height);width=int(renderer.width)
        left,bottom,right,top=bounds
        self.left=max(0,floor(left));self.top=max(0,floor(height-top))
        self.right=min(width,ceil(right));self.bottom=min(height,ceil(height-bottom))
        self.width=max(0,self.right-self.left);self.height=max(0,self.bottom-self.top)
        self.colours=[(255,255,255)]
        self.lookup={}
        for colour in colours:
            key=tuple(np.rint(np.asarray(colour[:3])*255).astype(int))
            if key not in self.lookup:
                self.lookup[key]=len(self.colours);self.colours.append(key)
        dtype=np.uint8 if len(self.colours)<=256 else np.uint16
        self.samples=np.zeros((self.height*self.width,8),dtype=dtype)
        self.depths=(np.full(self.samples.shape,-np.inf,dtype=np.float32) if depth else None)
        self.canvas_height=height

    def colour_id(self,colour):
        return self.lookup[tuple(np.rint(np.asarray(colour[:3])*255).astype(int))]

    def line(self,start,end,width,colour,*,depth=None):
        start=np.asarray(start,dtype=float).copy();end=np.asarray(end,dtype=float).copy()
        if not np.isfinite([start,end]).all():return
        start[1]=self.canvas_height-start[1];end[1]=self.canvas_height-end[1]
        vector=end-start;length=float(np.hypot(*vector))
        if length==0 or width<=0:return
        radius=width/2;steep=abs(vector[1])>abs(vector[0])
        order=[1,0] if steep else [0,1];p=start[order];q=end[order];delta=q-p
        lo=self.top if steep else self.left;hi=self.bottom if steep else self.right
        first=max(lo,floor(min(p[0],q[0])-radius-2))
        last=min(hi,ceil(max(p[0],q[0])+radius+2))
        along=np.arange(first,last)
        centre=p[1]+(along-p[0])*delta[1]/delta[0]
        offsets=np.arange(-ceil(radius)-3,ceil(radius)+4)
        a=np.broadcast_to(along[:,None],(len(along),len(offsets))).ravel()
        b=(np.floor(centre[:,None]).astype(int)+offsets).ravel()
        x,y=(b,a) if steep else (a,b)
        keep=(x>=self.left)&(x<self.right)&(y>=self.top)&(y<self.bottom)
        x=x[keep];y=y[keep]
        vx=x[:,None]+SAMPLES[:,0]-start[0];vy=y[:,None]+SAMPLES[:,1]-start[1]
        normal=(vx*vector[1]-vy*vector[0])/length
        distance=(vx*vector[0]+vy*vector[1])/length
        covered=(abs(normal)<=radius)&(distance>=0)&(distance<=length)
        pixels=(y-self.top)*self.width+x-self.left
        rows,samples=np.where(covered)
        if self.depths is not None and depth is not None:
            values=depth[0]+(depth[1]-depth[0])*distance[rows,samples]/length
            visible=values>=self.depths[pixels[rows],samples]-1e-6
            rows=rows[visible];samples=samples[visible];values=values[visible]
            self.depths[pixels[rows],samples]=values
        self.samples[pixels[rows],samples]=self.colour_id(colour)

    def marker(self,point,key,edge_colour,face_colour=None):
        edge,face,pad=primitive_samples(key)
        cx=int(np.floor(point[0]+.5));cy=self.canvas_height-int(np.ceil(point[1]-.5))
        x0=max(self.left,cx-pad);x1=min(self.right,cx+pad+1)
        y0=max(self.top,cy-pad);y1=min(self.bottom,cy+pad+1)
        if x0>=x1 or y0>=y1:return
        tile=self.samples.reshape(self.height,self.width,8)[y0-self.top:y1-self.top,x0-self.left:x1-self.left]
        selection=(slice(y0-cy+pad,y1-cy+pad),slice(x0-cx+pad,x1-cx+pad))
        if face_colour is not None:tile[face[selection]]=self.colour_id(face_colour)
        tile[edge[selection]]=self.colour_id(edge_colour)

    def triangle(self,vertices,colour,*,depth=None,bias_pixels=0,bias_depth=1e-5):
        """Rasterize a projected opaque face before its wire edges."""
        points=np.asarray(vertices,dtype=float).copy()
        points[:,1]=self.canvas_height-points[:,1]
        if not np.isfinite(points).all():return
        a,b,c=points
        determinant=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
        if abs(determinant)<1e-12:return
        left=max(self.left,floor(points[:,0].min()-1))
        right=min(self.right,ceil(points[:,0].max()+1))
        top=max(self.top,floor(points[:,1].min()-1))
        bottom=min(self.bottom,ceil(points[:,1].max()+1))
        if left>=right or top>=bottom:return
        yy,xx=np.mgrid[top:bottom,left:right]
        x=xx[...,None]+SAMPLES[:,0];y=yy[...,None]+SAMPLES[:,1]
        u=((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0]))/determinant
        v=((x-a[0])*(c[1]-a[1])-(y-a[1])*(c[0]-a[0]))/determinant
        covered=(u>=0)&(v>=0)&(u+v<=1)
        tile=self.samples.reshape(self.height,self.width,8)[top-self.top:bottom-self.top,left-self.left:right-self.left]
        if self.depths is not None and depth is not None:
            values=depth[0]+v*(depth[1]-depth[0])+u*(depth[2]-depth[0])
            gradient_x=((depth[1]-depth[0])*(c[1]-a[1])-(depth[2]-depth[0])*(b[1]-a[1]))/determinant
            gradient_y=((b[0]-a[0])*(depth[2]-depth[0])-(c[0]-a[0])*(depth[1]-depth[0]))/determinant
            values-=bias_pixels*max(abs(gradient_x),abs(gradient_y))+bias_depth
            depths=self.depths.reshape(self.height,self.width,8)[top-self.top:bottom-self.top,left-self.left:right-self.left]
            covered&=values>=depths
            depths[covered]=values[covered]
        tile[covered]=self.colour_id(colour)

    def draw(self,gc):
        if self.samples.size==0:return
        palette=np.asarray(self.colours,dtype=np.uint16)
        result=np.zeros((self.height*self.width,4),dtype=np.uint8)
        # Bound temporary RGB expansion independently of image dimensions.
        for start in range(0,len(result),65536):
            block=self.samples[start:start+65536]
            result[start:start+len(block),:3]=np.rint(palette[block].sum(axis=1)/8).astype(np.uint8)
            result[start:start+len(block),3]=np.any(block!=0,axis=1)*255
        image=result.reshape(self.height,self.width,4)
        # Agg's image primitive consumes rows from the lower edge upward.
        self.renderer.draw_image(gc,self.left,self.canvas_height-self.bottom,
                                 np.ascontiguousarray(image[::-1]))


def draw_markers(renderer,gc,points,shape,extent,width,edge,face):
    """Resolve a whole marker series once, including overlapping observations."""
    if abs(renderer.dpi-600)>1e-8:return False
    size=extent*72/renderer.dpi/(.8 if shape=='s' else 1)
    weight=width*72/renderer.dpi
    key=f'{shape}_{size:g}_{weight:g}_{int(face is not None)}'
    if key not in materials() or edge[3]!=1 or (face is not None and face[3]!=1):
        return False
    if not len(points):return True
    pad=primitive_samples(key)[2]+2
    left,bottom=points.min(axis=0)-pad;right,top=points.max(axis=0)+pad
    colours=[edge] if face is None else [edge,face]
    scene=SampleScene(renderer,(left,bottom,right,top),colours)
    for point in points:scene.marker(point,key,edge,face)
    scene.draw(gc)
    return True


class MultisampleLines(LineCollection):
    """Live vector collections with multisampled Agg export and Qt repainting."""

    native_markers=None

    def draw(self,renderer):
        if self.native_markers is not None and type(renderer).__name__=='RendererAgg' and abs(renderer.dpi-600)<1e-8:
            return
        if type(renderer).__name__!='RendererAgg' or abs(renderer.dpi-600)>1e-8:
            return super().draw(renderer)
        self.draw_samples(renderer)

    def draw_samples(self,renderer,markers=None):
        colours=list(self.get_colors())
        if markers is not None:colours.extend(markers.get_edgecolors())
        if not colours or any(c[3]!=1 for c in colours):
            return super().draw(renderer)
        extra=0
        if getattr(self,'_raster_extend_strokes',False):
            extra=float(self.get_linewidths().max())*renderer.dpi/144+2
        if markers is not None:
            extra=float(np.sqrt(markers.get_sizes()).max())*renderer.dpi/72+4
        bounds=self.axes.bbox.extents+[-extra,-extra,extra,extra]
        scene=SampleScene(renderer,bounds,colours)
        transform=self.get_transform();widths=self.get_linewidths();inks=self.get_colors()
        for i,path in enumerate(self.get_segments()):
            points=transform.transform(path)
            for start,end in zip(points[:-1],points[1:]):
                scene.line(start,end,widths[i%len(widths)]*renderer.dpi/72,inks[i%len(inks)])
        if markers is not None:
            points=markers.get_offset_transform().transform(markers.get_offsets())
            paths=markers.get_paths();sizes=np.sqrt(markers.get_sizes());edges=markers.get_edgecolors()
            weights=markers.get_linewidths()
            for i,point in enumerate(points):
                if not np.isfinite(point).all():continue
                shape='s' if len(paths[i%len(paths)].vertices)==5 else 'o'
                key=f'{shape}_{sizes[i%len(sizes)]:g}_{weights[i%len(weights)]:g}_0'
                scene.marker(point,key,edges[i%len(edges)])
        gc=renderer.new_gc()
        try:scene.draw(gc)
        finally:gc.restore()
        self.stale=False
