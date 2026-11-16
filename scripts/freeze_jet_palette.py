"""Freeze the actual jet(19/100/256) outputs from the native Sprint 11 capture."""

import numpy as np
from scipy.io import loadmat

from reference_common import ROOT, sha256, write_json


def main() -> None:
    source = ROOT / 'tests/reference/sprint11/native/stability_arrays.mat'
    captured = loadmat(source)
    tables = {f'jet{levels}': captured[f'jet{levels}'] for levels in (19, 100, 256)}
    target = ROOT / 'pyfracpaq/resources/jet_rgb.npz'
    np.savez_compressed(target, **tables)
    write_json(target.with_suffix('.json'), {
        'method': 'Unmodified RGB output from installed MATLAB jet, not a named Matplotlib palette.',
        'native_version': str(captured['native_version'][0]),
        'source': str(source.relative_to(ROOT)), 'source_sha256': sha256(source),
        'capture_script': 'scripts/capture_native_s1011.m',
        'capture_script_sha256': sha256(ROOT / 'scripts/capture_native_s1011.m'),
        'levels': [19, 100, 256], 'tables_sha256': sha256(target),
    })
    print('Native jet(19/100/256) tables frozen.')


if __name__ == '__main__':
    main()
