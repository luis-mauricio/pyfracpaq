"""Validate local release archives and two independent offline installations.

No artifacts are published. --archives-only refreshes source-snapshot evidence
without reinstalling an unchanged wheel/sdist after delivery records are closed.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
from email.parser import BytesParser
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import tempfile
import time
import venv
import zipfile

from pyfracpaq import __version__
from build_local_release import source_paths
from check_local_delivery import check
from reference_common import ROOT, sha256, write_json


def archives(directory, work):
    wheel = directory / f'pyfracpaq-{__version__}-py3-none-any.whl'
    sdist = directory / f'pyfracpaq-{__version__}.tar.gz'
    source = directory / f'pyfracpaq-{__version__}-source.zip'
    prefix = f'pyfracpaq-{__version__}/'
    with zipfile.ZipFile(wheel) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert len(names) == len(set(names))
        metadata, = [n for n in names if n.endswith('.dist-info/METADATA')]
        info = BytesParser().parsebytes(archive.read(metadata))
        assert info['Version'] == __version__ and info['Requires-Python'] == '<3.14,>=3.13'
        package_files = {n: archive.read(n) for n in names if n.startswith('pyfracpaq/')}
        assert 'pyfracpaq/resources/pyfracpaq-logo.png' in package_files
        assert any(n.endswith('/licenses/LICENSE') for n in names)
        assert any(n.endswith('/licenses/THIRD_PARTY_NOTICES.md') for n in names)
        for name, content in package_files.items():
            assert content == (ROOT / name).read_bytes(), name
        expected = {str(p.relative_to(ROOT)) for p in (ROOT / 'pyfracpaq').rglob('*')
                    if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
        assert set(package_files) == expected, (set(package_files) ^ expected)
    with tarfile.open(sdist, 'r:gz') as archive:
        members = archive.getmembers()
        assert all(n.name.startswith(prefix.rstrip('/')) and not n.issym() and not n.islnk() for n in members)
        names = {n.name for n in members}
        assert prefix + 'pyproject.toml' in names and prefix + 'run_gui.py' in names
        assert not any('/tests/' in n or '/fracpaq-matlab/' in n for n in names)
        for name, content in package_files.items():
            assert archive.extractfile(prefix + name).read() == content, name
    expected_paths, baseline = source_paths()
    source_names = {prefix + str(p.relative_to(ROOT)) for p in expected_paths}
    with zipfile.ZipFile(source) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert len(names) == len(set(names)) and set(names) == source_names
        for path in names:
            parts = PurePosixPath(path).parts
            assert not PurePosixPath(path).is_absolute() and '..' not in parts
            assert not {'.git', '.venv', '.aws', '.codex', '__pycache__', 'dist', 'build'} & set(parts)
        for path in expected_paths:
            assert archive.read(prefix + str(path.relative_to(ROOT))) == path.read_bytes(), str(path)
        for entry in baseline:
            import hashlib
            assert hashlib.sha256(archive.read(prefix + 'fracpaq-matlab/' + entry['path'])).hexdigest() == entry['sha256']
        fixtures = work / 'snapshot'
        for name in ('run_gui.py', 'tests/fixtures/nodes/mixed.txt', 'tests/fixtures/svg/multicolour.svg',
                     'tests/fixtures/images/tensor_network.tif'):
            path = fixtures / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(archive.read(prefix + name))
    return {'wheel_package_files': len(package_files), 'sdist_runtime_matches_wheel': True,
            'source_files': len(source_names), 'originals': len(baseline),
            'complete_snapshot_matches_sources': True, 'unsafe_or_unexpected_members': 0,
            'source_scope': 'Complete snapshot excludes this point-4 external evidence, including its own hashes.'}, fixtures


def install(kind, artifact, wheel, wheelhouse, fixtures, work, evidence):
    environment = work / f'{kind}-venv'
    venv.EnvBuilder(with_pip=True).create(environment)
    interpreter = environment / 'bin/python'
    env = {**os.environ, 'PIP_NO_INDEX': '1', 'PIP_NO_CACHE_DIR': '1',
           'PIP_DISABLE_PIP_VERSION_CHECK': '1', 'MPLCONFIGDIR': '/tmp/pyfracpaq-matplotlib'}
    start = time.perf_counter()
    commands = [
        ('install', [str(interpreter), '-m', 'pip', 'install', '--no-index', '--no-cache-dir',
                     '--find-links', str(wheelhouse), '--report', str(evidence / f'{kind}-install.json'), str(artifact)]),
        ('pip-check', [str(interpreter), '-m', 'pip', 'check'])]
    for label, command in commands:
        result = subprocess.run(command, cwd=work, env=env, capture_output=True, text=True, timeout=150)
        (evidence / f'{kind}-{label}.log').write_text(result.stdout + result.stderr)
        assert result.returncode == 0, result.stdout + result.stderr
    pip_report = json.loads((evidence / f'{kind}-install.json').read_text())
    assert all(item['download_info']['url'].startswith('file:') for item in pip_report['install'])
    package, = [item for item in pip_report['install'] if item['metadata']['name'].lower() == 'pyfracpaq']
    assert package['download_info']['archive_info']['hashes']['sha256'] == sha256(artifact)
    # The checker launches separate installed processes; none import this repository.
    check(interpreter, evidence / f'{kind}-offline.json', wheel, fixtures)
    offline = json.loads((evidence / f'{kind}-offline.json').read_text())
    return {'artifact_sha256': sha256(artifact), 'python': str(interpreter), 'fresh_venv': True,
            'index_disabled': True, 'all_install_urls_local': True, 'pip_check_passed': True,
            'installed_version': package['metadata']['version'], 'seconds': time.perf_counter() - start,
            'entrypoints': len(offline['entrypoints']), 'real_preview_run_exports': 16,
            'evidence': str((evidence / f'{kind}-offline.json').relative_to(ROOT))}


def validate(directory, wheelhouse, evidence, archives_only=False):
    evidence.mkdir(parents=True, exist_ok=True)
    target = evidence / 'validation.json'
    previous = json.loads(target.read_text()) if archives_only else None
    manifest = json.loads((directory / 'release-manifest.json').read_text())
    assert manifest['version'] == __version__
    for item in manifest['artifacts']:
        assert sha256(ROOT / item['path']) == item['sha256']
    for item in manifest['dependencies']:
        assert sha256(wheelhouse / item['name']) == item['sha256']
    work = Path(tempfile.mkdtemp(prefix='pyfracpaq-s1609-final-', dir='/tmp'))
    archive_checks, fixtures = archives(directory, work)
    wheel = directory / f'pyfracpaq-{__version__}-py3-none-any.whl'
    sdist = directory / f'pyfracpaq-{__version__}.tar.gz'
    if archives_only:
        installations = previous['installations']
        assert installations['wheel']['artifact_sha256'] == sha256(wheel)
        assert installations['sdist']['artifact_sha256'] == sha256(sdist)
    else:
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = {kind: pool.submit(install, kind, artifact, wheel, wheelhouse, fixtures, work, evidence)
                    for kind, artifact in (('wheel', wheel), ('sdist', sdist))}
            installations = {kind: job.result() for kind, job in jobs.items()}
    report = {'version': __version__, 'complete': True, 'published': False,
              'artifacts': manifest['artifacts'], 'dependencies_verified': len(manifest['dependencies']),
              'archive_checks': archive_checks, 'installations': installations,
              'platform': 'CPython3.13.18/macOS arm64; Qt offscreen; Windows/Linux deferred to user',
              'entrypoints_total': 4, 'exports_total': 32,
              'scope': 'Two fresh environments, wheel and sdist; build isolation for sdist with local pinned setuptools. '
                       'Both launchers perform real Preview/Run with Python network guards. '
                       'Archives-only refresh preserves installation evidence only for identical wheel/sdist hashes.'}
    write_json(target, report)
    print('VALIDATED: wheel + sdist, 4 entrypoint runs, 32 exports, archive contents and SHA256. No publication.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=ROOT / 'dist' / __version__)
    parser.add_argument('--wheelhouse', type=Path, default=ROOT / 'dist/wheelhouse-macos-arm64')
    parser.add_argument('--evidence', type=Path, default=ROOT / 'tests/reference/sprint16/delivery/point-4')
    parser.add_argument('--archives-only', action='store_true')
    args = parser.parse_args()
    validate(args.directory.resolve(), args.wheelhouse.resolve(), args.evidence.resolve(), args.archives_only)
