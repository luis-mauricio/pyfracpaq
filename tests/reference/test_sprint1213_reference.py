"""Genuine native outputs and explicitly approved scientific differences."""

import json

import numpy as np
from PIL import Image
import pytest

from reference_common import ROOT, REFERENCE, sha256


@pytest.mark.parametrize('sprint,pngs', [(12, 13), (13, 12)])
def test_native_provenance_files_are_genuine_and_sources_unchanged(sprint, pngs):
    provenance = json.loads((REFERENCE / f'sprint{sprint}/native_provenance.json').read_text())
    assert provenance['native_version'].startswith('24.2.')
    assert provenance['original_files_sha256_verified'] == 164
    assert len(provenance['extra_original_folder_files_preserved']) == 8
    assert sha256(ROOT / provenance['capture_script']) == provenance['capture_script_sha256']
    assert sum(p['path'].endswith('.png') for p in provenance['outputs']) == pngs
    for output in provenance['outputs']:
        path = ROOT / output['path']
        assert path.is_file() and sha256(path) == output['sha256']
        if path.suffix == '.png':
            assert output['size'] == [4724, 4724]
            assert output['dpi'][0] == pytest.approx(600, abs=.01)


def test_native_calls_are_distinguished_from_proposed_scientific_results():
    calls = json.loads((REFERENCE / 'sprint13/native/native_calls.json').read_text())
    assert calls['no_intersections']['success'] is False
    assert calls['zero_line']['success'] is False
    assert calls['density_only'] == {'success': True, 'figures': 3}
    blocks = json.loads((REFERENCE / 'sprint12/candidate/q14_comparison.json').read_text())
    assert blocks['native']['areas_pixels'] == [2721, 1368, 1368]
    assert blocks['proposed']['areas_pixels'] == [1444, 1444]
    density = json.loads((REFERENCE / 'sprint13/candidate/q20_density_comparison.json').read_text())
    assert density['native_formula'] == 'm/(2*pi*r)'
    assert density['proposed_formula'] == 'm/(2*pi*r^2)'


@pytest.mark.parametrize('sprint,count', [(12, 9), (13, 9)])
def test_approved_exports_match_manifest_and_shared_png_contract(sprint, count):
    folder = REFERENCE / f'sprint{sprint}/candidate'
    validation = json.loads((folder / 'validation.json').read_text())
    assert len(validation['figures']) == count
    for figure in validation['figures']:
        subfolder = folder / figure['tag'] if sprint == 12 else folder
        path = subfolder / figure['path']
        assert sha256(path) == figure['sha256']
        assert sha256(subfolder / figure['qa']) == figure['qa_sha256']
        with Image.open(path) as image:
            assert image.size == (4724, 4724)
            assert image.info['dpi'][0] == pytest.approx(600, abs=.01)
    if sprint == 13:
        assert not list(folder.glob('*.txt'))
        assert validation['production_registry'] == ['GRA-03', 'GRA-04', 'GRA-05', 'GRA-06', 'GRA-07',
                                                       'GRA-10', 'GRA-11', 'GRA-12']
        assert validation['approval']['statement'] == 'Aprovo ambos Q-14 e Extensão Q-20.'
    else:
        arrays = np.load(folder / 'arrays.npz')
        np.testing.assert_array_equal(arrays['unscaled_raster'], arrays['scaled10_raster'])
        np.testing.assert_allclose(arrays['scaled10_areas'], arrays['unscaled_areas'] / 100)
