"""Six source-named MLE figures from frozen fit and assessment results."""

import numpy as np
from math import floor,log10

from pyfracpaq.analysis.mle import survival
from pyfracpaq.domain.execution import AnalysisConfig
from pyfracpaq.plots.results import FigureOutput
from pyfracpaq.plots.style import figure_axes, legend, matlab_style, square_marker, title
from pyfracpaq.plots.ticks import automatic_limits
from pyfracpaq.plots.annotations import parameter_box

NAMES = {'power_law': ('Power Law', 'PowerLaw'),
         'exponential': ('Exponential', 'Exponential'),
         'lognormal': ('Lognormal', 'LogNormal')}


def _number(value):
    precision=max(5,floor(log10(abs(value)))+5) if value else 5
    return f'{value:.{precision}g}'


def render_mle(length_result, config: AnalysisConfig) -> tuple[FigureOutput, ...]:
    result = length_result.mle
    outputs = []
    with matlab_style():
        for population, records in (('trace', result.trace), ('segment', result.segment)):
            for record in records:
                fit = record.fit
                heading, suffix = NAMES[fit.kind]
                figure, axes = figure_axes((.13, .11, .775, .815))
                # Plot* uses unique observed lengths; fitting and K-S retain all
                # repetitions. Preserve this source display convention explicitly.
                observed = np.unique(fit.sample.original)
                frequencies = np.arange(len(observed), 0, -1) / len(observed)
                scale = frequencies[np.searchsorted(observed, fit.xmin)]
                estimated = survival(fit.tail, fit.kind, fit.xmin, fit.parameters) * scale
                axes.set_xscale('linear' if fit.kind == 'exponential' else 'log')
                axes.set_yscale('linear' if fit.kind == 'lognormal' else 'log')
                axes.plot(observed, frequencies, linestyle=':', marker=square_marker(), color=result.colour,
                          markerfacecolor=result.colour, markersize=8, label='Observed Data')
                positive = estimated > 0 if fit.kind != 'lognormal' else np.ones(len(estimated), dtype=bool)
                axes.plot(fit.tail[positive], estimated[positive], '-.', color='black',
                          linewidth=1 if fit.kind == 'exponential' else 2, label='Estimated Data')
                axes.axvline(fit.sample.retained[-1], color='red', linestyle='--', label='Upper cut-off')
                axes.axvline(fit.sample.retained[0], color='red', linestyle='--', label='Lower cut-off')
                if fit.kind=='exponential':
                    axes.set_xlim(*automatic_limits(observed))
                    axes.set_ylim(1e-4,1)
                else:
                    axes.set_xlim(float(observed[0]),float(observed[-1]))
                    axes.set_ylim((min(.001,float(frequencies[-1])),1) if fit.kind=='power_law' else (0,1))
                axes.set(xlabel=f'Length, {result.unit}', ylabel=r'Pr(l $\geq$ l)')
                axes.grid(True)
                if axes.get_xscale() == 'log':
                    axes.xaxis.grid(True, which='minor', linestyle=':', linewidth=.5,
                                    color=(25/255,)*3, alpha=63/255)
                if axes.get_yscale() == 'log':
                    axes.yaxis.grid(True, which='minor', linestyle=':', linewidth=.5,
                                    color=(25/255,)*3, alpha=63/255)
                axes.set_axisbelow(True)
                title(axes, f'{heading} Distribution MLE, {population} lengths')
                legend(axes, loc='upper right')
                p = dict(fit.parameters)
                if fit.kind == 'power_law':
                    parameters = rf'$\alpha = {_number(p["alpha"])},\ \mathit{{x_{{min}}}} = {_number(fit.xmin)}$'
                elif fit.kind == 'exponential':
                    parameters = rf'$\lambda = {_number(p["lambda"])}$'
                else:
                    parameters = rf'$\mu = {_number(p["mu"])},\ \sigma = {_number(p["sigma"])}$'
                parameter_box(figure,parameters)
                outputs.append(FigureOutput(f'FracPaQ2D_{population}lengthsFitting{suffix}', figure))
    return tuple(outputs)
