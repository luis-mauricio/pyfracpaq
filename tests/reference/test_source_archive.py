"""Verify source ZIP selection and preparation without executing Git commands."""

import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

import pytest

import prepare_source_archive as delivery
from pyfracpaq import __version__


def source_tree(root):
    for name in delivery.ROOT_FILES:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('required delivery file\n')
    for name in delivery.SOURCE_DIRECTORIES:
        (root / name).mkdir(parents=True, exist_ok=True)


def test_selection_excludes_reference_data_secrets_and_build_outputs(tmp_path):
    source_tree(tmp_path)
    for name in ('pyfracpaq/module.py', 'examples/sample.txt',
                 'docs/manual/assets/figure.png', 'docs/licenses/NOTICE'):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('public source')
    excluded = ('tests/reference/photo.png', 'fracpaq-matlab/code.m',
                '.aws/credentials', '.git/config', '.env', 'dist/old-source.zip',
                'docs/manual/build/log.txt', 'docs/manual/guide.aux',
                'docs/manual/guide.synctex.gz', 'pyfracpaq/__pycache__/module.pyc',
                'pyfracpaq/.env', 'pyfracpaq/module.py~', 'examples/.DS_Store')
    for name in excluded:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('private or temporary data')
    names = {p.relative_to(tmp_path).as_posix() for p in delivery.source_paths(tmp_path)}
    assert 'pyfracpaq/module.py' in names
    assert 'docs/manual/assets/figure.png' in names
    assert not names.intersection(excluded)


def test_linked_source_is_rejected(tmp_path):
    source_tree(tmp_path)
    target = tmp_path / 'private.txt'
    target.write_text('private content')
    (tmp_path / 'pyfracpaq/linked.txt').symlink_to(target)
    with pytest.raises(ValueError, match='Symlink'):
        delivery.source_paths(tmp_path)


def test_candidate_is_verified_without_external_commands(tmp_path, monkeypatch):
    def unexpected_command(*args, **kwargs):
        raise AssertionError('ZIP preparation must not execute Git or another external command.')

    monkeypatch.setattr(subprocess, 'run', unexpected_command)
    monkeypatch.setattr(subprocess, 'check_output', unexpected_command)
    report = delivery.prepare(tmp_path, tmp_path / 'source-evidence.json')
    archive = tmp_path / f'pyfracpaq-{__version__}-code.zip'
    assert report['git_commands_executed'] is False
    assert report['actual_index_changed'] is False
    assert report['published'] is False
    manifest = json.loads((tmp_path / 'publication-manifest.json').read_text())
    entry, = manifest['files_to_publish']
    assert entry['sha256'] == hashlib.sha256(archive.read_bytes()).hexdigest()
    prefix = f'pyfracpaq-{__version__}/'
    with zipfile.ZipFile(archive) as source:
        assert source.read(prefix + 'THIRD_PARTY_NOTICES.md') == (
            delivery.ROOT / 'THIRD_PARTY_NOTICES.md').read_bytes()
        assert source.read(prefix + 'docs/manual/pyfracpaq-user-manual.pdf') == (
            delivery.ROOT / 'docs/manual/pyfracpaq-user-manual.pdf').read_bytes()
        assert not any('/tests/' in name or '/fracpaq-matlab/' in name
                       for name in source.namelist())
