from __future__ import annotations

from typing import Iterable, Optional

import weakref

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
        frac = _normalize_fraction_arg(size, default=0.06, allow_zero=False)
        pad_frac = _normalize_fraction_arg(pad, default=0.04, allow_zero=True)
        if location in {"bottom", "top"}:
            pad_frac = max(pad_frac, 0.08)
        else:
            pad_frac = max(pad_frac, 0.05)
        pos = _compute_polar_colorbar_box(ax, frac=frac, pad_frac=pad_frac, location=location)
        cax = fig.add_axes(pos)
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
    if is_polar:
        _register_polar_colorbar(ax, cax, frac=frac, pad_frac=pad_frac, location=location)
    return cbar


def _normalize_fraction_arg(
    value,
    *,
    default: float,
    allow_zero: bool,
    assume_percent_if_gt1: bool = True,
) -> float:
    """Convert numeric/percent inputs to a 0..1 fraction."""
    result = float(default)
    if value is None:
        pass
    else:
        try:
            if isinstance(value, str):
                stripped = value.strip()
                if stripped.endswith('%'):
                    result = float(stripped[:-1]) / 100.0
                else:
                    result = float(stripped)
                    if assume_percent_if_gt1 and result > 1.0:
                        result = result / 100.0
            else:
                result = float(value)
                if assume_percent_if_gt1 and result > 1.0:
                    result = result / 100.0
        except Exception:
            result = float(default)
    minimum = 0.0 if allow_zero else 1e-6
    if allow_zero:
        if result < 0.0:
            result = 0.0
    else:
        if result < minimum:
            result = minimum
    return result


def _compute_polar_colorbar_box(ax: Axes, *, frac: float, pad_frac: float, location: str):
    fig = ax.figure
    bbox = ax.get_position()
    fig_w_in, fig_h_in = fig.get_size_inches()
    dpi = fig.dpi or 100.0
    fig_w_px = max(fig_w_in * dpi, 1.0)
    fig_h_px = max(fig_h_in * dpi, 1.0)
    width_px = max(bbox.width * fig_w_px, 1.0)
    height_px = max(bbox.height * fig_h_px, 1.0)
    circle_px = min(width_px, height_px)
    loc = (location or 'bottom').lower()
    frac = max(frac, 1e-6)
    pad_frac = max(pad_frac, 0.0)
    if loc in {'bottom', 'top'}:
        bar_w = min(circle_px / fig_w_px, bbox.width)
        bar_w = max(bar_w, 1.0 / fig_w_px)
        bar_h = max(circle_px * frac / fig_h_px, 1.0 / fig_h_px)
        pad_abs = pad_frac * circle_px / fig_h_px
        center_x = bbox.x0 + bbox.width / 2.0
        x0 = center_x - bar_w / 2.0
        x0 = max(0.0, min(x0, 1.0 - bar_w))
        if loc == 'top':
            y0 = min(bbox.y1 + pad_abs, 0.98 - bar_h)
            y0 = max(y0, 0.0)
        else:
            top_edge = bbox.y0 - pad_abs
            available = max(top_edge, 0.0)
            if bar_h > available:
                bar_h = max(min(available, bar_h), 1.0 / fig_h_px)
            y0 = max(top_edge - bar_h, 0.0)
        return [x0, y0, bar_w, bar_h]
    bar_w = max(circle_px * frac / fig_w_px, 1.0 / fig_w_px)
    pad_abs = pad_frac * circle_px / fig_w_px
    if loc == 'left':
        x0 = max(bbox.x0 - bar_w - pad_abs, 0.02)
    else:
        x0 = min(bbox.x1 + pad_abs, 0.98 - bar_w)
    y0 = bbox.y0
    bar_h = bbox.height
    return [x0, y0, bar_w, bar_h]


def _entry_alive(entry: dict) -> bool:
    ax_ref = entry.get('ax')
    cax_ref = entry.get('cax')
    if ax_ref is None or cax_ref is None:
        return False
    ax = ax_ref()
    cax = cax_ref()
    if ax is None or cax is None:
        return False
    if ax.figure is None or cax.figure is None:
        return False
    return True


def _apply_polar_colorbar_entry(entry: dict) -> bool:
    if not _entry_alive(entry):
        return False
    ax = entry['ax']()
    cax = entry['cax']()
    pos = _compute_polar_colorbar_box(ax, frac=entry['frac'], pad_frac=entry['pad_frac'], location=entry['location'])
    cax.set_position(pos)
    return True


def _update_polar_colorbars(fig: Figure) -> None:
    registry = getattr(fig, '_polar_colorbar_registry', [])
    alive = []
    for entry in registry:
        if _apply_polar_colorbar_entry(entry):
            alive.append(entry)
    fig._polar_colorbar_registry = alive


def _ensure_polar_colorbar_callbacks(fig: Figure) -> None:
    canvas = getattr(fig, 'canvas', None)
    if canvas is None:
        return
    if getattr(canvas, '_polar_colorbar_cids', None):
        return
    def _refresh(event):
        if event is not None and getattr(event, 'canvas', None) is not canvas:
            return
        _update_polar_colorbars(fig)
    cid_resize = canvas.mpl_connect('resize_event', _refresh)
    cid_draw = canvas.mpl_connect('draw_event', _refresh)
    canvas._polar_colorbar_cids = (cid_resize, cid_draw)


def _register_polar_colorbar(ax: Axes, cax: Axes, *, frac: float, pad_frac: float, location: str) -> None:
    fig = ax.figure
    if fig is None:
        return
    entry = {
        'ax': weakref.ref(ax),
        'cax': weakref.ref(cax),
        'frac': float(frac),
        'pad_frac': float(max(pad_frac, 0.0)),
        'location': location,
    }
    _apply_polar_colorbar_entry(entry)
    registry = []
    for existing in getattr(fig, '_polar_colorbar_registry', []):
        if _apply_polar_colorbar_entry(existing):
            registry.append(existing)
    registry.append(entry)
    fig._polar_colorbar_registry = registry
    _ensure_polar_colorbar_callbacks(fig)


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
    try:
        ax._shrink_base_bounds = tuple(ax.get_position().bounds)
    except Exception:
        pass


def shrink_axes_vertical(ax: Axes, *, factor: float = 0.9) -> None:
    """Shrink the axes height by a factor around its current center.

    Keeps x/width the same, adjusts y0 to preserve the vertical center. Applies
    light clamping to keep the axes within the figure bounds.
    """
    fig = ax.figure
    prepare_figure_layout(fig)
    base_bounds = getattr(ax, "_shrink_base_bounds", None)
    if base_bounds is None:
        bbox = ax.get_position()
        base_bounds = list(bbox.bounds)
        ax._shrink_base_bounds = base_bounds
    x0, y0, width, height = base_bounds
    factor = max(0.1, min(factor, 1.0))
    y_center = y0 + height / 2.0
    new_h = height * factor
    new_y0 = y_center - new_h / 2.0
    # Clamp within figure bounds
    if new_y0 < 0.02:
        new_y0 = 0.02
    if new_y0 + new_h > 0.98:
        new_y0 = 0.98 - new_h
    ax.set_position([x0, new_y0, width, new_h])
