"""Single registry for selection, validation and analysis availability.

The GUI is complete before all scientific implementations are available.
Pending entries have no compute callable and never return fabricated data.
"""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from math import isfinite
import re
from typing import TYPE_CHECKING

from pyfracpaq.domain import Dataset
from pyfracpaq.domain.execution import (
    AnalysisConfig, AnalysisResult, FieldError, RunContext,
)

if TYPE_CHECKING:
    from pyfracpaq.plots.results import FigureOutput

Progress = Callable[[int, str], None]
NUMERIC_TEXT = re.compile(
    r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z',
)
Compute = Callable[[Dataset, RunContext, Progress], object]
Render = Callable[[object, AnalysisConfig], tuple['FigureOutput', ...]]


@dataclass(frozen=True, slots=True)
class Parameter:
    name: str
    minimum: float | None = None
    maximum: float | None = None
    integer: bool = False
    positive: bool = False
    nonzero: bool = False
    choices: tuple[str, ...] = ()
    number_list: bool = False

    def validate(self, config: AnalysisConfig) -> None:
        text = str(config.value(self.name))
        if self.choices:
            if text not in self.choices:
                raise FieldError(self.name,
                                 f'Choose one of: {", ".join(self.choices)}.')
            return
        tokens = text.split() if self.number_list else [text]
        if not tokens:
            raise FieldError(self.name, 'Enter a nonempty list of numbers.')
        for token in tokens:
            if NUMERIC_TEXT.fullmatch(token) is None:
                raise FieldError(self.name, 'Enter a valid numeric value.')
            try:
                value = float(token)
            except ValueError as error:
                raise FieldError(self.name, 'Enter a valid number.') from error
            if not isfinite(value):
                raise FieldError(self.name, 'The value must be finite.')
            if self.integer and not value.is_integer():
                raise FieldError(self.name, 'Enter a whole number.')
            if self.positive and value <= 0:
                raise FieldError(self.name, 'The value must be positive.')
            if self.nonzero and abs(value) < 1e-8:
                raise FieldError(self.name, 'The value must be nonzero.')
            if self.minimum is not None and value < self.minimum:
                raise FieldError(self.name,
                                 f'The value must be at least {self.minimum:g}.')
            if self.maximum is not None and value > self.maximum:
                raise FieldError(self.name,
                                 f'The value must be at most {self.maximum:g}.')


NORTH = Parameter('edit_degfromnorth', -360, 360)
LENGTH_BINS = Parameter('popupmenu_histolengthbins', choices=('10', '20', '30', '50'))
CIRCLES = Parameter('edit_numscancircles', 2, integer=True)
STRESS = (
    Parameter('edit_sigma1', nonzero=True),
    Parameter('edit_sigma2', nonzero=True),
    Parameter('edit_thetasigma1', 0, 180),
    Parameter('edit_C0', 0), Parameter('edit_Pf', 0), Parameter('edit_mu', 0),
    NORTH,
)


@dataclass(frozen=True, slots=True)
class AnalysisSpec:
    id: str
    checkbox: str
    label: str
    parameters: tuple[Parameter, ...] = ()
    compute: Compute | None = None
    render: Render | None = None
    requires: tuple[str, ...] = ()
    cache_key: str | None = None
    cooperative: bool = False

    @property
    def available(self) -> bool:
        return self.compute is not None


def default_specs() -> tuple[AnalysisSpec, ...]:
    from pyfracpaq.analysis.angles import compute_angles
    from pyfracpaq.analysis.maps import compute_map
    from pyfracpaq.analysis.lengths import compute_lengths
    from pyfracpaq.analysis.circular import compute_circular
    from pyfracpaq.analysis.connectivity import compute_connectivity
    from pyfracpaq.analysis.tensors import compute_permeability
    from pyfracpaq.analysis.stability import compute_stability
    from pyfracpaq.analysis.profiles import compute_graphs, ALONG, CIRCULAR, FROM
    from pyfracpaq.analysis.wavelets import compute_wavelets

    # Rendering imports Matplotlib only when requested on the GUI thread.
    def map_renderer(data, config):
        from pyfracpaq.plots.maps import render_map
        return render_map(data, config)

    def histogram_renderer(data, config):
        from pyfracpaq.plots.angles import render_histogram
        return render_histogram(data, config)

    def rose_renderer(data, config):
        from pyfracpaq.plots.angles import render_rose
        return render_rose(data, config)

    def length_histogram_renderer(data, config):
        from pyfracpaq.plots.lengths import render_histograms
        return render_histograms(data, config)

    def loglog_renderer(data, config):
        from pyfracpaq.plots.lengths import render_loglog
        return render_loglog(data, config)

    def crossplot_renderer(data, config):
        from pyfracpaq.plots.lengths import render_crossplot
        return render_crossplot(data, config)

    def mle_renderer(data, config):
        from pyfracpaq.plots.mle import render_mle
        return render_mle(data, config)

    def connectivity_renderer(data, config):
        from pyfracpaq.plots.connectivity import render_connectivity
        return render_connectivity(data, config)

    def crack_renderer(data, config):
        from pyfracpaq.plots.tensors import render_crack_tensor
        return render_crack_tensor(data, config)

    def permeability_renderer(data, config):
        from pyfracpaq.plots.tensors import render_permeability
        return render_permeability(data, config)

    def stability_renderer(kind):
        def render(data, config):
            from pyfracpaq.plots.stability import render_stability
            return render_stability(data, config, kind)
        return render

    def intensity_renderer(data, config):
        from pyfracpaq.plots.circular import render_circular
        return render_circular(data, config, 'intensity')

    def variogram_renderer(data, config):
        from pyfracpaq.plots.variogram import render_variogram
        return render_variogram(data, config)

    def blocks_renderer(data, config):
        from pyfracpaq.plots.blocks import render_blocks
        return render_blocks(data, config)

    def wavelet_renderer(data, config):
        from pyfracpaq.plots.wavelets import render_wavelets
        return render_wavelets(data, config)

    def graph_renderer(identifier):
        def render(data, config):
            from pyfracpaq.plots.profiles import render_graph
            return render_graph(data, config, identifier)
        return render

    def density_renderer(data, config):
        from pyfracpaq.plots.circular import render_circular
        return render_circular(data, config, 'density')

    ready = {
        'WAV-01': (compute_wavelets, wavelet_renderer),
        'LEN-13': (compute_lengths, blocks_renderer),
        'LEN-15': (compute_lengths, variogram_renderer),
        **{key: (compute_graphs, graph_renderer(key)) for key in (*ALONG, *CIRCULAR, *FROM)},
        'MAP-01': (compute_map('traces'), map_renderer),
        'MAP-04': (compute_map('trace_length'), map_renderer),
        'MAP-05': (compute_map('segment_length'), map_renderer),
        'MAP-06': (compute_map('strike'), map_renderer),
        'MAP-07': (compute_circular, intensity_renderer),
        'MAP-08': (compute_circular, density_renderer),
        'ANG-01': (compute_angles, histogram_renderer),
        'ANG-02': (compute_angles, rose_renderer),
        'LEN-02': (compute_lengths, length_histogram_renderer),
        'LEN-03': (compute_lengths, loglog_renderer),
        'LEN-06': (compute_lengths, crossplot_renderer),
        'LEN-07': (compute_lengths, mle_renderer),
        'FLO-01': (compute_connectivity, connectivity_renderer),
        'FLO-08': (compute_angles, crack_renderer),
        'FLO-09': (compute_permeability, permeability_renderer),
        'MAP-11': (compute_stability, stability_renderer('slip')),
        'MAP-12': (compute_stability, stability_renderer('dilation')),
        'MAP-13': (compute_stability, stability_renderer('susceptibility')),
        'MAP-14': (compute_stability, stability_renderer('csf')),
    }
    records = [
        ('MAP-01', 'tracemap', 'Traces, segments', ()),
        ('MAP-04', 'tracemaplength', 'Traces, by length', ()),
        ('MAP-05', 'segmentmaplength', 'Segments, by length', ()),
        ('MAP-06', 'segmentmapstrike', 'Segments, by strike', (NORTH,)),
        ('MAP-07', 'intensitymap', 'Estimated Intensity, P21', (CIRCLES,)),
        ('MAP-08', 'densitymap', 'Estimated Density, P20', (CIRCLES,)),
        ('MAP-11', 'sliptendency', 'Slip tendency', STRESS),
        ('MAP-12', 'dilationtendency', 'Dilation tendency', STRESS),
        ('MAP-13', 'fracsuscep', 'Fracture susceptibility', STRESS),
        ('MAP-14', 'CSF', 'Critically stressed fractures', STRESS),
        ('LEN-02', 'histolength', 'Histogram of lengths', (LENGTH_BINS,)),
        ('LEN-03', 'logloglength', 'Log-log lengths', (LENGTH_BINS,)),
        ('LEN-07', 'mle', 'MLE analysis', (
            Parameter('edit_lc', 0, 100), Parameter('edit_uc', 0, 100))),
        ('LEN-06', 'crossplot', 'Cross-plot lengths v angles', (NORTH,)),
        ('LEN-13', 'blocksize', 'Block size graphs', ()),
        ('LEN-15', 'seglenvariogram', 'Variogram of segment lengths', ()),
        ('ANG-01', 'histoangle', 'Histogram of angles', (
            Parameter('popupmenu_histoanglebins',
                      choices=('10', '20', '30', '50')), NORTH)),
        ('ANG-02', 'rose', 'Rose diagram (equal area)', (
            Parameter('popupmenu_rosebins', choices=('5', '10', '20', '30')), NORTH)),
        ('FLO-01', 'triangle', 'I-Y-X connectivity', (
            Parameter('edit_numblocksmap', 2, integer=True),
            Parameter('edit_numpixelsItoY', 0))),
        ('FLO-08', 'cracktensor', 'Crack tensor plot', (NORTH,)),
        ('FLO-09', 'permellipse', 'Permeability plot (polar)', (
            Parameter('edit_lambda', 0, 1), NORTH)),
        ('WAV-01', 'wavelet', 'Run wavelet analysis', (
            Parameter('edit_aString', positive=True, integer=True, number_list=True),
            Parameter('edit_LString', positive=True, integer=True, number_list=True),
            Parameter('edit_DegString', 1, 360, integer=True))),
    ]
    for identifier, suffix, label in [
        ('GRA-03', 'tracelengthgraphalong', 'ALONG: Trace length'),
        ('GRA-04', 'segmentlengthgraphalong', 'ALONG: Segment length'),
        ('GRA-05', 'segmentstrikegraphalong', 'ALONG: Segment angle'),
        ('GRA-06', 'intensitygraphalong', 'ALONG: Estimated intensity, P21'),
        ('GRA-07', 'densitygraphalong', 'ALONG: Estimated density, P20'),
        ('GRA-10', 'tracelengthgraphfrom', 'FROM: Trace length'),
        ('GRA-11', 'segmentlengthgraphfrom', 'FROM: Segment length'),
        ('GRA-12', 'segmentanglegraphfrom', 'FROM: Segment angle'),
    ]:
        params = ((Parameter('edit_numscancirclesgraph', 2, integer=True),)
                  if identifier in ('GRA-06', 'GRA-07') else ())
        records.append((identifier, suffix, label, params))
    return tuple(AnalysisSpec(i, 'checkbox_' + c, label, p,
                              *ready.get(i, (None, None)),
                              requires=(('checkbox_logloglength',)
                                        if i == 'LEN-07' else ()),
                              cache_key=('angles' if i.startswith('ANG-') or i == 'FLO-08' else 'lengths'
                                         if i in ('LEN-02', 'LEN-03', 'LEN-06', 'LEN-07', 'LEN-13', 'LEN-15') else 'graphs'
                                         if i.startswith('GRA-') else 'circular'
                                         if i in ('MAP-07', 'MAP-08') else 'stability'
                                         if i in ('MAP-11', 'MAP-12', 'MAP-13', 'MAP-14') else None),
                              cooperative=i in ('MAP-07', 'MAP-08', 'LEN-02', 'LEN-03',
                                                'LEN-06', 'LEN-07', 'FLO-01', 'FLO-08',
                                                'FLO-09', 'ANG-01', 'ANG-02',
                                                'MAP-11', 'MAP-12', 'MAP-13', 'MAP-14',
                                                'LEN-13', 'LEN-15', 'WAV-01') or i.startswith('GRA-'))
                 for i, c, label, p in records)


class AnalysisRegistry:
    def __init__(self, specs: Iterable[AnalysisSpec] | None = None) -> None:
        self.specs = tuple(default_specs() if specs is None else specs)
        if len({s.id for s in self.specs}) != len(self.specs):
            raise ValueError('Analysis identifiers must be unique.')
        if len({s.checkbox for s in self.specs}) != len(self.specs):
            raise ValueError('Analysis selectors must be unique.')

    def selected(self, values: dict[str, bool | str]) -> tuple[str, ...]:
        return tuple(s.id for s in self.specs if values.get(s.checkbox) is True
                     and all(values.get(name) is True for name in s.requires))

    def validate(self, config: AnalysisConfig) -> tuple[AnalysisSpec, ...]:
        selected = tuple(s for s in self.specs if s.id in config.selected)
        if set(config.selected) - {s.id for s in selected}:
            raise FieldError('pushbutton_run', 'Unknown analysis selection.')
        if not selected:
            raise FieldError('pushbutton_run', 'Select at least one output.')
        for spec in selected:
            if any(config.value(name) is not True for name in spec.requires):
                raise FieldError(spec.checkbox, 'Enable the parent analysis first.')
            for parameter in spec.parameters:
                parameter.validate(config)
        if any(s.id.startswith('GRA-') for s in selected):
            from pyfracpaq.geometry.profiles import ProfileLine
            if not isinstance(config.profile_line, ProfileLine):
                raise FieldError('pushbutton_selectgraphendpoints',
                                 'Select two distinct end points on the preview first.')
        if any(s.id == 'WAV-01' for s in selected):
            from pyfracpaq.analysis.wavelets import parameters_from_config
            parameters_from_config(config)
        if any(s.id in ('MAP-11', 'MAP-12', 'MAP-13', 'MAP-14') for s in selected):
            from pyfracpaq.analysis.stability import parameters_from_config
            parameters_from_config(config)
        if any(s.id == 'LEN-07' for s in selected):
            if float(config.value('edit_lc')) + float(config.value('edit_uc')) >= 100:
                raise FieldError('edit_uc',
                                 'The two cut-offs must leave a nonempty sample.')
        if any(s.id == 'FLO-09' for s in selected):
            parameters = ((Parameter('edit_fixedaperture', 0),)
                          if config.value('radiobutton_fixedaperture') else (
                              Parameter('edit_aperturefactor', 0, .1),
                              Parameter('edit_apertureexponent', .5, 1)))
            for parameter in parameters:
                parameter.validate(config)
        unavailable = [s for s in selected if not s.available]
        if unavailable:
            raise FieldError(unavailable[0].checkbox,
                             'These outputs are not available in this version: '
                             + '; '.join(s.label for s in unavailable) + '.')
        return selected

    def execute(
        self, dataset: Dataset, context: RunContext, progress: Progress,
        interrupted: Callable[[], bool],
    ) -> tuple[AnalysisResult, ...]:
        specs = self.validate(context.config)
        results = []
        cache = {}
        for i, spec in enumerate(specs):
            if interrupted():
                return ()
            progress(round(100 * i / len(specs)), f'Running {spec.label}...')
            try:
                if spec.cache_key is not None and spec.cache_key in cache:
                    data = cache[spec.cache_key]
                else:
                    if spec.cooperative:
                        def local_progress(percent, message):
                            progress(round((100 * i + percent) / len(specs)), message)
                        data = spec.compute(dataset, context, local_progress,
                                            interrupted=interrupted)
                    else:
                        data = spec.compute(dataset, context, progress)
                    if spec.cache_key is not None:
                        cache[spec.cache_key] = data
            except InterruptedError:
                return ()
            except FieldError as error:
                raise FieldError(error.field, f'{spec.label}: {error}') from error
            except Exception as error:
                raise FieldError(spec.checkbox, f'{spec.label}: {error}') from error
            results.append(AnalysisResult(spec.id, data))
        progress(100, 'Calculations completed.')
        return tuple(results)
