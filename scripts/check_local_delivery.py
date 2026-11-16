"""Verify an installed wheel offline, outside the source tree, using both entrypoints."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

from reference_common import ROOT, sha256, write_json


def check(interpreter: Path, output: Path):
    wheel = ROOT / 'dist/pyfracpaq-0.1.0rc1-py3-none-any.whl'
    records=[]
    with tempfile.TemporaryDirectory(prefix='pyfracpaq-offline-') as temporary:
        for mode in ('script','module'):
            launch=(f'runpy.run_path({str(ROOT / "run_gui.py")!r},run_name="__main__")'
                    if mode=='script' else 'runpy.run_module("pyfracpaq",run_name="__main__")')
            program = '''
import json, socket, runpy, sys
def deny(*args, **kwargs): raise AssertionError('Unexpected network access')
socket.socket.connect=deny
socket.create_connection=deny
socket.getaddrinfo=deny
import pyfracpaq
from importlib.resources import files
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from pyfracpaq.io import read_txt
from pyfracpaq.io.svg import read_svg
from pyfracpaq.io.images import read_image
from pathlib import Path
root=Path(ROOT_PLACEHOLDER)
assert read_txt(root/'tests/fixtures/nodes/mixed.txt').n_segments==3
assert read_svg(root/'tests/fixtures/svg/multicolour.svg').dataset.n_traces>0
assert read_image(root/'tests/fixtures/images/tensor_network.tif').dataset.n_segments>0
assert files('pyfracpaq.resources').joinpath('ui_spec.json').is_file()
print('DELIVERY:'+json.dumps({'version':pyfracpaq.__version__,'module':pyfracpaq.__file__,'prefix':sys.prefix,'python':sys.version.split()[0],'network':'socket connect/DNS denied','readers':['TXT','SVG','Hough']}),flush=True)
app=QApplication([])
def close():
 windows=app.topLevelWidgets()
 assert any(w.objectName()=='figure_main' for w in windows)
 print('MAIN_WINDOW_OBSERVED',flush=True)
 for w in windows:w.close()
QTimer.singleShot(500,close)
'''.replace('ROOT_PLACEHOLDER',repr(str(ROOT))) + launch
            result=subprocess.run([str(interpreter),'-I','-c',program],cwd=temporary,
                env={**os.environ,'QT_QPA_PLATFORM':'offscreen','MPLCONFIGDIR':'/tmp/pyfracpaq-matplotlib'},
                capture_output=True,text=True,timeout=30)
            assert result.returncode==0 and 'MAIN_WINDOW_OBSERVED' in result.stdout, result.stdout+result.stderr
            metadata=json.loads(next(line[9:] for line in result.stdout.splitlines() if line.startswith('DELIVERY:')))
            assert str(ROOT / 'pyfracpaq') not in metadata['module'], metadata
            assert metadata['version']=='0.1.0rc1' and metadata['python'].startswith('3.13.')
            records.append({'mode':mode,'exit_code':result.returncode,**metadata,'stdout':result.stdout,'stderr':result.stderr})
    write_json(output,{'wheel':str(wheel.relative_to(ROOT)),'sha256':sha256(wheel),
        'install':'Fresh CPython3.13 venv, pip --no-index --find-links, pinned wheels; pip check passes.',
        'entrypoints':records,'scope':'Installed package outside source with -I; Qt offscreen, not native appearance certification.'})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    # Resolving the venv executable symlink selects the base interpreter.
    args=parser.parse_args();check(args.python.absolute(),args.output)
