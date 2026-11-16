"""Real trace geometry drawn without altering input coordinates."""

from matplotlib.collections import LineCollection
from matplotlib import font_manager
from matplotlib.figure import Figure

from pyfracpaq.domain import Dataset


def draw_preview(
    figure: Figure, dataset: Dataset | None = None,
    *, flip_x: bool = False, flip_y: bool = False,
) -> None:
    figure.clear()
    axes = figure.add_axes((.16, .12, .80, .82))
    families = {font.name for font in font_manager.fontManager.ttflist}
    family = 'Arial' if 'Arial' in families else 'DejaVu Sans'
    axes.set_facecolor('white')
    axes.tick_params(labelsize=9, direction='in', top=True, right=True)
    if dataset is not None:
        paths = [[n.point for n in t.nodes] for t in dataset.traces]
        axes.add_collection(LineCollection(
            paths, colors=[t.colour for t in dataset.traces], linewidths=.75, zorder=3,
        ))
        bounds = dataset.bounds
        for setter, low, high in (
            (axes.set_xlim, bounds.x_min, bounds.x_max),
            (axes.set_ylim, bounds.y_min, bounds.y_max),
        ):
            padding = max(1., abs(low)) * .01 if low == high else 0.
            setter(low - padding, high + padding)
        axes.set_xlabel(f'X, {dataset.length_unit}', fontsize=10, fontfamily=family)
        axes.set_ylabel(f'Y, {dataset.length_unit}', fontsize=10, fontfamily=family)
        axes.set_aspect('equal', adjustable='box')
    else:
        axes.set_xlim(0, 1)
        axes.set_ylim(0, 1)
        # The supplied startup screenshot has eleven ticks on both empty axes.
        ticks = [i / 10 for i in range(11)]
        labels = [f'{value:g}' for value in ticks]
        axes.set_xticks(ticks, labels=labels)
        axes.set_yticks(ticks, labels=labels)
    if flip_x:
        axes.invert_xaxis()
    if flip_y:
        axes.invert_yaxis()
    for label in (*axes.get_xticklabels(), *axes.get_yticklabels()):
        label.set_fontfamily(family)
