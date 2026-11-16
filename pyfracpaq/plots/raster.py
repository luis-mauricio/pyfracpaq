"""Eight-sample opaque primitives for native-style scientific raster plots.

Line and surface samples are composited before resolving the image. Markers
use ordinary Matplotlib paths separately. All coordinates use live transforms;
no scientific reference image or MATLAB runtime is read here.
"""

from math import ceil, floor

import numpy as np
from matplotlib.collections import LineCollection

from pyfracpaq.plots.markers import SAMPLES


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


class MultisampleLines(LineCollection):
    """Live vector collections with multisampled Agg export and Qt repainting."""

    def draw(self,renderer):
        if type(renderer).__name__!='RendererAgg' or abs(renderer.dpi-600)>1e-8:
            return super().draw(renderer)
        self.draw_samples(renderer)

    def draw_samples(self,renderer):
        colours=list(self.get_colors())
        if not colours or any(c[3]!=1 for c in colours):
            return super().draw(renderer)
        extra=0
        if getattr(self,'_raster_extend_strokes',False):
            extra=float(self.get_linewidths().max())*renderer.dpi/144+2
        bounds=self.axes.bbox.extents+[-extra,-extra,extra,extra]
        scene=SampleScene(renderer,bounds,colours)
        transform=self.get_transform();widths=self.get_linewidths();inks=self.get_colors()
        for i,path in enumerate(self.get_segments()):
            points=transform.transform(path)
            for start,end in zip(points[:-1],points[1:]):
                scene.line(start,end,widths[i%len(widths)]*renderer.dpi/72,inks[i%len(inks)])
        gc=renderer.new_gc()
        try:scene.draw(gc)
        finally:gc.restore()
        self.stale=False
