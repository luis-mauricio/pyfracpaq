from __future__ import annotations

from dataclasses import dataclass, field
from math import atan2, degrees, sqrt
from typing import Iterable, List, Tuple


@dataclass(frozen=True)
class Segment:
    """A single line segment defined by two endpoints (x1, y1) -> (x2, y2).

    Angle is returned as an orientation in degrees within [0, 180), suitable
    for fracture trace analysis where direction is not signed.
    """

    x1: float
    y1: float
    x2: float
    y2: float

    def length(self) -> float:
        dx = self.x2 - self.x1
        dy = self.y2 - self.y1
        return sqrt(dx * dx + dy * dy)

    def angle_deg(self) -> float:
        """Return orientation angle in degrees folded to [0, 180).

        Uses arctan2(dy, dx) in degrees within (-180, 180], then folds.
        """
        dx = self.x2 - self.x1
        dy = self.y2 - self.y1
        a = degrees(atan2(dy, dx))  # (-180, 180]
        # Fold direction: treat 0~360 as 0~180 by modulo 180
        a180 = a % 180.0
        # Normalize -0.0 to 0.0 for aesthetics
        return 0.0 if abs(a180) < 1e-12 else a180


@dataclass
class Trace:
    """A trace composed of one or more segments.

    Many datasets represent each fracture as a single segment; this class
    also supports polyline fractures split into multiple contiguous segments.
    """

    segments: List[Segment] = field(default_factory=list)

    def total_length(self) -> float:
        return sum(s.length() for s in self.segments)

    def orientations_deg(self) -> List[float]:
        return [s.angle_deg() for s in self.segments]


@dataclass
class TraceMap:
    """A collection of traces composing a map."""

    traces: List[Trace] = field(default_factory=list)

    @classmethod
    def from_segments(cls, segments: Iterable[Segment]) -> "TraceMap":
        return cls(traces=[Trace([s]) for s in segments])

    def all_segments(self) -> List[Segment]:
        return [s for t in self.traces for s in t.segments]

    def map_limits(self) -> Tuple[float, float, float, float]:
        """Return (xmin, xmax, ymin, ymax) limits across all segments."""
        xs: List[float] = []
        ys: List[float] = []
        for s in self.all_segments():
            xs.extend([s.x1, s.x2])
            ys.extend([s.y1, s.y2])
        if not xs or not ys:
            return (0.0, 0.0, 0.0, 0.0)
        return (min(xs), max(xs), min(ys), max(ys))

