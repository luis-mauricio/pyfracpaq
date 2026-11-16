"""Source-order labelled I/X/Y count table with atomic file replacement."""

import logging
import os
from pathlib import Path
import tempfile

from pyfracpaq.io.figures import validate_tag


def export_connectivity(counts: tuple[int, int, int], tag: str,
                        directory: Path | str) -> Path:
    validate_tag(tag)
    if len(counts) != 3 or any(isinstance(x, bool) or not isinstance(x, int) or x < 0 for x in counts):
        raise ValueError('Connectivity counts must be three nonnegative integers in I/Y/X order.')
    ni, ny, nx = counts
    target = Path(directory).resolve() / f'FracPaQ2Dconnectivity_{tag}.txt'
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='ascii', newline='\n',
                                         prefix='.pyfracpaq-', suffix='.txt',
                                         dir=target.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(f'I {ni}\nX {nx}\nY {ny}\n')
        replaced = target.exists()
        os.replace(temporary, target)
        logging.getLogger(__name__).info('%s connectivity TXT: %s', 'Replaced' if replaced else 'Saved', target)
        return target
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
