"""Sprint 4 cases and a static emulation of Q-05, never a MATLAB execution."""

from dataclasses import replace

import numpy as np

from pyfracpaq.domain import Dataset
from pyfracpaq.io import read_txt
from reference_common import ROOT
from sprint3_reference import reference_config

INPUT = ROOT / 'tests/fixtures/nodes/lengths_edges.txt'
SELECTED = ('LEN-02', 'LEN-03', 'LEN-06')


def length_config(selected=SELECTED, **changes):
    config = reference_config(selected, **changes)
    return replace(config, input=replace(config.input, path=INPUT))


def edge_dataset() -> Dataset:
    return read_txt(INPUT)


def emulate_legacy_censor(dataset: Dataset) -> dict:
    """Translate only the supplied faulty predicates/filter ordering for evidence.

    Not a product mode. The native reference remains unexecuted. MATLAB's short
    logical index selects the first retained-count angles after lengths lost NaNs.
    """
    b = dataset.bounds
    excluded = []
    for trace in dataset.traces:
        first, wrong_last = trace.nodes[0], trace.nodes[len(trace.segments) - 1]
        excluded.append(
            first.x in (b.x_min, b.x_max) or first.y in (b.x_min, b.y_max)
            or wrong_last.x in (b.x_min, b.x_max)
            or wrong_last.y in (b.x_max, b.y_max))
    arrays = dataset.as_arrays()
    keep = ~np.asarray(excluded)
    segment_keep = keep[arrays.segment_trace_ids]
    retained_count = int(segment_keep.sum())
    return {
        'scope': 'Static Python emulation of supplied source, not MATLAB execution.',
        'trace_keep': keep.tolist(), 'segment_keep': segment_keep.tolist(),
        'lengths': arrays.segment_lengths[segment_keep].tolist(),
        'misaligned_angles': arrays.raw_angles[:retained_count].tolist(),
        'angles_with_common_mask': arrays.raw_angles[segment_keep].tolist(),
    }
