from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Tuple

from ..types import Segment, Trace


def read_segments_txt(path: str | Path) -> List[Segment]:
    """Read segments from a whitespace- or comma-separated text file.

    Expected columns per line (at minimum): x1 y1 x2 y2
    Extra columns are ignored. Blank lines and lines starting with '#' are skipped.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)

    segments: List[Segment] = []
    with p.open("r", encoding="utf-8") as f:
        for ln in f:
            line = ln.strip()
            if not line or line.startswith("#"):
                continue
            # Support comma or whitespace delimiters
            parts: List[str]
            if "," in line:
                parts = [x.strip() for x in line.split(",") if x.strip()]
            else:
                parts = line.split()
            if len(parts) < 4:
                # Skip malformed lines silently; could also raise ValueError
                continue
            try:
                x1, y1, x2, y2 = map(float, parts[:4])
            except ValueError:
                continue
            segments.append(Segment(x1, y1, x2, y2))
    return segments


def read_traces_txt(path: str | Path) -> List[Trace]:
    """Read traces from a text file with polylines per line.

    Each non-empty, non-comment line should contain an even number of values:
    x1 y1 x2 y2 [x3 y3 ... xn yn]. Commas are also accepted as separators.

    Returns a list of Trace objects, where consecutive point pairs on a line
    form segments; duplicate consecutive points are ignored.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)

    traces: List[Trace] = []
    with p.open("r", encoding="utf-8") as f:
        for ln in f:
            line = ln.strip()
            if not line or line.startswith("#"):
                continue
            # Allow comma or whitespace-delimited values
            if "," in line:
                parts = [x.strip() for x in line.split(",") if x.strip()]
            else:
                parts = line.split()
            # Keep only numeric convertible tokens
            vals: List[float] = []
            for t in parts:
                try:
                    vals.append(float(t))
                except ValueError:
                    # stop at first non-numeric
                    break
            if len(vals) < 4:
                continue
            # Ensure even number of coordinates (pairs of x,y)
            if len(vals) % 2 == 1:
                vals = vals[:-1]
            pts: List[Tuple[float, float]] = [(vals[i], vals[i + 1]) for i in range(0, len(vals), 2)]
            if len(pts) < 2:
                continue
            segs: List[Segment] = []
            prev = pts[0]
            for cur in pts[1:]:
                if cur == prev:
                    continue
                segs.append(Segment(prev[0], prev[1], cur[0], cur[1]))
                prev = cur
            if segs:
                traces.append(Trace(segs))
    return traces
