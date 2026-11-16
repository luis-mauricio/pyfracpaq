"""Package-relative assets, independent of the process working directory."""

from importlib.resources import files
import json


def resource_bytes(name: str) -> bytes:
    return files(__package__).joinpath(name).read_bytes()


def resource_text(name: str) -> str:
    return files(__package__).joinpath(name).read_text(encoding='utf-8')


def ui_specification() -> dict:
    return json.loads(resource_text('ui_spec.json'))
