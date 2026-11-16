"""Standalone drawing helpers: palettes, ellipse, arcs and centered axes."""

import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Polygon

from pyfracpaq.analysis.compatibility import cosd, sind
from pyfracpaq.analysis.palettes import cmocean
from pyfracpaq.plots.connectivity import ternary_coordinates


def apply_cmocean(axes, name, levels=256, *, reverse=False, pivot=None, limits=None):
    cmap = ListedColormap(cmocean(name, levels, reverse=reverse, pivot=pivot, limits=limits))
    for artist in (*axes.images, *axes.collections):
        artist.set_cmap(cmap)
        if limits is not None:
            artist.set_clim(*limits)
    return cmap


def plot_ellipse(axes, major: float, minor: float, north_angle: float, colour='blue'):
    if not np.isfinite([major, minor, north_angle]).all() or min(major, minor) <= 0:
        raise ValueError('Ellipse diameters must be finite and positive.')
    theta = np.arange(0, 2 * np.pi + 1e-10, .01)
    angle = 90 - north_angle
    x = major / 2 * np.cos(theta) * cosd(angle) - minor / 2 * np.sin(theta) * sind(angle)
    y = major / 2 * np.cos(theta) * sind(angle) + minor / 2 * np.sin(theta) * cosd(angle)
    patch = Polygon(np.column_stack((x, y)), facecolor=colour, edgecolor='black')
    axes.add_patch(patch)
    for diameter, a in ((major, angle), (minor, angle + 90)):
        axes.plot(np.array([-1, 1]) * diameter / 2 * cosd(a) * 1.2,
                  np.array([-1, 1]) * diameter / 2 * sind(a) * 1.2, color='black')
    axes.autoscale_view()
    axes.set_aspect('equal')
    axes.set_axis_off()
    return patch


def plot_arc(axes, radius: float, start: float, end: float, *, dotted=False):
    if not np.isfinite([radius, start, end]).all() or radius < 0 or end < start:
        raise ValueError('Arc needs finite nonnegative radius and increasing angles.')
    azimuth = np.arange(start, end + 1e-10, 5)
    return axes.plot(radius * sind(azimuth), radius * cosd(azimuth),
                      color='blue', linestyle=':' if dotted else '-', linewidth=2)


def centered_axes(axes, origin=(0., 0.)):
    if not np.isfinite(origin).all() or len(origin) != 2:
        raise ValueError('Centered axes require a finite two-dimensional origin.')
    x, y = max(abs(v) for v in axes.get_xlim()), max(abs(v) for v in axes.get_ylim())
    axes.set(xlim=(origin[0] - x, origin[0] + x), ylim=(origin[1] - y, origin[1] + y))
    axes.spines[['top', 'right']].set_visible(False)
    axes.spines['left'].set_position(('data', origin[0]))
    axes.spines['bottom'].set_position(('data', origin[1]))
    axes.set_xticks(np.linspace(origin[0] - x, origin[0] + x, 9))
    axes.set_yticks(np.linspace(origin[1] - y, origin[1] + y, 9))


def ternary_frame(axes):
    scale = 2 / np.sqrt(3)
    axes.plot([0, scale / 2, scale, 0], [-1, 0, -1, -1], color='black')
    for i in range(1, 10):
        for points in (((i * scale / 20, -1 + i / 10), ((20 - i) * scale / 20, -1 + i / 10)),
                       ((i * scale / 20, -1 + i / 10), (i * scale / 10, -1)),
                       ((i * scale / 10, -1), (scale / 2 + i * scale / 20, -i / 10))):
            axes.plot(*np.asarray(points).T, color='red', linestyle=':', linewidth=.25)
    axes.set_aspect('equal')
    axes.set_axis_off()


def ternary_points(axes, percentages, *, label='', connect=False, colour='blue'):
    xy = ternary_coordinates(percentages)
    return axes.plot(*xy.T, linestyle='-' if connect else 'none', marker='o', color=colour, label=label)
