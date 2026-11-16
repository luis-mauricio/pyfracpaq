"""Basic map data and explicit legacy colour indices."""

from dataclasses import dataclass
from collections.abc import Callable

import numpy as np
from numpy.typing import ArrayLike, NDArray

from pyfracpaq.analysis.compatibility import matlab_round, strike_indices
from pyfracpaq.domain import Dataset
from pyfracpaq.domain.execution import RunContext


def length_indices(lengths: ArrayLike) -> NDArray[np.int64]:
    values = np.asarray(lengths, dtype=np.float64)
    result = np.maximum(1, matlab_round(values / values.max() * 256)).astype(int) - 1
    result.setflags(write=False)
    return result


@dataclass(frozen=True, slots=True)
class MapResult:
    dataset: Dataset
    kind: str
    colour_indices: NDArray[np.int64] | None


def compute_map(kind: str) -> Callable:
    if kind not in ('traces', 'trace_length', 'segment_length', 'strike'):
        raise ValueError(f'Unknown map kind: {kind}.')

    def compute(dataset: Dataset, context: RunContext,
                progress: Callable[[int, str], None]) -> MapResult:
        arrays, config = dataset.as_arrays(), context.config
        indices = None
        if kind == 'trace_length':
            indices = length_indices(arrays.trace_lengths)
        elif kind == 'segment_length':
            indices = length_indices(arrays.segment_lengths)
        elif kind == 'strike':
            indices = strike_indices(arrays.raw_angles,
                                     float(config.value('edit_degfromnorth')),
                                     config.flip_x, config.flip_y)
        return MapResult(dataset, kind, indices)
    return compute
