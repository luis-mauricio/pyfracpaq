"""Frozen cmocean RGB tables extracted from FracPaQ 2.8; see manifest/licences."""

from functools import lru_cache
from io import BytesIO
import json

import numpy as np
from numpy.typing import NDArray

from pyfracpaq.resources import resource_bytes, resource_text


@lru_cache(maxsize=1)
def _tables() -> dict[str, NDArray[np.float64]]:
    with np.load(BytesIO(resource_bytes('cmocean_rgb.npz'))) as archive:
        tables = {name: archive[name] for name in archive.files}
    for table in tables.values():
        table.setflags(write=False)
    return tables


def cmocean(name: str, levels: int = 256, *, reverse: bool = False,
            pivot: float | None = None, limits: tuple[float, float] | None = None
            ) -> NDArray[np.float64]:
    """Source channel interpolation, optional reversal and explicit caxis pivot."""
    if isinstance(levels, bool) or not isinstance(levels, int) or levels < 1:
        raise ValueError('Palette levels must be a positive integer.')
    names = json.loads(resource_text('cmocean_manifest.json'))['names']
    if name not in names:
        raise ValueError(f'Unknown cmocean palette: {name}.')
    table = _tables()[names[name]]
    coordinates = np.linspace(1, len(table), levels)
    rgb = np.column_stack([np.interp(coordinates, np.arange(1, len(table) + 1),
                                    table[:, channel]) for channel in range(3)])
    if reverse:
        rgb = rgb[::-1].copy()
    if pivot is not None:
        if limits is None or len(limits) != 2 or not np.isfinite([pivot, *limits]).all() \
                or limits[0] >= limits[1]:
            raise ValueError('Palette pivot requires finite increasing colour limits.')
        extent = max(abs(limits[0] - pivot), abs(limits[1] - pivot))
        positions = np.linspace(pivot - extent, pivot + extent, levels)
        sample = np.linspace(*limits, levels)
        rgb = np.column_stack([np.interp(sample, positions, rgb[:, channel]) for channel in range(3)])
    elif limits is not None:
        raise ValueError('Colour limits require an explicit pivot.')
    rgb.setflags(write=False)
    return rgb


@lru_cache(maxsize=4)
def matlab_rgb(name: str, *, reverse: bool = False) -> NDArray[np.float64]:
    """Nominal hot/bone tables reconstructed in Sprint 6 (not native captures)."""
    if name not in ('hot', 'bone'):
        raise ValueError(f'Unknown MATLAB RGB palette: {name}.')
    with np.load(BytesIO(resource_bytes('matlab_rgb.npz'))) as archive:
        table = archive[name].copy()
    if reverse:
        table = table[::-1].copy()
    table.setflags(write=False)
    return table


@lru_cache(maxsize=6)
def matlab_jet(levels: int = 100, *, reverse: bool = False) -> NDArray[np.float64]:
    """Exact jet tables captured locally from MATLAB; no interpolation of RGB."""
    if isinstance(levels, bool) or not isinstance(levels, int) or levels not in (19, 100, 256):
        raise ValueError('Frozen MATLAB jet levels must be 19, 100 or 256.')
    with np.load(BytesIO(resource_bytes('jet_rgb.npz'))) as archive:
        table = archive[f'jet{levels}'].copy()
    if reverse:
        table = table[::-1].copy()
    table.setflags(write=False)
    return table
