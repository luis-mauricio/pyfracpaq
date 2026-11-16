"""Source-named ALONG/FROM scatter plots and the coupled circular profile map."""

from dataclasses import replace

import numpy as np
from matplotlib.patches import Circle
from matplotlib.ticker import StrMethodFormatter

from pyfracpaq.analysis.profiles import CIRCULAR, GraphResult
from pyfracpaq.domain.execution import AnalysisConfig
from pyfracpaq.geometry.primitives import bounds_from_points
from pyfracpaq.plots.results import FigureOutput
from pyfracpaq.plots.raster import MultisampleLines
from pyfracpaq.plots.style import LEGEND_MAP_RECTANGLE, figure_axes, legend, map_axes, matlab_style, square_marker
from pyfracpaq.plots.ticks import automatic_limits

NAMES = {'GRA-03': ('tracelengthalonggraph', 'Trace lengths', 'Trace length'),
         'GRA-04': ('segmentlengthalonggraph', 'Segment lengths', 'Segment length'),
         'GRA-05': ('segmentanglealonggraph', 'Segment angles', 'Segment angle, degrees'),
         'GRA-10': ('tracelengthfromgraph', 'Trace lengths', 'Trace length'),
         'GRA-11': ('segmentlengthfromgraph', 'Segment lengths', 'Segment length'),
         'GRA-12': ('segmentanglefromgraph', 'Segment angles', 'Segment angle, degrees')}


def _nice_limits(values):
    low, high = float(values.min()), float(values.max())
    if low == high:
        pad = max(1., abs(low) * .05)
        return low - pad, high + pad
    return automatic_limits(values)


def _scatter(x, y, *, basename, heading, xlabel, ylabel, angle=False, along=False,
              line_length=1):
    figure, axes = figure_axes((.13, .11, .775, .815))
    axes.plot(x, y, 'o', color='blue', markerfacecolor='blue', markersize=6, linestyle='none')
    axes.set(xlabel=xlabel, ylabel=ylabel)
    axes.yaxis.set_major_formatter(StrMethodFormatter('{x:g}'))
    axes.set_title(heading, fontsize=11, fontweight='bold', pad=3.36 if '$' in heading else 3)
    if along:
        axes.set_xlim(0, float(np.max(x)) if len(x) and np.max(x) > 0 else line_length)
        if not angle:
            high = float(np.max(y)) if len(y) else 0
            axes.set_ylim(0, high if high > 0 else 1)
            if high == 0:
                axes.set_yticks([0])
    elif len(x):
        axes.set_xlim(*_nice_limits(np.asarray(x)))
        if not angle:
            axes.set_ylim(*_nice_limits(np.asarray(y)))
    if angle:
        axes.set_ylim(0, 180)
    if not len(x):
        axes.text(.5, .5, 'No noncoincident intersections with the selected line.',
                  transform=axes.transAxes, ha='center', va='center', fontsize=9)
    axes.grid(True)
    return FigureOutput('guiFracPaQ2D_' + basename, figure)


def _circle_map(result, config):
    figure, axes = figure_axes(LEGEND_MAP_RECTANGLE)
    dataset, line, circles = result.dataset, result.line, result.circles
    axes.add_collection(MultisampleLines([[n.point for n in t.nodes] for t in dataset.traces],
                                       colors=[dataset.traces[0].colour], linewidths=.75))
    axes.plot([line.start[0], line.end[0]], [line.start[1], line.end[1]], color='magenta', linewidth=1)
    for point, colour, label in ((line.start, 'cyan', 'Point 1'), (line.end, 'lime', 'Point 2')):
        axes.plot(*point, marker=square_marker(), color=colour, markerfacecolor=colour, markersize=6,
                  linestyle='-', linewidth=1, label=label)
    for centre in circles.centres:
        axes.add_patch(Circle(centre, circles.radius, fill=False, edgecolor='red', linewidth=.5))
    envelope = bounds_from_points([node.point for node in dataset.nodes])
    map_axes(axes, replace(dataset, bounds=envelope), config)
    legend(axes, outside_bottom=True, ncol=2)
    axes.set_title(f'Mapped trace segments, n={dataset.n_segments}', fontsize=11, fontweight='bold', pad=2.64)
    return FigureOutput('guiFracPaQ2D_graphtracemap', figure)


def render_graph(result: GraphResult, config: AnalysisConfig,
                  identifier: str) -> tuple[FigureOutput, ...]:
    unit = result.dataset.length_unit
    with matlab_style():
        if identifier in CIRCULAR:
            first = next(key for key in CIRCULAR if key in config.selected)
            if identifier != first:
                return ()
            circular = result.circles
            singular = 'metre' if unit == 'metres' else 'pixel'
            figures = [_circle_map(result, config)]
            for values, name, subject, code, power in (
                (circular.intensity, 'intensity', 'Intensity', 'P21', -1),
                (circular.density, 'density', 'Density', 'P20', -2),
            ):
                figures.append(_scatter(circular.distances, values,
                    basename=name + 'alonggraph',
                    heading=f'Estimated {name} ({code}), {singular}' + rf'$^{{{power}}}$',
                    xlabel=f'Distance along line from point 1, {unit}',
                    ylabel=f'{subject}, {unit}' + rf'$^{{{power}}}$',
                    along=True, line_length=result.line.length))
            return tuple(figures)
        basename, heading, subject = NAMES[identifier]
        along = identifier in ('GRA-03', 'GRA-04', 'GRA-05')
        angle = identifier in ('GRA-05', 'GRA-12')
        if along:
            x = result.along.distances
            y = getattr(result.along, {'GRA-03': 'trace_lengths', 'GRA-04': 'segment_lengths',
                                      'GRA-05': 'raw_angles'}[identifier])
        else:
            arrays = result.dataset.as_arrays()
            x = result.trace_distances if identifier == 'GRA-10' else result.segment_distances
            y = arrays.trace_lengths if identifier == 'GRA-10' else arrays.raw_angles if angle else arrays.segment_lengths
        return (_scatter(x, y, basename=basename, heading=heading,
            xlabel=(f'Distance along line from point 1, {unit}' if along else f'Perpendicular distance from line, {unit}'),
            ylabel=subject if angle else f'{subject}, {unit}', angle=angle, along=along,
            line_length=result.line.length),)
