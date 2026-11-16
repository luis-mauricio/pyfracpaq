"""Four-panel Hough diagnostic from full arrays, without widget screenshots."""

from io import BytesIO

import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.transforms import Bbox
from mpl_toolkits.mplot3d import Axes3D

from pyfracpaq.analysis.hough import HoughResult
from pyfracpaq.plots.results import FigureOutput
from pyfracpaq.plots.style import MatlabAxes, MatlabFigure, matlab_style, title
from pyfracpaq.plots.ticks import MatlabLocator
from pyfracpaq.plots.raster import SampleScene
from pyfracpaq.resources import resource_bytes


class HoughAxes(Axes3D):
    """Keep a tight square ruler for the three source orthographic views.

    The mesh remains a live 3-D artist. At the original axis-aligned camera
    angles, use the same ordinary rectangular rulers as MATLAB. Rotating the
    camera restores Matplotlib's interactive 3-D rulers.
    """

    native_role = None

    def apply_aspect(self,position=None):
        native=getattr(self,'_native_frame_position',None)
        if native is not None:
            self._set_position(native,which='active')
        else:super().apply_aspect(position)

    def draw(self,renderer):
        views={'rho':(0,0),'plan':(90,-90),'theta':(0,-90)}
        if self.native_role not in views or (self.elev,self.azim)!=views[self.native_role]:
            return super().draw(renderer)
        frame=MatlabAxes(self.figure,self.get_position(original=True))
        frame._native_viewport_x=.2
        frame._native_viewport_y=-.26545
        frame._native_viewport_scale=.999947
        frame.set_box_aspect(1)
        frame.xaxis.set_major_locator(MatlabLocator(6))
        frame.yaxis.set_major_locator(MatlabLocator(8 if self.native_role=='plan' else 6))
        frame.tick_params(direction='in',top=True,right=True)
        if self.native_role=='rho':
            frame.set(xlim=self.get_ylim(),ylim=self.get_zlim(),
                      xlabel=self.get_ylabel(),ylabel=self.get_zlabel())
        elif self.native_role=='plan':
            frame.set(xlim=self.get_xlim(),ylim=self.get_ylim(),
                      xlabel=self.get_xlabel(),ylabel=self.get_ylabel())
        else:
            frame.set(xlim=self.get_xlim(),ylim=self.get_zlim(),
                      xlabel=self.get_xlabel(),ylabel=self.get_zlabel())
        frame.patch.set_visible(False)
        title(frame,self.get_title().rstrip('\n'))
        frame.apply_aspect()
        old_view=self.viewLim.frozen();old_title=self.title.get_visible();old_axis=self._axis3don
        old_patch=self.patch.get_visible()
        old_position=self.get_position().frozen()
        # Orthographic projection of a unit box spans box_aspect / distance.
        # Centre its viewport and remove the Axes3D label-reservation padding.
        span=float(self._box_aspect.max()/self._dist)
        self.viewLim.set(Bbox.from_extents(-span/2,-span/2,span/2,span/2))
        self._set_position(frame.get_position(),which='active')
        self._native_frame_position=frame.get_position().frozen()
        self._axis3don=False;self.title.set_visible(False)
        self.patch.set_visible(False)
        widths=[]
        if type(renderer).__name__=='RendererAgg':
            unit=renderer.dpi/72
            for collection in self.collections:
                old=collection.get_linewidths().copy();widths.append((collection,old))
                collection.set_linewidths(np.maximum(1,np.floor(old*unit))/unit)
        try:
            frame.draw(renderer)
            if type(renderer).__name__=='RendererAgg' and abs(renderer.dpi-600)<1e-8:
                _draw_orthographic_mesh(frame,renderer,self._hough_result,self._hough_palette,self.native_role)
            else:
                super().draw(renderer)
        finally:
            self._native_frame_position=None
            for collection,old in widths:collection.set_linewidths(old)
            self.viewLim.set(old_view);self._axis3don=old_axis
            self.title.set_visible(old_title);self._set_position(old_position,which='active')
            self.patch.set_visible(old_patch)


def _draw_orthographic_mesh(frame,renderer,result,cmap,role):
    """Resolve the source cameras with a depth test at each raster subsample.

    Native independent-mesh properties specify triangle strips, a face offset
    factor of 1.5 and bias of .0001. Whole-quad painter sorting loses hidden
    edges at intersecting peaks. Rotated/vector views retain live surfaces.
    """
    z=result.accumulator
    maximum=max(1,int(z.max()))
    colours=cmap(z/maximum)
    colours[:,:,:3]=np.floor(colours[:,:,:3]*255)/255
    white=(1.,1.,1.,1.);black=(0.,0.,0.,1.)
    scene=SampleScene(renderer,frame.bbox.extents+[-3,-3,3,3],
                      [*colours.reshape(-1,4),white,black],depth=True)
    width=np.floor(.5*renderer.dpi/72*8)/8
    if role=='plan':
        x,y=np.meshgrid(result.theta,result.rho)
        projected=frame.transData.transform(np.stack((x,y),axis=2).reshape(-1,2)).reshape(*z.shape,2)
        depths=z.astype(float)
    else:
        horizontal=np.broadcast_to(result.rho[:,None],z.shape) if role=='rho' else np.broadcast_to(result.theta,z.shape)
        projected=frame.transData.transform(np.stack((horizontal,z),axis=2).reshape(-1,2)).reshape(*z.shape,2)
        depths=(np.broadcast_to(result.theta,z.shape) if role=='rho' else
                np.broadcast_to(-result.rho[:,None],z.shape)).astype(float)
    bias=.0001*max(1,float(np.ptp(depths)))
    for j in range(z.shape[1]-1):
        for i in range(z.shape[0]-1):
            # Column-wise triangle strips use the opposite diagonal from a
            # generic quad fan. The distinction matters on nonplanar cells.
            for indices in (((i,j),(i,j+1),(i+1,j)),((i,j+1),(i+1,j),(i+1,j+1))):
                scene.triangle([projected[k] for k in indices],white,
                               depth=[depths[k] for k in indices],
                               bias_pixels=1.5,bias_depth=bias)
    for j in range(z.shape[1]-1):
        for i in range(z.shape[0]):
            scene.line(projected[i,j],projected[i,j+1],width,colours[i,j],
                       depth=(depths[i,j],depths[i,j+1]))
    for j in range(z.shape[1]):
        for i in range(z.shape[0]-1):
            scene.line(projected[i,j],projected[i+1,j],width,colours[i,j],
                       depth=(depths[i,j],depths[i+1,j]))
    if role!='plan':
        low,high=frame.get_xlim()
        ends=frame.transData.transform([(low,result.threshold),(high,result.threshold)])
        scene.line(*ends,width,black,depth=(float(depths.max()),)*2)
    gc=renderer.new_gc()
    try:scene.draw(gc)
    finally:gc.restore()


def _palettes() -> dict:
    with np.load(BytesIO(resource_bytes('matlab_rgb.npz'))) as data:
        return {name: ListedColormap(data[name], name='matlab_' + name) for name in data.files}


def _mesh(axes, result: HoughResult, maximum: int, cmap, *, plane: bool) -> None:
    x, y = np.meshgrid(result.theta, result.rho)
    z = result.accumulator
    axes._hough_result=result;axes._hough_palette=cmap
    surface = axes.plot_surface(x, y, z, rstride=1, cstride=1, linewidth=.5,
                                 antialiased=False, shade=False, color='white')
    surface.set_edgecolor(cmap(z[:-1, :-1].ravel() / maximum))
    if plane:
        px, py = np.meshgrid(result.theta[[0, -1]], result.rho[[0, -1]])
        axes.plot_surface(px, py, np.full((2, 2), result.threshold),
                          color=cmap(result.threshold / maximum), shade=False,
                          linewidth=.5, edgecolor='black', antialiased=False)
    low, high = float(result.rho[0]), float(result.rho[-1])
    if low == high:
        low, high = low - .5, high + .5
    axes.set(xlim=(result.theta[0], result.theta[-1]), ylim=(low, high), zlim=(0, maximum),
             xlabel=r'$\theta$, degrees', ylabel=r'$\rho$, pixels', zlabel='H')
    axes.set_proj_type('ortho')
    axes.set_box_aspect((1, 1, 1))
    axes.grid(False)
    for axis in (axes.xaxis,axes.yaxis,axes.zaxis):
        axis.pane.set_facecolor((1,1,1,0))
        axis.pane.set_edgecolor((1,1,1,0))


def render_hough(result: HoughResult) -> FigureOutput:
    if result.accumulator.size > 1_100_000:
        raise MemoryError('The full-resolution Hough diagnostic exceeds its mesh '
                          'budget (1,100,000 cells per panel). Use a smaller image.')
    palettes = _palettes()
    with matlab_style():
        figure = MatlabFigure()
        # Original subplot slots, measured in the native four-panel capture.
        raw = figure.add_axes((.13, .5838372093, .3346590909, .3212846058), axes_class=MatlabAxes)
        side_rho = figure.add_axes((.5703409091, .5838372093, .3346590909, .3212846058), axes_class=HoughAxes)
        plan = figure.add_axes((.13, .11, .3346590909, .3212846058), axes_class=HoughAxes)
        side_theta = figure.add_axes((.5703409091, .11, .3346590909, .3212846058), axes_class=HoughAxes)
        side_rho.native_role='rho';plan.native_role='plan';side_theta.native_role='theta'
        raw.xaxis.set_major_locator(MatlabLocator(6))
        raw.yaxis.set_major_locator(MatlabLocator(6))
        height, width = result.image.shape
        raw.imshow(result.image, origin='lower', cmap=palettes['bone'], vmin=0, vmax=255,
                   extent=(.5, width + .5, .5, height + .5), interpolation='nearest')
        raw.set(xlim=(0, width), ylim=(0, height), xlabel='X, pixels', ylabel='Y, pixels')
        raw.set_aspect('equal')
        title(raw, 'Raw binary image')
        maximum = max(1, int(result.accumulator.max()))
        _mesh(side_rho, result, maximum, palettes['hot'], plane=True)
        side_rho.view_init(elev=0, azim=0)
        side_rho.set_xticks([])
        side_rho.set_xlabel('')
        title(side_rho, 'Hough peaks, side view')
        _mesh(plan, result, maximum, palettes['hot'], plane=False)
        plan.view_init(elev=90, azim=-90)
        plan.invert_yaxis()
        plan.set_zticks([])
        plan.set_zlabel('')
        title(plan, 'Hough peaks, plan view')
        _mesh(side_theta, result, maximum, palettes['hot'], plane=True)
        side_theta.view_init(elev=0, azim=-90)
        side_theta.set_yticks([])
        side_theta.set_ylabel('')
        title(side_theta, 'Hough peaks, side view')
        for axes in figure.axes:
            axes.tick_params(direction='in', labelsize=10, top=True, right=True)
            axes.xaxis.label.set_size(11)
            axes.yaxis.label.set_size(11)
            if hasattr(axes,'zaxis'):
                axes.zaxis.label.set_size(11)
            axes.title.set_fontsize(11)
        raw.tick_params(direction='out',top=False,right=False)
    return FigureOutput('FracPaQ2D_Houghstuff', figure)
