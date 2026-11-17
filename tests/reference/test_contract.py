"""Validate the completeness and integrity of the Sprint 0 evidence."""

import json
import re
import shutil
from collections import Counter
from pathlib import Path

import pytest

import source_manifest
from build_parity_index import CONTROLS, inventory_rows
from extract_fig_reference import PANELS, extract
from reference_common import ORIGINAL, REFERENCE, ROOT, sha256


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def test_original_distribution_unchanged():
    source_manifest.verify()
    files = read_json(REFERENCE / 'source_manifest.json')['files']
    assert len(files) == 164
    assert Counter(Path(p['path']).suffix.lower() for p in files)['.m'] == 82


@pytest.mark.parametrize('change', ['modify', 'add', 'remove'])
def test_manifest_detects_source_changes(tmp_path, monkeypatch, change):
    original = tmp_path / 'original'
    original.mkdir()
    sample = original / 'sample.m'
    sample.write_text('original')
    monkeypatch.setattr(source_manifest, 'ORIGINAL', original)
    monkeypatch.setattr(source_manifest, 'distribution_files',
                        lambda: sorted(p for p in original.rglob('*') if p.is_file()))
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps(source_manifest.snapshot()))
    monkeypatch.setattr(source_manifest, 'MANIFEST', manifest)
    if change == 'modify':
        sample.write_text('changed')
    elif change == 'add':
        (original / 'extra.m').write_text('extra')
    else:
        sample.unlink()
    with pytest.raises(SystemExit, match='Distribuição divergiu'):
        source_manifest.verify()


def test_matrix_covers_every_inventory_id_once():
    rows = inventory_rows()
    matrix = (ROOT / 'docs/parity/matrix.md').read_text()
    ids = re.findall(r'^\| ([A-Z]+-\d{2}) \|', matrix, re.MULTILINE)
    assert len(ids) == len(set(ids)) == 164
    assert set(ids) == rows.keys()
    assert Counter(key.split('-')[0] for key in ids) == {
        'UI': 19, 'IN': 18, 'MAP': 18, 'LEN': 16, 'ANG': 9,
        'FLO': 13, 'WAV': 12, 'GRA': 13, 'EXP': 6, 'AUX': 19, 'Q': 21,
    }


@pytest.mark.parametrize('name,count', [('guiFracPaQ2D', 154), ('guiWaveletDialog', 14)])
def test_fig_extraction_reproduces_all_saved_properties(name, count):
    actual = extract(ORIGINAL / f'{name}.fig')
    assert actual == read_json(REFERENCE / 'gui' / f'{name}.json')
    assert len(actual['objects']) == count
    assert len({o['tag'] for o in actual['objects']}) == count


def test_opening_layout_and_raw_defaults_are_distinct():
    data = read_json(REFERENCE / 'gui/guiFracPaQ2D.json')
    objects = {o['tag']: o for o in data['objects']}
    assert data['object_counts']['uicontrol'] == 119
    maps = objects['uibgTabMaps']['normalized_figure_rect']
    for panel in PANELS:
        assert objects[panel]['opening_normalized_figure_rect'] == maps
    assert objects['uibgTabAngles']['normalized_figure_rect'] != maps
    assert objects['popupmenu_rosebins']['saved_properties']['Value'] == 1
    assert objects['edit_FilenameTag']['saved_properties']['String'] == 'Run1'
    assert objects['figure_main']['saved_properties']['Units'] == 'characters'


def test_control_mapping_names_existing_objects_and_ids():
    objects = read_json(REFERENCE / 'gui/guiFracPaQ2D.json')['objects']
    tags = {o['tag'] for o in objects}
    for group, rows in CONTROLS.items():
        assert len(rows) == sum(key.startswith(group + '-') for key in inventory_rows())
        for controls in rows:
            assert set(controls.split()) <= tags
    table = (ROOT / 'docs/parity/controls.md').read_text()
    tagged = {o['tag'] for o in objects if not o['tag'].startswith('untagged_')}
    assert {tag for tag in re.findall(r'^\| `([^`]+)`', table, re.MULTILINE)} == tagged


def test_questions_are_registered_without_fake_results():
    text = (ROOT / 'docs/parity/divergences.md').read_text()
    assert re.findall(r'^## (Q-\d{2})', text, re.MULTILINE) == [
        f'Q-{i:02d}' for i in range(1, 22)]
    assert text.count('Resultado original executado: **indisponível**') == 7
    assert text.count('Resultado original executado: **disponível**') == 14
    assert (REFERENCE / 'sprint8/native/native_fits.json').is_file()
    assert (REFERENCE / 'sprint9/native/native_topology.json').is_file()
    assert (REFERENCE / 'sprint11/native/native_calls.json').is_file()
    assert (REFERENCE / 'sprint12/native/native_calls.json').is_file()
    assert (REFERENCE / 'sprint13/native/native_calls.json').is_file()


def test_source_catalog_covers_all_matlab_files():
    data = read_json(REFERENCE / 'source_catalog.json')
    assert len(data) == 82
    assert {Path(d['path']).name for d in data} == {p.name for p in ORIGINAL.glob('*.m')}
    for entry in data:
        assert sha256(ROOT / entry['path']) == entry['sha256']
        assert entry['lines'] > 0


def test_capture_catalog_keeps_missing_goldens_explicit():
    data = read_json(REFERENCE / 'capture_catalog.json')
    assert len(data['screens']) == 8
    assert len(data['figures']) == 53
    assert len(data['data_and_intermediates']) == 14
    for figure in data['figures']:
        assert figure['name'].endswith('{tag}.png')
        if figure['matlab_png'] is None:
            assert 'Pendente' in figure['status']
        else:
            assert (ROOT / figure['matlab_png']).is_file()
            assert 'homologação' in figure['status']
        for capture in figure.get('evidence', {}).get('native', []):
            assert sha256(ROOT / capture['path']) == capture['sha256']


def check_manual_image_integrity(reference):
    data = read_json(reference / 'manual/manifest.json')
    policy = read_json(reference / 'image_distribution_policy.json')
    assert policy['directory'] == 'tests/reference/manual'
    local_only = {item['path']: item['sha256'] for item in policy['local_only_images']}
    registered = {item['path']: item['sha256'] for item in data['images']}
    assert local_only and local_only.items() <= registered.items()
    assert data['pages'] == 39
    assert data['source_sha256'] == sha256(ROOT / data['source'])
    assert len(data['images']) == 103
    for entry in data['images']:
        path = reference / 'manual' / entry['path']
        if entry['path'] in local_only and not path.exists():
            continue
        assert sha256(path) == entry['sha256']
        assert 'Não é golden' in entry['role']
    for page in {s['page'] for s in data['unextracted_images']}:
        assert (reference / 'manual' / f'page-{page:02d}.png').is_file()


def test_manual_images_preserve_provenance_and_hashes():
    check_manual_image_integrity(REFERENCE)


@pytest.mark.parametrize('missing_required', [False, True])
def test_public_manual_copy_allows_only_the_registered_local_image_to_be_missing(
        tmp_path, missing_required):
    omitted = ['page-09-image-00.png']
    if missing_required:
        omitted.append('page-04-image-00.png')
    shutil.copytree(REFERENCE / 'manual', tmp_path / 'manual',
                    ignore=shutil.ignore_patterns(*omitted))
    shutil.copyfile(REFERENCE / 'image_distribution_policy.json',
                    tmp_path / 'image_distribution_policy.json')
    if missing_required:
        with pytest.raises(FileNotFoundError):
            check_manual_image_integrity(tmp_path)
    else:
        check_manual_image_integrity(tmp_path)


def test_dependency_notices_are_preserved():
    for dependency in read_json(REFERENCE / 'dependency_licenses.json'):
        paths = [notice['path'] for notice in dependency['notices']]
        assert len(paths) == len(set(paths))
        if not dependency['notices']:
            assert dependency['license_expression'] or dependency['license_metadata']
            assert dependency['notices_status'].startswith('no_notice_file_in_wheel')
        else:
            assert dependency['notices_status'] == 'copied_from_wheel'
        for notice in dependency['notices']:
            assert sha256(ROOT / notice['path']) == notice['sha256']
