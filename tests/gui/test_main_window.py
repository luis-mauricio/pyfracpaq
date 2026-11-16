"""Real Qt flows against the FIG contract and TXT geometric oracles."""

from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from threading import Event, get_ident

import numpy as np
import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QCheckBox, QGroupBox, QLineEdit, QWidget
from shiboken6 import isValid

from pyfracpaq import CONTACT_EMAIL,RELEASE_DATE,__version__
from pyfracpaq.analysis import AnalysisRegistry, AnalysisSpec
from pyfracpaq.app import configure_application
from pyfracpaq.gui import MainWindow
from pyfracpaq.gui.controls import HOUGH, NAVIGATION, PANELS, reference_text
from pyfracpaq.gui.main_window import INTERACTIVE
from reference_common import ROOT

MIXED = ROOT / 'tests/fixtures/nodes/mixed.txt'


@pytest.fixture
def window(qapp, qtbot):
    configure_application(qapp)
    result = MainWindow()
    result.resize(1250, 739)
    result.show()
    qtbot.waitExposed(result)
    yield result
    if isValid(result):
        result.close()
        qtbot.waitUntil(lambda: not isValid(result), timeout=5000)


def preview(window, qtbot, path=MIXED):
    window.controls['edit_filename'].setText(str(path))
    with qtbot.waitSignal(window.job_completed, timeout=5000):
        qtbot.mouseClick(window.controls['pushbutton_preview'], Qt.MouseButton.LeftButton)
    assert window.dataset is not None


def close_messages(window):
    for message in list(window.messages):
        message.accept()


def test_all_reference_objects_types_defaults_and_opening_state(window):
    c = window.controls
    assert set(c.widgets) == set(c.specs)
    assert len(c.widgets) == 142
    assert all(c[name].objectName() == name for name in c.specs)
    for name, spec in c.specs.items():
        widget = c[name]
        style = spec.get('Style')
        if style in ('checkbox', 'radiobutton'):
            assert widget.isChecked() == bool(spec.get('Value', 0)), name
            assert widget.text() == reference_text(spec['String']), name
        elif style == 'edit':
            assert widget.text() == reference_text(spec.get('String', '')), name
        elif style == 'popupmenu':
            assert [widget.itemText(i) for i in range(widget.count())] == spec['String']
            assert widget.currentIndex() == 1
        elif style in ('text', 'pushbutton'):
            expected=(f'Version {__version__}, {RELEASE_DATE}   E-mail: {CONTACT_EMAIL}'
                      if name=='text4' else reference_text(spec['String']).strip())
            assert widget.text().strip() == expected, name
        elif isinstance(widget, QGroupBox):
            assert widget.title().replace('&&', '&') == reference_text(spec.get('Title', ''))
    assert c['edit_filename'].isEnabled()
    assert not c['pushbutton_preview'].isEnabled()
    assert not c['pushbutton_run'].isEnabled()
    assert not window.stack.isVisible()
    assert all(not c[name].isEnabled() for name in NAVIGATION)
    assert all(not c[name].isEnabled() for name in HOUGH)
    assert c['label_stats'].text() == ''
    assert c['text_message'].text() == 'Ready.'


def test_preview_statistics_navigation_and_flips_do_not_change_arrays(window, qtbot):
    preview(window, qtbot)
    d = window.dataset
    c = window.controls
    assert (d.n_traces, d.n_segments, d.n_nodes) == (2, 3, 5)
    assert c['label_stats'].text().splitlines() == [
        'Min. X coordinate: 0', 'Min. Y coordinate: 0',
        'Max. X coordinate: 4', 'Max. Y coordinate: 6',
        'Number of traces: 2', 'Number of segments: 3', 'Number of nodes: 5',
    ]
    assert c['edit_numpixelsItoY'].text() == '0.01'
    assert c['pushbutton_run'].isEnabled()
    assert window.stack.isVisible() and window.stack.currentIndex() == 0
    for i, name in enumerate(NAVIGATION):
        qtbot.mouseClick(c[name], Qt.MouseButton.LeftButton)
        assert window.stack.currentIndex() == i
        assert c[PANELS[i]].isVisible()
        assert all(not c[panel].isVisible() for j, panel in enumerate(PANELS) if i != j)
    original = d.as_arrays().node_coordinates.copy()
    for flip_x, flip_y in ((True, False), (True, True), (False, True), (False, False)):
        c['pushbutton_flipx'].setChecked(flip_x)
        c['pushbutton_flipy'].setChecked(flip_y)
        axes = window.figure.axes[0]
        assert axes.xaxis_inverted() == flip_x
        assert axes.yaxis_inverted() == flip_y
        np.testing.assert_array_equal(d.as_arrays().node_coordinates, original)


@pytest.mark.parametrize('field,text', [
    ('edit_filename', 'another.txt'), ('edit_scaling', '2'),
    ('edit_houghpeaks', '200'), ('edit_houghthreshold', '0.4'),
    ('edit_fillgap', '8'), ('edit_minlength', '4'),
])
def test_input_changes_invalidate_old_preview(window, qtbot, field, text):
    preview(window, qtbot)
    window.controls[field].setText(text)
    assert window.dataset is None
    assert window.preview_input is None
    assert not window.controls['pushbutton_run'].isEnabled()
    assert not window.stack.isVisible()
    assert window.controls['label_stats'].text() == ''


def test_type_inference_manual_override_and_browse_cancel(window, qtbot, monkeypatch):
    from pyfracpaq.gui import main_window

    c = window.controls
    c['edit_filename'].setText('/tmp/EXAMPLE.SVG')
    assert c['radiobutton_node'].isChecked()
    c['edit_filename'].setText('/tmp/PHOTO.TIFF')
    assert c['radiobutton_image'].isChecked()
    assert all(c[name].isEnabled() for name in HOUGH)
    c['radiobutton_node'].setChecked(True)
    assert all(not c[name].isEnabled() for name in HOUGH)
    preview(window, qtbot)
    before = window.dataset, window.revision, c['edit_filename'].text()
    monkeypatch.setattr(main_window.QFileDialog, 'getOpenFileName', lambda *a: ('', ''))
    window.browse()
    assert (window.dataset, window.revision, c['edit_filename'].text()) == before
    monkeypatch.setattr(main_window.QFileDialog, 'getOpenFileName',
                        lambda *a: ('/tmp/FILE.JPG', ''))
    window.browse()
    assert c['edit_filename'].text() == '/tmp/FILE.JPG'
    assert c['radiobutton_image'].isChecked() and window.dataset is None


def test_dependencies_and_choices_survive_navigation(window, qtbot):
    preview(window, qtbot)
    c = window.controls
    c['checkbox_sliptendency'].setChecked(True)
    assert c['edit_sigma1'].isEnabled()
    c['checkbox_sliptendency'].setChecked(False)
    assert not c['edit_sigma1'].isEnabled()
    c['checkbox_densitymap'].setChecked(True)
    assert c['edit_numscancircles'].isEnabled()
    c['checkbox_densitymap'].setChecked(False)
    assert not c['edit_numscancircles'].isEnabled()
    c['checkbox_logloglength'].setChecked(True)
    c['checkbox_mle'].setChecked(True)
    assert c['edit_lc'].isEnabled()
    c['checkbox_permellipse'].setChecked(True)
    assert c['edit_fixedaperture'].isEnabled()
    assert not c['edit_aperturefactor'].isEnabled()
    c['radiobutton_scaledaperture'].setChecked(True)
    assert c['edit_aperturefactor'].isEnabled()
    assert not c['edit_fixedaperture'].isEnabled()
    c['checkbox_wavelet'].setChecked(True)
    assert c['edit_aString'].isEnabled()
    c['checkbox_intensitygraphalong'].setChecked(True)
    assert c['edit_numscancirclesgraph'].isEnabled()
    for name in NAVIGATION:
        qtbot.mouseClick(c[name], Qt.MouseButton.LeftButton)
    assert c['checkbox_mle'].isChecked() and c['radiobutton_scaledaperture'].isChecked()


def test_unavailable_outputs_are_explicit_and_do_not_create_files(window, qtbot, tmp_path, monkeypatch):
    preview(window, qtbot)
    monkeypatch.chdir(tmp_path)
    # The absolute source is unaffected by a new output working directory.
    window.controls['edit_sigma1'].setText('invalid but not selected')
    # All production analyses are implemented now. Exercise the registry's
    # unavailable-extension diagnostic with an explicitly disabled test entry.
    window.registry = AnalysisRegistry([replace(spec, compute=None, render=None)
        if spec.id == 'WAV-01' else spec for spec in window.registry.specs])
    window.controls['checkbox_wavelet'].setChecked(True)
    window.run_selected()
    assert window.last_error is not None
    assert 'not available' in window.last_error.message
    assert window.last_error.field != 'edit_sigma1'
    assert window.last_config is not None
    assert not window.busy and not list(tmp_path.iterdir())
    close_messages(window)


def test_frozen_configuration_and_worker_use_one_snapshot(window, qtbot, tmp_path, monkeypatch):
    preview(window, qtbot)
    gate = Event()
    started = Event()
    calls = []
    main_thread = get_ident()

    def compute(dataset, context, progress):
        calls.append((context, get_ident(), dataset.total_length))
        started.set()
        assert gate.wait(3)
        progress(100, 'Measured total length.')
        return dataset.total_length

    window.registry = AnalysisRegistry([
        AnalysisSpec('MAP-01', 'checkbox_tracemap', 'Traces, segments', compute=compute),
    ])
    monkeypatch.chdir(tmp_path)
    window.run_selected()
    qtbot.waitUntil(started.is_set)
    assert not window.controls['pushbutton_run'].isEnabled()
    assert window.controls['pushbutton_exit'].isEnabled()
    captured = window.last_config
    assert captured.tag == 'Run1' and captured.selected == ('MAP-01',)
    assert calls[0][1] != main_thread
    assert calls[0][2] == 11
    with pytest.raises(FrozenInstanceError):
        captured.tag = 'changed'
    window.controls['edit_FilenameTag'].setText('Changed after capture')
    assert calls[0][0].config.tag == 'Run1'
    temporary = calls[0][0].temporary_directory
    assert temporary.is_dir()
    with qtbot.waitSignal(window.job_completed, timeout=5000):
        gate.set()
    assert not temporary.exists()
    assert window.controls['pushbutton_run'].isEnabled()
    assert window.last_error is None


def test_failure_focus_and_recovery_after_invalid_file(window, qtbot, tmp_path):
    path = tmp_path / 'arquivo inválido.txt'
    path.write_text('0\t0\t1\n')
    window.controls['edit_filename'].setText(str(path))
    with qtbot.waitSignal(window.job_completed, timeout=5000):
        window.preview()
    assert window.dataset is None
    assert window.last_error.field == 'edit_filename'
    assert ':1:3:' in window.last_error.message
    assert not window.controls['pushbutton_run'].isEnabled()
    close_messages(window)
    qtbot.waitUntil(lambda: window.controls['edit_filename'].hasFocus())
    preview(window, qtbot)
    assert window.last_error is None


def test_programmatic_edit_during_preview_discards_stale_worker_result(window, qtbot, monkeypatch):
    from pyfracpaq.gui import main_window
    original_reader = main_window.read_txt
    entered, release = Event(), Event()

    def delayed(*args, **kwargs):
        entered.set()
        assert release.wait(3)
        return original_reader(*args, **kwargs)

    monkeypatch.setattr(main_window, 'read_txt', delayed)
    window.controls['edit_filename'].setText(str(MIXED))
    window.preview()
    qtbot.waitUntil(entered.is_set)
    window.controls['edit_scaling'].setText('2')
    with qtbot.waitSignal(window.job_completed, timeout=5000):
        release.set()
    assert window.dataset is None
    assert not window.controls['pushbutton_run'].isEnabled()


def test_scale_and_external_file_change_require_new_preview(window, qtbot, tmp_path):
    source = tmp_path / 'source.txt'
    source.write_text(MIXED.read_text())
    preview(window, qtbot, source)
    source.write_text('0\t0\t8\t0\n')
    window.run_selected()
    assert window.dataset is None
    assert 'changed' in window.last_error.message
    close_messages(window)
    window.controls['edit_scaling'].setText('2')
    with qtbot.waitSignal(window.job_completed, timeout=5000):
        window.preview()
    assert window.dataset.length_unit == 'metres'
    assert window.dataset.total_length == 4


def test_closing_during_work_waits_and_leaves_unrelated_windows_open(window, qtbot):
    preview(window, qtbot)
    entered, release = Event(), Event()

    def compute(dataset, context, progress):
        entered.set()
        assert release.wait(3)
        return dataset.total_length

    window.registry = AnalysisRegistry([
        AnalysisSpec('MAP-01', 'checkbox_tracemap', 'Traces, segments', compute=compute),
    ])
    other = QWidget()
    qtbot.addWidget(other)
    other.show()
    window.run_selected()
    qtbot.waitUntil(entered.is_set)
    qtbot.mouseClick(window.controls['pushbutton_exit'], Qt.MouseButton.LeftButton)
    assert window.busy and window._closing
    release.set()
    qtbot.waitUntil(lambda: not isValid(window), timeout=5000)
    assert other.isVisible()


def test_selected_parameter_error_opens_its_panel_and_focuses_field(window, qtbot):
    preview(window, qtbot)
    c = window.controls
    c['checkbox_densitymap'].setChecked(True)
    c['edit_numscancircles'].setText('2.5')
    window.stack.setCurrentIndex(4)
    window.run_selected()
    assert window.last_error.field == 'edit_numscancircles'
    assert window.stack.currentIndex() == 0
    close_messages(window)
    qtbot.waitUntil(lambda: c['edit_numscancircles'].hasFocus())


def test_real_renderer_exports_on_main_thread_and_owns_only_its_windows(
    window, qtbot, tmp_path, monkeypatch,
):
    from matplotlib.figure import Figure
    from PIL import Image
    from pyfracpaq.plots import FigureOutput, draw_preview

    preview(window, qtbot)
    render_threads = []

    def render(dataset, config):
        render_threads.append(get_ident())
        figure = Figure()
        draw_preview(figure, dataset, flip_x=config.flip_x, flip_y=config.flip_y)
        return (FigureOutput('FracPaQ2D_test', figure),)

    window.registry = AnalysisRegistry([
        AnalysisSpec('MAP-01', 'checkbox_tracemap', 'Traces, segments',
                     compute=lambda dataset, context, progress: dataset, render=render),
    ])
    monkeypatch.chdir(tmp_path)
    with qtbot.waitSignal(window.job_completed, timeout=5000):
        window.run_selected()
    assert window.last_error is None
    assert render_threads == [get_ident()]
    target = tmp_path / 'FracPaQ2D_test_Run1.png'
    with Image.open(target) as image:
        assert image.size == (4724, 4724)
    assert len(window.figure_windows) == 1
    figure_window = window.figure_windows[0]
    assert figure_window.isVisible() and figure_window.toolbar.actions()
    other = QWidget()
    qtbot.addWidget(other)
    other.show()
    window.close()
    qtbot.waitUntil(lambda: not isValid(window))
    assert not isValid(figure_window)
    assert other.isVisible()


def test_worker_failure_identifies_analysis_and_restores_run(window, qtbot):
    preview(window, qtbot)

    def fail(dataset, context, progress):
        raise ArithmeticError('A numerical problem')

    window.registry = AnalysisRegistry([
        AnalysisSpec('MAP-01', 'checkbox_tracemap', 'Traces, segments', compute=fail),
    ])
    with qtbot.waitSignal(window.job_completed, timeout=5000):
        window.run_selected()
    assert window.last_error.field == 'checkbox_tracemap'
    assert window.last_error.message == 'Traces, segments: A numerical problem'
    assert not window.busy and window.controls['pushbutton_run'].isEnabled()
    assert window.dataset is not None
    close_messages(window)


def test_disabled_mle_is_not_selected_and_suboptions_are_cleared(window, qtbot):
    preview(window, qtbot)
    c = window.controls
    c['checkbox_logloglength'].setChecked(True)
    c['checkbox_mle'].setChecked(True)
    assert 'LEN-07' in window.capture_run().selected
    c['checkbox_logloglength'].setChecked(False)
    assert not c['checkbox_mle'].isChecked()
    assert not c['checkbox_mle'].isEnabled()
    assert 'LEN-07' not in window.capture_run().selected
    c['checkbox_shownodes'].setChecked(True)
    c['checkbox_tracemap'].setChecked(False)
    assert not c['checkbox_shownodes'].isChecked()
    c['checkbox_rose'].setChecked(False)
    assert not c['checkbox_rosecolour'].isChecked()


def test_missing_svg_image_and_bad_scale_produce_no_dataset(window, qtbot):
    c = window.controls
    for path, field in [('/tmp/example.SVG', 'edit_filename'),
                        ('/tmp/example.JPG', 'edit_filename')]:
        c['edit_filename'].setText(path)
        with qtbot.waitSignal(window.job_completed, timeout=5000):
            window.preview()
        assert not window.busy and window.dataset is None
        assert window.last_error.field == field
        assert 'not available' not in window.last_error.message
        close_messages(window)
    c['edit_filename'].setText(str(MIXED))
    c['edit_scaling'].setText('nan')
    window.preview()
    assert not window.busy and window.last_error.field == 'edit_scaling'
    close_messages(window)


def test_main_window_factory_is_singleton(qapp, qtbot):
    from pyfracpaq.app import create_main_window

    configure_application(qapp)
    first = create_main_window()
    second = create_main_window()
    assert first is second
    first.close()
    qtbot.waitUntil(lambda: not isValid(first))


def test_sprint3_real_selected_outputs_and_ezrose(window, qtbot, tmp_path, monkeypatch):
    from PIL import Image

    preview(window, qtbot)
    for spec in window.registry.specs:
        window.controls[spec.checkbox].setChecked(spec.id in (
            'MAP-01', 'MAP-04', 'MAP-05', 'MAP-06', 'ANG-01', 'ANG-02'))
    window.controls['checkbox_shownodes'].setChecked(True)
    window.controls['checkbox_rosecolour'].setChecked(True)
    window.controls['checkbox_roselengthweighted'].setChecked(True)
    window.controls['checkbox_showrosemean'].setChecked(True)
    window.controls['edit_degfromnorth'].setText('10')
    window.controls['pushbutton_flipx'].setChecked(True)
    monkeypatch.chdir(tmp_path)
    with qtbot.waitSignal(window.job_completed, timeout=15000):
        window.run_selected()
    assert window.last_error is None
    assert len(window.figure_windows) == 6
    expected = {
        'FracPaQ2D_tracemap_Run1.png', 'FracPaQ2D_tracelengthmap_Run1.png',
        'FracPaQ2D_segmentlengthmap_Run1.png', 'FracPaQ2D_segmentstrikemap_Run1.png',
        'FracPaQ2D_histoangle_Run1.png', 'FracPaQ2D_roseangleEqArea_Run1.png',
    }
    assert {path.name for path in tmp_path.glob('*.png')} == expected
    for path in tmp_path.glob('*.png'):
        with Image.open(path) as image:
            assert image.size == (4724, 4724)
            assert abs(image.info['dpi'][0] - 600) < .01
    angles = (tmp_path / 'FracPaQ2DEZROSE_Run1.txt').read_text().splitlines()
    assert len(angles) == 6
    assert [float(a) for a in angles] == sorted(float(a) for a in angles)
    assert all(len(a.split('.')[-1]) == 2 for a in angles)


def test_smaller_desktop_scrolls_and_preserves_keyboard_access(window, qtbot):
    preview(window, qtbot)
    window.resize(800, 480)
    qtbot.waitUntil(lambda: window.scroll.horizontalScrollBar().maximum() > 0)
    assert window.scroll.verticalScrollBar().maximum() > 0
    window.controls['checkbox_wavelet'].setChecked(True)
    window.focus_field('edit_aString')
    qtbot.waitUntil(lambda: window.controls['edit_aString'].hasFocus())
    field = window.controls['edit_aString']
    position = field.mapTo(window.scroll.viewport(), QPoint(0, 0))
    assert 0 <= position.x() < window.scroll.viewport().width()
    assert 0 <= position.y() < window.scroll.viewport().height()


def test_sprint4_seven_length_figures_censoring_and_raw_txt(window, qtbot, tmp_path, monkeypatch):
    from PIL import Image
    from sprint4_reference import INPUT

    preview(window, qtbot, INPUT)
    for spec in window.registry.specs:
        window.controls[spec.checkbox].setChecked(spec.id in ('LEN-02', 'LEN-03', 'LEN-06'))
    window.controls['checkbox_censor'].setChecked(True)
    window.controls['edit_degfromnorth'].setText('10')
    window.controls['pushbutton_flipy'].setChecked(True)
    before = window.dataset.as_arrays().segment_lengths.copy()
    monkeypatch.chdir(tmp_path)
    with qtbot.waitSignal(window.job_completed, timeout=20000):
        window.run_selected()
    assert window.last_error is None
    assert len(window.figure_windows) == 7
    assert len(list(tmp_path.glob('*.png'))) == 7
    assert len(list(tmp_path.glob('*.txt'))) == 3
    for target in tmp_path.glob('*.png'):
        with Image.open(target) as image:
            assert image.size == (4724, 4724)
            assert abs(image.info['dpi'][0] - 600) < .01
    assert (tmp_path / 'FracPaQ2Dsegmentangleslengths_Run1.txt').read_bytes() \
        == b' 90.00\t  3.00\n  0.00\t  4.00\n 36.87\t  5.00\n'
    np.testing.assert_array_equal(window.dataset.as_arrays().segment_lengths, before)


def test_sprint4_default_run_is_now_available(window, qtbot, tmp_path, monkeypatch):
    preview(window, qtbot)
    monkeypatch.chdir(tmp_path)
    with qtbot.waitSignal(window.job_completed, timeout=15000):
        window.run_selected()
    assert window.last_error is None
    assert len(window.figure_windows) == 5
    assert len(list(tmp_path.glob('*.png'))) == 5
    assert len(list(tmp_path.glob('*.txt'))) == 4


@pytest.mark.parametrize('selected', [('MAP-08',), ('MAP-07', 'MAP-08')])
def test_sprint7_run_circular_selection_exports_coupled_txt_and_one_scan_map(
        window, qtbot, tmp_path, monkeypatch, selected):
    preview(window, qtbot)
    for spec in window.registry.specs:
        window.controls[spec.checkbox].setChecked(spec.id in selected)
    window.controls['edit_numscancircles'].setText('3')
    window.controls['checkbox_showcircles'].setChecked(True)
    window.controls['pushbutton_flipy'].setChecked(True)
    before = window.dataset.as_arrays().segment_coordinates.copy()
    monkeypatch.chdir(tmp_path)
    with qtbot.waitSignal(window.job_completed, timeout=15000):
        window.run_selected()
    assert window.last_error is None
    assert len(window.figure_windows) == len(selected) + 1
    assert len(list(tmp_path.glob('*.png'))) == len(selected) + 1
    assert (tmp_path / 'FracPaQ2D_scancircle_Run1.png').is_file()
    assert (tmp_path / 'FracPaQ2Ddensity_Run1.txt').is_file()
    assert (tmp_path / 'FracPaQ2Dintensity_Run1.txt').is_file()
    assert len(list(tmp_path.glob('*.txt'))) == 2
    np.testing.assert_array_equal(window.dataset.as_arrays().segment_coordinates, before)


def test_sprint4_crossplot_alone_and_all_censored_error(window, qtbot, tmp_path, monkeypatch):
    preview(window, qtbot)
    for spec in window.registry.specs:
        window.controls[spec.checkbox].setChecked(spec.id == 'LEN-06')
    monkeypatch.chdir(tmp_path)
    with qtbot.waitSignal(window.job_completed, timeout=10000):
        window.run_selected()
    assert window.last_error is None
    assert len(window.figure_windows) == 1
    output = tmp_path / 'FracPaQ2D_crossplotsegmentlengthangle_Run1.png'
    assert output.is_file()
    prior = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    window.controls['checkbox_logloglength'].setChecked(True)
    window.controls['checkbox_censor'].setChecked(True)
    with qtbot.waitSignal(window.job_completed, timeout=5000):
        window.run_selected()
    assert window.last_error.field == 'checkbox_censor'
    assert 'excluded every' in window.last_error.message
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == prior
    assert len(window.figure_windows) == 1
    assert window.stack.currentIndex() == 1
    close_messages(window)


def test_sprint5_svg_preview_multicolour_map_and_individual_colour(window, qtbot, tmp_path, monkeypatch):
    from pyfracpaq.io.colours import hex_rgb
    source = tmp_path / 'map.SVG'
    source.write_bytes((ROOT / 'tests/fixtures/svg/multicolour.svg').read_bytes())
    monkeypatch.chdir(tmp_path)
    preview(window, qtbot, source)
    assert window.dataset.input_mode == 'svg'
    assert window.dataset.colours == ((0, 0, 1), (1, 0, 0))
    assert len(list(tmp_path.glob('*converted.txt'))) == 2
    for spec in window.registry.specs:
        window.controls[spec.checkbox].setChecked(spec.id in ('MAP-01', 'MAP-06'))
    with qtbot.waitSignal(window.job_completed, timeout=15000):
        window.run_selected()
    assert window.last_error is None and len(window.figure_windows) == 3
    assert (tmp_path / 'FracPaQ2D_tracemap_multicolour_Run1.png').is_file()
    preview(window, qtbot, tmp_path / 'map_colourFF0000_converted.txt')
    assert window.dataset.colours == (hex_rgb('FF0000'),)
    assert window.dataset.n_traces == 1


def test_sprint5_stale_svg_result_does_not_publish_conversion(window, qtbot, tmp_path, monkeypatch):
    from pyfracpaq.gui import main_window
    original = main_window.read_svg
    entered, release = Event(), Event()
    source = tmp_path / 'stale.svg'
    source.write_bytes((ROOT / 'tests/fixtures/svg/simple.svg').read_bytes())

    def delayed(*args, **kwargs):
        result = original(*args, **kwargs)
        entered.set()
        assert release.wait(3)
        return result

    monkeypatch.setattr(main_window, 'read_svg', delayed)
    window.controls['edit_filename'].setText(str(source))
    window.preview()
    qtbot.waitUntil(entered.is_set)
    window.controls['edit_scaling'].setText('2')
    with qtbot.waitSignal(window.job_completed, timeout=5000):
        release.set()
    assert window.dataset is None
    assert not list(tmp_path.glob('*converted.txt'))


def test_sprint6_image_preview_diagnostic_rescale_invalidation_and_default_run(
        window, qtbot, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = ROOT / 'tests/fixtures/images/directional.tif'
    window.controls['edit_houghpeaks'].setText('100')
    preview(window, qtbot, source)
    assert window.dataset.input_mode == 'image'
    assert window.dataset.bounds.x_max == window.dataset.bounds.y_max == 32
    assert len(window.figure_windows) == 1
    assert (tmp_path / 'FracPaQ2D_Houghstuff_Run1.png').is_file()
    with qtbot.waitSignal(window.job_completed, timeout=20000):
        window.run_selected()
    assert window.last_error is None and len(window.figure_windows) == 6
    assert len(list(tmp_path.glob('*.png'))) == 6
    before = window.dataset.total_length
    window.controls['edit_scaling'].setText('2')
    assert window.dataset is None
    preview(window, qtbot, source)
    assert window.dataset.bounds.x_max == 16
    assert window.dataset.total_length == before / 2
    window.controls['edit_fillgap'].setText('8')
    assert window.dataset is None and not window.controls['pushbutton_run'].isEnabled()


def test_sprint6_invalid_metadata_and_parameters_do_not_create_diagnostics(
        window, qtbot, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    c = window.controls
    c['edit_filename'].setText(str(ROOT / 'tests/fixtures/images/rgb_invalid.tif'))
    c['edit_houghpeaks'].setText('100.5')
    window.preview()
    assert not window.busy and window.last_error.field == 'edit_houghpeaks'
    close_messages(window)
    c['edit_houghpeaks'].setText('100')
    with qtbot.waitSignal(window.job_completed, timeout=5000):
        window.preview()
    assert window.dataset is None and window.last_error.field == 'edit_filename'
    assert '8-bit grayscale' in window.last_error.message
    assert not list(tmp_path.iterdir())
    close_messages(window)


def test_sprint6_no_lines_still_exports_hough_and_identifies_parameter(
        window, qtbot, tmp_path, monkeypatch):
    from PIL import Image
    source = tmp_path / 'blank.tif'
    Image.new('L', (16, 12), 255).save(source)
    monkeypatch.chdir(tmp_path)
    window.controls['edit_filename'].setText(str(source))
    with qtbot.waitSignal(window.job_completed, timeout=10000):
        window.preview()
    assert window.dataset is None
    assert window.last_error.field == 'edit_minlength'
    assert 'No Hough lines' in window.last_error.message
    assert (tmp_path / 'FracPaQ2D_Houghstuff_Run1.png').is_file()
    assert len(window.figure_windows) == 1
    assert not window.controls['pushbutton_run'].isEnabled()
    close_messages(window)
