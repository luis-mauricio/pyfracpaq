"""GUI semivariogram and the plotting half of the complementary variogram API."""

import numpy as np

from pyfracpaq.analysis.variogram import VariogramResult, experimental_variogram
from pyfracpaq.domain.execution import AnalysisConfig
from pyfracpaq.plots.results import FigureOutput
from pyfracpaq.plots.style import figure_axes, matlab_style, square_marker, title
from pyfracpaq.plots.ticks import automatic_limits


def render_variogram(length_result, config: AnalysisConfig) -> tuple[FigureOutput, ...]:
    result = length_result.variogram
    with matlab_style():
        figure, axes = figure_axes((.13, .11, .775, .815))
        axes.plot(result.distance, result.values, color='r', marker=square_marker(), linestyle='none', markersize=6,
                  markerfacecolor='none')
        if np.isfinite(result.values).any():
            axes.set_xlim(*automatic_limits(result.distance))
            axes.set_ylim(*automatic_limits(result.values))
        axes.set(xlabel=f'h, {length_result.unit}', ylabel=r'$\gamma$ (h)')
        if not np.isfinite(result.values).any():
            axes.text(.5, .5, 'No contributing pairs within the selected lag range.',
                      transform=axes.transAxes, ha='center', va='center', fontsize=9)
        axes.grid(True)
        title(axes, f'Semivariogram, n={len(result.sample_indices)}')
    return (FigureOutput('FracPaQ2D_segmentlength_variogram', figure),)


def variogram(coordinates, values, *, plotit: bool = False, **options
               ) -> tuple[VariogramResult, FigureOutput | None]:
    """Advanced API: compute the source options, optionally construct its figure.

    Call on the UI thread when requesting a figure. The numerical core stays
    graphics-free; callers decide how to show/export the returned figure.
    MATLAB's ``type`` option is spelled ``kind`` in the numerical Python API.
    """
    result = experimental_variogram(coordinates, values, **options)
    if not plotit:
        return result, None
    with matlab_style():
        if result.theta is None:
            figure, axes = figure_axes((.13, .11, .775, .815))
            axes.plot(result.distance, result.values, 'o--' if result.counts is not None else '.')
            axes.set(xlabel='h', ylabel=r'$\gamma$ (h)')
        else:
            from matplotlib.figure import Figure
            figure = Figure()
            axes = figure.add_axes((.13, .11, .775, .815), projection='3d')
            if result.counts is not None:
                radius, theta = np.meshgrid(result.distance, result.theta, indexing='ij')
                axes.plot_surface(radius * np.cos(theta), radius * np.sin(theta), result.values)
            else:
                axes.scatter(result.distance * np.cos(result.theta), result.distance * np.sin(result.theta), result.values)
            axes.set(xlabel='h y-direction', ylabel='h x-direction', zlabel=r'$\gamma$ (h)')
        axes.set_title('directional variogram' if result.theta is not None else '(Semi-)Variogram')
    return result, FigureOutput('FracPaQ2D_variogram_api', figure)
