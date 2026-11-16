"""Rebuild package RGB data from the untouched, supplied cmocean.m."""

import hashlib
import json
from pathlib import Path
import re

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
NAMES = ('deep', 'matter', 'algae', 'dense', 'balance', 'gray', 'oxy', 'solar',
         'phase', 'haline', 'speed', 'thermal', 'turbid', 'delta', 'curl',
         'amp', 'tempo', 'ice')


def extract(text: str) -> dict:
    matches = re.findall(r"case\s+(?:\{)?'([a-z]{3})'(?:\})?\s*RGB\s*=\s*\[(.*?)\];",
                         text, flags=re.DOTALL)
    tables = {prefix: np.fromstring(body.replace(';', ' '), sep=' ').reshape(-1, 3)
              for prefix, body in matches}
    if len(tables) != 18:
        raise ValueError(f'Expected 18 RGB tables, found {len(tables)}.')
    return tables


def main() -> None:
    source = ROOT / 'fracpaq-matlab/cmocean.m'
    tables = extract(source.read_text())
    directory = ROOT / 'pyfracpaq/resources'
    np.savez_compressed(directory / 'cmocean_rgb.npz', **tables)
    manifest = {
        'source': str(source.relative_to(ROOT)),
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'names': {name: name[:3] for name in NAMES},
        'tables': {key: {'shape': list(value.shape),
                         'float64_le_sha256': hashlib.sha256(
                             value.astype('<f8').tobytes()).hexdigest()}
                   for key, value in tables.items()},
        'licences': 'cmocean_LICENSE.txt',
        'method': 'Original decimal tokens to float64; no external cmocean dependency.',
    }
    (directory / 'cmocean_manifest.json').write_text(
        json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
