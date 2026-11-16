"""Exercise both entrypoints outside the source directory without a display."""

import os
from pathlib import Path
import subprocess
import sys

import pytest

from reference_common import ROOT


@pytest.mark.parametrize('mode', ['script', 'module'])
def test_entrypoint_starts_and_closes_its_window(mode, tmp_path):
    target = str(ROOT / 'run_gui.py')
    launch = (f'runpy.run_path({target!r}, run_name="__main__")' if mode == 'script'
              else 'runpy.run_module("pyfracpaq", run_name="__main__")')
    program = (
        'import runpy; from PySide6.QtWidgets import QApplication; '
        'from PySide6.QtCore import QTimer; '
        'app=QApplication([]); '
        'QTimer.singleShot(200, lambda: '
        '[w.close() for w in app.topLevelWidgets()]); ' + launch
    )
    env = dict(os.environ, QT_QPA_PLATFORM='offscreen')
    result = subprocess.run([sys.executable, '-c', program], cwd=tmp_path,
                            env=env, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'FracPaQ version 2.8 reference' in result.stdout
    assert 'Traceback' not in result.stderr
    assert not list(tmp_path.iterdir())
