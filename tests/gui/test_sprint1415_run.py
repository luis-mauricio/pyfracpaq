"""Worker/Run integration, auxiliary dialog Run/Cancel and explicit local tools."""

from threading import Event

import numpy as np
from PIL import Image
import pytest
from shiboken6 import isValid

from pyfracpaq.app import configure_application
from pyfracpaq.gui import MainWindow
from pyfracpaq.gui.wavelet_dialog import WaveletDialog
from pyfracpaq.tools.__main__ import main as tool
from reference_common import REFERENCE, ROOT


def close_widget(widget, qtbot):
    for message in widget.messages:
        message.accept()
    widget.close()
    if isinstance(widget, MainWindow):
        qtbot.waitUntil(lambda: not isValid(widget), timeout=5000)


@pytest.mark.parametrize('source', ['nodes/mixed.txt', 'svg/multicolour.svg', 'images/tensor_network.tif'])
def test_main_wavelets_run_from_all_inputs_without_unselected_parameter_validation(
        qapp, qtbot, tmp_path, monkeypatch, source):
    configure_application(qapp);window = MainWindow();window.show();qtbot.waitExposed(window)
    monkeypatch.chdir(tmp_path)
    window.controls['edit_filename'].setText(str(ROOT / 'tests/fixtures' / source))
    with qtbot.waitSignal(window.job_completed, timeout=10000):
        window.preview()
    for spec in window.registry.specs:
        window.controls[spec.checkbox].setChecked(spec.id == 'WAV-01')
    window.controls['edit_aString'].setText('2 3')
    window.controls['edit_LString'].setText('2')
    window.controls['edit_DegString'].setText('45')
    window.controls['edit_sigma1'].setText('unused')
    window.controls['edit_degfromnorth'].setText('unused')
    # Small scientific fixture for fast UI regression; a separate validation
    # captures the actual 1944x1944 raster/FFT through the production registry.
    pixels = np.full((8, 10), 255, np.uint8);pixels[2, 2:8] = 0
    monkeypatch.setattr('pyfracpaq.io.wavelets.rasterize_wavelets', lambda _: pixels)
    with qtbot.waitSignal(window.job_completed, timeout=20000):
        window.run_selected()
    assert window.last_error is None
    assert len(list(tmp_path.glob('FracPaQ2Dwavelet_a*_Run1.png'))) == 2
    assert len(list(tmp_path.glob('FracPaQ2Dwavelet_theta_a*_Run1.txt'))) == 2
    assert (tmp_path / 'FracPaQ2D_wavelet_traces.png').is_file()
    close_widget(window, qtbot)


def test_auxiliary_dialog_reference_defaults_run_and_idle_cancel(qapp, qtbot, tmp_path):
    configure_application(qapp)
    raster = REFERENCE / 'sprint14/native/morlet/FracPaQ2D_wavelet_traces.png'
    dialog = WaveletDialog(raster, directory=tmp_path);dialog.show();qtbot.waitExposed(dialog)
    assert len(dialog.widgets) == 14
    assert dialog.widgets['edit_aString'].text() == '2 4 8 16'
    assert dialog.widgets['edit_DegString'].text() == '20'
    dialog.widgets['edit_aString'].setText('2');dialog.widgets['edit_LString'].setText('2 1')
    dialog.widgets['edit_DegString'].setText('45')
    with qtbot.waitSignal(dialog.job_completed, timeout=10000):
        dialog.widgets['pb_Run'].click()
    assert dialog.failure is None
    assert (tmp_path / 'FracPaQ2Dwavelet_a2_Run1.png').is_file()
    assert (tmp_path / 'FracPaQ2Dwavelet_theta_a2.txt').is_file()
    assert not (tmp_path / 'FracPaQ2D_wavelet_traces.png').exists()  # Raster reused.
    assert dialog.widgets['text_Message'].text() == 'Ready'
    dialog.widgets['pb_Cancel'].click();assert not dialog.isVisible()
    for figure in dialog.figure_windows:
        figure.close()


def test_dialog_cancel_while_running_waits_for_its_worker(qapp, qtbot, tmp_path, monkeypatch):
    configure_application(qapp)
    import pyfracpaq.gui.wavelet_dialog as module
    entered, released = Event(), Event()
    def work(*args, interrupted, **kwargs):
        entered.set()
        released.wait(2)
        assert interrupted()
        raise InterruptedError('Cancelled')
    monkeypatch.setattr(module, 'analyse_wavelet_image', work)
    dialog = WaveletDialog(REFERENCE / 'sprint14/native/morlet/FracPaQ2D_wavelet_traces.png', directory=tmp_path)
    dialog.show();dialog.run_analysis();qtbot.waitUntil(entered.is_set)
    dialog.reject();assert dialog.thread is not None and dialog.closing
    with qtbot.waitSignal(dialog.job_completed, timeout=5000):
        released.set()
    assert dialog.thread is None and not dialog.isVisible()
    assert not list(tmp_path.iterdir())


def test_explicit_local_preprocess_and_move_commands(tmp_path):
    output = tmp_path / 'prepared.tif';panel = tmp_path / 'stages.png'
    assert tool(['preprocess', str(REFERENCE / 'sprint15/native/MacduffColourCropped.jpg'),
                 str(output), '--panel', str(panel)]) == 0
    with Image.open(output) as image:
        assert image.mode == 'L' and set(np.unique(image)).issubset({0, 255})
    assert panel.is_file()
    source = tmp_path / 'move.dat';source.write_text('1 2 3\n4 5 6')
    assert tool(['move', str(source), str(tmp_path / 'converted.txt')]) == 0
