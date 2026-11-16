"""Three block figures sharing the computed scientific raster statistics."""

from dataclasses import replace


from pyfracpaq.geometry.primitives import bounds_from_points

from pyfracpaq.plots.results import FigureOutput
from pyfracpaq.plots.raster import MultisampleLines
from pyfracpaq.plots.style import figure_axes, map_axes, matlab_style, square_marker, title


def render_blocks(length_result, config):
    result = length_result.blocks
    count = len(result.areas)
    colour = result.dataset.traces[0].colour
    unit = result.dataset.length_unit
    outputs = []
    with matlab_style():
        figure, axes = figure_axes((.13, .11, .775, .815))
        axes.add_collection(MultisampleLines([[node.point for node in trace.nodes]
                            for trace in result.dataset.traces], colors=[colour], linewidths=.75))
        axes.plot(result.centroids[:, 0], result.centroids[:, 1], 'ro', markersize=6,
                  markerfacecolor='red', linestyle='none')
        envelope = bounds_from_points([node.point for node in result.dataset.nodes])
        map_axes(axes, replace(result.dataset, bounds=envelope), config)
        title(axes, f'Block centroids, n={count}')
        if not count:
            _empty(axes, 'No enclosed white components.')
        outputs.append(FigureOutput('FracPaQ2D_blocksizecentroidmap', figure))
        figure, axes = figure_axes((.13, .11, .775, .815))
        axes.set_box_aspect(1)
        axes.set(xscale='log', yscale='log', xlabel=f'Block size (area), {unit}' + r'$^2$',
                 ylabel='Cumulative frequency')
        if count:
            cumulative = result.complementary
            positive = cumulative.complementary > 0
            axes.plot(cumulative.centres[positive], cumulative.complementary[positive],
                      marker=square_marker(), linestyle='none', color=colour, markerfacecolor=colour)
            axes.set(xlim=(float(result.areas.min()) * .9, float(result.areas.max()) * 1.1),
                     ylim=(.1, count * 1.2))
            if not positive.any():
                _empty(axes, 'No positive complementary frequencies (constant block area).')
        else:
            _empty(axes, 'No enclosed white components.')
        axes.grid(True, which='both')
        title(axes, f'Block sizes (areas), n={count}')
        outputs.append(FigureOutput('FracPaQ2D_blocksizeloglog', figure))
        figure, axes = figure_axes((.13, .11, .775, .815))
        axes.set_box_aspect(1)
        if count:
            histogram = result.histogram
            axes.bar(histogram.centres, histogram.frequencies / count * 100,
                     width=histogram.bar_width, facecolor=colour, edgecolor='black', linewidth=.5)
            axes.set_xlim(0, float(result.areas.max()) * 1.1)
        else:
            _empty(axes, 'No enclosed white components.')
        axes.set(xlabel=f'Block size (area), {unit}' + r'$^2$', ylabel='Frequency, %')
        axes.grid(True)
        title(axes, f'Block sizes (areas), n={count}')
        outputs.append(FigureOutput('FracPaQ2D_blocksizehisto', figure))
    return tuple(outputs)


def _empty(axes, text):
    axes.text(.5, .5, text, ha='center', va='center', transform=axes.transAxes, fontsize=9,
              wrap=True)
