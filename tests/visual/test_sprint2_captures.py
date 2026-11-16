"""Audit recorded Qt smoke captures; these are not MATLAB visual goldens."""

import json

from PIL import Image
import pytest

from reference_common import REFERENCE, ROOT, sha256


@pytest.mark.parametrize('percent', [100, 125, 150, 200])
def test_dpi_captures_have_full_text_and_reference_macro_proportions(percent):
    folder = REFERENCE / 'sprint2' / f'dpi-{percent}'
    manifest = json.loads((folder / 'manifest.json').read_text())
    assert manifest['platform'] == 'offscreen'
    assert manifest['logical_size'] == [1366, 768]
    assert manifest['device_pixel_ratio'] == percent / 100
    assert manifest['text_fit_violations'] == []
    assert manifest['focus_check']['has_focus']
    assert max(manifest['macro_position_deviation_pixels'].values()) <= 2
    assert manifest['input_sha256'] == sha256(ROOT / manifest['input'])
    assert {c['state'] for c in manifest['captures']} == {
        'initial', 'preview', 'maps', 'lengths', 'angles', 'fluid', 'wavelets', 'graphs',
    }
    for capture in manifest['captures']:
        path = folder / capture['path']
        assert sha256(path) == capture['sha256']
        with Image.open(path) as image:
            assert list(image.size) == capture['raster_size']
            assert abs(image.width - 1366 * percent / 100) <= 1
            assert abs(image.height - 768 * percent / 100) <= 1
