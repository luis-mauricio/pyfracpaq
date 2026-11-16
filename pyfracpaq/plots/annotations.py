"""Source-style top-aligned parameter boxes with physical text insets."""

from math import ceil

from matplotlib import font_manager
from matplotlib.text import Text
from matplotlib.transforms import IdentityTransform,Bbox


class ParameterBox(Text):
    """A figure Text retaining the native annotation's upper-left anchor.

    The frame uses the full hhea line height and reserves script descent.
    Native FitBoxToText also keeps an extra em on the right of its text.
    Both rules were measured on independent deterministic Plot* replays.
    """

    def _geometry(self,renderer):
        size=self.get_fontsize();unit=renderer.points_to_pixels(1)
        font=font_manager.get_font(font_manager.findfont(self.get_fontproperties()))
        metrics=font.get_sfnt_table('hhea');em=font.units_per_EM
        ascent=metrics['ascent']/em*size;descent=-metrics['descent']/em*size
        text=self.get_text();width=renderer.get_text_width_height_descent(text,self.get_fontproperties(),True)[0]
        extra=max(0,ceil(size*.45)-descent*.2) if '_' in text else 0
        height=(ascent+descent+extra+10)*unit
        width+=(10+.87*size)*unit
        x,y=self.get_transform().transform(self.get_position())
        return Bbox.from_bounds(x,y-height,width,height),(x+5*unit,y-5*unit)

    def draw(self,renderer):
        if not self.get_visible():return
        box,point=self._geometry(renderer);patch=self._bbox_patch
        patch.set_bounds(*box.bounds);patch.set_transform(IdentityTransform());patch.set_mutation_scale(1)
        patch.draw(renderer)
        old_position=self.get_position();old_transform=self.get_transform()
        self._bbox_patch=None
        self.set_position(point);self.set_transform(IdentityTransform())
        try:super().draw(renderer)
        finally:
            self.set_position(old_position);self.set_transform(old_transform);self._bbox_patch=patch


def parameter_box(figure,text):
    label=ParameterBox(.2,.325,text,ha='left',va='top',fontsize=10,
                       transform=figure.transFigure)
    label.set_bbox({'boxstyle':'square,pad=0','facecolor':'white','edgecolor':'black','linewidth':.5})
    label.set_figure(figure);figure.texts.append(label)
    return label
