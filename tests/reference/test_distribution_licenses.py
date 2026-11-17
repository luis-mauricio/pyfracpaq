"""Exercise public ZIP checks against missing notices and accidental payloads."""

import json
import os
import subprocess
import sys
import zipfile

import pytest

from check_distribution_licenses import validate_archive, validate_repository
from pyfracpaq import __version__
from reference_common import ROOT


PREFIX = f'pyfracpaq-{__version__}/'


@pytest.fixture
def payload():
    manifest = json.loads((ROOT / 'docs/licenses/manifest.json').read_text())
    names = {'LICENSE', 'THIRD_PARTY_NOTICES.md', 'requirements.txt',
             'docs/licenses/README.md', 'docs/licenses/manifest.json'}
    names.update(item['path'] for item in manifest['notice_files'])
    names.update(item['path'] for item in manifest['dependency_notice_files'])
    names.update(item['path'] for item in manifest['assets'])
    return {name: (ROOT / name).read_bytes() for name in names}


def write_archive(tmp_path, payload):
    path = tmp_path / 'candidate.zip'
    with zipfile.ZipFile(path, 'w') as archive:
        for name, content in payload.items():
            archive.writestr(PREFIX + name, content)
    return path


def test_reviewed_tree_and_source_zip_preserve_notices(tmp_path, payload):
    tree = validate_repository()
    archive = validate_archive(write_archive(tmp_path, payload))
    assert archive['notice_files'] == tree['notice_files']
    assert archive['upstream_supplements'] == tree['upstream_supplements']
    assert archive['reviewed_assets'] == tree['reviewed_assets']
    assert not archive['matlab_distribution_included']
    assert not archive['bundled_dependencies_included']


def test_cannot_drop_original_copyright(tmp_path, payload):
    payload['LICENSE'] = payload['LICENSE'].replace(
        b'Copyright 2017 FracPaQ Contributors - David Healy, Roberto Rizzo', b'')
    with pytest.raises(ValueError, match='Original FracPaQ license'):
        validate_archive(write_archive(tmp_path, payload))


def test_missing_qt_license_fails(tmp_path, payload):
    del payload['docs/licenses/qt/LGPL-3.0-only.txt']
    with pytest.raises(ValueError, match='Missing notice'):
        validate_archive(write_archive(tmp_path, payload))


def test_missing_dependency_notice_fails(tmp_path, payload):
    del payload['docs/licenses/dependencies/numpy/licenses/LICENSE.txt']
    with pytest.raises(ValueError, match='Missing notice'):
        validate_archive(write_archive(tmp_path, payload))


@pytest.mark.parametrize('name', [
    'fracpaq-matlab/SD11A.txt', 'manual-original.m', 'dialog.fig',
    'dependencies/pyside6.whl', 'Qt/libQt6Core.dylib',
    'tests/reference/manual/photo.png', '../outside.txt', '.env',
    'wheelhouse-macos-arm64/readme.txt', 'foo\\bar.txt', 'docs/fonts/Arial.ttf',
])
def test_unexpected_payload_fails(tmp_path, payload, name):
    payload[name] = b'accidental reference or bundled dependency'
    with pytest.raises(ValueError):
        validate_archive(write_archive(tmp_path, payload))


def test_new_resource_requires_provenance_review(tmp_path, payload):
    payload['pyfracpaq/resources/new-logo.png'] = b'unreviewed artwork'
    with pytest.raises(ValueError, match='Resource inventory differs'):
        validate_archive(write_archive(tmp_path, payload))


def test_new_example_requires_provenance_review(tmp_path, payload):
    payload['examples/new-photo.png'] = b'unreviewed example'
    with pytest.raises(ValueError, match='Example inventory differs'):
        validate_archive(write_archive(tmp_path, payload))


def test_new_manual_image_requires_provenance_review(tmp_path, payload):
    payload['docs/manual/assets/new-photo.png'] = b'unreviewed manual image'
    with pytest.raises(ValueError, match='Manual image inventory differs'):
        validate_archive(write_archive(tmp_path, payload))


def test_changed_resource_or_notice_fails(tmp_path, payload):
    for name, message in [('pyfracpaq/resources/cmocean_rgb.npz', 'Asset needs'),
                          ('docs/licenses/qt/GPL-3.0-only.txt', 'Changed notice')]:
        changed = {**payload, name: payload[name] + b'changed'}
        with pytest.raises(ValueError, match=message):
            validate_archive(write_archive(tmp_path, changed))


def test_changed_qt_pin_requires_review(tmp_path, payload):
    payload['requirements.txt'] = payload['requirements.txt'].replace(
        b'pyside6==6.12.0', b'pyside6==99.0.0')
    with pytest.raises(ValueError, match='Qt dependency version needs review'):
        validate_archive(write_archive(tmp_path, payload))


def test_duplicate_and_symlink_members_fail(tmp_path, payload):
    path = write_archive(tmp_path, payload)
    with zipfile.ZipFile(path, 'a') as archive:
        with pytest.warns(UserWarning, match='Duplicate name'):
            archive.writestr(PREFIX + 'LICENSE', payload['LICENSE'])
    with pytest.raises(ValueError, match='Duplicate path'):
        validate_archive(path)
    path = write_archive(tmp_path, payload)
    with zipfile.ZipFile(path, 'a') as archive:
        link = zipfile.ZipInfo(PREFIX + 'linked-file')
        link.external_attr = 0o120777 << 16
        archive.writestr(link, b'/outside')
    with pytest.raises(ValueError, match='Symlink'):
        validate_archive(path)


@pytest.mark.parametrize('acknowledge', [False, True])
def test_legacy_build_cannot_write_a_public_candidate(tmp_path, acknowledge):
    output = tmp_path / 'public'
    command = [sys.executable, str(ROOT / 'scripts/build_local_release.py'),
               '--wheelhouse', str(tmp_path / 'unused-wheelhouse'),
               '--output-directory', str(output)]
    if acknowledge:
        command.append('--internal-reference-archive')
    result = subprocess.run(command, cwd=ROOT, env={**os.environ, 'PYTHONPATH': str(ROOT)},
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 2
    assert 'public' in result.stderr.lower()
    assert not output.exists()
