"""Create once, or verify, the immutable FracPaQ source baseline."""

import argparse
import json

from reference_common import ORIGINAL, REFERENCE, distribution_files, sha256
from reference_common import write_json

MANIFEST = REFERENCE / 'source_manifest.json'


def snapshot() -> dict:
    return {
        'schema_version': 1,
        'reference_version': 'FracPaQ 2.8 / 2.8.0, March 2021',
        'origin': 'Distribuição local fornecida; commit upstream não informado.',
        'files': [
            {'path': str(p.relative_to(ORIGINAL)), 'bytes': p.stat().st_size,
             'sha256': sha256(p)}
            for p in distribution_files()
        ],
    }


def verify() -> None:
    expected = json.loads(MANIFEST.read_text(encoding='utf-8'))
    actual = snapshot()
    if expected != actual:
        old = {p['path']: p for p in expected['files']}
        new = {p['path']: p for p in actual['files']}
        changes = [p for p in sorted(old.keys() | new.keys())
                   if old.get(p) != new.get(p)]
        raise SystemExit(f'Distribuição divergiu da referência: {changes}')
    print(f"SHA-256: {len(actual['files'])} arquivos originais intactos.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--create', action='store_true',
                        help='Criar baseline; recusa sobrescrever um existente.')
    args = parser.parse_args()
    if args.create:
        if MANIFEST.exists():
            parser.error('Baseline já existe; use a verificação sem --create.')
        write_json(MANIFEST, snapshot())
    verify()


if __name__ == '__main__':
    main()
