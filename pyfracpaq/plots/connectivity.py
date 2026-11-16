"""Topology node map, two shared-scale heatmaps and the I/Y/X ternary diagram."""

from math import sqrt

import numpy as np
from matplotlib.colors import ListedColormap, Normalize

from pyfracpaq.analysis.connectivity import ConnectivityResult
from pyfracpaq.analysis.palettes import matlab_rgb
from pyfracpaq.domain.execution import AnalysisConfig
from pyfracpaq.plots.colourbars import colourbar
from pyfracpaq.plots.results import FigureOutput
from pyfracpaq.plots.raster import MultisampleLines
from pyfracpaq.plots.style import COLOUR_MAP_RECTANGLE, LEGEND_MAP_RECTANGLE, figure_axes, legend, map_axes, matlab_style, title

CL2 = np.array([[50, 0, 50], [0, 33, 67]], dtype=float)
CL357 = np.array([[8.3 / 9.3 * 100, 0, 1 / 9.3 * 100],
                  [0, .8925 / 1.8925 * 100, 1 / 1.8925 * 100]])


def ternary_coordinates(percentages) -> np.ndarray:
    values = np.asarray(percentages, dtype=float).reshape(-1, 3)
    if not np.isfinite(values).all() or np.any(values < 0) or not np.allclose(values.sum(axis=1), 100):
        raise ValueError('Ternary percentages must be nonnegative and sum to 100.')
    # Columns Y/X/I; exact equilateral geometry instead of the 173.2 approximation.
    return np.column_stack(((values[:, 1] + values[:, 2] / 2) / 100 * 2 / sqrt(3),
                            values[:, 2] / 100 - 1))


def _triangle(topology, colour) -> FigureOutput:
    figure, axes = figure_axes((.13, .11, .775, .815))
    width = 2 / sqrt(3)
    axes.plot([0, width / 2, width, 0], [-1, 0, -1, -1], color='black', linewidth=.75)
    for percent in range(10, 100, 10):
        for fixed in range(3):
            points = np.zeros((2, 3))
            points[:, fixed] = percent
            other = [index for index in range(3) if index != fixed]
            points[0, other[0]], points[1, other[1]] = 100 - percent, 100 - percent
            axes.plot(*ternary_coordinates(points).T, color='red', linestyle=':', linewidth=.25)
    for label, point in (('Y', (-.05, -1)), ('X', (1.2, -1)), ('I', (.575, .03))):
        axes.text(*point, label)
    for values, label in ((CL2, '2'), (CL357, '3.57')):
        coordinates = ternary_coordinates(values)
        axes.plot(*coordinates.T, color=colour, linewidth=1)
        axes.text(*coordinates[-1], rf'$C_L = {label}$', fontsize=10)
    ni, ny, nx = topology.counts
    total = ni + ny + nx
    if total:
        axes.plot(*ternary_coordinates([ny / total * 100, nx / total * 100, ni / total * 100])[0],
                  'o', markerfacecolor=colour, markeredgecolor='black', markersize=12)
        ratios = f'Y:X:I = {ny/total:.2f}:{nx/total:.2f}:{ni/total:.2f}'
    else:
        axes.text(width / 2, -.5, 'No I/Y/X nodes after cleanup.', ha='center', fontsize=9,
                  bbox={'facecolor': 'white', 'edgecolor': 'none'})
        ratios = 'Y:X:I undefined (total=0)'
    axes.set(xlim=(-.056596561076222685, 1.2112970994554746), ylim=(-1, 0), aspect='equal')
    axes.set_axis_off()
    title(axes, 'Connectivity of traces\n' + ratios)
    return FigureOutput('FracPaQ2D_IYXtriangle', figure)


def render_connectivity(result: ConnectivityResult, config: AnalysisConfig) -> tuple[FigureOutput, ...]:
    topology = result.topology
    dataset = topology.dataset
    ni, ny, nx = topology.counts
    outputs = []
    with matlab_style():
        figure, axes = figure_axes(LEGEND_MAP_RECTANGLE)
        axes.add_collection(MultisampleLines([[n.point for n in t.nodes] for t in dataset.traces],
                                           colors='black', linewidths=.5, zorder=2))
        for label, nodes, colour in (('I', topology.i_nodes, 'blue'),
                                     ('X', topology.x_nodes, 'red'), ('Y', topology.y_nodes, 'lime')):
            if len(nodes.coordinates):
                axes.plot(*nodes.coordinates.T, 'o', color=colour, markerfacecolor=colour,
                          markersize=3, label=label, zorder=3)
        if axes.lines:
            legend(axes, outside_bottom=True, ncol=3)
        map_axes(axes, dataset, config)
        axes.grid(True)
        axes.set_title('Connectivity node types\n' + rf'$n_I={ni},\ n_Y={ny},\ n_X={nx}$',
                       fontsize=11, fontweight='bold')
        outputs.append(FigureOutput('FracPaQ2D_IYXnodes_traces', figure))
        palette = ListedColormap(matlab_rgb('hot', reverse=True))
        norm = Normalize(0, result.maximum or 1)
        for field, heading, label, basename in (
            (result.xy_heatmap, f'(X+Y)-nodes, n_X+n_Y={nx + ny}', 'Number of (X+Y)-nodes', 'XYnodes'),
            (result.i_heatmap, f'I-nodes, n_I={ni}', 'Number of I-nodes', 'Inodes'),
        ):
            figure, axes = figure_axes(COLOUR_MAP_RECTANGLE)
            axes.imshow(field.values, origin='lower', extent=field.extent, interpolation='nearest',
                        cmap=palette, norm=norm)
            map_axes(axes, dataset, config)
            bar = colourbar(axes, cmap=palette, norm=norm, ticks=[0] if result.maximum == 0 else None)
            bar.set_label(label)
            title(axes, heading)
            outputs.append(FigureOutput(f'FracPaQ2D_{basename}_traces_heat', figure))
        outputs.append(_triangle(topology, dataset.traces[0].colour))
    return tuple(outputs)
