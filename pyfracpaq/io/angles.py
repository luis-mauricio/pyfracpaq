"""Atomic, headerless legacy EZROSE export."""

import logging
import os
from pathlib import Path
import tempfile

import numpy as np
from numpy.typing import ArrayLike

from pyfracpaq.io.figures import validate_tag


def export_ezrose(angles: ArrayLike, tag: str, directory: Path | str) -> Path:
    validate_tag(tag)
    # Preserve source order for ties, including the sign of rounded zero.
    # MATLAB's TXT export keeps these signs; an unstable sort rearranges them.
    values = np.sort(np.asarray(angles, dtype=np.float64).ravel(), kind='stable')
    if not len(values) or not np.isfinite(values).all():
        raise ValueError('EZROSE requires nonempty finite angles.')
    target = Path(directory).resolve() / f'FracPaQ2DEZROSE_{tag}.txt'
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='ascii', newline='\n',
                                         prefix='.pyfracpaq-', suffix='.txt',
                                         dir=target.parent, delete=False) as stream:
            temporary = Path(stream.name)
            for value in values:
                stream.write(f'{value:6.2f}\n')
        replaced = target.exists()
        os.replace(temporary, target)
        logging.getLogger(__name__).info('%s EZROSE TXT: %s',
                                        'Replaced' if replaced else 'Saved', target)
        return target
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
