from __future__ import annotations

from typing import Iterable, Optional

from matplotlib.axes import Axes
from matplotlib.cm import ScalarMappable
from matplotlib.figure import Figure
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib import rcParams


def prepare_figure_layout(fig: Figure) -> None:
    """Disable layout engines to allow precise manual spacing.

    Avoids warnings and clipping when using axes_grid1 for axis-wide colorbars
    and when tightening title/top margins programmatically.
    """
    try:
        fig.set_constrained_layout(False)
    except Exception:
        pass
    try:
        # Matplotlib >= 3.8
        fig.set_layout_engine(None)
    except Exception:
        pass


def axis_wide_colorbar(
    ax: Axes,
    mappable: ScalarMappable,
    *,
    location: str = "bottom",
    size: str | float = "6%",
    pad: float = 0.70,
    ticks: Optional[Iterable[float]] = None,
    label: Optional[str] = None,
    gid: Optional[str] = None,
    boundaries: Optional[Iterable[float]] = None,
):
    """Attach a colorbar aligned to the given axes width.

    - location: one of 'bottom' or 'right'
    - size: relative thickness, e.g., '5%'
    - pad: gap between axes and colorbar (in inches fraction)
    """
    fig = ax.figure
    prepare_figure_layout(fig)
    orientation = "horizontal" if location in {"bottom", "top"} else "vertical"

    # Special handling for polar axes: append_axes inherits projection
    # which triggers a NotImplementedError in colorbar. Build a new
    # standard Axes aligned to the target instead.
    is_polar = getattr(ax, "name", "") == "polar"
    if is_polar:
        # Normalize size to a fraction of the target axes height
        if isinstance(size, str) and size.endswith('%'):
            frac = float(size[:-1]) / 100.0
        else:
            try:
                frac = float(size)
                # if passed as percent, convert; otherwise assume fraction
                if frac > 1.0:
                    frac = frac / 100.0
            except Exception:
                frac = 0.06
        # Pad as fraction of axes height; if pad in (0,1], use directly; if >1, treat as percent
        if pad is None:
            pad_frac = 0.04
        else:
            try:
                p = float(pad)
                pad_frac = (p/100.0) if (p > 1.0) else p
            except Exception:
                pad_frac = 0.04
        bbox = ax.get_position()
        bar_h = bbox.height * frac
        if location in {"bottom", "top"}:
            bar_w = bbox.width
            x0 = bbox.x0
            if location == "bottom":
                # Place cbar near figure bottom (outside the polar plot area)
                # Raise a tiny bit for spacing
                y0 = 0.09
            else:
                y0 = min(bbox.y1 + pad_frac, 0.98 - bar_h)
            cax = fig.add_axes([x0, y0, bar_w, bar_h])
        else:
            # right/left: align vertically with axes
            bar_w = bbox.width * frac
            y0 = bbox.y0
            if location == "right":
                x0 = min(bbox.x1 + pad_frac, 0.98 - bar_w)
            else:
                x0 = max(bbox.x0 - bar_w - pad_frac, 0.02)
            cax = fig.add_axes([x0, y0, bar_w, bbox.height])
    else:
        divider = make_axes_locatable(ax)
        cax = divider.append_axes(location, size=size, pad=pad)

    # Remove any existing colorbar axes with the same gid (avoid duplicates)
    if gid:
        for ax2 in list(fig.axes):
            try:
                if getattr(ax2, 'get_gid', lambda: None)() == gid:
                    ax2.remove()
            except Exception:
                pass
    # When boundaries are provided, use them to create a discrete colorbar and draw edges
    if boundaries is not None:
        try:
            cbar = fig.colorbar(
                mappable,
                cax=cax,
                orientation=orientation,
                boundaries=list(boundaries),
                spacing="proportional",
                drawedges=True,
            )
        except Exception:
            # Fallback without boundaries
            cbar = fig.colorbar(mappable, cax=cax, orientation=orientation)
    else:
        cbar = fig.colorbar(mappable, cax=cax, orientation=orientation)
    if label:
        cbar.set_label(label)
    if ticks is not None:
        try:
            cbar.set_ticks(list(ticks))
        except Exception:
            pass
    # Remove minor ticks (e.g., boundaries) to avoid double tick rows
    try:
        cbar.ax.minorticks_off()
    except Exception:
        pass
    try:
        if gid:
            cbar.ax.set_gid(gid)
    except Exception:
        pass
    return cbar


def center_title_over_axes(
    fig: Figure,
    ax: Axes,
    text: str,
    *,
    y: float = 0.98,
    top: float = 0.92,
):
    """Place a suptitle visually centered over the axes and reserve top space."""
    prepare_figure_layout(fig)
    # Remove any existing suptitle explicitly to avoid duplicates on redraw/reuse
    try:
        prev = getattr(fig, "_suptitle", None)
        if prev is not None:
            try:
                prev.remove()
            except Exception:
                pass
    except Exception:
        pass
    bbox = ax.get_position()
    x_center = (bbox.x0 + bbox.x1) / 2.0
    fig.suptitle(text, y=y, x=x_center, ha="center")
    try:
        fig.subplots_adjust(top=top)
    except Exception:
        pass


def title_above_axes(
    ax: Axes,
    text: str,
    *,
    offset_points: int = 2,
    top: float = 0.96,
    fontsize: float | None = None,
    adjust_layout: bool = True,
):
    """Place a title just above the axes with a tiny offset.

    Anchors at (0.5, 1.0) in axes coordinates and nudges upward
    by `offset_points`. Reserves a small top margin to avoid clipping.
    """
    fig = ax.figure
    prepare_figure_layout(fig)
    if adjust_layout:
        try:
            fig.subplots_adjust(top=top)
        except Exception:
            pass
    if fontsize is None:
        # Match typical axes title size for consistency
        fontsize = rcParams.get('axes.titlesize', rcParams.get('font.size', 10))
    ax.annotate(
        text,
        xy=(0.5, 1.0),
        xycoords="axes fraction",
        xytext=(0, offset_points),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=fontsize,
        clip_on=False,
    )


def reserve_axes_margins(ax: Axes, *, top: float = 0.06, bottom: float = 0.10) -> None:
    """Set absolute top/bottom figure margins and resize the axes.

    The parameters are absolute fractions of the figure height (0..1), not
    increments. For example, bottom=0.30 places the bottom of the axes at 30%
    of the figure height, regardless of its current position. Safeguards
    ensure the axes height remains positive and within [0, 1].
    """
    fig = ax.figure
    prepare_figure_layout(fig)
    bbox = ax.get_position()
    # Clamp margins to sane limits (allow zero if requested)
    bottom = max(0.0, min(bottom, 0.9))
    top = max(0.0, min(top, 0.9))
    new_y0 = max(bottom, 0.0)
    new_top = min(1.0 - top, 1.0)
    # Keep at least 10% of original height
    min_h = max(0.1 * bbox.height, 0.05)
    new_h = max(new_top - new_y0, min_h)
    ax.set_position([bbox.x0, new_y0, bbox.width, new_h])


def shrink_axes_vertical(ax: Axes, *, factor: float = 0.9) -> None:
    """Shrink the axes height by a factor around its current center.

    Keeps x/width the same, adjusts y0 to preserve the vertical center. Applies
    light clamping to keep the axes within the figure bounds.
    """
    fig = ax.figure
    prepare_figure_layout(fig)
    bbox = ax.get_position()
    factor = max(0.1, min(factor, 1.0))
    y_center = bbox.y0 + bbox.height / 2.0
    new_h = bbox.height * factor
    new_y0 = y_center - new_h / 2.0
    # Clamp within figure bounds
    if new_y0 < 0.02:
        new_y0 = 0.02
    if new_y0 + new_h > 0.98:
        new_y0 = 0.98 - new_h
    ax.set_position([bbox.x0, new_y0, bbox.width, new_h])
