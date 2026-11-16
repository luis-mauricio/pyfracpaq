"""Colourbars aligned to the plot, with fixed physical clearance from its labels.

Both axes use one layout calculation on every Qt/Agg/savefig draw. Small figures
reserve space by reducing the active plot slot, never by moving the colourbar
into the plot or its labels. The original slot remains available on enlargement.
"""

from collections.abc import Callable
from dataclasses import dataclass
from math import isfinite

from matplotlib.axes import Axes
from matplotlib.colorbar import Colorbar
from matplotlib.transforms import Bbox

DEFAULT_PAD_POINTS = 25.


@dataclass(frozen=True, slots=True)
class _ColourbarLayout:
    host: Axes
    scale: Axes
    location: str
    pad_points: float
    thickness: float
    original_locator: Callable | None

    @property
    def horizontal(self) -> bool:
        return self.location in ('bottom', 'top')

    def _place(self, slot: Bbox, renderer) -> tuple[Bbox, float]:
        self.host.apply_aspect(slot)
        plot = self.host.get_window_extent(renderer)
        axis = self.host.xaxis if self.horizontal else self.host.yaxis
        tight = axis.get_tightbbox(renderer) if self.host.axison else None
        facing = Bbox.union([plot, tight]) if tight is not None else plot
        owner = self.host.get_figure()
        width, height = owner.bbox.width, owner.bbox.height
        gap = renderer.points_to_pixels(self.pad_points)
        if self.location == 'bottom':
            rect = Bbox.from_bounds(plot.x0, facing.y0 - gap - self.thickness * height,
                                    plot.width, self.thickness * height)
        elif self.location == 'top':
            rect = Bbox.from_bounds(plot.x0, facing.y1 + gap,
                                    plot.width, self.thickness * height)
        elif self.location == 'left':
            rect = Bbox.from_bounds(facing.x0 - gap - self.thickness * width, plot.y0,
                                    self.thickness * width, plot.height)
        else:
            rect = Bbox.from_bounds(facing.x1 + gap, plot.y0,
                                    self.thickness * width, plot.height)
        position = owner.transSubfigure.inverted().transform_bbox(rect)
        self.scale.apply_aspect(position)
        length = (rect.width if self.horizontal else rect.height) * .01 / renderer.points_to_pixels(1)
        self.scale.tick_params(which='major', direction='in', length=length, width=.5)
        scale_axis = self.scale.xaxis if self.horizontal else self.scale.yaxis
        labels = scale_axis.get_tightbbox(renderer)
        occupied = Bbox.union([rect, labels]) if labels is not None else rect
        edge = renderer.points_to_pixels(2)
        if self.location == 'bottom':
            overflow = owner.bbox.y0 + edge - occupied.y0
        elif self.location == 'top':
            overflow = occupied.y1 - owner.bbox.y1 + edge
        elif self.location == 'left':
            overflow = owner.bbox.x0 + edge - occupied.x0
        else:
            overflow = occupied.x1 - owner.bbox.x1 + edge
        return position, overflow

    def positions(self, renderer) -> tuple[Bbox, Bbox]:
        slot = (self.original_locator(self.host, renderer) if self.original_locator is not None
                else self.host.get_position(original=True)).frozen()
        owner = self.host.get_figure()
        # Aspect constraints may make the visible box move by half the change
        # to its slot. Iterating converges without a second canvas draw, also
        # accounting for tick/offset/MathText changes as the slot gets smaller.
        for _ in range(40):
            position, overflow = self._place(slot, renderer)
            if overflow <= 1e-7:
                return slot, position
            x0, y0, x1, y1 = slot.extents
            unit = owner.bbox.height if self.horizontal else owner.bbox.width
            delta = overflow / unit
            minimum = min(renderer.points_to_pixels(1) / unit,
                          slot.height if self.horizontal else slot.width)
            if self.location == 'bottom':
                y0 = min(y0 + delta, y1 - minimum)
            elif self.location == 'top':
                y1 = max(y1 - delta, y0 + minimum)
            elif self.location == 'left':
                x0 = min(x0 + delta, x1 - minimum)
            else:
                x1 = max(x1 - delta, x0 + minimum)
            adjusted = Bbox.from_extents(x0, y0, x1, y1)
            if adjusted.bounds == slot.bounds:
                break  # Physically too small for text plus even a one-point plot.
            slot = adjusted
        position, _ = self._place(slot, renderer)
        return slot, position


@dataclass(frozen=True, slots=True)
class _LayoutLocator:
    layout: _ColourbarLayout
    index: int

    def __call__(self, axes, renderer) -> Bbox:
        return self.layout.positions(renderer)[self.index]


def colourbar(host: Axes, *, location: str = 'bottom', pad: float | None = None,
              thickness: float = .025, **kwargs) -> Colorbar:
    """Match plot endpoints and keep *pad* points outside its facing labels.

    Bottom/top match X endpoints; left/right match Y endpoints. Pad defaults to
    25 points (independent of window size/DPI); thickness is a figure fraction.
    Small figures reserve an active slot without changing the original slot,
    limits, aspect, palette, normalization or samples.
    """
    if location not in ('bottom', 'top', 'left', 'right'):
        raise ValueError('Choose bottom, top, left or right for the colourbar.')
    orientation = 'horizontal' if location in ('bottom', 'top') else 'vertical'
    if 'orientation' in kwargs:
        raise ValueError('Colourbar orientation is determined by its location.')
    pad = DEFAULT_PAD_POINTS if pad is None else pad
    if not isfinite(pad) or pad < 0 or not isfinite(thickness) or thickness <= 0:
        raise ValueError('Colourbar pad in points must be finite/nonnegative and thickness finite/positive.')
    scale = host.get_figure().add_axes(host.get_position(original=True))
    layout = _ColourbarLayout(host, scale, location, pad, thickness, host.get_axes_locator())
    host.set_axes_locator(_LayoutLocator(layout, 0))
    # Install before Colorbar, which wraps this locator for native extensions.
    scale.set_axes_locator(_LayoutLocator(layout, 1))
    bar = Colorbar(scale, location=location, orientation=orientation, **kwargs)
    # R2024b color rulers use 9pt for both ticks and their label, independently
    # of the host's 10pt ticks/11pt labels. Keep geometry in the shared locator.
    scale.tick_params(labelsize=9, direction='in', width=.5)
    scale.xaxis.label.set_size(9)
    scale.yaxis.label.set_size(9)
    bar.outline.set_linewidth(.5)
    return bar
