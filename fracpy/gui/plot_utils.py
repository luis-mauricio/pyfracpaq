from __future__ import annotations

from typing import Iterable, Optional

from matplotlib.axes import Axes
from matplotlib.cm import ScalarMappable
from matplotlib.figure import Figure
from mpl_toolkits.axes_grid1 import make_axes_locatable


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
    size: str = "6%",
    pad: float = 0.70,
    ticks: Optional[Iterable[float]] = None,
    label: Optional[str] = None,
):
    """Attach a colorbar aligned to the given axes width.

    - location: one of 'bottom' or 'right'
    - size: relative thickness, e.g., '5%'
    - pad: gap between axes and colorbar (in inches fraction)
    """
    fig = ax.figure
    prepare_figure_layout(fig)
    divider = make_axes_locatable(ax)
    cax = divider.append_axes(location, size=size, pad=pad)
    orientation = "horizontal" if location in {"bottom", "top"} else "vertical"
    cbar = fig.colorbar(mappable, cax=cax, orientation=orientation)
    if label:
        cbar.set_label(label)
    if ticks is not None:
        try:
            cbar.set_ticks(list(ticks))
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
    bbox = ax.get_position()
    x_center = (bbox.x0 + bbox.x1) / 2.0
    fig.suptitle(text, y=y, x=x_center, ha="center")
    try:
        fig.subplots_adjust(top=top)
    except Exception:
        pass

