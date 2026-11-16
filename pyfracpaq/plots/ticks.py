"""MATLAB-style decimal ticks and tick-aligned automatic display limits.

Only presentation is affected. The native linear-ruler probes use 1/2/5
decades, up to eleven intervals for explicit limits and ten for auto limits.
"""

import math

import numpy as np
from matplotlib.ticker import Locator


def decimal_step(span: float, intervals: int = 10) -> float:
    if not math.isfinite(span) or span <= 0:
        return 1.
    raw = span / max(1, intervals)
    exponent = math.floor(math.log10(raw))
    base = 10. ** exponent
    for value in (1., 2., 5., 10.):
        if value * base >= raw * (1 - 1e-12):
            return value * base
    return 10 * base


def automatic_limits(values) -> tuple[float, float]:
    values = np.asarray(values)
    finite = values[np.isfinite(values)]
    if not finite.size:
        return 0., 1.
    low, high = float(finite.min()), float(finite.max())
    if low == high:
        padding = max(1., abs(low) * .05)
        return low - padding, high + padding
    step = decimal_step(high - low)
    return math.floor(low / step) * step, math.ceil(high / step) * step


class MatlabLocator(Locator):
    """Use native decimal intervals, thinning only for smaller windows."""

    def __init__(self,intervals=11):
        self.intervals=intervals

    def __call__(self):
        return self.tick_values(*self.axis.get_view_interval())

    def tick_values(self, vmin, vmax):
        low, high = sorted((vmin, vmax))
        intervals = self.intervals
        if self.axis is not None:
            intervals = min(intervals, max(2, int(self.axis.get_tick_space()*1.25)))
        step = decimal_step(high - low, intervals)
        start = math.ceil(low / step - 1e-12)
        stop = math.floor(high / step + 1e-12)
        ticks = np.arange(start, stop + 1, dtype=float) * step
        return self.raise_if_exceeds(ticks)

