"""Linear presentation rules against actual R2024b ruler measurements."""

import json

import numpy as np
import pytest

from pyfracpaq.plots.ticks import MatlabLocator, automatic_limits
from reference_common import REFERENCE

PROBES = json.loads((REFERENCE / 'sprint16/final/native-style/probes.json').read_text())


@pytest.mark.parametrize('probe', PROBES, ids=lambda p: str(p['range']))
def test_decimal_ticks_and_automatic_limits_match_native_probe(probe):
    values = probe['range']
    np.testing.assert_allclose(MatlabLocator().tick_values(*values), probe['manual']['xtick'],
                               rtol=1e-12, atol=0)
    np.testing.assert_allclose(automatic_limits(values), probe['auto']['xlim'],
                               rtol=1e-12, atol=0)


def test_small_window_thins_ticks_without_changing_limits():
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from pyfracpaq.plots.style import figure_axes, matlab_style
    with matlab_style():
        figure, axes = figure_axes()
        axes.set_xlim(0, 1997.7)
        figure.set_size_inches(8, 8)
        canvas = FigureCanvasAgg(figure)
        canvas.draw()
        large = len(axes.get_xticks())
        figure.set_size_inches(2, 2)
        canvas.draw()
        assert len(axes.get_xticks()) < large
        assert axes.get_xlim() == (0, 1997.7)
