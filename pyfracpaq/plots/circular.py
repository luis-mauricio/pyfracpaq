"""Scan windows and local P21/P20 heatmaps with explicit MATLAB axes."""

import numpy as np
from matplotlib.collections import EllipseCollection
from matplotlib.colors import ListedColormap, Normalize

from pyfracpaq.analysis.circular import CircularResult
from pyfracpaq.analysis.palettes import matlab_rgb
from pyfracpaq.domain.execution import AnalysisConfig
from pyfracpaq.plots.colourbars import colourbar
from pyfracpaq.plots.results import FigureOutput
from pyfracpaq.plots.raster import MultisampleLines
from pyfracpaq.plots.style import COLOUR_MAP_RECTANGLE, figure_axes, map_axes, matlab_style, title


def render_circular(result: CircularResult, config: AnalysisConfig,
                    kind: str) -> tuple[FigureOutput, ...]:
    if kind not in ('intensity', 'density'):
        raise ValueError(f'Unknown circular map: {kind}.')
    dataset, grid = result.dataset, result.grid
    outputs = []
    first = next(i for i in config.selected if i in ('MAP-07', 'MAP-08'))
    own_id = 'MAP-07' if kind == 'intensity' else 'MAP-08'
    with matlab_style():
        if config.value('checkbox_showcircles') and first == own_id:
            figure, axes = figure_axes((.13, .11, .775, .815))
            axes.add_collection(MultisampleLines(
                [[n.point for n in trace.nodes] for trace in dataset.traces],
                colors=[dataset.traces[0].colour], linewidths=.75, zorder=3))
            diameters = np.full(len(grid.x) * len(grid.y), 2 * grid.radius)
            axes.add_collection(EllipseCollection(
                diameters, diameters, np.zeros_like(diameters), units='xy',
                offsets=grid.centres, offset_transform=axes.transData,
                facecolors='none', edgecolors='red', linewidths=.25, zorder=4))
            map_axes(axes, dataset, config)
            title(axes, f'Mapped trace segments, n={dataset.n_segments}')
            outputs.append(FigureOutput('FracPaQ2D_scancircle', figure))
        figure, axes = figure_axes(COLOUR_MAP_RECTANGLE)
        values = result.intensity if kind == 'intensity' else result.density
        maximum = float(values.max())
        # The original [0,0] caxis is invalid for empty windows. Preserve zero
        # arrays and show a single zero tick; only the display norm needs a span.
        norm = Normalize(0, maximum if maximum > 0 else 1)
        palette = ListedColormap(matlab_rgb('hot', reverse=True))
        axes.imshow(values, cmap=palette, norm=norm, origin='lower',
                    interpolation='nearest', extent=grid.extent)
        map_axes(axes, dataset, config)
        subject, symbol, power = (('Intensity', 'P21', 1) if kind == 'intensity'
                                  else ('Density', 'P20', 2))
        title(axes, f'Estimated {subject} of segments ({symbol})')
        bar = colourbar(axes, cmap=palette, norm=norm,
                        ticks=[0] if maximum == 0 else None)
        unit = 'metre' if dataset.pixels_per_metre is not None else 'pixel'
        bar.set_label(f'{subject} of segments ({symbol}), {unit}$^{{-{power}}}$')
        outputs.append(FigureOutput(f'FracPaQ2D_{kind}{symbol}', figure))
    return tuple(outputs)
