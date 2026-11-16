"""Shared sampling pattern for lines and grids.

Marker artists use ordinary Matplotlib square/circle paths at every DPI.
The native marker atlas is historical audit evidence, not a runtime input.
"""

import numpy as np

SAMPLES=np.array([[9,5],[7,11],[13,9],[5,3],[3,13],[1,7],[11,15],[15,1]],dtype=float)/16-.5
