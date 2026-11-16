"""Exit remains available between actual PNG exports on the GUI thread."""

from matplotlib.figure import Figure
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QKeySequence
from PySide6.QtTest import QTest
from shiboken6 import isValid

from pyfracpaq.analysis.registry import AnalysisRegistry, AnalysisSpec
from pyfracpaq.app import configure_application
from pyfracpaq.gui import MainWindow
from pyfracpaq.plots.results import FigureOutput
from reference_common import ROOT


def test_exit_between_exports_stops_pending_outputs_and_keeps_other_windows(
        qapp, qtbot, tmp_path, monkeypatch):
    configure_application(qapp)
    window = MainWindow();window.show()
    window.controls['edit_filename'].setText(str(ROOT/'tests/fixtures/nodes/mixed.txt'))
    with qtbot.waitSignal(window.job_completed, timeout=5000):window.preview()
    def render(data, config):
        outputs=[]
        for name in ('first','second','third'):
            figure=Figure();figure.add_subplot().plot([0,1],[0,1])
            outputs.append(FigureOutput(name,figure))
        return tuple(outputs)
    window.registry=AnalysisRegistry([AnalysisSpec('MAP-01','checkbox_tracemap',
        'Traces',compute=lambda *args:1,render=render)])
    for spec in window.registry.specs:window.controls[spec.checkbox].setChecked(True)
    other=QWidget();qtbot.addWidget(other);other.show()
    original=window.present_figure;observed=[]
    def present(output,context):
        assert window.busy and not window.controls['pushbutton_run'].isEnabled()
        result=original(output,context);observed.append(output.basename)
        QTimer.singleShot(0,window.close)
        return result
    monkeypatch.setattr(window,'present_figure',present);monkeypatch.chdir(tmp_path)
    with qtbot.waitSignal(window.job_completed, timeout=10000):window.run_selected()
    qtbot.waitUntil(lambda:not isValid(window),timeout=5000)
    assert observed==['first']
    assert {p.name for p in tmp_path.glob('*.png')}=={'first_Run1.png'}
    assert not list(tmp_path.glob('.pyfracpaq-*'))
    assert other.isVisible()


def test_standard_close_shortcut_closes_only_the_focused_figure(qapp, qtbot):
    from pyfracpaq.gui.figures import FigureWindow
    configure_application(qapp)
    owner=MainWindow();owner.show()
    first=FigureWindow(Figure(),'first',owner);first.show()
    second=FigureWindow(Figure(),'second',owner);second.show();second.activateWindow()
    qtbot.waitExposed(second)
    qtbot.waitUntil(second.isActiveWindow,timeout=5000)
    second.canvas.setFocus()
    QTest.keySequence(second,QKeySequence(QKeySequence.StandardKey.Close))
    qtbot.waitUntil(lambda:not isValid(second),timeout=5000)
    assert first.isVisible() and owner.isVisible()
    first.close();owner.close()
