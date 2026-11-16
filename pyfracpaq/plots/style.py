"""Shared axes, text, legends and responsive colourbars in the MATLAB theme."""

from contextlib import contextmanager
from importlib.resources import as_file, files
from math import ceil, floor

from matplotlib import font_manager, rc_context, rc_params_from_file
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.colors import ListedColormap, Normalize
from matplotlib.markers import MarkerStyle
from matplotlib.transforms import Affine2D, Bbox, ScaledTranslation
from matplotlib.text import Text
from matplotlib.lines import Line2D

from pyfracpaq.analysis.palettes import cmocean
from pyfracpaq.domain import Dataset
from pyfracpaq.domain.execution import AnalysisConfig
from pyfracpaq.plots.colourbars import colourbar
from pyfracpaq.plots.ticks import MatlabLocator
from pyfracpaq.plots.markers import native_marker_renderer
from pyfracpaq.plots.grids import native_grids
from pyfracpaq.plots.tex import native_mathtext
from pyfracpaq.plots.legends import OutsideLegend
from pyfracpaq.plots.dashes import native_dashes

COLOUR_MAP_RECTANGLE=(.13,.225325,.775,.70935)
ROSE_RECTANGLE=(.13,.2043,.775,.7285)
LEGEND_MAP_RECTANGLE=(.13,.191175,.775,.74065)


@contextmanager
def matlab_style(font_family: str = 'Arial'):
    with as_file(files('pyfracpaq.resources').joinpath('fracpaq_matlab.mplstyle')) as path:
        params = rc_params_from_file(path, use_default_template=False, fail_on_error=True)
    families = {font.name for font in font_manager.fontManager.ttflist}
    selected = font_family if font_family in families else 'Arial' if 'Arial' in families else 'DejaVu Sans'
    params['font.family'] = [selected]
    with rc_context(params):
        yield


class MatlabFigure(Figure):
    """Keep draw-time math/font settings identical for Agg and Qt repainting."""

    def draw(self, renderer):
        # Mathtext resolves its custom font table at draw time, after a
        # renderer's construction context has normally ended.
        with matlab_style():
            # A figure can also be constructed directly outside the theme.
            # Resolve generic families once so later bbox queries outside this
            # draw context measure the same actual font (including Qt resize).
            generic={'sans-serif','serif','cursive','monospace','fantasy','sans'}
            for text in self.findobj(match=Text):
                if any(family in generic for family in text.get_fontfamily()):
                    path=font_manager.findfont(text.get_fontproperties())
                    text.set_fontfamily(font_manager.FontProperties(fname=path).get_name())
            with native_mathtext(renderer),native_marker_renderer(renderer,self.dpi),native_dashes(self,renderer):
                return super().draw(renderer)


class MatlabAxes(Axes):
    """Native tick lengths track the longest active plot dimension."""

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        # MATLAB's default Layer='bottom': data can cover the ruler/frame.
        self.set_axisbelow(True)
        for spine in self.spines.values():spine.set_zorder(.75)

    def apply_aspect(self, position=None):
        super().apply_aspect(position)
        # The native raster viewport uses inclusive integer device pixels.
        # Quantise only the display box; limits and scientific coordinates stay
        # unchanged. This also keeps repeated Qt/Agg draws idempotent.
        owner=self.get_figure();root=self.get_figure(root=True)
        p=owner.transSubfigure.transform_bbox(self._position)
        height=root.bbox.y1;pixel_height=floor(height)
        if self.get_aspect()!='auto' or self.get_box_aspect() is not None:
            # Use quarter-device-pixel spans for the calibrated print viewport.
            # Preserve the data/box aspect rather than rounding both spans
            # independently; marker centres are rasterised separately.
            width=max(.25,floor(p.width*4)/4)*getattr(self,'_native_viewport_scale',1.)
            span=width*p.height/p.width if p.width>0 else .25
            cx=floor((p.x0+p.x1)/2);cy=round((p.y0+p.y1)/2)+.5
            cx+=getattr(self,'_native_viewport_x',0)
            cy+=getattr(self,'_native_viewport_y',0)
            left=cx-width/2;right=cx+width/2
            bottom=cy-span/2;top=cy+span/2
        else:
            width=max(.25,floor(p.width*4)/4)
            span=max(.25,floor(p.height*4)/4)
            cx=floor((p.x0+p.x1)/2);cy=round((p.y0+p.y1)/2)+.5
            left=cx-width/2;right=cx+width/2
            bottom=cy-span/2;top=cy+span/2
        box=Bbox.from_extents(left,bottom,right,top)
        self._set_position(owner.transSubfigure.inverted().transform_bbox(box),which='active')

    def draw(self, renderer):
        locator = self.get_axes_locator()
        self.apply_aspect(locator(self, renderer) if locator else None)
        length = .01 * max(self.bbox.width, self.bbox.height) * 72 / self.figure.dpi
        width=max(1,floor(.5*self.figure.dpi/72))*72/self.figure.dpi
        self.tick_params(which='major', length=length, width=width)
        self.tick_params(which='minor', length=length / 2, width=width)
        with native_grids(self,renderer):
            return super().draw(renderer)


def figure_axes(rectangle: tuple[float, float, float, float] = (.14, .14, .72, .72)
                ) -> tuple[Figure, Axes]:
    figure = MatlabFigure()
    axes = figure.add_axes(rectangle, axes_class=MatlabAxes)
    axes._native_viewport_y=(.5 if rectangle==COLOUR_MAP_RECTANGLE else
                            .25 if rectangle==LEGEND_MAP_RECTANGLE else 0)
    axes.xaxis.set_major_locator(MatlabLocator())
    axes.yaxis.set_major_locator(MatlabLocator())
    axes.tick_params(direction='in', top=True, right=True)
    if rectangle==COLOUR_MAP_RECTANGLE:
        axes.tick_params(axis='x',pad=5.87)
    for spine in axes.spines.values():
        spine.set_linewidth(.5)
    return figure, axes


def title(axes: Axes, text: str, *, pad: float = 3.5) -> None:
    # Native20cm/600dpi exports place the first line2.5pt lower than the
    # previous source-only estimate. Keep the original blank second line.
    if pad==3.5 and '$' in text and ('_' in text or '^' in text):pad=6
    axes.set_title(text + '\n', fontsize=11, fontweight='bold', pad=pad)


def legend(axes: Axes, *, outside_bottom=False, **kwargs):
    handles,_=axes.get_legend_handles_labels()
    markers_only=bool(handles) and all(isinstance(h,Line2D) and h.get_linestyle() in ('None','none','') for h in handles)
    options=dict(frameon=True,fancybox=False,edgecolor=(.15,.15,.15),framealpha=1,
                 fontsize=9,handlelength=(8 if markers_only else 30)/9,
                 handletextpad=5.4/9,borderpad=3/9,borderaxespad=8.12/9,
                 labelspacing=2.52/9,columnspacing=.7)
    options.update(kwargs)
    if outside_bottom:
        options.update(loc='upper center',borderaxespad=0)
        _,labels=axes.get_legend_handles_labels()
        result=OutsideLegend(axes,handles,labels,**options)
        axes.legend_=result
        result._remove_method=axes._remove_legend
    else:result=axes.legend(**options)
    result.get_frame().set_linewidth(.5)
    # Native legend tokens and text have independent insets. Applying physical
    # translations to their live artists keeps the measured outer frame and
    # responsive placement intact (including outside legends).
    root=axes.get_figure(root=True)
    for text in result.get_texts():
        text.set_transform(text.get_transform()+ScaledTranslation(-1.32/72,-.96/72,root.dpi_scale_trans))
    for line in result.get_lines():
        line.set_transform(line.get_transform()+ScaledTranslation(.84/72,-.96/72,root.dpi_scale_trans))
        if line.get_marker() not in ('None','none','',None):
            line.set_markeredgewidth(max(1,line.get_markeredgewidth()))
    return result


def square_marker():
    # Native PNG probes: the square occupies 80% of the nominal marker extent.
    # Matplotlib uses the full extent. Keep the nominal size/API unchanged.
    return MarkerStyle('s', transform=Affine2D().scale(.8))


def strike_colourbar(axes: Axes, levels: int) -> None:
    bar = colourbar(axes, cmap=ListedColormap(cmocean('phase', levels)),
                    norm=Normalize(0, 180), ticks=list(range(0, 181, 20)))
    bar.set_label('Segment strike, degrees')


def map_axes(axes: Axes, dataset: Dataset, config: AnalysisConfig) -> None:
    bounds = dataset.bounds
    for setter, low, high in ((axes.set_xlim, bounds.x_min, bounds.x_max),
                              (axes.set_ylim, bounds.y_min, bounds.y_max)):
        pad = max(1., abs(low)) * .01 if low == high else 0.
        setter(low - pad, high + pad)
    axes.set_aspect('equal', adjustable='box')
    axes.set_xlabel(f'X, {dataset.length_unit}')
    axes.set_ylabel(f'Y, {dataset.length_unit}')
    if config.flip_x:
        axes.invert_xaxis()
    if config.flip_y:
        axes.invert_yaxis()
