"""Atomic common PNG export with the FracPaQ guiPrint print geometry."""

import logging
import os
from pathlib import Path
import re
import tempfile
from typing import TYPE_CHECKING

from pyfracpaq import __version__

if TYPE_CHECKING:
    from matplotlib.figure import Figure

LOG = logging.getLogger(__name__)
PRINT_SIZE_INCHES = 20 / 2.54
PRINT_DPI = 600


def validate_tag(tag: str) -> str:
    if not isinstance(tag, str):
        raise ValueError('The filename tag must be text.')
    if tag in ('.', '..') or re.search(r'[\\/:*?"<>|\x00-\x1f\x7f]', tag):
        raise ValueError('The filename tag cannot contain a path or reserved characters.')
    return tag


def export_png(
    figure: 'Figure', basename: str, tag: str, directory: Path | str,
) -> Path:
    """Write basename_{tag}.png without changing the on-screen figure size."""
    validate_tag(tag)
    if not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]*', basename):
        raise ValueError('The figure basename must be a filename, without a path.')
    directory = Path(directory).resolve()
    target = directory / f'{basename}_{tag}.png'
    old_size = figure.get_size_inches().copy()
    replaced = target.exists()
    temporary = None
    try:
        from matplotlib import rc_context

        with tempfile.NamedTemporaryFile(
            prefix='.pyfracpaq-', suffix='.png', dir=directory, delete=False,
        ) as stream:
            temporary = Path(stream.name)
        figure.set_size_inches(PRINT_SIZE_INCHES, PRINT_SIZE_INCHES, forward=False)
        with rc_context({'savefig.bbox': None}):
            figure.savefig(temporary, format='png', dpi=PRINT_DPI,
                           bbox_inches=None, metadata={
                               'Software': f'PyFracPaQ {__version__}; FracPaQ 2.8 reference',
                           })
        os.replace(temporary, target)
        LOG.info('%s PNG: %s', 'Replaced' if replaced else 'Saved', target)
        return target
    finally:
        figure.set_size_inches(*old_size, forward=False)
        if temporary is not None and temporary.exists():
            temporary.unlink()
