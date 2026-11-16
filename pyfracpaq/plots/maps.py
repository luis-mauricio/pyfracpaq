"""The four basic map renderers, shared by Qt and noninteractive export."""

import numpy as np
from matplotlib.colors import ListedColormap, LogNorm
from matplotlib.collections import PathCollection
from matplotlib.markers import MarkerStyle
from matplotlib.transforms import IdentityTransform

from pyfracpaq.analysis.compatibility import matlab_round
from pyfracpaq.analysis.maps import MapResult
from pyfracpaq.analysis.palettes import cmocean
from pyfracpaq.domain.execution import AnalysisConfig
from pyfracpaq.plots.colourbars import colourbar
from pyfracpaq.plots.results import FigureOutput
from pyfracpaq.plots.raster import MultisampleLines
from pyfracpaq.plots.style import (
    COLOUR_MAP_RECTANGLE, figure_axes, map_axes, matlab_style, square_marker, strike_colourbar, title,
)


def render_map(result: MapResult, config: AnalysisConfig) -> tuple[FigureOutput, ...]:
    dataset, kind = result.dataset, result.kind
    arrays = dataset.as_arrays()
    with matlab_style():
        rectangle = (COLOUR_MAP_RECTANGLE if kind != 'traces'
                     else (.13, .11, .775, .815))
        figure, axes = figure_axes(rectangle)
        paths = ([np.array([n.point for n in trace.nodes]) for trace in dataset.traces]
                 if kind in ('traces', 'trace_length')
                 else arrays.segment_coordinates.reshape(-1, 2, 2))
        if kind == 'traces':
            colour = dataset.traces[0].colour
            lines=MultisampleLines(paths, colors=[colour], linewidths=.75, zorder=3)
            axes.add_collection(lines)
            if config.value('checkbox_shownodes'):
                # Retain the native painter order: two endpoints then midpoint
                # for each segment, followed by that trace's halfway point.
                # One collection avoids thousands of individual line artists.
                circle=MarkerStyle('o');square=square_marker()
                circle_path=circle.get_path().transformed(circle.get_transform())
                square_path=square.get_path().transformed(square.get_transform())
                points=[];paths=[];sizes=[];colours=[]
                for trace in dataset.traces:
                    for segment in trace.segments:
                        points.extend((segment.start.point,segment.end.point,segment.midpoint))
                        paths.extend((circle_path,circle_path,square_path))
                        sizes.extend((16,16,36));colours.extend(('black','black','red'))
                    points.append(trace.midpoint);paths.append(circle_path);sizes.append(36);colours.append('red')
                markers=PathCollection(paths,sizes=sizes,offsets=points,offset_transform=axes.transData,
                    facecolors='none',edgecolors=colours,linewidths=.5,zorder=4,clip_on=False)
                markers.set_transform(IdentityTransform());axes.add_collection(markers)
            heading = (f'Mapped traces (n={dataset.n_traces}), segments '
                       f'(n={dataset.n_segments}) & nodes (n={dataset.n_nodes})')
            basename = 'FracPaQ2D_tracemap'
        elif kind == 'strike':
            palette = cmocean('phase', 180)
            axes.add_collection(MultisampleLines(paths, colors=palette[result.colour_indices],
                                                linewidths=.75, zorder=3))
            strike_colourbar(axes, 180)
            heading = f'Segment strike map, n={dataset.n_segments}'
            basename = 'FracPaQ2D_segmentstrikemap'
        else:
            is_trace = kind == 'trace_length'
            values = arrays.trace_lengths if is_trace else arrays.segment_lengths
            maximum = float(values.max())
            palette = cmocean('haline', 256)
            # Q-17: preserve linear colour lookup independently of the log bar.
            axes.add_collection(MultisampleLines(paths, colors=palette[result.colour_indices],
                                                linewidths=.75, zorder=3))
            ticks = maximum / np.array([1000, 12, 3, 1])
            bar = colourbar(axes, cmap=ListedColormap(palette),
                            norm=LogNorm(maximum / 1000, maximum), ticks=ticks)
            bar.minorticks_off()
            bar.set_ticklabels([f'{value:.0f}' for value in matlab_round(ticks)])
            subject = 'Trace' if is_trace else 'Segment'
            bar.set_label(f'{subject} length, {dataset.length_unit}')
            heading = f'{subject} length map, n={len(values)}'
            basename = f'FracPaQ2D_{"trace" if is_trace else "segment"}lengthmap'
        map_axes(axes, dataset, config)
        title(axes, heading)
    outputs = (FigureOutput(basename, figure),)
    map_ids = {'traces': 'MAP-01', 'trace_length': 'MAP-04',
               'segment_length': 'MAP-05', 'strike': 'MAP-06'}
    first_map = next((i for i in config.selected if i in map_ids.values()), None)
    if len(dataset.colours) > 1 and first_map == map_ids[kind]:
        extra = render_multicolour(dataset, config)
        outputs = outputs + (extra,) if kind == 'traces' else (extra,) + outputs
    return outputs


def render_multicolour(dataset, config: AnalysisConfig) -> FigureOutput:
    with matlab_style():
        figure, axes = figure_axes((.13, .11, .775, .815))
        axes.add_collection(MultisampleLines(
            [[n.point for n in trace.nodes] for trace in dataset.traces],
            colors=[trace.colour for trace in dataset.traces], linewidths=.75, zorder=3))
        map_axes(axes, dataset, config)
        title(axes, f'Multicolour traces (n={dataset.n_traces}), segments '
              f'(n={dataset.n_segments}) & nodes (n={dataset.n_nodes})')
    return FigureOutput('FracPaQ2D_tracemap_multicolour', figure)
