"""Standalone GUIDE wavelet dialog replica, reusing an explicitly selected raster."""

from pathlib import Path
import json

import numpy as np
from PIL import Image
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QDialog, QGroupBox, QLabel, QLineEdit, QMessageBox, QPushButton, QRadioButton

from pyfracpaq.analysis.wavelets import parameters_from_config, analyse_wavelet_image
from pyfracpaq.domain.execution import AnalysisConfig, InputConfig
from pyfracpaq.gui.figures import FigureWindow
from pyfracpaq.gui.layout import reference_rect
from pyfracpaq.io.figures import export_png
from pyfracpaq.io.wavelets import normalize_raster, export_wavelets
from pyfracpaq.plots.wavelets import render_wavelets
from pyfracpaq.resources import resource_text
from pyfracpaq.workers import JobWorker


class WaveletDialog(QDialog):
    job_completed = Signal()

    def __init__(self, raster, *, directory=None, tag='Run1', parent=None):
        super().__init__(parent)
        self.setObjectName('figure1')
        self.setWindowTitle('Wavelet Analysis with FracPaQ')
        self.resize(520, 320)
        self.raster = Path(raster).resolve()
        self.directory = Path(directory or Path.cwd()).resolve()
        self.tag = tag
        self.thread = self.worker = None
        self.result = self.failure = None
        self.closing = False
        self.figure_windows = []
        self.messages = []
        self.widgets = {'figure1': self}
        self.spec = json.loads(resource_text('wavelet_dialog.json'))
        for obj in self.spec['objects']:
            if obj['tag'] == 'figure1':
                continue
            owner = self.widgets[obj['parent']]
            style = obj.get('Style')
            text = obj.get('String', '')
            cls = {'edit': QLineEdit, 'text': QLabel, 'pushbutton': QPushButton,
                   'radiobutton': QRadioButton}.get(style, QGroupBox)
            widget = cls(text if style else obj.get('Title', ''), owner)
            widget.setObjectName(obj['tag'])
            widget.setFont(QFont('Arial', int(obj.get('FontSize', 12))))
            if isinstance(widget, QRadioButton):
                widget.setChecked(bool(obj.get('Value', 0)))
            self.widgets[obj['tag']] = widget
        self.widgets['pb_Run'].clicked.connect(self.run_analysis)
        self.widgets['pb_Cancel'].clicked.connect(self.reject)
        self._layout()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'spec'):
            self._layout()

    def _layout(self):
        records = {obj['tag']: obj for obj in self.spec['objects']}
        for obj in self.spec['objects']:
            if obj['tag'] == 'figure1':
                continue
            parent = records[obj['parent']]
            width, height = parent['Position'][2:]
            x, y, w, h = obj['Position']
            widget = self.widgets[obj['tag']]
            widget.setGeometry(reference_rect((x / width, y / height, w / width, h / height),
                                               widget.parentWidget().width(), widget.parentWidget().height()))

    def capture(self):
        values = {}
        for name in ('edit_aString', 'edit_LString', 'edit_DegString'):
            values[name] = self.widgets[name].text()
        values['radiobutton_Morlet'] = self.widgets['radiobutton_Morlet'].isChecked()
        return AnalysisConfig(tuple(values.items()), ('WAV-01',), self.tag, False, False,
                              InputConfig(self.raster, 'image', None, (), None))

    def run_analysis(self):
        if self.thread is not None:
            return
        try:
            cfg = self.capture()
            parameters = parameters_from_config(cfg)
        except ValueError as error:
            self._error(str(error))
            return
        self.failure = self.result = None
        def operation(progress, interrupted):
            with Image.open(self.raster) as image:
                if image.mode not in ('L', 'RGB'):
                    raise ValueError('Wavelet tool requires an 8-bit L or RGB PNG raster.')
                pixels = np.asarray(image)
                if pixels.ndim == 3:
                    pixels = np.floor(pixels @ np.array([.298936021293776, .587043074451121,
                                                         .114020904255103]) + .5).astype(np.uint8)
            result = analyse_wavelet_image(normalize_raster(pixels), parameters,
                                            progress=progress, interrupted=interrupted)
            if interrupted():
                raise InterruptedError('Wavelet tool cancelled before export.')
            export_wavelets(result, cfg.tag, self.directory, auxiliary=True)
            return cfg, result
        for name, widget in self.widgets.items():
            if isinstance(widget, (QLineEdit, QPushButton, QRadioButton)) and name != 'pb_Cancel':
                widget.setEnabled(False)
        self.thread = QThread(self)
        self.worker = JobWorker(operation, 'pb_Run')
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(lambda _, message: self.widgets['text_Message'].setText(message))
        self.worker.result.connect(self._result)
        self.worker.failed.connect(self._failure)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self._finished)
        self.thread.finished.connect(self.thread.deleteLater)
        self.widgets['text_Message'].setText('Running...')
        self.thread.start()

    def _result(self, result):
        self.result = result

    def _failure(self, error):
        self.failure = error

    def _error(self, message):
        dialog = QMessageBox(QMessageBox.Icon.Warning, 'Input error', message, parent=self)
        self.messages.append(dialog)
        dialog.open()

    def _finished(self):
        self.thread = self.worker = None
        try:
            if self.closing:
                super().reject()
                return
            if self.failure is not None:
                self._error(self.failure.message)
            elif self.result is not None:
                cfg, result = self.result
                for output in render_wavelets(result, cfg):
                    export_png(output.figure, output.basename, cfg.tag, self.directory)
                    window = FigureWindow(output.figure, output.basename, self)
                    self.figure_windows.append(window)
                    window.show()
        except Exception as error:
            self._error(str(error))
        finally:
            for widget in self.widgets.values():
                widget.setEnabled(True)
            self.widgets['text_Message'].setText('Ready')
            self.job_completed.emit()

    def reject(self):
        if self.thread is not None:
            self.closing = True
            self.thread.requestInterruption()
            self.widgets['text_Message'].setText('Closing after current calculation...')
            return
        super().reject()

    def closeEvent(self, event):
        if self.thread is not None:
            self.reject()
            event.ignore()
        else:
            event.accept()
