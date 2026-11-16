"""Use a reproducible Qt platform for dependency checks, not visual acceptance."""

import os
import tempfile
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) /
                                         'pyfracpaq-matplotlib'))
