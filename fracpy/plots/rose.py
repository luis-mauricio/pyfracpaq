from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt

import numpy as np

from ..stats.orientation import rose_hist


def plot_rose(
    angles_deg: np.ndarray,
    bins: int = 18,
    bidirectional: bool = True,
    ax: Optional[plt.Axes] = None,
    facecolor: str = "C0",
    edgecolor: str = "white",
    alpha: float = 0.9,
) -> plt.Axes:
    """Plot a rose diagram from orientation angles (degrees)."""
    theta, radii = rose_hist(angles_deg, bins=bins, bidirectional=bidirectional)
    if ax is None:
        fig, ax = plt.subplots(subplot_kw={"projection": "polar"}, figsize=(6, 6))
    width = 2 * np.pi / bins
    bars = ax.bar(theta, radii, width=width, bottom=0.0, align="center",
                  facecolor=facecolor, edgecolor=edgecolor, alpha=alpha)
    ax.set_theta_zero_location("E")  # 0° to the right
    ax.set_theta_direction(-1)        # clockwise
    ax.set_title("Rose Diagram")
    return ax

