"""Run both source entrypoints from a runtime-only copy, without installing PyFracPaQ.

Reuses the Preview/Run/network assertions of the legacy wheel checker, but
requires source imports, no installed project and no tests/scripts in the copy.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from pyfracpaq import __version__
from check_local_delivery import PROGRAM
from reference_common import write_json


def check_source(interpreter, source, output):
    records = []
    with tempfile.TemporaryDirectory(prefix='pyfracpaq-codigo-ação-') as temporary:
        for mode in ('script', 'module'):
            work = Path(temporary) / mode
            shutil.copytree(source, work, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store'))
            assert not (work / 'tests').exists() and not (work / 'scripts').exists()
            (work / 'Amostra com acentos ação.TXT').write_text('0\t0\t4\t0\n1\t2\t4\t2\t4\t6\n')
            shutil.copyfile(work / 'examples/colours.svg', work / 'multicolour.svg')
            shutil.copyfile(work / 'examples/network.tif', work / 'tensor_network.tif')
            hashes = {str(p.relative_to(work)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in (work / 'pyfracpaq').rglob('*') if p.is_file()}
            parameters = {'mode': mode, 'version': __version__, 'package_hashes': hashes,
                          'source_root': str(work)}
            program = PROGRAM.replace('PARAMETERS', repr(json.dumps(parameters)))
            env = {k: v for k, v in os.environ.items() if k not in ('PYTHONPATH', 'PYTHONHOME')}
            env.update(QT_QPA_PLATFORM='offscreen', MPLCONFIGDIR='/tmp/pyfracpaq-matplotlib')
            result = subprocess.run([str(interpreter), '-s', '-E', '-c', program], cwd=work,
                                    env=env, capture_output=True, text=True, timeout=60)
            assert result.returncode == 0, result.stdout + result.stderr
            metadata = json.loads(next(line[9:] for line in result.stdout.splitlines()
                                       if line.startswith('DELIVERY:')))
            assert metadata['source_execution'] and metadata['gui_preview_and_run']
            records.append({'mode': mode, **metadata, 'stdout': result.stdout, 'stderr': result.stderr})
    write_json(output, {'version': __version__, 'project_installed': False,
                       'source': str(source), 'entrypoints': records,
                       'scope': 'Runtime ZIP copy without tests/scripts/reference MATLAB; source imports only, '
                                'no project metadata installed, Preview/Run and exports, Python network guards. '
                                'Qt offscreen; separate native VS Code check records the real launch.'})
    print('Source-only execution passed both entrypoints, Preview/Run and 16 exports.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', type=Path, required=True)
    parser.add_argument('--source-folder', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    check_source(args.python.absolute(), args.source_folder.resolve(), args.output.resolve())
