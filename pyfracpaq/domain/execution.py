"""Frozen execution contracts, independent of widgets and graphics backends."""

from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

from pyfracpaq.geometry.profiles import ProfileLine

ControlValue: TypeAlias = bool | str


@dataclass(frozen=True, slots=True)
class InputConfig:
    path: Path
    kind: str
    pixels_per_metre: float | None
    extraction: tuple[tuple[str, str], ...]
    file_stamp: tuple[int, int] | None


@dataclass(frozen=True, slots=True)
class AnalysisConfig:
    values: tuple[tuple[str, ControlValue], ...]
    selected: tuple[str, ...]
    tag: str
    flip_x: bool
    flip_y: bool
    input: InputConfig
    profile_line: ProfileLine | None = None

    def value(self, name: str) -> ControlValue:
        return dict(self.values)[name]


@dataclass(frozen=True, slots=True)
class RunContext:
    config: AnalysisConfig
    output_directory: Path
    temporary_directory: Path
    run_id: str


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    analysis_id: str
    data: object


class FieldError(ValueError):
    def __init__(self, field: str, message: str) -> None:
        self.field = field
        super().__init__(message)
