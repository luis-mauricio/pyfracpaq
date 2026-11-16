"""Reproducible directional input/configurations for Sprint 3 figure audits."""

from pathlib import Path

from pyfracpaq.domain import TraceInput
from pyfracpaq.domain.construction import build_dataset
from pyfracpaq.domain.execution import AnalysisConfig, InputConfig
from pyfracpaq.resources import ui_specification

SELECTED = ('MAP-01', 'MAP-04', 'MAP-05', 'MAP-06', 'ANG-01', 'ANG-02')


def reference_config(selected=SELECTED, **changes) -> AnalysisConfig:
    spec, values = ui_specification(), {}
    for obj in spec['objects']:
        name, style = obj['tag'], obj.get('Style')
        if style in ('checkbox', 'radiobutton'):
            values[name] = bool(obj.get('Value', 0))
        elif style == 'edit':
            value = obj.get('String', '')
            values[name] = '' if isinstance(value, list) else value
        elif style == 'popupmenu':
            index = spec['opening_values'].get(name, obj.get('Value', 1)) - 1
            values[name] = obj['String'][index]
    values.update(changes)
    return AnalysisConfig(tuple(values.items()), selected, 'Run1', False, False,
                          InputConfig(Path('directional.txt'), 'node', None, (), None))


def directional_dataset():
    # Four cardinal/diagonal traces plus a bent trace, unequal lengths.
    return build_dataset([
        TraceInput(((0, 0), (0, 8))),
        TraceInput(((2, 0), (8, 0))),
        TraceInput(((2, 2), (6, 6))),
        TraceInput(((2, 6), (6, 2))),
        TraceInput(((8, 2), (8, 6), (6, 8))),
    ])
