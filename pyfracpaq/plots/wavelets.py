"""Wavelet four-panel figures with subplot-local responsive vertical scales."""

import numpy as np
from matplotlib.colors import ListedColormap, Normalize
from matplotlib.patches import Circle, Polygon
from matplotlib.transforms import ScaledTranslation
from matplotlib.ticker import StrMethodFormatter

from pyfracpaq.analysis.compatibility import histcount_indices, sind, cosd
from pyfracpaq.analysis.palettes import cmocean, matlab_rgb
from pyfracpaq.plots.colourbars import colourbar
from pyfracpaq.plots.results import FigureOutput
from pyfracpaq.plots.style import MatlabAxes, MatlabFigure, matlab_style
from pyfracpaq.plots.ticks import MatlabLocator, automatic_limits


def draw_wavelet_rose(axes, degrees, delta, colour):
    edges = np.arange(0, 361, delta, dtype=float)
    if not len(degrees):
        axes.text(.5, .5, 'No coefficients above the 50% threshold.', transform=axes.transAxes,
                  ha='center', va='center', fontsize=8)
        axes.set_axis_off()
        return
    ids = histcount_indices(degrees, edges)
    counts = np.bincount(ids[ids >= 0], minlength=len(edges) - 1).astype(float)
    half = len(counts) // 2
    counts[[0, half]] = (counts[0] + counts[half]) / 2
    counts[[half - 1, -1]] = (counts[half - 1] + counts[-1]) / 2
    theta = np.column_stack((edges[:-1], edges[1:])).ravel()
    radii = 50 * np.sqrt(np.repeat(counts / len(degrees) * 100, 2))
    vertices = np.vstack((np.column_stack((radii * sind(theta), radii * cosd(theta))), [0, 0], [0, 0]))
    axes.add_patch(Polygon(vertices, facecolor=colour, edgecolor=colour, linewidth=.5))
    contours = 50 * np.sqrt([1, 5, 10, 20, 30, 50])
    larger = contours[contours > float(vertices.max())]
    limit = float(larger[0]) if len(larger) else float(max(contours[-1], vertices.max()))
    for percent, radius in zip((1, 5, 10, 20, 30, 50), contours):
        if radius <= limit:
            axes.add_patch(Circle((0, 0), radius, fill=False, edgecolor='black', linewidth=.25))
            axes.text(-radius, 0, f'{percent}%', fontsize=8, clip_on=False,
                       ha='right', va='center',
                       bbox={'facecolor': 'white', 'edgecolor': 'none', 'pad': 3})
    axes.axhline(0, color='black', linewidth=.25)
    axes.axvline(0, color='black', linewidth=.25)
    axes.set(xlim=(-limit, limit), ylim=(-limit, limit), aspect='equal')
    axes.set_axis_off()


def render_wavelets(result, config):
    outputs = []
    with matlab_style():
        for scale in result.scales:
            figure = MatlabFigure()
            panels = figure.subfigures(2, 2, wspace=0, hspace=0)
            for owner, left, image, palette, heading in (
                (panels[0, 0], .26, result.image, matlab_rgb('bone'), 'Binary image'),
                (panels[0, 1], .1406818182, scale.coefficients, cmocean('thermal'), f'WC map, a={scale.scale}')):
                axes = owner.add_axes((left, .1676744186, .5198 if left<.2 else .52025, .6187597089), axes_class=MatlabAxes)
                axes._native_viewport_x=.375 if left<.2 else .25
                axes._native_viewport_y=-.75
                axes.xaxis.set_major_locator(MatlabLocator());axes.yaxis.set_major_locator(MatlabLocator())
                ny, nx = image.shape
                axes.imshow(image, origin='upper', extent=(.5, nx + .5, ny + .5, .5),
                            cmap=ListedColormap(palette), vmin=0, vmax=1, interpolation='nearest')
                axes.set(xlabel='X, pixels', ylabel='Y, pixels', aspect='equal')
                axes.tick_params(direction='out',top=False,right=False)
                axes.set_title(heading + '\n', fontsize=11, fontweight='bold',pad=3.5)
                if config.flip_x:
                    axes.invert_xaxis()
                if config.flip_y:
                    axes.invert_yaxis()
                colourbar(axes, cmap=ListedColormap(palette), norm=Normalize(0, 1),
                           location='right', thickness=.0464285714, ticks=np.linspace(0, 1, 6))
            rose = panels[1, 0].add_axes((.26, .22, .6693181818, .6187597089), axes_class=MatlabAxes)
            rose._native_viewport_x=1
            rose._native_viewport_y=-.5
            draw_wavelet_rose(rose, scale.doubled_degrees, result.parameters.angular_step, result.colour)
            rose.set_title(r'Distribution of $\theta_{opt}$, WC threshold=' + f'{scale.threshold:.2f}\n',
                           fontsize=11, fontweight='bold',pad=4.25)
            rose.title.set_transform(rose.title.get_transform()+ScaledTranslation(.24/72,0,figure.dpi_scale_trans))
            hist = panels[1, 1].add_axes((.1406818182, .22, .6693181818, .6187597089), axes_class=MatlabAxes)
            hist._native_viewport_y=-.5
            hist.xaxis.set_major_locator(MatlabLocator());hist.yaxis.set_major_locator(MatlabLocator())
            hist.xaxis.set_major_formatter(StrMethodFormatter('{x:g}'))
            positive = scale.histogram_counts > 0
            width = scale.histogram_centres[1] - scale.histogram_centres[0]
            hist.bar(scale.histogram_centres[positive], np.log10(scale.histogram_counts[positive]),
                     width=width, facecolor=result.colour, edgecolor='black', linewidth=.5)
            hist.plot([scale.threshold] * 2, [0, float(scale.histogram_counts.max())], color='red', linewidth=2)
            hist.set(xlabel=r'$WC_{opt}$', ylabel=r'$\log_{10}$(frequency)',
                     xlim=(0,automatic_limits([0,max(float(scale.coefficients.max())*1.07,np.finfo(float).tiny)])[1]),
                     ylim=(0, max(.1, np.log10(float(scale.histogram_counts.max()) * 1.1))))
            hist.set_title(f'WC histogram, a={scale.scale}\n', fontsize=11, fontweight='bold',pad=3.5)
            hist.set_box_aspect(1)
            hist.grid(True)
            outputs.append(FigureOutput(f'FracPaQ2Dwavelet_a{scale.scale}', figure))
    return tuple(outputs)
