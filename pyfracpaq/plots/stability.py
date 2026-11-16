"""Stability maps/roses and the coupled Mohr figure, using shared colourbars."""

import numpy as np
from matplotlib.colors import ListedColormap, Normalize
from matplotlib.patches import Circle, Polygon
from matplotlib.ticker import FuncFormatter, MaxNLocator

from pyfracpaq.analysis.compatibility import cosd, sind
from pyfracpaq.analysis.palettes import matlab_jet
from pyfracpaq.analysis.stability import KINDS, StabilityField, StabilityResult
from pyfracpaq.domain.execution import AnalysisConfig
from pyfracpaq.plots.colourbars import colourbar
from pyfracpaq.plots.results import FigureOutput
from pyfracpaq.plots.raster import MultisampleLines
from pyfracpaq.plots.style import COLOUR_MAP_RECTANGLE, ROSE_RECTANGLE, figure_axes, legend, map_axes, matlab_style, title
from pyfracpaq.plots.ticks import MatlabLocator

NAMES = {'slip': ('sliptendency', 'Normalised slip tendency', r'$T_s$'),
         'dilation': ('dilationtendency', 'Dilation tendency', r'$T_d$'),
         'susceptibility': ('fracsuscep', 'Fracture susceptibility', r'$S_f$'),
         'csf': ('CSF', 'Critically stressed fractures', 'CSF')}


class _UnitTicks(MaxNLocator):
    """MATLAB's tenths at print size, fewer ticks when a window gets small."""
    def __call__(self):
        self.set_params(nbins=min(10, max(2, self.axis.get_tick_space())))
        return super().__call__()


def _norm(field: StabilityField) -> Normalize:
    low, high = field.colour_range
    if low == high:
        # Display-only range so Colorbar cannot change the constant scientific
        # limits or silently expand a vmin==vmax norm shared with another plot.
        pad = max(1., abs(low)) * .01
        maximum = np.finfo(float).max
        return Normalize(max(-maximum, low - pad), min(maximum, high + pad))
    return Normalize(low, high)


def _bar(axes, field, parameters, levels, *, rose=False):
    table = matlab_jet(levels, reverse=field.kind == 'susceptibility')
    constant = field.colour_range[0] == field.colour_range[1]
    # A constant field and its sole tick must display the same colour.
    palette = ListedColormap(table[:1] if constant else table)
    ticks = [field.colour_range[0]] if constant else None
    if field.kind == 'csf':
        ticks = [0, 1]
    bar = colourbar(axes, cmap=palette, norm=_norm(field), ticks=ticks)
    if field.kind in ('slip', 'dilation'):
        bar.locator = _UnitTicks()
        bar.formatter = FuncFormatter(lambda value, _: f'{value:g}')
        bar.update_ticks()
    if field.kind == 'csf':
        bar.set_ticklabels(['Non-CSF', 'CSF'])
        label = rf'Critically Stressed Fractures, $P_f$={parameters.pore_pressure:g} MPa'
    elif field.kind == 'susceptibility':
        label = r'Fracture susceptibility ($\Delta P_f$), MPa'
    else:
        label = NAMES[field.kind][1] + (f', {NAMES[field.kind][2]}' if rose else '')
    bar.set_label(label)
    return bar


def render_mohr(result: StabilityResult) -> FigureOutput:
    parameters, data = result.parameters, result.mohr
    figure, axes = figure_axes((.13, .11, .775, .815))
    axes.plot(data.normal, data.shear, color='black', linewidth=1, label='Stress')
    if parameters.pore_pressure > 0:
        axes.plot(data.effective_normal, data.shear, color='blue', linewidth=1, label='Effective stress')
    axes.plot([0, parameters.sigma1],
              [parameters.cohesion, parameters.friction * parameters.sigma1 + parameters.cohesion],
              color='red', linewidth=1, label='Sliding or Failure')
    legend(axes, loc='upper left' if parameters.pore_pressure > 0 else 'upper right')
    axes.set(xlabel='Normal stress, MPa', ylabel='Shear stress, MPa',
             xlim=(0, 1.1 * parameters.sigma1), ylim=(0, .5 * parameters.sigma1), aspect='equal')
    axes.xaxis.set_major_locator(MatlabLocator(6))
    axes.yaxis.set_major_locator(MatlabLocator(6))
    axes.grid(True)
    title(axes, rf'Mohr diagram $\mu$={parameters.friction:g}, $C_0$={parameters.cohesion:g} MPa')
    return FigureOutput('FracPaQ2D_Mohrplot', figure)


def _map(result, config, field):
    figure, axes = figure_axes(COLOUR_MAP_RECTANGLE)
    arrays, parameters = result.dataset.as_arrays(), result.parameters
    palette = matlab_jet(100, reverse=field.kind == 'susceptibility')
    axes.add_collection(MultisampleLines(arrays.segment_coordinates.reshape(-1, 2, 2),
                                       colors=palette[field.map_indices], linewidths=.75, zorder=3))
    map_axes(axes, result.dataset, config)
    _bar(axes, field, parameters, 100)
    sigma1, sigma2 = parameters.sigma1, parameters.sigma2
    if field.kind == 'csf':
        sigma1 -= parameters.pore_pressure
        sigma2 -= parameters.pore_pressure
        stress_labels = (r"$\sigma_1'$", r"$\sigma_2'$")
    else:
        stress_labels = (r'$\sigma_1$', r'$\sigma_2$')
    connector = ' for ' if field.kind in ('slip', 'dilation') else ' '
    title(axes, f'{NAMES[field.kind][1]}{connector}{stress_labels[0]}={sigma1:g} MPa, '
                f'{stress_labels[1]}={sigma2:g} MPa, ' + rf'$\theta$={parameters.theta:g}°')
    return FigureOutput(f'FracPaQ2D_{NAMES[field.kind][0]}map', figure)


def _rose(result, field):
    figure, axes = figure_axes(ROSE_RECTANGLE)
    rose, parameters = result.rose, result.parameters
    palette = matlab_jet(19, reverse=field.kind == 'susceptibility')
    for index in range(36):
        vertices = np.vstack(([0., 0.], rose.vertices[2 * index:2 * index + 2]))
        colour = palette[field.rose_indices[index]]
        axes.add_patch(Polygon(vertices, closed=True, facecolor=colour, edgecolor=colour, linewidth=.5))
    for percent in (1, 5, 10, 20, 30, 50):
        radius = 50 * np.sqrt(percent)
        if radius <= rose.limit:
            axes.add_patch(Circle((0, 0), radius, fill=False, edgecolor='black', linewidth=.25))
            axes.text(-radius, 0, f'{percent}%', fontsize=8, ha='right', va='center',
                      bbox={'facecolor': 'white', 'edgecolor': 'none', 'pad': 3})
    radius = 50 * np.sqrt(50) * 1.1
    axes.plot([-radius, radius], [0, 0], color='black', linewidth=.25)
    axes.plot([0, 0], [-radius, radius], color='black', linewidth=.25)
    point = rose.limit * np.array([sind(parameters.theta), cosd(parameters.theta)])
    axes.plot([point[0], -point[0]], [point[1], -point[1]], color='red', linewidth=1.5)
    axes.text(*(point * 1.05), r'Azimuth $\sigma_1$', fontsize=9)
    axes.set(xlim=(-rose.limit, rose.limit), ylim=(-rose.limit, rose.limit), aspect='equal')
    axes.set_axis_off()
    _bar(axes, field, parameters, 19, rose=True)
    # Keep the azimuth annotation clear of the title for a vertical sigma1.
    title(axes, 'Segment angles (equal area), colour-coded by ' + NAMES[field.kind][2], pad=8)
    return FigureOutput(f'FracPaQ2D_{NAMES[field.kind][0]}rose', figure)


def render_stability(result: StabilityResult, config: AnalysisConfig,
                      kind: str) -> tuple[FigureOutput, ...]:
    field = result.field(kind)
    first = next(KINDS[key] for key in KINDS if key in config.selected)
    with matlab_style():
        outputs = []
        if kind == first:
            basic_maps = {'MAP-01', 'MAP-04', 'MAP-05', 'MAP-06'}
            if len(result.dataset.colours) > 1 and not basic_maps.intersection(config.selected):
                from pyfracpaq.plots.maps import render_multicolour
                outputs.append(render_multicolour(result.dataset, config))
            outputs.append(render_mohr(result))
        outputs.extend((_map(result, config, field), _rose(result, field)))
    return tuple(outputs)
