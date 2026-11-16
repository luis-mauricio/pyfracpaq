"""Approval, real MATLAB captures, full production runs and complete AUX coverage."""

import json
from pathlib import Path

import numpy as np
from PIL import Image
import pytest

from pyfracpaq.io.nodes import read_txt
from pyfracpaq.io.svg import read_svg
from reference_common import ROOT, REFERENCE, sha256


@pytest.mark.parametrize('sprint', [14, 15])
def test_native_capture_checksums_and_original_integrity(sprint):
    data = json.loads((REFERENCE / f'sprint{sprint}/native_provenance.json').read_text())
    assert data['original_files_sha256_verified'] == 164
    assert len(data['extra_original_folder_files_preserved']) == 8
    for path, expected in data['scripts'].items():
        assert sha256(ROOT / path) == expected
    for output in data['outputs']:
        assert sha256(ROOT / output['path']) == output['sha256']


def test_q12_approval_full_raster_fft_and_exports():
    data = json.loads((REFERENCE / 'sprint14/validation.json').read_text())
    assert data['approval']['statement'] == 'Aprovo a Q-12.'
    assert len(data['cases']) == 2
    for case in data['cases']:
        folder = REFERENCE / 'sprint14/production' / case['kernel']
        assert case['shape_yx'] == [1944, 1944] and case['selected'] > 0
        output = folder / case['figure']['path']
        assert sha256(output) == case['figure']['sha256']
        with Image.open(output) as image:
            assert image.size == (4724, 4724) and image.info['dpi'][0] == pytest.approx(600, abs=.01)
        with Image.open(folder / 'FracPaQ2D_wavelet_traces.png') as image:
            assert image.size == (1944, 1944)
        txt = np.loadtxt(folder / f"FracPaQ2Dwavelet_theta_a32_{case['kernel']}.txt")
        assert len(txt) == 2 * case['selected']
        assert np.isfinite(txt).all()


def test_legacy_destinations_cover_all_original_files_and_aux_ids():
    data = json.loads((ROOT / 'docs/parity/legacy-files.json').read_text())
    manifest = json.loads((REFERENCE / 'source_manifest.json').read_text())['files']
    assert data['count'] == len(data['files']) == 164
    assert {entry['path'] for entry in data['files']} == {entry['path'] for entry in manifest}
    assert all(entry['role'] and entry['disposition'] for entry in data['files'])
    table = (ROOT / 'docs/parity/legacy.md').read_text()
    assert all(f'| AUX-{i:02d} |' in table for i in range(1, 20))


def test_examples_and_packaged_dialog_provenance():
    for entry in json.loads((ROOT / 'examples/provenance.json').read_text()):
        assert sha256(ROOT / entry['path']) == entry['sha256']
    assert read_txt(ROOT / 'examples/rectangles.txt').n_traces == 2
    assert read_txt(ROOT / 'examples/profiles.txt').n_traces == 2
    assert len(read_svg(ROOT / 'examples/colours.svg').dataset.colours) == 2
    dialog = json.loads((ROOT / 'pyfracpaq/resources/wavelet_dialog_provenance.json').read_text())
    assert sha256(ROOT / 'pyfracpaq/resources/wavelet_dialog.json') == dialog['sha256']
    assert sha256(ROOT / dialog['source']) == dialog['source_sha256']
