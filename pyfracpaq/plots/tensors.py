"""Source-named north-up, clockwise crack/permeability polar figures."""

import numpy as np
from matplotlib.ticker import FuncFormatter

from pyfracpaq.analysis.tensors import PermeabilityResult
from pyfracpaq.domain.execution import AnalysisConfig
from pyfracpaq.plots.results import FigureOutput
from pyfracpaq.plots.style import MatlabFigure, legend, matlab_style
from pyfracpaq.plots.ticks import decimal_step


def _polar_axes(*, crack=False):
    figure = MatlabFigure()
    # Calibrated print composition: crack legend reserves space below its circle.
    rectangle = (.1299, .1759, .775, .74417) if crack else (.13, .11, .775, .815)
    axes = figure.add_axes(rectangle, projection='polar')
    axes.set_theta_zero_location('N')
    axes.set_theta_direction(-1)
    axes.set_thetagrids(np.arange(0, 360, 30))
    axes.tick_params(labelsize=10)
    axes.tick_params(axis='x',pad=0)
    axes.set_rlabel_position(10)
    axes.grid(True, color=(.15, .15, .15), alpha=.15, linewidth=.5)
    axes.spines['polar'].set_color((.15, .15, .15, .15))
    axes.spines['polar'].set_linewidth(.5)
    return figure, axes


def _radial_scale(axes, values):
    maximum = float(np.max(values))
    if maximum <= 0:
        axes.set_ylim(0, 1)
        axes.set_yticks([0])
    else:
        step = decimal_step(maximum)
        upper = np.ceil(maximum / step) * step
        step = decimal_step(upper, 5)
        axes.set_yticks(np.arange(int(np.floor(upper / step + 1e-12)) + 1) * step)
        axes.set_ylim(0, upper)
    def label(value, _):
        if value == 0:
            return '0'
        exponent = int(np.floor(np.log10(abs(value))))
        if exponent < -3 or exponent >= 4:
            return rf'${value / 10. ** exponent:g}\times10^{{{exponent}}}$'
        return f'{value:g}'
    axes.yaxis.set_major_formatter(FuncFormatter(label))
    # PolarAxes hides the origin tick; the MATLAB radial ruler labels it.
    axes.text(0, 0, '0', ha='center', va='center', fontsize=10)


def _polar_title(axes, text, *, crack=False):
    axes.set_title(text, fontsize=11, fontweight='bold', pad=6,
                   y=1.061 if crack else 1.078)


def render_crack_tensor(angular_result, config: AnalysisConfig) -> tuple[FigureOutput, ...]:
    result = angular_result.crack
    with matlab_style():
        figure, axes = _polar_axes(crack=True)
        axes.plot(result.alpha, result.zero, color='magenta', linewidth=1.5, label=r'$0^{th}$')
        for rank, colour, label in zip(result.ranks, ('blue', 'red', 'lime'),
                                        (r'$2^{nd}$', r'$4^{th}$', r'$8^{th}$')):
            axes.plot(result.alpha, rank.polar, color=colour, linewidth=1.5, label=label)
        _radial_scale(axes, result.zero)
        legend(axes, outside_bottom=True, ncol=4)
        _polar_title(axes, f'Crack tensors, n={len(result.lengths)}', crack=True)
    return (FigureOutput('FracPaQ2D_cracktensor', figure),)


def render_permeability(result: PermeabilityResult, config: AnalysisConfig
                        ) -> tuple[FigureOutput, ...]:
    with matlab_style():
        figure, axes = _polar_axes()
        axes.plot(result.alpha, result.polar, color='blue', linewidth=1.5)
        _radial_scale(axes, result.polar)
        unit = result.unit.replace('^2', r'$^2$')
        _polar_title(axes, f'Permeability tensor, {unit}')
    return (FigureOutput('FracPaQ2D_permeability_polar', figure),)
