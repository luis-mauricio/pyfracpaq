"""Check an installed wheel outside the source tree with network guards.

Both entrypoints perform Preview and a real GUI Run in independent directories.
This verifies the installed distribution, resources and exports, not native
appearance (Qt offscreen). Installation itself is an explicit separate step.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

from pyfracpaq import __version__
from reference_common import ROOT, sha256, write_json


PROGRAM = r'''
import hashlib, importlib.metadata, json, runpy, socket, sys, traceback
from pathlib import Path
parameters = json.loads(PARAMETERS)
attempts = []
def deny(*args, **kwargs):
    attempts.append(repr(args))
    raise AssertionError('Unexpected network access')
socket.socket.connect = deny
socket.socket.connect_ex = deny
socket.create_connection = deny
socket.getaddrinfo = deny
try:
    socket.create_connection(('example.invalid', 80))
except AssertionError:
    pass
assert len(attempts) == 1
attempts.clear()
import pyfracpaq
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PIL import Image
from pyfracpaq.io import read_txt
from pyfracpaq.io.svg import read_svg
from pyfracpaq.io.images import read_image
prefix = Path(sys.prefix).resolve()
package = Path(pyfracpaq.__file__).resolve().parent
if parameters.get('source_root'):
    assert package == Path(parameters['source_root']).resolve() / 'pyfracpaq', package
    try:
        importlib.metadata.version('pyfracpaq')
    except importlib.metadata.PackageNotFoundError:
        pass
    else:
        raise AssertionError('Source validation must not install the project')
    assert not (Path(parameters['source_root']) / 'tests').exists()
    assert not (Path(parameters['source_root']) / 'scripts').exists()
else:
    assert package.is_relative_to(prefix), (package, prefix)
    assert importlib.metadata.version('pyfracpaq') == parameters['version']
assert pyfracpaq.__version__ == parameters['version']
assert sys.version_info[:2] == (3, 13)
for name, expected in parameters['package_hashes'].items():
    target = package.parent / name
    assert target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest() == expected, name
assert read_txt('Amostra com acentos ação.TXT').n_segments == 3
assert read_svg('multicolour.svg').dataset.n_traces > 0
assert read_image('tensor_network.tif').dataset.n_segments > 0
app = QApplication([])
state = {'window': None, 'completed': False}
def fail():
    traceback.print_exc()
    app.exit(1)
def completed(kind):
    try:
        window = state['window']
        assert window.last_error is None, window.last_error
        if kind == 'preview':
            assert window.dataset.n_segments == 3
            for spec in window.registry.specs:
                window.controls[spec.checkbox].setChecked(spec.id in ('MAP-01', 'LEN-02', 'ANG-01'))
            window.controls['edit_FilenameTag'].setText('Offline ação')
            QTimer.singleShot(0, window.run_selected)
        elif kind == 'run':
            outputs = sorted(Path.cwd().glob('FracPaQ2D*.png'))
            tables = sorted(Path.cwd().glob('FracPaQ2D*.txt'))
            assert len(outputs) == 4 and len(tables) == 4, (outputs, tables)
            exports = []
            for path in outputs:
                with Image.open(path) as image:
                    assert image.size == (4724, 4724)
                    assert abs(image.info['dpi'][0] - 600) < .01
                    assert parameters['version'] in image.info['Software']
                assert path.name.endswith('_Offline ação.png')
                exports.append({'name': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
            for path in tables:
                assert path.name.endswith('_Offline ação.txt') and path.stat().st_size > 0
                exports.append({'name': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
            assert len(window.figure_windows) == 4
            assert not attempts, attempts
            assert not list(Path.cwd().glob('.pyfracpaq-*'))
            state['completed'] = True
            print('DELIVERY:' + json.dumps({'version': pyfracpaq.__version__, 'module': str(package),
                  'prefix': str(prefix), 'python': sys.version.split()[0],
                  'source_execution': bool(parameters.get('source_root')),
                  'network': 'Python socket connect/connect_ex/create_connection and DNS denied',
                  'network_guard_selftest': True, 'network_attempts': attempts,
                  'verified_package_files': len(parameters['package_hashes']),
                  'readers': ['TXT', 'SVG', 'Hough'], 'gui_preview_and_run': True,
                  'exports': exports}), flush=True)
            for item in app.topLevelWidgets():
                item.close()
    except BaseException:
        fail()
def start():
    try:
        window = next(w for w in app.topLevelWidgets() if w.objectName() == 'figure_main')
        state['window'] = window
        footer = window.controls['text4'].text()
        assert parameters['version'] in footer and 'November 2026' in footer and 'luismauricio@me.com' in footer
        window.job_completed.connect(completed)
        window.controls['edit_filename'].setText(str(Path('Amostra com acentos ação.TXT').absolute()))
        window.preview()
    except BaseException:
        fail()
def timeout():
    if not state['completed']:
        print('Delivery check timed out', flush=True)
        app.exit(2)
QTimer.singleShot(0, start)
QTimer.singleShot(45000, timeout)
if parameters['mode'] == 'script':
    runpy.run_path('run_gui.py', run_name='__main__')
else:
    runpy.run_module('pyfracpaq', run_name='__main__')
'''


def check(interpreter: Path, output: Path, wheel: Path, fixtures: Path = ROOT):
    with zipfile.ZipFile(wheel) as archive:
        package_hashes = {name: hashlib.sha256(archive.read(name)).hexdigest()
                          for name in archive.namelist() if name.startswith('pyfracpaq/') and not name.endswith('/')}
        assert 'pyfracpaq/resources/pyfracpaq-logo.png' in package_hashes
    records = []
    with tempfile.TemporaryDirectory(prefix='pyfracpaq-offline-ação-') as temporary:
        for mode in ('script', 'module'):
            work = Path(temporary) / mode
            work.mkdir()
            for original, target in (
                ('tests/fixtures/nodes/mixed.txt', 'Amostra com acentos ação.TXT'),
                ('tests/fixtures/svg/multicolour.svg', 'multicolour.svg'),
                ('tests/fixtures/images/tensor_network.tif', 'tensor_network.tif'),
                ('run_gui.py', 'run_gui.py')):
                shutil.copyfile(fixtures / original, work / target)
            parameters = {'mode': mode, 'version': __version__, 'package_hashes': package_hashes}
            program = PROGRAM.replace('PARAMETERS', repr(json.dumps(parameters)))
            result = subprocess.run([str(interpreter), '-I', '-c', program], cwd=work,
                env={**os.environ, 'QT_QPA_PLATFORM': 'offscreen', 'MPLCONFIGDIR': '/tmp/pyfracpaq-matplotlib',
                     'PIP_NO_INDEX': '1', 'PIP_DISABLE_PIP_VERSION_CHECK': '1'},
                capture_output=True, text=True, timeout=60)
            assert result.returncode == 0, result.stdout + result.stderr
            metadata = json.loads(next(line[9:] for line in result.stdout.splitlines() if line.startswith('DELIVERY:')))
            assert not Path(metadata['module']).is_relative_to(ROOT / 'pyfracpaq'), metadata
            records.append({'mode': mode, 'exit_code': result.returncode, **metadata,
                            'stdout': result.stdout, 'stderr': result.stderr})
    write_json(output, {'wheel': str(wheel), 'sha256': sha256(wheel), 'entrypoints': records,
                       'scope': 'Installed files match every wheel package file; -I, cwd outside source; '
                                'TXT/SVG/Hough; real Preview/Run; network guards; Qt offscreen, not native appearance certification.'})
    print(f'Installed {__version__} passed both entrypoints, Preview/Run, 16 exports and offline/resource checks.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--wheel', type=Path, default=ROOT / 'dist' / __version__ / f'pyfracpaq-{__version__}-py3-none-any.whl')
    parser.add_argument('--source-root', type=Path, default=ROOT, help='Fixtures/launcher from the extracted complete source ZIP.')
    args = parser.parse_args()
    # Resolving the venv executable symlink would select the base interpreter.
    check(args.python.absolute(), args.output, args.wheel.resolve(), args.source_root.resolve())
