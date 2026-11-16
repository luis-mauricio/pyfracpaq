"""Native stipple lengths, keeping the nominal stroke width unchanged."""

from contextlib import contextmanager
from math import floor

from matplotlib.lines import Line2D


@contextmanager
def native_dashes(figure,renderer):
    if type(renderer).__name__!='RendererAgg':
        yield;return
    restored=[]
    for line in figure.findobj(match=Line2D):
        if line.get_linestyle() not in (':','--','-.'):continue
        offset,pattern=line._unscaled_dash_pattern
        if pattern is None:continue
        old=line._dash_pattern
        factor=max(1,floor(line.get_linewidth()*renderer.dpi/72))*72/renderer.dpi
        line._dash_pattern=(offset*factor,[value*factor for value in pattern])
        restored.append((line,old))
    try:yield
    finally:
        for line,old in restored:line._dash_pattern=old
