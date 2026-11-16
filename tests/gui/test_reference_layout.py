"""Regression coverage for the reported navigation, proportions and startup size."""

import json

import pytest
from PySide6.QtCore import QPoint, QSize, Qt
from PySide6.QtWidgets import QGroupBox, QLineEdit

from pyfracpaq.app import configure_application
from pyfracpaq.gui import MainWindow
from pyfracpaq.gui.controls import NAVIGATION, PANELS
from pyfracpaq.gui.layout import initial_window_size
from pyfracpaq.resources import ui_specification
from reference_common import ROOT


@pytest.fixture
def window(qapp, qtbot):
    configure_application(qapp)
    result = MainWindow()
    result.resize(1250, 739)
    result.show()
    qtbot.waitExposed(result)
    yield result
    result.close()


def test_border_and_font_metadata_survive_resource_extraction():
    original = json.loads((ROOT / 'tests/reference/gui/guiFracPaQ2D.json').read_text())
    source = {o['tag']: o['saved_properties'] for o in original['objects']}
    for obj in ui_specification()['objects']:
        for prop in ('BorderType', 'FontWeight', 'FontSize', 'HorizontalAlignment'):
            if prop in source[obj['tag']]:
                assert obj[prop] == source[obj['tag']][prop]
    assert source['uibgTabButtons']['BorderType'] == 'none'


def test_navigation_has_no_outer_box_and_matches_six_equal_reference_rectangles(window):
    c = window.controls
    group = c['uibgTabButtons']
    assert group.property('referenceBorder') == 'none'
    assert group.layout() is None
    image = group.grab().toImage()
    assert {image.pixelColor(x, image.height() - 1).name()
            for x in range(image.width())} == {'#f0f0f0'}
    original = json.loads((ROOT / 'tests/reference/gui/guiFracPaQ2D.json').read_text())
    rects = {o['tag']: o['opening_normalized_figure_rect'] for o in original['objects']}
    widths, heights, tops = [], [], []
    for name in NAVIGATION:
        button = c[name]
        x, y, w, h = rects[name]
        pos = button.mapTo(window.board, QPoint())
        actual = (pos.x(), pos.y(), button.width(), button.height())
        expected = (x * window.board.width(), (1 - y - h) * window.board.height(),
                    w * window.board.width(), h * window.board.height())
        assert all(abs(a - b) <= 2 for a, b in zip(actual, expected)), name
        widths.append(button.width())
        heights.append(button.height())
        tops.append(pos.y())
    assert max(widths) - min(widths) <= 1
    assert max(heights) - min(heights) <= 1
    assert len(set(tops)) == 1
    assert min(heights) >= 49  # Regression: the former layout collapsed these to 30px.


@pytest.mark.parametrize('screen', [QSize(1366, 768), QSize(1440, 900), QSize(1920, 1080),QSize(2560,1440)])
def test_startup_uses_full_available_width_and_bounded_height(screen):
    size = initial_window_size(screen)
    assert size.width() == screen.width()
    assert size.height() + 32 <= screen.height() * .95
    assert 0 < size.height() <= 739


def test_main_window_opens_across_available_screen_without_maximizing_height(qapp,qtbot):
    configure_application(qapp)
    window = MainWindow()
    assert window.size() == initial_window_size(window.screen().availableGeometry().size())
    window.show()
    qtbot.waitExposed(window)
    available=window.screen().availableGeometry()
    assert window.frameGeometry().width()==available.width()
    assert window.frameGeometry().left()==available.left()
    assert available.contains(window.frameGeometry())
    assert not window.isMaximized() and not window.isFullScreen()
    window.close()


def test_all_panels_preserve_tree_and_reference_internal_arrangement(window):
    c = window.controls
    assert window.windowTitle() == 'FracPaQ'
    assert window.stack.count() == 6
    for index, name in enumerate(PANELS):
        assert window.stack.widget(index) is c[name]
        assert c[name].size() == window.stack.size()
    assert c['uipanel6'].y() < c['uipanel5'].y()  # Original Maps: colours above stability.
    assert c['checkbox_mle'].x() < c['checkbox_blocksize'].x()
    assert c['checkbox_logloglength'].x() < c['checkbox_crossplot'].x()
    assert c['uipanel1'].width() / window.board.width() == pytest.approx(.16124, abs=.001)
    assert c['uibgTabMaps'].width() / window.board.width() == pytest.approx(.36576, abs=.001)
    for spec in c.reference['objects']:
        name = spec['tag']
        if spec['type'] in ('figure', 'axes') or name in PANELS:
            continue
        widget = c[name]
        expected_parent = window.board if spec['parent'] == 'figure_main' else c[spec['parent']]
        assert widget.parentWidget() is expected_parent, name
        if isinstance(widget, QGroupBox):
            assert widget.layout() is None
        elif isinstance(widget, QLineEdit) and 'HorizontalAlignment' in spec:
            flag = {'left': Qt.AlignmentFlag.AlignLeft, 'center': Qt.AlignmentFlag.AlignHCenter,
                    'right': Qt.AlignmentFlag.AlignRight}[spec['HorizontalAlignment']]
            assert widget.alignment() & flag


def test_labels_do_not_cover_fields_and_navigation_stays_equal_after_resize(window, qtbot):
    window.resize(1100, 650)
    qtbot.waitUntil(lambda: window.board.width() == window.scroll.viewport().width())
    c = window.controls
    for name in ('label_houghpeaks', 'label_minlength', 'label_numscancircles', 'text13'):
        label = c[name]
        assert not label.geometry().intersects(label.buddy().geometry()), name
    assert len({c[name].height() for name in NAVIGATION}) == 1
    assert window.scroll.horizontalScrollBar().maximum() == 0
    assert window.scroll.verticalScrollBar().maximum() == 0
