"""Atomic source-format segment coordinates/raw strikes, emitted only for slip."""

import logging
import os
from pathlib import Path
import tempfile

from pyfracpaq.domain import Dataset
from pyfracpaq.io.figures import validate_tag


def export_segmentdata(dataset: Dataset, tag: str, directory: Path | str) -> Path:
    validate_tag(tag)
    target = Path(directory).resolve() / f'FracPaQ2Dsegmentdata_{tag}.txt'
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='ascii', newline='\n',
                                         prefix='.pyfracpaq-', suffix='.txt',
                                         dir=target.parent, delete=False) as stream:
            temporary = Path(stream.name)
            for sequence, segment in enumerate(dataset.segments, 1):
                x1, y1 = segment.start.point
                x2, y2 = segment.end.point
                stream.write(f'{sequence:4d}\t{x1:8.4f}\t{y1:8.4f}\t{x2:8.4f}\t{y2:8.4f}\t{segment.raw_angle:3.1f}\n')
        replaced = target.exists()
        os.replace(temporary, target)
        logging.getLogger(__name__).info('%s segmentdata TXT: %s', 'Replaced' if replaced else 'Saved', target)
        return target
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
