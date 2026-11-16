"""Two canvas clicks and immutable snapshots through real Qt worker/export flows."""

from matplotlib.backend_bases import KeyEvent, MouseEvent
import numpy as np
from PIL import Image
import pytest
from shiboken6 import isValid

from pyfracpaq.app import configure_application
from pyfracpaq.gui import MainWindow
from reference_common import ROOT
from sprint1213_reference import block_dataset, graph_dataset


@pytest.fixture
def window(qapp, qtbot):
    configure_application(qapp)
    result = MainWindow()
    result.show()
    qtbot.waitExposed(result)
    yield result
    if isValid(result):
        for message in result.messages:
            message.accept()
        result.close()
        qtbot.waitUntil(lambda: not isValid(result), timeout=5000)


def preview(window, qtbot, path):
    window.controls['edit_filename'].setText(str(path))
    with qtbot.waitSignal(window.job_completed, timeout=10000):
        window.preview()
    assert window.dataset is not None
    window.canvas.draw()


def click(window, point, *, button=1):
    window.canvas.draw()
    axes = window.figure.axes[0]
    xy = axes.transData.transform(point)
    event = MouseEvent('button_press_event', window.canvas, *xy, button=button)
    window.canvas.callbacks.process('button_press_event', event)


def select(window, keys):
    for spec in window.registry.specs:
        window.controls[spec.checkbox].setChecked(spec.id in keys)


def write_nodes(path, dataset):
    path.write_text('\n'.join('\t'.join(str(value) for point in trace.points for value in point)
                              for trace in dataset.source_traces) + '\n')
    return path


def test_two_clicks_duplicate_cancel_flip_and_input_invalidation(window, qtbot):
    c = window.controls
    assert not c['pushbutton_selectgraphendpoints'].isEnabled()
    preview(window, qtbot, ROOT / 'tests/fixtures/nodes/mixed.txt')
    c['pushbutton_selectgraphendpoints'].click()
    assert window.profile_picker.active and not c['pushbutton_run'].isEnabled()
    click(window, (1, 1))
    assert window.profile_picker.pending == pytest.approx((1, 1))
    click(window, (1, 1))
    assert window.profile_picker.active and window.profile_picker.line is None
    click(window, (3, 4))
    line = window.profile_picker.line
    assert line.start == pytest.approx((1, 1)) and line.end == pytest.approx((3, 4))
    assert c['pushbutton_run'].isEnabled()
    snapshot = window.capture_run()
    c['pushbutton_selectgraphendpoints'].click()
    click(window, (2, 1))
    window.canvas.callbacks.process('key_press_event', KeyEvent('key_press_event', window.canvas, 'escape'))
    assert window.profile_picker.line == line and not window.profile_picker.active
    c['pushbutton_flipx'].setChecked(True)
    c['edit_degfromnorth'].setText('40')
    assert window.profile_picker.line == line and len(window.figure.axes[0].lines) >= 1
    c['edit_scaling'].setText('2')
    assert window.profile_picker.line is None and window.dataset is None
    assert snapshot.profile_line == line


@pytest.mark.parametrize('source', ['nodes/mixed.txt', 'svg/multicolour.svg', 'images/tensor_network.tif'])
def test_six_along_from_outputs_from_cached_txt_svg_or_hough(window, qtbot, tmp_path, monkeypatch, source):
    monkeypatch.chdir(tmp_path)
    preview(window, qtbot, ROOT / 'tests/fixtures' / source)
    dataset = window.dataset
    bounds = dataset.bounds
    y = (bounds.y_min + bounds.y_max) / 2
    window.profile_picker.start()
    click(window, (bounds.x_min + .1 * (bounds.x_max - bounds.x_min), y))
    click(window, (bounds.x_min + .9 * (bounds.x_max - bounds.x_min), y))
    line = window.profile_picker.line
    assert line is not None
    select(window, ('GRA-03', 'GRA-04', 'GRA-05', 'GRA-10', 'GRA-11', 'GRA-12'))
    # Any accidental re-read during Graphs would fail; preview remains cached.
    monkeypatch.setattr('pyfracpaq.gui.main_window.read_txt', lambda *_args, **_kwargs: pytest.fail('Unexpected re-import'))
    with qtbot.waitSignal(window.job_completed, timeout=25000):
        window.run_selected()
    assert window.last_error is None
    assert window.last_config.profile_line == line
    assert len(list(tmp_path.glob('guiFracPaQ2D_*Run1.png'))) == 6
    assert not list(tmp_path.glob('*.txt'))
    with Image.open(tmp_path / 'guiFracPaQ2D_tracelengthfromgraph_Run1.png') as image:
        assert image.size == (4724, 4724) and image.info['dpi'][0] == pytest.approx(600, abs=.01)


def test_absent_selection_fails_before_creating_any_file(window, qtbot, tmp_path, monkeypatch):
    preview(window, qtbot, ROOT / 'tests/fixtures/nodes/mixed.txt')
    monkeypatch.chdir(tmp_path)
    select(window, ('GRA-03',))
    window.run_selected()
    assert window.last_error.field == 'pushbutton_selectgraphendpoints'
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('source', ['nodes/mixed.txt', 'images/tensor_network.tif'])
def test_variogram_only_run_emits_one_figure_and_three_lengths_tables(window, qtbot, tmp_path, monkeypatch, source):
    monkeypatch.chdir(tmp_path)
    preview(window, qtbot, ROOT / 'tests/fixtures' / source)
    select(window, ('LEN-15',))
    expected = window.dataset.as_arrays().segment_midpoints.copy()
    before = set(tmp_path.iterdir())
    with qtbot.waitSignal(window.job_completed, timeout=15000):
        window.run_selected()
    assert window.last_error is None
    created = set(tmp_path.iterdir()) - before
    assert sum(p.suffix == '.png' for p in created) == 1
    assert sum(p.suffix == '.txt' for p in created) == 3
    assert (tmp_path / 'FracPaQ2D_segmentlength_variogram_Run1.png').is_file()
    np.testing.assert_array_equal(window.dataset.as_arrays().segment_midpoints, expected)


@pytest.mark.parametrize('scale', [None, 10])
def test_approved_blocks_run_preserves_resolution_and_calibrates_area(
        window, qtbot, tmp_path, monkeypatch, scale):
    monkeypatch.chdir(tmp_path)
    source = write_nodes(tmp_path / 'rectangles.txt', block_dataset())
    if scale is not None:
        window.controls['edit_scaling'].setText(str(scale))
    preview(window, qtbot, source)
    select(window, ('LEN-13',))
    before = set(tmp_path.iterdir())
    with qtbot.waitSignal(window.job_completed, timeout=20000):
        window.run_selected()
    assert window.last_error is None
    blocks = window._job_result[0].data.blocks
    factor = scale or 1
    np.testing.assert_allclose(blocks.areas, np.array([1444, 1444]) / factor ** 2)
    np.testing.assert_allclose(blocks.centroids, np.array([[30, 30], [90, 50]]) / factor)
    created = set(tmp_path.iterdir()) - before
    assert sum(path.suffix == '.png' for path in created) == 3
    assert sum(path.suffix == '.txt' for path in created) == 3
    assert [path.name for path in created if path.suffix == '.bmp'] == ['FracPaQ2D_blocksize.bmp']
    with Image.open(tmp_path / 'FracPaQ2D_blocksize.bmp') as image:
        assert image.size == (100, 60) and image.mode == 'L'


@pytest.mark.parametrize('selected', [('GRA-06',), ('GRA-07',), ('GRA-06', 'GRA-07')])
def test_approved_circular_graphs_run_couples_both_profiles_once_with_area_density(
        window, qtbot, tmp_path, monkeypatch, selected):
    monkeypatch.chdir(tmp_path)
    source = write_nodes(tmp_path / 'graphs.txt', graph_dataset())
    preview(window, qtbot, source)
    window.profile_picker.start()
    click(window, (-5.5, 0))
    click(window, (5.5, 0))
    window.controls['edit_numscancirclesgraph'].setText('3')
    select(window, selected)
    before = set(tmp_path.iterdir())
    initial_windows = len(window.figure_windows)
    with qtbot.waitSignal(window.job_completed, timeout=20000):
        window.run_selected()
    assert window.last_error is None
    created = set(tmp_path.iterdir()) - before
    assert {path.name for path in created} == {
        'guiFracPaQ2D_graphtracemap_Run1.png', 'guiFracPaQ2D_intensityalonggraph_Run1.png',
        'guiFracPaQ2D_densityalonggraph_Run1.png'}
    assert len(window.figure_windows) == initial_windows + 3
    circle = window._job_result[0].data.circles
    assert circle.radius == pytest.approx(11 / 6)
    assert circle.endpoints_inside.tolist() == [0, 2, 0]
    np.testing.assert_allclose(circle.density, [0, 1 / (np.pi * circle.radius ** 2), 0])
    assert all(result.data is window._job_result[0].data for result in window._job_result)


def test_all_sprint1213_outputs_share_caches_and_export_thirteen_figures(
        window, qtbot, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = write_nodes(tmp_path / 'combined.txt', block_dataset())
    preview(window, qtbot, source)
    window.profile_picker.start()
    click(window, (15, 40))
    click(window, (105, 40))
    window.controls['edit_numscancirclesgraph'].setText('3')
    selected = ('LEN-13', 'LEN-15', 'GRA-03', 'GRA-04', 'GRA-05',
                'GRA-06', 'GRA-07', 'GRA-10', 'GRA-11', 'GRA-12')
    select(window, selected)
    before = set(tmp_path.iterdir())
    with qtbot.waitSignal(window.job_completed, timeout=30000):
        window.run_selected()
    assert window.last_error is None
    lengths = [result.data for result in window._job_result if result.analysis_id.startswith('LEN-')]
    graphs = [result.data for result in window._job_result if result.analysis_id.startswith('GRA-')]
    assert len(lengths) == 2 and lengths[0] is lengths[1]
    assert len(graphs) == 8 and all(result is graphs[0] for result in graphs)
    created = set(tmp_path.iterdir()) - before
    assert sum(path.suffix == '.png' for path in created) == 13
    assert sum(path.suffix == '.txt' for path in created) == 3
    assert sum(path.suffix == '.bmp' for path in created) == 1
