from __future__ import annotations

from typing import Iterable, Optional

import matplotlib.pyplot as plt

from ..types import Segment


def plot_tracemap(
    segments: Iterable[Segment],
    ax: Optional[plt.Axes] = None,
    color: str = "b",
    linewidth: float = 1.0,
    equal_aspect: bool = True,
    show_nodes: bool = False,
    node_color: str = "k",
    node_size: float = 5.0,
) -> plt.Axes:
    """Plot a simple trace map from segments."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 6))
    for s in segments:
        ax.plot([s.x1, s.x2], [s.y1, s.y2], color=color, lw=linewidth)
    if show_nodes:
        xs = []
        ys = []
        for s in segments:
            xs.extend([s.x1, s.x2])
            ys.extend([s.y1, s.y2])
        ax.scatter(xs, ys, s=node_size, c=node_color, marker='o', alpha=0.7, linewidths=0)
    if equal_aspect:
        ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("X pixels")
    ax.set_ylabel("Y pixels")
    ax.set_title("")
    return ax
