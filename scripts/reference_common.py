"""Shared, read-only access to the original distribution."""

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / 'fracpaq-matlab'
REFERENCE = ROOT / 'tests' / 'reference'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n',
        encoding='utf-8',
    )


def distribution_files() -> list[Path]:
    return sorted(path for path in ORIGINAL.rglob('*') if path.is_file())
