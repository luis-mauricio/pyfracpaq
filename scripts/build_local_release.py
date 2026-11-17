"""Build INTERNAL wheels, sdist and a MATLAB reference archive without network.

The prior release stays intact. Installation/validation and publication are
separate operations; this command alone never certifies or publishes a release.
"""

import argparse
from datetime import date, datetime, timezone
from email.parser import BytesParser
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from pyfracpaq import __version__
from reference_common import ROOT, sha256, write_json


EXCLUDED_PARTS = {'__pycache__', '.pytest_cache', '.git', '.codex', '.agents', '.aws'}


def source_paths():
    names = ['pyfracpaq', 'scripts', 'tests', 'docs', 'examples', '.vscode', '.gitignore',
             'AGENTS.md', 'README.md', 'CHANGELOG.md',
             'LICENSE', 'THIRD_PARTY_NOTICES.md', 'pyproject.toml', 'MANIFEST.in',
             'requirements.txt', 'requirements-dev.txt', 'run_gui.py']
    paths = []
    for name in names:
        path = ROOT / name
        paths.extend(p for p in path.rglob('*') if p.is_file()) if path.is_dir() else paths.append(path)
    selected = []
    for path in paths:
        parts = path.relative_to(ROOT).parts
        # This point's reports contain the archive hash: including them would
        # introduce a circular self-reference and stale in-progress evidence.
        if parts[:5] == ('tests', 'reference', 'sprint16', 'delivery', 'point-4'):
            continue
        if (EXCLUDED_PARTS.intersection(parts) or path.name == '.DS_Store'
                or path.name.startswith(('.env', '.pyfracpaq-'))
                or path.suffix in ('.pyc', '.pyo', '.tmp', '.bak', '.asv')):
            continue
        if path.is_symlink():
            raise ValueError(f'Source snapshot must not follow symlinks: {path}')
        selected.append(path)
    baseline = json.loads((ROOT / 'tests/reference/source_manifest.json').read_text())['files']
    for entry in baseline:
        path = ROOT / 'fracpaq-matlab' / entry['path']
        assert sha256(path) == entry['sha256'], path
        selected.append(path)
    return sorted(set(selected)), baseline


def dependency_wheels(wheelhouse):
    packages = []
    found = {}
    for source in sorted(wheelhouse.glob('*.whl')):
        with zipfile.ZipFile(source) as archive:
            metadata, = [p for p in archive.namelist()
                          if p.endswith('.dist-info/METADATA') and p.count('/') == 1]
            info = BytesParser().parsebytes(archive.read(metadata))
        key = canonicalize_name(info['Name'])
        assert key not in found, f'Duplicate dependency: {key}'
        found[key] = info['Version']
        packages.append({'name': source.name, 'distribution': info['Name'], 'version': info['Version'],
                         'bytes': source.stat().st_size, 'sha256': sha256(source)})
    requirements = []
    for filename in ('requirements.txt', 'requirements-dev.txt'):
        for line in (ROOT / filename).read_text().splitlines():
            line = line.strip()
            if line and not line.startswith(('#', '-r')):
                requirements.append(Requirement(line))
    expected = {canonicalize_name(r.name): r for r in requirements}
    assert found.keys() == expected.keys(), (found.keys() - expected.keys(), expected.keys() - found.keys())
    assert all(found[key] in requirement.specifier for key, requirement in expected.items())
    return packages


def build(wheelhouse, output, build_date, snapshot_only=False):
    output.mkdir(parents=True, exist_ok=True)
    assert output != wheelhouse, 'Keep dependency wheels separate from release artifacts.'
    packages = dependency_wheels(wheelhouse)
    epoch = int(datetime.combine(build_date, datetime.min.time(), timezone.utc).timestamp())
    log = ''
    if not snapshot_only:
        with tempfile.TemporaryDirectory(prefix='pyfracpaq-build-') as temporary:
            stage = Path(temporary)
            shutil.copytree(ROOT / 'pyfracpaq', stage / 'pyfracpaq',
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store'))
            for name in ('docs', 'examples'):
                shutil.copytree(ROOT / name, stage / name)
            for name in ('pyproject.toml', 'MANIFEST.in', 'README.md', 'CHANGELOG.md', 'LICENSE',
                         'THIRD_PARTY_NOTICES.md', 'requirements.txt', 'requirements-dev.txt', 'run_gui.py'):
                shutil.copyfile(ROOT / name, stage / name)
            program = ('from setuptools.build_meta import build_sdist, build_wheel; '
                       f'build_sdist({str(output)!r}); build_wheel({str(output)!r})')
            result = subprocess.run([sys.executable, '-I', '-c', program], cwd=stage,
                                    env={**os.environ, 'SOURCE_DATE_EPOCH': str(epoch),
                                         'PIP_NO_INDEX': '1', 'PIP_DISABLE_PIP_VERSION_CHECK': '1'},
                                    capture_output=True, text=True, timeout=120)
            log = result.stdout + result.stderr
            assert result.returncode == 0, log
    wheel = output / f'pyfracpaq-{__version__}-py3-none-any.whl'
    sdist = output / f'pyfracpaq-{__version__}.tar.gz'
    assert wheel.is_file() and sdist.is_file(), 'Build the wheel and sdist first.'
    paths, baseline = source_paths()
    target = output / f'pyfracpaq-{__version__}-internal-reference.zip'
    with tempfile.NamedTemporaryFile(prefix='.pyfracpaq-release-', suffix='.zip', dir=output, delete=False) as f:
        temporary = Path(f.name)
    try:
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=3) as archive:
            for path in paths:
                info = zipfile.ZipInfo(f'pyfracpaq-{__version__}/' + str(path.relative_to(ROOT)),
                                       date_time=(*build_date.timetuple()[:3], 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, path.read_bytes())
        with zipfile.ZipFile(temporary) as archive:
            assert archive.testzip() is None
        temporary.replace(target)
    finally:
        if temporary.exists():
            temporary.unlink()
    artifacts = [{'path': str(p.relative_to(ROOT)), 'bytes': p.stat().st_size, 'sha256': sha256(p)}
                 for p in (wheel, sdist, target)]
    write_json(output / 'release-manifest.json', {
        'version': __version__, 'reference': 'FracPaQ MATLAB 2.8', 'date': build_date.isoformat(),
        'status': 'INTERNAL ONLY. Includes original reference material; not a public release.',
        'platform': 'macOS arm64 / CPython3.13.18; Windows/Linux deferred by user',
        'artifacts': artifacts, 'dependencies': packages,
        'dependency_directory': os.path.relpath(wheelhouse, output),
        'original_baseline_files': len(baseline), 'user_outputs_included': False,
        'notes': 'Wheel/sdist contain the installable application; the complete source ZIP also contains '
                 'the exact164 original reference files and earlier test evidence. This point-4 evidence '
                 'is external to the archive to avoid circular hashes. No venvs, credentials, caches, '
                 'root exports or eight extra original-folder outputs are included. '
                 'Dependency wheels are transported separately in wheelhouse-macos-arm64.'})
    (output / 'SHA256SUMS').write_text(''.join(f"{p['sha256']}  {Path(p['path']).name}\n" for p in artifacts))
    if log:
        (output / 'build.log').write_text(log)
    print(f'Built local {__version__}: wheel, sdist, {len(paths)}-file source ZIP; '
          f'{len(packages)} pinned dependency wheels. No publication.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheelhouse', type=Path, required=True)
    parser.add_argument('--output-directory', type=Path, default=ROOT / 'dist' / 'internal' / __version__)
    parser.add_argument('--internal-reference-archive', action='store_true',
                        help='Acknowledge that this legacy build includes original MATLAB reference files; do not publish.')
    parser.add_argument('--build-date', type=date.fromisoformat, default=date(2026, 11, 16))
    parser.add_argument('--snapshot-only', action='store_true',
                        help='Refresh the complete source ZIP after validation; preserve wheel/sdist.')
    args = parser.parse_args()
    if not args.internal_reference_archive:
        parser.error('Internal build only. For the public source ZIP use prepare_source_archive.py. '
                     'To build private reference material explicitly pass --internal-reference-archive.')
    if 'public' in args.output_directory.resolve().parts:
        parser.error('Internal artifacts must not be written to a public delivery directory.')
    build(args.wheelhouse.resolve(), args.output_directory.resolve(), args.build_date, args.snapshot_only)
