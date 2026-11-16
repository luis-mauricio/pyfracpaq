"""Source six-stage photographic preparation panel."""

from matplotlib.colors import ListedColormap

from pyfracpaq.plots.results import FigureOutput
from pyfracpaq.plots.style import figure_axes, matlab_style


def render_preprocess(result):
    with matlab_style():
        figure, first = figure_axes((.07, .55, .24, .34))
        fields = ('grayscale', 'median', 'difference', 'edges', 'closed', 'processed')
        titles = ('Grayscale of input', 'Median filter', 'Median filter - raw gray',
                  'Sobel edges', 'Closed edges', 'Thinned & inverted')
        for i, (field, title) in enumerate(zip(fields, titles)):
            axes = first if i == 0 else figure.add_axes((.07 + (i % 3) * .32, .55 - (i // 3) * .45, .24, .34))
            values = getattr(result, field)
            axes.imshow(values, cmap='gray', vmin=0, vmax=1 if values.dtype.kind == 'b' else 255,
                        interpolation='nearest')
            axes.set_title(title, fontsize=10)
            axes.set_axis_off()
    return FigureOutput('FracPaQ2D_imagePreprocess', figure)
