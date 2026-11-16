"""Outside legends keep a physical gap below the facing axis labels."""

from matplotlib.legend import Legend
from matplotlib.transforms import IdentityTransform


class OutsideLegend(Legend):
    def _place(self,renderer):
        plot=self.axes.get_window_extent(renderer)
        labels=self.axes.xaxis.get_tightbbox(renderer)
        bottom=min(plot.y0,labels.y0) if labels is not None else plot.y0
        anchor=(plot.x0+plot.width/2,bottom-renderer.points_to_pixels(8.84))
        self.set_bbox_to_anchor(anchor,transform=IdentityTransform())

    def draw(self,renderer):
        self._place(renderer)
        return super().draw(renderer)

    def get_window_extent(self,renderer=None):
        if renderer is None:renderer=self.get_figure(root=True)._get_renderer()
        self._place(renderer)
        return super().get_window_extent(renderer)
