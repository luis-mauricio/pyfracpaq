"""Prepare the usage ZIP from an explicit source list, without invoking Git.

Only application code, resources, examples, user documentation and notices are
included. Git staging, commits and publication remain the maintainer's actions.
"""

import argparse
import json
from pathlib import Path
import shutil
import tempfile
import zipfile

from pyfracpaq import __version__
from reference_common import ROOT, sha256, write_json
from check_distribution_licenses import validate_archive, validate_repository


ROOT_FILES = (
    'run_gui.py', 'requirements.txt', 'pyproject.toml', 'README.md', 'LICENSE',
    'THIRD_PARTY_NOTICES.md', '.vscode/launch.json', '.vscode/settings.json',
    'docs/install.md', 'docs/user-guide.md', 'docs/release-notes.md',
)
SOURCE_DIRECTORIES = ('pyfracpaq', 'examples', 'docs/manual', 'docs/licenses')
IGNORED_PARTS = {'__pycache__', 'build', '.pytest_cache', '.git', '.venv'}
TEMPORARY_SUFFIXES = {
    '.pyc', '.pyo', '.tmp', '.temp', '.bak', '.asv', '.swp', '.swo',
    '.aux', '.log', '.toc', '.out', '.fls', '.fdb_latexmk', '.xdv',
}


def source_paths(root):
    """Select delivery files; never enumerate the full repository or Git index."""
    paths = {root / name for name in ROOT_FILES}
    for directory in SOURCE_DIRECTORIES:
        base = root / directory
        if base.is_symlink():
            raise ValueError(f'Symlink in delivery sources: {base}')
        for path in base.rglob('*'):
            if IGNORED_PARTS.intersection(path.relative_to(base).parts):
                continue
            if path.is_symlink():
                raise ValueError(f'Symlink in delivery sources: {path}')
            if (not path.is_file() or path.name.startswith(('.', '~'))
                    or path.name.endswith(('~', '.synctex.gz'))
                    or path.suffix in TEMPORARY_SUFFIXES):
                continue
            paths.add(path)
    for path in paths:
        if path.is_symlink() or not path.is_file():
            raise ValueError(f'Missing or linked delivery source: {path}')
        if path.stat().st_size >= 100 * 1024**2:
            raise ValueError(f'Delivery source exceeds 100 MiB: {path}')
    return sorted(paths)


def prepare(output_directory, evidence):
    output_directory = Path(output_directory).resolve()
    evidence = Path(evidence).resolve()
    validate_repository(ROOT)
    paths = source_paths(ROOT)
    work = Path(tempfile.mkdtemp(prefix='pyfracpaq-source-', dir='/tmp'))
    archive = work / f'pyfracpaq-{__version__}-code.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as target:
        for path in paths:
            target.write(path, f'pyfracpaq-{__version__}/{path.relative_to(ROOT).as_posix()}')
    license_check = validate_archive(archive)
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
    for path in paths:
        assert sha256(path) == sha256(runtime / path.relative_to(ROOT)), str(path)
    output_directory.mkdir(parents=True, exist_ok=True)
    destination = output_directory / archive.name
    temporary_destination = destination.with_suffix('.zip.tmp')
    shutil.copyfile(archive, temporary_destination)
    temporary_destination.replace(destination)
    archive = destination
    write_json(output_directory / 'publication-manifest.json', {
        'version': __version__, 'published': False,
        'scope': 'Public source ZIP only; original MATLAB files and dependency binaries excluded. '
                 'Full Git clone and historical local archives have a different scope.',
        'files_to_publish': [{'name': archive.name, 'bytes': archive.stat().st_size,
                              'sha256': sha256(archive)}],
        'license_check': license_check,
        'excluded_artifacts': ['*-source.zip', '*-internal-reference.zip', '*.whl',
                               '*.tar.gz', 'wheelhouse*'],
    })
    (output_directory / 'SHA256SUMS').write_text(f'{sha256(archive)}  {archive.name}\n')
    report = {'version': __version__, 'published': False, 'actual_index_changed': False,
              'git_commands_executed': False,
              'snapshot_files': len(paths), 'snapshot_bytes': sum(p.stat().st_size for p in paths),
              'archive': str(archive.relative_to(ROOT)) if archive.is_relative_to(ROOT) else str(archive),
              'archive_sha256': sha256(archive),
              'archive_bytes': archive.stat().st_size, 'runtime_files': sum(p.is_file() for p in runtime.rglob('*')),
              'runtime_folder': str(runtime), 'tests_and_reports_absent_from_zip': True,
              'all_runtime_modules_and_resources_match': True,
              'source_files': [{'path': p.relative_to(ROOT).as_posix(),
                                'bytes': p.stat().st_size, 'sha256': sha256(p)} for p in paths],
              'license_check': license_check,
              'scope': 'Usage ZIP from an explicit source list, assembled and checked without Git. '
                       'Full clone and remote GitHub ZIP review are separate stages.'}
    write_json(evidence, report)
    print(json.dumps({'runtime_folder': str(runtime), 'archive_bytes': archive.stat().st_size,
                      'runtime_files': report['runtime_files']}))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-directory', type=Path, default=ROOT / 'dist' / __version__ / 'public')
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.output_directory.resolve(), args.evidence.resolve())
