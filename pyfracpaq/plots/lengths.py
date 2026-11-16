"""Seven basic Lengths figures, rendered identically for Qt and Agg."""

import logging

import numpy as np
from matplotlib.ticker import (LogFormatterMathtext, LogLocator, NullFormatter,
                               MaxNLocator, StrMethodFormatter)

from pyfracpaq.analysis.lengths import LengthResult
from pyfracpaq.domain.execution import AnalysisConfig
from pyfracpaq.plots.results import FigureOutput
from pyfracpaq.plots.style import figure_axes, matlab_style, square_marker, title
from pyfracpaq.plots.ticks import MatlabLocator

RECTANGLE = (.13, .11, .775, .815)
LOG_TICKS = np.array([1e-3, 1e-2, 1e-1, 1, 10, 100, 1000, 10000])


def _axes():
    figure, axes = figure_axes(RECTANGLE)
    axes.set_box_aspect(1)
    axes.grid(True)
    axes.set_axisbelow(True)
    return figure, axes


def _length_markers(axes, minimum: float, maximum: float, bottom: float, top: float,
                    diagonal: float | None = None) -> None:
    for value in (minimum, maximum):
        axes.plot([value, value], [bottom, top], color='red', linewidth=1)
    if diagonal is not None:
        axes.plot([diagonal, diagonal], [bottom, top], color='red',
                  linestyle='--', linewidth=1)


def render_histograms(result: LengthResult, config: AnalysisConfig
                      ) -> tuple[FigureOutput, ...]:
    outputs = []
    with matlab_style():
        for subject, histogram, stats in (
            ('Trace', result.trace_histogram, result.trace_statistics),
            ('Segment', result.segment_histogram, result.segment_statistics),
        ):
            figure, axes = _axes()
            upper = float(histogram.frequencies.max()) * 1.2
            axes.bar(histogram.centres, histogram.frequencies, width=histogram.bar_width,
                     facecolor=result.colour, edgecolor='black', linewidth=.5)
            _length_markers(axes, stats.minimum, stats.maximum, 0, upper)
            axes.set(xlim=(0, stats.maximum * 1.1), ylim=(0, upper),
                     xlabel=f'{subject} length, {result.unit}', ylabel='Frequency')
            left_colour, right_colour = (0., .447, .741), (.85, .325, .098)
            axes.yaxis.label.set_color(left_colour)
            axes.tick_params(axis='y', colors=left_colour)
            axes.spines['left'].set_color(left_colour)
            axes.yaxis.set_major_locator(MatlabLocator())
            axes.yaxis.set_major_formatter(StrMethodFormatter('{x:g}'))
            axes.grid(True, color=left_colour, alpha=.15)
            right = axes.twinx()
            right.set_ylim(0, upper / stats.count * 100)
            right.set_ylabel('Frequency, %', color=right_colour, labelpad=5.125)
            right.tick_params(axis='y', direction='in', colors=right_colour)
            right.spines['right'].set_color(right_colour)
            right.spines['left'].set_visible(False)
            right.yaxis.set_major_locator(MatlabLocator())
            right.yaxis.set_major_formatter(StrMethodFormatter('{x:g}'))
            title(axes, f'{subject} lengths, n={stats.count}')
            outputs.append(FigureOutput(f'FracPaQ2D_histo{subject.lower()}length', figure))
    return tuple(outputs)


def render_loglog(result: LengthResult, config: AnalysisConfig
                  ) -> tuple[FigureOutput, ...]:
    outputs = []
    with matlab_style():
        for subject, histogram, cumulative, stats in (
            ('Trace', result.trace_histogram, result.trace_complementary,
             result.trace_statistics),
            ('Segment', result.segment_histogram, result.segment_complementary,
             result.segment_statistics),
        ):
            for complementary in (False, True):
                figure, axes = _axes()
                centres = cumulative.centres if complementary else histogram.centres
                values = (cumulative.complementary if complementary
                          else histogram.frequencies)
                positive = values > 0
                axes.set(xscale='log', yscale='log')
                axes.yaxis.set_major_locator(LogLocator(base=10, subs=(1.,)))
                for axis in (axes.xaxis, axes.yaxis):
                    axis.set_major_formatter(LogFormatterMathtext(base=10, labelOnlyBase=True))
                    axis.set_minor_locator(LogLocator(base=10, subs=tuple(range(2, 10))))
                    axis.set_minor_formatter(NullFormatter())
                axes.grid(True, which='minor', linestyle=':', linewidth=.5,
                          color=(25/255,)*3, alpha=63/255)
                axes.plot(centres[positive], values[positive], linestyle='none', marker=square_marker(),
                          color=result.colour, markerfacecolor=result.colour,
                          linewidth=1, markeredgewidth=1)
                upper = (stats.count if complementary else float(values.max())) * 1.2
                _length_markers(axes, stats.minimum, stats.maximum, .1, upper,
                                result.maximum_possible_length if complementary else None)
                maximum = (max(stats.maximum, result.maximum_possible_length)
                           if complementary else stats.maximum)
                minimum = (min(stats.minimum, result.maximum_possible_length)
                           if complementary else stats.minimum)
                # Do not reverse/clip the curve when a polyline exceeds the diagonal.
                axes.set_xticks(LOG_TICKS)
                axes.set(xlim=(minimum * .9, maximum * 1.1), ylim=(.1, upper),
                         xlabel=f'{subject} length, {result.unit}',
                         ylabel='Cumulative frequency, C(L)' if complementary
                         else 'Frequency, n(L)')
                if not positive.any():
                    axes.text(.5, .5, 'No positive complementary frequencies.',
                              ha='center', va='center', transform=axes.transAxes, fontsize=9)
                logging.getLogger(__name__).info(
                    '%s %s: %s zero-frequency bins omitted from log display.',
                    subject, 'complementary distribution' if complementary else 'density',
                    int(np.count_nonzero(~positive)))
                family = 'Cumulative distribution' if complementary else 'Density distribution'
                title(axes, f'{family} of {subject.lower()} lengths, n={stats.count}')
                suffix = '' if complementary else 'density'
                outputs.append(FigureOutput(
                    f'FracPaQ2D_loglogplot{subject.lower()}length{suffix}', figure))
    return tuple(outputs)


def render_crossplot(result: LengthResult, config: AnalysisConfig
                      ) -> tuple[FigureOutput, ...]:
    with matlab_style():
        figure, axes = _axes()
        axes.plot(result.cross_angles, result.cross_lengths, linestyle='none', marker=square_marker(),
                  color=result.colour, markerfacecolor=result.colour, markersize=2)
        for value, linestyle in ((result.segment_statistics.minimum, '-'),
                                  (result.segment_statistics.maximum, '-'),
                                  (result.maximum_possible_length, '--')):
            axes.plot([0, 360], [value, value], color='red', linewidth=1,
                      linestyle=linestyle)
        axes.set(xlim=(-10, 370), ylim=(0, result.segment_statistics.maximum * 1.1),
                 xlabel='Trace segment angle, degrees',
                 ylabel=f'Trace segment length, {result.unit}')
        axes.set_xticks(np.arange(0, 361, 60))
        title(axes, f'Trace segment lengths versus angles, n={result.segment_statistics.count}')
    return (FigureOutput('FracPaQ2D_crossplotsegmentlengthangle', figure),)
