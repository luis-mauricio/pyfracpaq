"""Complementary historical roses; no extra main-window selectors."""

import numpy as np
from matplotlib.patches import Polygon

from pyfracpaq.analysis.compatibility import cosd, sind
from pyfracpaq.plots.auxiliary import centered_axes, plot_arc


def draw_historical_rose(axes, result, *, azimuth=0, colour='blue'):
    if result.kind == 'linear':
        x, y = result.vertices.T
        rotated = np.column_stack((x * cosd(azimuth) + y * sind(azimuth),
                                    -x * sind(azimuth) + y * cosd(azimuth)))
        axes.add_patch(Polygon(rotated, facecolor=colour, edgecolor=colour))
        limit = max(1., float(np.max(np.abs(rotated))))
    else:
        limit = max(1., float(result.radii.max()))
        inner = limit / 10
        for i, radius in enumerate(result.radii):
            if radius <= 0:
                continue
            for theta in result.edges[i:i + 2]:
                axes.plot([inner * sind(theta), radius * sind(theta)],
                          [inner * cosd(theta), radius * cosd(theta)], color='blue', linewidth=2)
        for radius in (limit, limit / 2, limit / np.sqrt(2) if result.square_root else limit / 4):
            plot_arc(axes, radius, 0, 360, dotted=True)
        axes.plot([-limit, limit], [0, 0], color='black')
        axes.plot([0, 0], [-limit, limit], color='black')
    axes.set(xlim=(-limit, limit), ylim=(-limit, limit), aspect='equal')
    axes.set_axis_off()
    return axes
