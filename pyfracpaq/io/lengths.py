"""Three headerless Lengths tables with atomic per-file replacement."""

import logging
import os
from pathlib import Path
import tempfile

import numpy as np
from numpy.typing import ArrayLike

from pyfracpaq.io.figures import validate_tag


def export_lengths(trace_lengths: ArrayLike, segment_lengths: ArrayLike,
                   raw_angles: ArrayLike, tag: str, directory: Path | str
                   ) -> tuple[Path, ...]:
    validate_tag(tag)
    traces, segments, angles = (np.asarray(a, dtype=np.float64)
                                for a in (trace_lengths, segment_lengths, raw_angles))
    if any(a.ndim != 1 or not len(a) or not np.isfinite(a).all()
           for a in (traces, segments, angles)) or angles.shape != segments.shape:
        raise ValueError('Length exports require nonempty finite, aligned vectors.')
    if np.any(traces <= 0) or np.any(segments <= 0):
        raise ValueError('Exported lengths must be positive.')
    tables = (
        ('FracPaQ2Dsegmentlengths', np.sort(segments), '%6.2f'),
        ('FracPaQ2Dtracelengths', np.sort(traces), '%6.2f'),
        ('FracPaQ2Dsegmentangleslengths', np.column_stack((angles, segments)),
         '%6.2f\t%6.2f'),
    )
    targets, staged = [], []
    directory = Path(directory).resolve()
    try:
        # Finish all writes before replacing any target. Individual replacements
        # are atomic, as for the common PNG/EZROSE exporters; not a filesystem transaction.
        for basename, values, fmt in tables:
            target = directory / f'{basename}_{tag}.txt'
            targets.append(target)
            with tempfile.NamedTemporaryFile(mode='w', encoding='ascii', newline='\n',
                                             prefix='.pyfracpaq-', suffix='.txt',
                                             dir=directory, delete=False) as stream:
                staged.append(Path(stream.name))
                np.savetxt(stream, values, fmt=fmt, newline='\n')
        for temporary, target in zip(staged, targets):
            replaced = target.exists()
            os.replace(temporary, target)
            logging.getLogger(__name__).info('%s Lengths TXT: %s',
                                            'Replaced' if replaced else 'Saved', target)
        return tuple(targets)
    finally:
        for temporary in staged:
            if temporary.exists():
                temporary.unlink()
