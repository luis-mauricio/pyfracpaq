from __future__ import annotations

from typing import Iterable

import numpy as np

from ..types import Segment


def lengths(segments: Iterable[Segment]) -> np.ndarray:
    """Return segment lengths as a NumPy array."""
    return np.array([s.length() for s in segments], dtype=float)

