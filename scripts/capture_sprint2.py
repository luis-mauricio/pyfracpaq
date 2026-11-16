"""Capture actual Qt states offscreen and audit text fit at the selected DPR."""

import argparse
import json
import os
from pathlib import Path

from reference_common import REFERENCE, ROOT, sha256, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--width', type=int, default=1250)
    parser.add_argument('--height', type=int, default=739)
    parser.add_argument('--input', type=Path, default=ROOT/'tests/fixtures/nodes/mixed.txt')
    args = parser.parse_args()
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    os.environ.setdefault('MPLCONFIGDIR', str(Path('/private/tmp/pyfracpaq-matplotlib')))
    from PySide6.QtCore import QRect, QTimer, Qt
    from PySide6.QtWidgets import QApplication, QCheckBox, QGroupBox, QLabel, QRadioButton

    from pyfracpaq.app import configure_application
    from pyfracpaq.gui import MainWindow
    from pyfracpaq.gui.controls import NAVIGATION, PANELS

    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication([])
    configure_application(app)
    window = MainWindow()
    startup = {'logical_size': [window.width(), window.height()],
               'available_size': [window.screen().availableGeometry().width(),
                                  window.screen().availableGeometry().height()],
               'maximized': window.isMaximized()}
    window.show()
    app.processEvents()
    # The first show applies the requested full-screen-width startup policy.
    # Review captures deliberately exercise the explicit --width/--height.
    window.resize(args.width, args.height)
    app.processEvents()
    entries = []
    violations = []

    def capture(name: str) -> None:
        app.processEvents()
        window.canvas.draw()
        path = output / f'{name}.png'
        pixmap = window.grab()
        assert pixmap.save(str(path))
        entries.append({'state': name, 'path': path.name, 'sha256': sha256(path),
                        'raster_size': [pixmap.width(), pixmap.height()]})
        for tag, widget in window.controls.widgets.items():
            if not widget.isVisible():
                continue
            fm = widget.fontMetrics()
            if isinstance(widget, (QCheckBox, QRadioButton)):
                if widget.sizeHint().width() > widget.width():
                    violations.append({'state': name, 'control': tag, 'issue': 'button text width',
                                       'required': widget.sizeHint().width(), 'width': widget.width()})
            elif isinstance(widget, QGroupBox):
                if fm.horizontalAdvance(widget.title().replace('&&', '&')) + 16 > widget.width():
                    violations.append({'state': name, 'control': tag, 'issue': 'group title width'})
            elif isinstance(widget, QLabel) and widget.text():
                rect = fm.boundingRect(QRect(0, 0, widget.width(), 10000),
                                       Qt.TextFlag.TextWordWrap, widget.text())
                if rect.height() > widget.height() + 1:
                    violations.append({'state': name, 'control': tag, 'issue': 'label text height',
                                       'required': rect.height(), 'height': widget.height()})

    def ready(kind: str) -> None:
        if window.last_error is not None:
            raise RuntimeError(window.last_error.message)
        capture('preview')
        for i, panel in enumerate(PANELS):
            window.controls[NAVIGATION[i]].click()
            capture(NAVIGATION[i].removeprefix('pb').removesuffix('Tab').lower())
        window.focus_field('edit_FilenameTag')
        app.processEvents()
        tag_has_focus = window.controls['edit_FilenameTag'].hasFocus()
        assert tag_has_focus, 'Keyboard focus did not reach the filename tag.'
        logical = [window.width(), window.height()]
        navigation = {}
        for tag in NAVIGATION:
            button = window.controls[tag]
            position = window.controls.specs[tag]['Position']
            parent = button.parentWidget()
            x, y, width, height = position
            expected = (round(x * parent.width()), round((1 - y - height) * parent.height()),
                        round(width * parent.width()), round(height * parent.height()))
            actual = (button.x(), button.y(), button.width(), button.height())
            navigation[tag] = {'actual': actual, 'expected': expected,
                               'maximum_deviation_pixels': max(abs(a - b) for a, b in zip(actual, expected))}
        macro_deviations = {}
        for name, (widget, position) in window.board.anchors.items():
            if name == 'axes_tracemap':
                continue
            x, y, width, height = position
            expected = (round(x * window.board.width()),
                        round((1 - y - height) * window.board.height()),
                        round(width * window.board.width()),
                        round(height * window.board.height()))
            actual = (widget.x(), widget.y(), widget.width(), widget.height())
            macro_deviations[name] = max(abs(a - b) for a, b in zip(actual, expected))
        write_json(output / 'manifest.json', {
            'scope': f'Qt {app.platformName()} captures; not MATLAB reference or visual parity approval.',
            'platform': app.platformName(), 'qt_scale_factor': os.environ.get('QT_SCALE_FACTOR', '1'),
            'device_pixel_ratio': window.devicePixelRatioF(), 'logical_size': logical,
            'startup': startup, 'navigation_geometry': navigation,
            'navigation_border': window.controls['uibgTabButtons'].property('referenceBorder'),
            'font': app.font().family(), 'input': str(args.input.resolve()),
            'input_sha256': sha256(args.input.resolve()),
            'captures': entries, 'text_fit_violations': violations,
            'focus_check': {'control': 'edit_FilenameTag', 'has_focus': tag_has_focus},
            'macro_geometry': {
                name: [widget.x(), widget.y(), widget.width(), widget.height()]
                for name, (widget, _) in window.board.anchors.items()
                if name != 'axes_tracemap'
            },
            'macro_position_deviation_pixels': macro_deviations,
            'reference_limit': 'FIG parent-relative control rectangles with integer rounding, '
                               'explicit panel title insets and local repairs for clipped labels. '
                               'Supplied manual screenshots guide proportions/style; '
                               'not native MATLAB pixel parity approval.',
        })
        print(f'{len(entries)} states; DPR {window.devicePixelRatioF():g}; '
              f'{len(violations)} text-fit violations.')
        window.close()

    def start() -> None:
        capture('initial')
        window.controls['edit_filename'].setText(str(args.input.resolve()))
        window.job_completed.connect(lambda kind: QTimer.singleShot(0, lambda: ready(kind)))
        window.preview()

    QTimer.singleShot(0, start)
    QTimer.singleShot(15000, app.quit)
    app.exec()
    if not (output / 'manifest.json').exists():
        raise RuntimeError('Capture did not finish.')
    if violations:
        raise SystemExit('Text-fit audit failed; see manifest.json.')


if __name__ == '__main__':
    main()
