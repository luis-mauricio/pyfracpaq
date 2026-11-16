"""Exercise scientific imports and the QtAgg bridge; record actual versions."""

import argparse
import importlib.metadata as metadata
import os
import platform
import shutil
import sys
import tempfile
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) /
                                         'pyfracpaq-matplotlib'))

from reference_common import write_json


def check() -> dict:
    import defusedxml.ElementTree as xml
    import numpy as np
    import scipy.linalg
    import scipy.stats
    from matplotlib import font_manager
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
    from matplotlib.figure import Figure
    from PIL import Image
    from PySide6 import QtCore, QtGui, QtWidgets
    from skimage.transform import hough_line

    assert sys.version_info[:2] == (3, 13), 'Use CPython 3.13.x.'
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    app.setStyle('Fusion')
    figure = Figure(figsize=(2, 2), dpi=100)
    figure.add_subplot().plot([0, 1], [0, 1])
    canvas = FigureCanvasQTAgg(figure)
    canvas.draw()
    assert canvas.get_width_height() == (200, 200)
    agg = FigureCanvasAgg(Figure(figsize=(2, 2), dpi=100))
    agg.draw()
    np.testing.assert_allclose(scipy.linalg.eigvalsh(np.eye(2)), [1, 1])
    assert scipy.stats.ks_2samp([1, 2], [1, 2], method='exact').statistic == 0
    h, theta, rho = hough_line(np.eye(8, dtype=bool))
    assert h.max() > 0 and theta.size and rho.size
    assert Image.new('L', (8, 8)).mode == 'L'
    assert xml.fromstring('<svg/>').tag == 'svg'
    font = font_manager.findfont('Arial', fallback_to_default=False)
    assert 'Arial' in QtGui.QFontDatabase.families()
    screen = app.primaryScreen()
    result = {
        'python': platform.python_version(), 'implementation': platform.python_implementation(),
        'os': platform.platform(), 'architecture': platform.machine(),
        'qt': QtCore.qVersion(), 'qt_platform': app.platformName(),
        'screen': {'width': screen.size().width(), 'height': screen.size().height(),
                   'device_pixel_ratio': screen.devicePixelRatio(),
                   'logical_dpi': screen.logicalDotsPerInch()},
        'font': {'family': 'Arial', 'matplotlib_path': font},
        'packages': {d.metadata['Name']: d.version
                     for d in sorted(metadata.distributions(),
                                     key=lambda d: d.metadata['Name'].lower())},
        'matlab_executable': shutil.which('matlab'),
        'octave_executable': shutil.which('octave'),
        'checks': ['Qt Widgets/Fusion', 'QtAgg canvas draw', 'Agg canvas draw',
                   'SciPy eigenvalues/K-S', 'scikit-image Hough', 'Pillow L',
                   'defusedxml', 'Arial Qt/Matplotlib'],
        'scope': 'Smoke test de dependências; não valida GUI nem paridade MATLAB.',
    }
    canvas.close()
    app.processEvents()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = check()
    write_json(args.output, result)
    print(f"Python {result['python']}, Qt {result['qt']}: "
          f"{len(result['checks'])} verificações OK ({result['qt_platform']}).")


if __name__ == '__main__':
    main()
