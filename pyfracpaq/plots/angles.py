"""Angular histogram and equal-area rose in the common MATLAB-style theme."""

import numpy as np
from matplotlib.patches import Circle, Polygon
from matplotlib.ticker import MaxNLocator, StrMethodFormatter

from pyfracpaq.analysis.angles import AngularResult
from pyfracpaq.analysis.compatibility import cosd, sind
from pyfracpaq.analysis.palettes import cmocean
from pyfracpaq.domain.execution import AnalysisConfig
from pyfracpaq.plots.results import FigureOutput
from pyfracpaq.plots.ticks import MatlabLocator
from pyfracpaq.plots.style import (
    ROSE_RECTANGLE, figure_axes, matlab_style, strike_colourbar, title,
)


def render_histogram(result: AngularResult, config: AnalysisConfig
                     ) -> tuple[FigureOutput, ...]:
    with matlab_style():
        figure, axes = figure_axes((.13, .11, .775, .815))
        centres, frequencies = result.centres, result.frequencies
        axes.bar(centres, frequencies, width=centres[1] - centres[0],
                 facecolor=result.colour, edgecolor='black', linewidth=.5)
        upper = float(frequencies.max()) * 1.1
        axes.set_ylim(0, upper)
        axes.set_xlim(-10, 370)
        axes.set_xticks(np.arange(0, 361, 60))
        axes.set_xlabel('Trace segment angle, degrees')
        axes.set_ylabel('Frequency')
        left_colour, right_colour = (0., .447, .741), (.85, .325, .098)
        axes.yaxis.label.set_color(left_colour)
        axes.tick_params(axis='y', colors=left_colour)
        axes.spines['left'].set_color(left_colour)
        axes.set_box_aspect(1)
        axes.yaxis.set_major_locator(MatlabLocator())
        axes.yaxis.set_major_formatter(StrMethodFormatter('{x:g}'))
        axes.grid(True, color=left_colour, alpha=.15)
        axes.set_axisbelow(True)
        right = axes.twinx()
        right.set_ylim(0, upper / frequencies.sum() * 100)
        right.set_ylabel('Frequency, %', labelpad=5.125)
        right.yaxis.label.set_color(right_colour)
        right.tick_params(direction='in', axis='y', colors=right_colour)
        right.spines['right'].set_color(right_colour)
        right.spines['left'].set_visible(False)
        right.yaxis.set_major_locator(MatlabLocator())
        right.yaxis.set_major_formatter(StrMethodFormatter('{x:g}'))
        title(axes, f'Trace segment angles, n={len(result.angles) // 2}')
    return (FigureOutput('FracPaQ2D_histoangle', figure),)


def render_rose(result: AngularResult, config: AnalysisConfig
                ) -> tuple[FigureOutput, ...]:
    rose = result.rose
    coloured = bool(config.value('checkbox_rosecolour'))
    with matlab_style():
        rectangle = (ROSE_RECTANGLE if coloured
                     else (.13, .11, .775, .815))
        figure, axes = figure_axes(rectangle)
        if coloured:
            half = (len(rose.edges) - 1) // 2
            palette = cmocean('phase', half + 1)
            for index in range(len(rose.edges) - 1):
                vertices = np.vstack(([0., 0.], rose.vertices[2 * index:2 * index + 2]))
                axes.add_patch(Polygon(vertices, closed=True,
                                       facecolor=palette[index % half],
                                       edgecolor=palette[index % half],
                                       linewidth=.5))
            strike_colourbar(axes, half + 1)
        else:
            axes.add_patch(Polygon(rose.vertices, closed=True, facecolor=result.colour,
                                   edgecolor=result.colour, linewidth=.5))
        for percent in (1, 5, 10, 20, 30, 50):
            radius = 50 * np.sqrt(percent)
            if radius <= rose.limit:
                axes.add_patch(Circle((0, 0), radius, fill=False, edgecolor='black',
                                      linewidth=.25))
                axes.text(-radius, 0, f'{percent}%', fontsize=8, ha='right', va='center',
                          clip_on=False, bbox={'facecolor': 'white', 'edgecolor': 'none',
                                               'pad': 3})
        radius = 50 * np.sqrt(50) * 1.1
        axes.plot([-radius, radius], [0, 0], color='black', linewidth=.25)
        axes.plot([0, 0], [-radius, radius], color='black', linewidth=.25)
        if config.value('checkbox_showrosemean'):
            mean = result.statistics.mean
            point = rose.limit * np.array([sind(mean), cosd(mean)])
            axes.plot([point[0], -point[0]], [point[1], -point[1]],
                      color='red', linewidth=1, label='Axial mean')
        axes.set(xlim=(-rose.limit, rose.limit), ylim=(-rose.limit, rose.limit),
                 aspect='equal')
        axes.set_axis_off()
        weighting = ', length weighted' if rose.weighted else ''
        title(axes, f'Segment angles (equal area{weighting}), n={len(result.angles) // 2}')
    return (FigureOutput('FracPaQ2D_roseangleEqArea', figure),)
