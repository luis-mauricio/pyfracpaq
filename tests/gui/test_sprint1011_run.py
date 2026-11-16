"""Real Qt Run flows for tensors and all four approved stability analyses."""

from pathlib import Path
import shutil

import numpy as np
from PIL import Image
import pytest
from shiboken6 import isValid

from pyfracpaq.app import configure_application
from pyfracpaq.gui import MainWindow
from reference_common import ROOT


@pytest.fixture
def window(qapp, qtbot):
    configure_application(qapp)
    result = MainWindow()
    result.resize(1250, 739)
    result.show()
    qtbot.waitExposed(result)
    yield result
    if isValid(result):
        for message in result.messages:
            message.accept()
        result.close()
        qtbot.waitUntil(lambda: not isValid(result), timeout=5000)


def preview(window, qtbot, source):
    window.controls['edit_filename'].setText(str(source))
    with qtbot.waitSignal(window.job_completed, timeout=10000):
        window.preview()
    assert window.dataset is not None


def select(window, identifiers):
    for spec in window.registry.specs:
        window.controls[spec.checkbox].setChecked(spec.id in identifiers)


def test_crack_only_run_emits_ezrose_and_can_share_angular_outputs(window, qtbot, tmp_path, monkeypatch):
    preview(window, qtbot, ROOT / 'tests/fixtures/nodes/mixed.txt')
    monkeypatch.chdir(tmp_path)
    select(window, ('FLO-08',))
    window.controls['edit_sigma1'].setText('inactive invalid')
    with qtbot.waitSignal(window.job_completed, timeout=15000):
        window.run_selected()
    assert window.last_error is None
    assert [p.name for p in tmp_path.glob('*.png')] == ['FracPaQ2D_cracktensor_Run1.png']
    assert (tmp_path / 'FracPaQ2DEZROSE_Run1.txt').is_file()
    select(window, ('ANG-01', 'ANG-02', 'FLO-08'))
    with qtbot.waitSignal(window.job_completed, timeout=15000):
        window.run_selected()
    assert window.last_error is None
    assert len(list(tmp_path.glob('*.png'))) == 3 and len(list(tmp_path.glob('*.txt'))) == 1


@pytest.mark.parametrize('source', ['nodes/mixed.txt', 'svg/multicolour.svg', 'images/tensor_network.tif'])
def test_all_new_outputs_run_from_txt_svg_and_hough(window, qtbot, tmp_path, monkeypatch, source):
    monkeypatch.chdir(tmp_path)
    local = tmp_path / Path(source).name
    shutil.copyfile(ROOT / 'tests/fixtures' / source, local)
    preview(window, qtbot, local)
    initial = len(window.figure_windows)
    before = window.dataset.as_arrays().segment_coordinates.copy()
    select(window, ('MAP-11', 'MAP-12', 'MAP-13', 'MAP-14', 'FLO-08', 'FLO-09'))
    window.controls['edit_thetasigma1'].setText('30')
    window.controls['pushbutton_flipx'].setChecked(True)
    window.controls['edit_degfromnorth'].setText('12')
    with qtbot.waitSignal(window.job_completed, timeout=30000):
        window.run_selected()
    assert window.last_error is None
    extra = int(len(window.dataset.colours) > 1)
    assert len(window.figure_windows) == initial + 11 + extra
    assert len(list(tmp_path.glob('FracPaQ2D_Mohrplot_*.png'))) == 1
    assert len(list(tmp_path.glob('FracPaQ2D_*tendency*Run1.png'))) == 4
    assert (tmp_path / 'FracPaQ2DEZROSE_Run1.txt').is_file()
    assert (tmp_path / 'FracPaQ2Dsegmentdata_Run1.txt').is_file()
    with Image.open(tmp_path / 'FracPaQ2D_sliptendencymap_Run1.png') as image:
        assert image.size == (4724, 4724) and abs(image.info['dpi'][0] - 600) < .01
    np.testing.assert_array_equal(window.dataset.as_arrays().segment_coordinates, before)


@pytest.mark.parametrize('fixed', [True, False])
def test_zero_permeability_and_scaled_aperture_run_without_unselected_validation(
        window, qtbot, tmp_path, monkeypatch, fixed):
    preview(window, qtbot, ROOT / 'tests/fixtures/nodes/mixed.txt')
    monkeypatch.chdir(tmp_path)
    select(window, ('FLO-09',))
    window.controls['radiobutton_fixedaperture' if fixed else 'radiobutton_scaledaperture'].setChecked(True)
    window.controls['edit_fixedaperture'].setText('0' if fixed else 'inactive invalid')
    window.controls['edit_aperturefactor'].setText('inactive invalid' if fixed else '.01')
    window.controls['edit_apertureexponent'].setText('inactive invalid' if fixed else '.75')
    window.controls['edit_lambda'].setText('0')
    with qtbot.waitSignal(window.job_completed, timeout=15000):
        window.run_selected()
    assert window.last_error is None
    assert len(list(tmp_path.glob('*.png'))) == 1 and not list(tmp_path.glob('*.txt'))
    assert not np.any(window.figure_windows[-1].canvas.figure.axes[0].lines[0].get_ydata())


@pytest.mark.parametrize('kind,field,value', [
    ('MAP-13', 'edit_mu', '0'), ('MAP-12', 'edit_sigma2', '100'),
])
def test_q17_undefined_combinations_fail_before_any_output(window, qtbot, tmp_path, monkeypatch,
                                                          kind, field, value):
    preview(window, qtbot, ROOT / 'tests/fixtures/nodes/mixed.txt')
    monkeypatch.chdir(tmp_path)
    select(window, (kind,))
    window.controls['edit_sigma1'].setText('100')
    window.controls[field].setText(value)
    window.run_selected()
    assert window.last_error is not None and window.last_error.field == field
    assert not list(tmp_path.iterdir())
