"""Contextual validation and exact filename/export contracts."""

from dataclasses import replace
import json
from pathlib import Path

from matplotlib import rc_context
from matplotlib.figure import Figure
import numpy as np
from PIL import Image
import pytest

from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.domain.execution import AnalysisConfig, FieldError, InputConfig
from pyfracpaq.io.figures import export_png, validate_tag
from pyfracpaq.resources import resource_bytes, ui_specification
from reference_common import ROOT, sha256


def config(selected=('MAP-01',), **changes):
    spec = ui_specification()
    values = {}
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
    if 'LEN-07' in selected:
        values['checkbox_logloglength'] = True
    source = InputConfig(Path('/source.txt'), 'node', None, (), None)
    return AnalysisConfig(tuple(values.items()), selected, 'Run1', False, False, source)


def test_unselected_parameters_are_not_validated():
    registry = AnalysisRegistry()
    assert registry.validate(config(edit_sigma1='bad', edit_aString='not a list',
                                    edit_lambda='bad'))[0].id == 'MAP-01'


@pytest.mark.parametrize('selected,changes,field', [
    (('MAP-07',), {'edit_numscancircles': '2.5'}, 'edit_numscancircles'),
    (('FLO-01',), {'edit_numpixelsItoY': '-1'}, 'edit_numpixelsItoY'),
    (('FLO-09',), {'edit_lambda': 'nan'}, 'edit_lambda'),
    (('FLO-09',), {'edit_fixedaperture': '-1'}, 'edit_fixedaperture'),
    (('WAV-01',), {'edit_aString': '__import__("os")'}, 'edit_aString'),
    (('WAV-01',), {'edit_LString': ''}, 'edit_LString'),
    (('LEN-07',), {'edit_lc': '60', 'edit_uc': '40'}, 'edit_uc'),
    (('ANG-02',), {'popupmenu_rosebins': '12'}, 'popupmenu_rosebins'),
])
def test_selected_parameter_validation_has_field_context(selected, changes, field):
    with pytest.raises(FieldError) as raised:
        AnalysisRegistry().validate(config(selected, **changes))
    assert raised.value.field == field


@pytest.mark.parametrize('tag', ['../escape', 'a/b', r'a\b', 'a:b', 'a\n', '..', 'a*'])
def test_tag_cannot_escape_or_silently_change(tag):
    with pytest.raises(ValueError):
        validate_tag(tag)


def test_png_geometry_tag_dpi_and_atomic_replacement(tmp_path):
    figure = Figure(figsize=(3, 2), dpi=100)
    figure.add_subplot().plot([0, 1], [1, 0], color='black')
    old_size = figure.get_size_inches().copy()
    with rc_context({'savefig.bbox': 'tight'}):
        target = export_png(figure, 'FracPaQ2D_test', 'Execução 1', tmp_path)
    assert target.name == 'FracPaQ2D_test_Execução 1.png'
    with Image.open(target) as image:
        assert image.size == (4724, 4724)
        assert abs(image.info['dpi'][0] - 600) < .01
        assert 'PyFracPaQ' in image.info['Software']
        assert image.convert('L').getextrema()[0] < 50
    np.testing.assert_array_equal(figure.get_size_inches(), old_size)
    assert not list(tmp_path.glob('.pyfracpaq-*'))
    unrelated = tmp_path / 'another_run.txt'
    unrelated.write_text('keep')
    export_png(figure, 'FracPaQ2D_test', 'Execução 1', tmp_path)
    assert unrelated.read_text() == 'keep'
    assert export_png(figure, 'FracPaQ2D_test', '', tmp_path).name == 'FracPaQ2D_test_.png'


def test_failed_export_preserves_previous_file_and_figure_size(tmp_path, monkeypatch):
    figure = Figure(figsize=(3, 2))
    target = tmp_path / 'base_Run1.png'
    target.write_bytes(b'previous output')
    old_size = figure.get_size_inches().copy()

    def fail(*a, **kw):
        raise OSError('simulated write failure')

    monkeypatch.setattr(figure, 'savefig', fail)
    with pytest.raises(OSError):
        export_png(figure, 'base', 'Run1', tmp_path)
    assert target.read_bytes() == b'previous output'
    np.testing.assert_array_equal(figure.get_size_inches(), old_size)
    assert not list(tmp_path.glob('.pyfracpaq-*'))


def test_package_assets_are_exact_copies_and_controls_cover_reference():
    for entry in json.loads(resource_bytes('provenance.json')):
        assert resource_bytes(entry['path']) == (ROOT / entry['source']).read_bytes()
    spec = ui_specification()
    assert spec['source_sha256'] == sha256(ROOT / spec['source'])
    assert len(spec['objects']) == 142
