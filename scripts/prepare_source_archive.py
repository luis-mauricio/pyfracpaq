"""Validate a source snapshot and export its runtime ZIP using real Git attributes.

Only a temporary Git repository is written. The user's index, history and remote
are untouched; this prepares a candidate, not a commit or publication.
"""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

from pyfracpaq import __version__
from reference_common import ROOT, sha256, write_json


def prepare(output_directory, evidence):
    files = subprocess.check_output(
        ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT
    ).decode().split('\0')
    files = sorted({name for name in files if name and (ROOT / name).is_file()})
    forbidden = {'.git', '.venv', '.aws', '.codex', '.agents', '__pycache__', 'dist', 'build', 'fracpaq-matlab'}
    for name in files:
        path = Path(name)
        assert not forbidden.intersection(path.parts), name
        assert not path.name.startswith(('.env', '.pyfracpaq-')), name
        assert not path.is_absolute() and '..' not in path.parts
        assert not (ROOT / path).is_symlink(), name
        assert (ROOT / path).stat().st_size < 100 * 1024**2, name
    work = Path(tempfile.mkdtemp(prefix='pyfracpaq-git-source-', dir='/tmp'))
    repository = work / 'repository'
    repository.mkdir()
    for name in files:
        target = repository / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    subprocess.run(['git', 'init', '-q', str(repository)], check=True)
    subprocess.run(['git', 'add', '--all'], cwd=repository, check=True, capture_output=True)
    tree = subprocess.check_output(['git', 'write-tree'], cwd=repository, text=True).strip()
    output_directory.mkdir(parents=True, exist_ok=True)
    archive = output_directory / f'pyfracpaq-{__version__}-code.zip'
    subprocess.run(['git', 'archive', '--format=zip', f'--prefix=pyfracpaq-{__version__}/',
                    f'--output={archive}', tree], cwd=repository, check=True)
    extract = work / 'download'
    with zipfile.ZipFile(archive) as source:
        assert source.testzip() is None
        names = source.namelist()
        assert not any('/tests/' in name or '/scripts/' in name or '/docs/parity/' in name
                       or '/docs/decisions/' in name for name in names)
        assert not any('/requirements-dev.txt' in name for name in names)
        source.extractall(extract)
    runtime = extract / f'pyfracpaq-{__version__}'
    for required in ('run_gui.py', 'requirements.txt', 'pyfracpaq/__main__.py',
                     'pyfracpaq/resources/pyfracpaq-logo.png', '.vscode/launch.json',
                     'docs/install.md', 'docs/user-guide.md', 'docs/release-notes.md',
                     'examples/network.tif', 'LICENSE', 'THIRD_PARTY_NOTICES.md'):
        assert (runtime / required).is_file(), required
    for path in (ROOT / 'pyfracpaq').rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
            assert sha256(path) == sha256(runtime / path.relative_to(ROOT)), str(path)
    report = {'version': __version__, 'published': False, 'actual_index_changed': False,
              'snapshot_files': len(files), 'snapshot_bytes': sum((ROOT / n).stat().st_size for n in files),
              'temporary_repository': str(repository), 'temporary_tree': tree,
              'archive': str(archive.relative_to(ROOT)), 'archive_sha256': sha256(archive),
              'archive_bytes': archive.stat().st_size, 'runtime_files': sum(p.is_file() for p in runtime.rglob('*')),
              'runtime_folder': str(runtime), 'tests_and_reports_absent_from_zip': True,
              'all_runtime_modules_and_resources_match': True,
              'scope': 'Candidate working-tree snapshot in a temporary Git repository; real git archive/export-ignore. '
                       'GitHub publication and actual remote Download ZIP belong to point 5.'}
    write_json(evidence, report)
    print(json.dumps({'runtime_folder': str(runtime), 'archive_bytes': archive.stat().st_size,
                      'runtime_files': report['runtime_files']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-directory', type=Path, default=ROOT / 'dist' / __version__)
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.output_directory.resolve(), args.evidence.resolve())
