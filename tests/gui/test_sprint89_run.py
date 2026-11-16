"""Approved MLE/connectivity flows through the production Run registry."""

from pathlib import Path
import shutil

import numpy as np
import pytest
from shiboken6 import isValid

from pyfracpaq.app import configure_application
from pyfracpaq.gui import MainWindow
from reference_common import ROOT


@pytest.fixture
def window(qapp,qtbot):
    configure_application(qapp)
    result=MainWindow();result.resize(1250,739)
    result.show();qtbot.waitExposed(result)
    yield result
    if isValid(result):
        result.close();qtbot.waitUntil(lambda:not isValid(result),timeout=5000)


def preview(window,qtbot,source):
    window.controls['edit_filename'].setText(str(source))
    with qtbot.waitSignal(window.job_completed,timeout=10000):window.preview()
    assert window.dataset is not None


def test_mle_run_shares_lengths_cache_and_saves_six_fits_plus_loglog(window,qtbot,tmp_path,monkeypatch):
    preview(window,qtbot,ROOT/'tests/fixtures/nodes/mixed.txt')
    for spec in window.registry.specs:window.controls[spec.checkbox].setChecked(spec.id=='LEN-03')
    window.controls['checkbox_mle'].setChecked(True)
    before=window.dataset.as_arrays().segment_coordinates.copy()
    monkeypatch.chdir(tmp_path)
    with qtbot.waitSignal(window.job_completed,timeout=20000):window.run_selected()
    assert window.last_error is None
    assert len(window.figure_windows)==10
    assert len(list(tmp_path.glob('*.png')))==10
    assert len(list(tmp_path.glob('*Fitting*.png')))==6
    assert len(list(tmp_path.glob('*.txt')))==3
    np.testing.assert_array_equal(window.dataset.as_arrays().segment_coordinates,before)


@pytest.mark.parametrize('source', ['tests/fixtures/svg/multicolour.svg','tests/fixtures/images/rectangular.tif'])
def test_connectivity_run_from_svg_and_hough_has_four_consistent_figures(window,qtbot,tmp_path,monkeypatch,source):
    monkeypatch.chdir(tmp_path)
    local=tmp_path/Path(source).name
    shutil.copyfile(ROOT/source,local)
    preview(window,qtbot,local)
    initial=len(window.figure_windows)
    for spec in window.registry.specs:window.controls[spec.checkbox].setChecked(spec.id=='FLO-01')
    window.controls['edit_numblocksmap'].setText('3')
    with qtbot.waitSignal(window.job_completed,timeout=15000):window.run_selected()
    assert window.last_error is None
    assert len(window.figure_windows)==initial+4
    text=(tmp_path/'FracPaQ2Dconnectivity_Run1.txt').read_text()
    assert [row.split()[0] for row in text.splitlines()]==['I','X','Y']
    assert len(list(tmp_path.glob('FracPaQ2D_*nodes*_Run1.png')))==3


def test_excessive_mle_cuts_fail_before_any_family_output(window,qtbot,tmp_path,monkeypatch):
    preview(window,qtbot,ROOT/'tests/fixtures/nodes/mixed.txt')
    for spec in window.registry.specs:window.controls[spec.checkbox].setChecked(spec.id=='LEN-03')
    window.controls['checkbox_mle'].setChecked(True)
    window.controls['edit_lc'].setText('49')
    monkeypatch.chdir(tmp_path)
    with qtbot.waitSignal(window.job_completed,timeout=10000):window.run_selected()
    assert window.last_error is not None and window.last_error.field=='edit_lc'
    assert not list(tmp_path.iterdir())
    for message in window.messages:message.accept()
