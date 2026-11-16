"""Coupled circular intensity/density tables, preserving source row format."""

import logging
import os
from pathlib import Path
import tempfile

import numpy as np
from numpy.typing import ArrayLike

from pyfracpaq.io.figures import validate_tag


def export_circular(centres: ArrayLike, intensity: ArrayLike, density: ArrayLike,
                    tag: str, directory: Path | str) -> tuple[Path, Path]:
    validate_tag(tag)
    centres, intensity, density = (np.asarray(a, dtype=np.float64)
                                   for a in (centres, intensity, density))
    if (centres.ndim != 2 or centres.shape[1] != 2 or not len(centres)
            or intensity.shape != (len(centres),) or density.shape != intensity.shape
            or any(not np.isfinite(a).all() for a in (centres, intensity, density))
            or np.any(intensity < 0) or np.any(density < 0)):
        raise ValueError('Circular exports require aligned finite centres and nonnegative rates.')
    staged, targets = [], []
    directory = Path(directory).resolve()
    try:
        for subject, values in (('intensity', intensity), ('density', density)):
            target = directory / f'FracPaQ2D{subject}_{tag}.txt'
            targets.append(target)
            with tempfile.NamedTemporaryFile(mode='w', encoding='ascii', newline='\n',
                                             prefix='.pyfracpaq-', suffix='.txt',
                                             dir=directory, delete=False) as stream:
                staged.append(Path(stream.name))
                np.savetxt(stream, np.column_stack((centres, values)),
                           fmt='%8.1f %8.1f %14.8f', newline='\n')
        # All writes complete first; atomic per-file replacement, not a group transaction.
        for temporary, target in zip(staged, targets):
            replaced = target.exists()
            os.replace(temporary, target)
            logging.getLogger(__name__).info('%s circular TXT: %s',
                                            'Replaced' if replaced else 'Saved', target)
        return tuple(targets)
    finally:
        for temporary in staged:
            if temporary.exists():
                temporary.unlink()
