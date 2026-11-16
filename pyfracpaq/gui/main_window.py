"""Reference main window, preview invalidation and frozen background jobs."""

from dataclasses import dataclass
from collections.abc import Callable
import logging
from pathlib import Path
import tempfile
from uuid import uuid4

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import QSignalBlocker, QThread, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QCloseEvent, QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QProgressDialog, QPushButton, QRadioButton, QScrollArea,
)

from pyfracpaq import __version__
from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.domain import Dataset, validate_scale
from pyfracpaq.domain.execution import (
    AnalysisConfig, AnalysisResult, FieldError, InputConfig, RunContext,
)
from pyfracpaq.analysis.registry import Progress
from pyfracpaq.io import read_txt
from pyfracpaq.io.svg import SvgImport, read_svg, write_conversion
from pyfracpaq.io.images import ImageImport, read_image
from pyfracpaq.analysis.hough import parameters_from_controls
from pyfracpaq.io.figures import export_png, validate_tag
from pyfracpaq.plots import FigureOutput, draw_preview
from pyfracpaq.resources import resource_bytes
from pyfracpaq.workers import JobFailure, JobWorker
from pyfracpaq.workers.jobs import Operation

from .controls import AspectImage, Controls, HOUGH, NAVIGATION, PANELS
from .figures import FigureWindow
from .layout import ReferenceBoard, build_forms, initial_window_size
from .profile_selection import ProfilePicker

LOG = logging.getLogger(__name__)
INTERACTIVE = (QLineEdit, QCheckBox, QRadioButton, QComboBox, QPushButton)
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.tif', '.tiff'}


@dataclass(frozen=True, slots=True)
class PreviewResult:
    dataset: Dataset | None
    config: InputConfig
    revision: int
    svg: SvgImport | None = None
    image: ImageImport | None = None
    context: RunContext | None = None


class MainWindow(QMainWindow):
    job_completed = Signal(str)
    error_reported = Signal(str, str)

    def __init__(self, registry: AnalysisRegistry | None = None) -> None:
        super().__init__()
        self.setObjectName('figure_main')
        self.setWindowTitle('FracPaQ')
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.registry = registry if registry is not None else AnalysisRegistry()
        self.dataset: Dataset | None = None
        self.preview_input: InputConfig | None = None
        self.last_config: AnalysisConfig | None = None
        self.last_context: RunContext | None = None
        self.last_error: JobFailure | None = None
        self.thread: QThread | None = None
        self.worker: JobWorker | None = None
        self.progress_dialog: QProgressDialog | None = None
        self.figure_windows: list[FigureWindow] = []
        self.messages: list[QMessageBox] = []
        self.revision = 0
        self._closing = False
        self._job_kind = ''
        self._job_result = None
        self._job_failure = None
        self._rendering = False
        self._pending_figures = None
        self._temporary = None
        self.controls = Controls()
        c = self.controls
        c.add('figure_main', self)
        self.board = ReferenceBoard(c)
        self.scroll = QScrollArea()
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.board)
        self.setCentralWidget(self.scroll)
        self.figure = Figure(facecolor='#f0f0f0')
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.profile_picker = ProfilePicker(
            self.canvas, changed=self._profile_changed, status=self._status,
            can_pick=lambda: self.dataset is not None and not self.busy and not self._closing)
        c.add('axes_tracemap', self.canvas)
        self.board.anchor('axes_tracemap', self.canvas)
        for name, filename in [('axes_logo', 'FracPaQlogo.jpeg'),
                               ('axes_icon', 'FracPaQicon.jpeg')]:
            pixmap = QPixmap()
            pixmap.loadFromData(resource_bytes(filename))
            label = AspectImage(pixmap)
            label.setToolTip(f'PyFracPaQ {__version__}; reference FracPaQ 2.8')
            c.add(name, label)
            self.board.anchor(name, label)
        self.stack = build_forms(c, self.board)
        self._connect_controls()
        self._set_tab_order()
        self._sync_state()
        draw_preview(self.figure)
        self.board.position_preview_axes()
        available = self.screen().availableGeometry()
        self.resize(initial_window_size(available.size()))
        self.move(available.center() - self.rect().center())
        LOG.info('PyFracPaQ %s — FracPaQ version 2.8 reference', __version__)

    @property
    def busy(self) -> bool:
        return self.thread is not None or self._rendering

    def _connect_controls(self) -> None:
        c = self.controls
        c['edit_filename'].textChanged.connect(self._filename_changed)
        c['edit_scaling'].textChanged.connect(self._input_changed)
        for name in HOUGH:
            c[name].textChanged.connect(self._input_changed)
        for name in ('radiobutton_node', 'radiobutton_image'):
            c[name].toggled.connect(
                lambda checked: self._input_changed() if checked else None,
            )
        for name in NAVIGATION:
            index = NAVIGATION.index(name)
            c[name].clicked.connect(
                lambda _=False, i=index: self.stack.setCurrentIndex(i),
            )
        for widget in c.widgets.values():
            if isinstance(widget, (QCheckBox, QRadioButton)):
                widget.toggled.connect(self._dependencies_changed)
        for spec in self.registry.specs:
            widget = c[spec.checkbox]
            if not spec.available:
                widget.setToolTip('This output is not available in this version.')
        c['pushbutton_browse'].clicked.connect(self.browse)
        c['pushbutton_preview'].clicked.connect(self.preview)
        c['pushbutton_run'].clicked.connect(self.run_selected)
        c['pushbutton_exit'].clicked.connect(self.close)
        c['pushbutton_flipx'].toggled.connect(self._flip_changed)
        c['pushbutton_flipy'].toggled.connect(self._flip_changed)
        c['pushbutton_selectgraphendpoints'].clicked.connect(self.profile_picker.start)

    def _set_tab_order(self) -> None:
        c = self.controls
        names = ['edit_filename', 'pushbutton_browse', 'radiobutton_image',
                 'radiobutton_node', *HOUGH, 'edit_scaling', 'pushbutton_flipx',
                 'pushbutton_flipy', 'pushbutton_preview', *NAVIGATION]
        names += [name for name, widget in c.widgets.items()
                  if isinstance(widget, INTERACTIVE) and name not in names
                  and name not in ('edit_FilenameTag', 'pushbutton_run',
                                   'pushbutton_exit')]
        names += ['edit_FilenameTag', 'pushbutton_run', 'pushbutton_exit']
        for first, second in zip(names, names[1:]):
            self.setTabOrder(c[first], c[second])

    @Slot()
    def _dependencies_changed(self) -> None:
        source = self.sender()
        c = self.controls
        if source is c['checkbox_tracemap'] and not source.isChecked():
            c['checkbox_shownodes'].setChecked(False)
        if source in (c['checkbox_intensitymap'], c['checkbox_densitymap']):
            if not any(c[name].isChecked() for name in
                       ('checkbox_intensitymap', 'checkbox_densitymap')):
                c['checkbox_showcircles'].setChecked(False)
        if source is c['checkbox_logloglength']:
            c.censor_available = source.isChecked()
            if not source.isChecked():
                c['checkbox_mle'].setChecked(False)
                c['checkbox_censor'].setChecked(False)
        if source is c['checkbox_rose'] and not source.isChecked():
            for name in ('checkbox_roselengthweighted', 'checkbox_showrosemean',
                         'checkbox_rosecolour'):
                c[name].setChecked(False)
        self.controls.dependencies()
        if self.busy:
            self._disable_during_job()

    @Slot()
    def _filename_changed(self) -> None:
        c = self.controls
        suffix = Path(c['edit_filename'].text()).suffix.lower()
        target = ('radiobutton_image' if suffix in IMAGE_EXTENSIONS else
                  'radiobutton_node' if suffix in ('.txt', '.svg') else None)
        if target:
            blockers = [QSignalBlocker(c[name])
                        for name in ('radiobutton_image', 'radiobutton_node')]
            c[target].setChecked(True)
            del blockers
        self._input_changed()

    @Slot()
    def _input_changed(self) -> None:
        self.profile_picker.clear()
        self.revision += 1
        self.dataset = None
        self.preview_input = None
        self.controls['label_stats'].clear()
        draw_preview(self.figure)
        self.board.position_preview_axes()
        self.canvas.draw_idle()
        self._status('Input changed. Click Preview.')
        self._sync_state()

    def _disable_during_job(self) -> None:
        for name, widget in self.controls.widgets.items():
            if isinstance(widget, INTERACTIVE) and name != 'pushbutton_exit':
                widget.setEnabled(False)

    def _sync_state(self) -> None:
        c = self.controls
        for widget in c.widgets.values():
            if isinstance(widget, INTERACTIVE):
                widget.setEnabled(True)
        c.dependencies()
        ready = self.dataset is not None
        for name in (*NAVIGATION, 'pushbutton_run', 'pushbutton_flipx',
                     'pushbutton_flipy'):
            c[name].setEnabled(ready and not self.busy)
        c['pushbutton_run'].setEnabled(ready and not self.busy and not self.profile_picker.active)
        c['pushbutton_selectgraphendpoints'].setEnabled(
            ready and not self.busy and not self.profile_picker.active)
        filename = c['edit_filename'].text()
        c['pushbutton_preview'].setEnabled(
            bool(filename.strip()) and filename != '[no file selected]'
            and not self.busy
        )
        self.stack.setVisible(ready and not self._closing)
        if self.busy or self._closing:
            self._disable_during_job()

    def _status(self, text: str) -> None:
        self.controls['text_message'].setText(text)
        LOG.info('%s', text)

    def capture_input(self) -> InputConfig:
        c = self.controls
        text = c['edit_filename'].text()
        if not text.strip() or text == '[no file selected]':
            raise FieldError('edit_filename', 'Choose an input file.')
        try:
            path = Path(text).expanduser().resolve()
        except (OSError, ValueError) as error:
            raise FieldError('edit_filename', 'Invalid input path.') from error
        try:
            scaling = c['edit_scaling'].text().strip()
            scale = validate_scale(float(scaling) if scaling else None)
        except ValueError as error:
            raise FieldError('edit_scaling', str(error)) from error
        try:
            stat = path.stat()
            stamp = stat.st_mtime_ns, stat.st_size
        except OSError:
            stamp = None
        return InputConfig(
            path, 'image' if c['radiobutton_image'].isChecked() else 'node', scale,
            tuple((name, c[name].text()) for name in HOUGH), stamp,
        )

    def capture_run(self) -> AnalysisConfig:
        values = self.controls.values()
        try:
            tag = validate_tag(values['edit_FilenameTag'])
        except ValueError as error:
            raise FieldError('edit_FilenameTag', str(error)) from error
        return AnalysisConfig(
            tuple(values.items()), self.registry.selected(values), tag,
            self.controls['pushbutton_flipx'].isChecked(),
            self.controls['pushbutton_flipy'].isChecked(), self.capture_input(),
            profile_line=self.profile_picker.line,
        )

    @Slot()
    def browse(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self, 'Select input file', str(Path.cwd()),
            'Supported files (*.txt *.TXT *.svg *.SVG *.jpg *.JPG *.jpeg *.JPEG '
            '*.tif *.TIF *.tiff *.TIFF);;Node files (*.txt *.TXT *.svg *.SVG);;'
            'Image files (*.jpg *.JPG *.jpeg *.JPEG *.tif *.TIF *.tiff *.TIFF)',
        )
        if filename:
            self.controls['edit_filename'].setText(filename)

    @Slot()
    def preview(self) -> None:
        if self.busy:
            return
        try:
            config = self.capture_input()
            image_parameters = None
            context = None
            if config.kind == 'image':
                image_parameters = parameters_from_controls(config.extraction)
                snapshot = self.capture_run()
                self._temporary = tempfile.TemporaryDirectory(prefix='pyfracpaq-preview-')
                context = RunContext(snapshot, Path.cwd().resolve(), Path(self._temporary.name),
                                     uuid4().hex)
            elif config.path.suffix.lower() not in ('.txt', '.svg'):
                raise FieldError('edit_filename',
                                 'Node preview requires a TXT or supported SVG file.')
        except FieldError as error:
            self._error(str(error), error.field)
            return
        self._input_changed()
        revision = self.revision

        def operation(
            progress: Progress, interrupted: Callable[[], bool],
        ) -> PreviewResult | None:
            progress(-1, 'Reading node file...')
            svg = image = None
            if config.kind == 'image':
                image = read_image(config.path, image_parameters,
                                   pixels_per_metre=config.pixels_per_metre,
                                   progress=progress, interrupted=interrupted)
                dataset = image.dataset
            elif config.path.suffix.lower() == '.svg':
                svg = read_svg(config.path, pixels_per_metre=config.pixels_per_metre)
                dataset = svg.dataset
            else:
                dataset = read_txt(config.path, pixels_per_metre=config.pixels_per_metre)
            if interrupted():
                return None
            progress(100, 'Collecting fracture trace data...')
            return PreviewResult(dataset, config, revision, svg, image, context)

        self._start_job('preview', operation, 'edit_filename')

    @Slot()
    def run_selected(self) -> None:
        if self.busy:
            return
        try:
            if self.profile_picker.active:
                raise FieldError('pushbutton_selectgraphendpoints',
                                 'Finish selecting the line or press Escape first.')
            if self.dataset is None:
                raise FieldError('edit_filename',
                                 'Click Preview before running analyses.')
            config = self.capture_run()
            self.last_config = config
            if config.input != self.preview_input:
                self._input_changed()
                raise FieldError('edit_filename',
                                 'The input changed. Click Preview again.')
            self.registry.validate(config)
        except FieldError as error:
            self._error(str(error), error.field)
            return
        self._temporary = tempfile.TemporaryDirectory(prefix='pyfracpaq-run-')
        context = RunContext(config, Path.cwd().resolve(), Path(self._temporary.name),
                             uuid4().hex)
        self.last_context = context
        dataset = self.dataset

        def operation(
            progress: Progress, interrupted: Callable[[], bool],
        ) -> tuple[AnalysisResult, ...]:
            return self.registry.execute(dataset, context, progress, interrupted)

        self._start_job('run', operation, 'pushbutton_run')

    def _start_job(self, kind: str, operation: Operation, field: str) -> None:
        self._job_kind = kind
        self._job_result = None
        self._job_failure = None
        self.last_error = None
        self.thread = QThread(self)
        self.worker = JobWorker(operation, field)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self._progress)
        self.worker.result.connect(self._store_result)
        self.worker.failed.connect(self._store_failure)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self._job_finished)
        self.thread.finished.connect(self.thread.deleteLater)
        label = 'Reading node file...' if kind == 'preview' else 'Running...'
        self.progress_dialog = QProgressDialog(label, '', 0, 0, self)
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.setWindowTitle('Preview' if kind == 'preview' else 'Run')
        self.progress_dialog.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.show()
        self._status('Reading node file...' if kind == 'preview' else 'Running...')
        self._sync_state()
        self.thread.start()

    @Slot(int, str)
    def _progress(self, value: int, text: str) -> None:
        if self._closing:
            return
        if self.progress_dialog is not None:
            self.progress_dialog.setLabelText(text)
            self.progress_dialog.setRange(0, 0 if value < 0 else 100)
            if value >= 0:
                self.progress_dialog.setValue(value)
        self._status(text)

    @Slot(object)
    def _store_result(self, result: object) -> None:
        self._job_result = result

    @Slot(object)
    def _store_failure(self, failure: JobFailure) -> None:
        self._job_failure = failure

    @Slot()
    def _job_finished(self) -> None:
        kind = self._job_kind
        self.worker = None
        self.thread = None
        deferred = False
        try:
            if self._closing:
                self.close()
                return
            if self._job_failure is not None:
                self._error(self._job_failure.message, self._job_failure.field,
                            self._job_failure.exception_type)
            elif kind == 'preview':
                result = self._job_result
                if (isinstance(result, PreviewResult)
                        and result.revision == self.revision):
                    self._accept_preview(result)
                else:
                    self._status('Input changed. Click Preview.')
            else:
                self._accept_run(self._job_result or ())
                deferred = True
        except Exception as error:
            LOG.exception('Result presentation failed')
            field = (error.field if isinstance(error, FieldError)
                     else 'edit_filename' if kind == 'preview' else 'pushbutton_run')
            self._error(str(error), field, type(error).__name__)
        finally:
            if not deferred:
                self._finish_job(kind)

    def _finish_job(self, kind: str) -> None:
        self._rendering = False
        if self._pending_figures is not None:
            self._pending_figures.close()
            self._pending_figures = None
        if self.progress_dialog is not None:
            self.progress_dialog.close()
            self.progress_dialog.deleteLater()
            self.progress_dialog = None
        if self._temporary is not None:
            self._temporary.cleanup()
            self._temporary = None
        if self._closing:
            self._job_result = None
            self.close()
        else:
            self._sync_state()
            if kind == 'preview' and self.dataset is not None:
                self.controls['pbMapsTab'].setFocus()
        self.job_completed.emit(kind)

    def _accept_preview(self, result: PreviewResult) -> None:
        if self.capture_input() != result.config:
            self._status('Input changed. Click Preview.')
            return
        if result.svg is not None:
            write_conversion(result.svg)
        if result.image is not None:
            from pyfracpaq.plots.hough import render_hough
            self.present_figure(render_hough(result.image.hough), result.context)
            if result.dataset is None:
                raise FieldError('edit_minlength', 'No Hough lines survived extraction. '
                                 'Review peaks, threshold, gap and minimum length; '
                                 'the Hough diagnostic has been saved.')
        self.dataset = result.dataset
        self.preview_input = result.config
        d, b = self.dataset, self.dataset.bounds
        statistics = (('Min. X coordinate', b.x_min), ('Min. Y coordinate', b.y_min),
                      ('Max. X coordinate', b.x_max), ('Max. Y coordinate', b.y_max),
                      ('Number of traces', d.n_traces),
                      ('Number of segments', d.n_segments),
                      ('Number of nodes', d.n_nodes))
        self.controls['label_stats'].setText('\n'.join(f'{label}: {value:g}'
                                                     for label, value in statistics))
        tolerance = f'{max(b.width, b.height) / 1000:.2f}'
        self.controls['edit_numpixelsItoY'].setText(tolerance)
        self.stack.setCurrentIndex(0)
        self._draw_preview()
        LOG.info('Traces: %s; segments: %s; nodes: %s; units: %s',
                 d.n_traces, d.n_segments, d.n_nodes, d.length_unit)
        for diagnostic in d.diagnostics:
            LOG.info('Line %s, node %s: %s', diagnostic.source_line,
                     diagnostic.source_node_index + 1, diagnostic.message)
        self._status('Ready. Click Run to generate maps and graphs.')
        self.controls['pbMapsTab'].setFocus()

    def _accept_run(self, results: tuple[AnalysisResult, ...]) -> None:
        specs = {spec.id: spec for spec in self.registry.specs}

        def outputs():
            for result in results:
                spec = specs[result.analysis_id]
                if spec.render is not None:
                    try:
                        for output in spec.render(result.data, self.last_context.config):
                            yield spec, output
                    except Exception as error:
                        raise FieldError(spec.checkbox, f'{spec.label}: {error}') from error

        self._pending_figures = outputs()
        self._rendering = True
        self._sync_state()
        QTimer.singleShot(0, self._present_next)

    @Slot()
    def _present_next(self) -> None:
        if self._closing:
            self._finish_job('run')
            return
        field = 'pushbutton_run'
        try:
            spec, output = next(self._pending_figures)
            field = spec.checkbox
            self._progress(-1, f'Saving PNG: {output.basename}...')
            self.present_figure(output, self.last_context)
        except StopIteration:
            self._status('Completed. Selected outputs have been generated.')
            self._finish_job('run')
            return
        except Exception as error:
            LOG.exception('Figure presentation failed')
            self._error(str(error), error.field if isinstance(error, FieldError) else field,
                        type(error).__name__)
            self._finish_job('run')
            return
        # Keep Qt responsive between exports, without reentrant processEvents
        # or drawing Matplotlib from a worker thread. One PNG is atomic work.
        QTimer.singleShot(0, self._present_next)

    def present_figure(self, output: FigureOutput, context: RunContext) -> FigureWindow:
        export_png(output.figure, output.basename, context.config.tag,
                   context.output_directory)
        window = FigureWindow(output.figure, output.basename, self)
        self.figure_windows.append(window)
        window.destroyed.connect(lambda: self._forget_figure(window))
        window.show()
        return window

    def _forget_figure(self, window: FigureWindow) -> None:
        if window in self.figure_windows:
            self.figure_windows.remove(window)

    @Slot()
    def _flip_changed(self) -> None:
        if self.dataset is not None:
            self._draw_preview()
            self._status('Axes flipped.')

    def _draw_preview(self) -> None:
        draw_preview(self.figure, self.dataset,
                     flip_x=self.controls['pushbutton_flipx'].isChecked(),
                     flip_y=self.controls['pushbutton_flipy'].isChecked())
        if self.dataset is not None:
            self.profile_picker.draw(self.figure.axes[0])
        self.board.position_preview_axes()
        self.canvas.draw_idle()

    def _profile_changed(self) -> None:
        self._draw_preview()
        self._sync_state()

    def focus_field(self, name: str) -> None:
        self.activateWindow()
        widget = self.controls.widgets.get(name, self.controls['edit_filename'])
        ancestor = widget
        while ancestor is not None:
            if ancestor.objectName() in PANELS:
                self.stack.setCurrentIndex(PANELS.index(ancestor.objectName()))
                break
            ancestor = ancestor.parentWidget()
        panel_scroll = self.stack.currentWidget()
        if isinstance(panel_scroll, QScrollArea) and self.stack.isVisible():
            panel_scroll.ensureWidgetVisible(widget)
        self.scroll.ensureWidgetVisible(widget)
        widget.setFocus(Qt.FocusReason.OtherFocusReason)
        if isinstance(widget, QLineEdit):
            widget.selectAll()

    def _error(
        self, message: str, field: str, exception_type: str = 'InputError',
    ) -> None:
        self.last_error = JobFailure(message, field, exception_type)
        self._status(message.splitlines()[0])
        LOG.error('%s', message)
        box = QMessageBox(QMessageBox.Icon.Critical, 'Input error',
                          message[:800], QMessageBox.StandardButton.Ok, self)
        box.setTextFormat(Qt.TextFormat.PlainText)
        box.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        if len(message) > 800:
            box.setDetailedText(message)
        self.messages.append(box)
        box.finished.connect(lambda: QTimer.singleShot(
            0, lambda: self.focus_field(field) if not self._closing else None,
        ))
        box.destroyed.connect(
            lambda: self.messages.remove(box) if box in self.messages else None,
        )
        box.show()
        self.focus_field(field)
        self.error_reported.emit(message, field)

    def closeEvent(self, event: QCloseEvent) -> None:
        self._closing = True
        for window in list(self.figure_windows):
            window.close()
        for message in list(self.messages):
            message.close()
        if self.busy:
            if self.thread is not None:
                self.thread.requestInterruption()
            self._status('Closing after the current operation...')
            self._sync_state()
            event.ignore()
            return
        event.accept()
