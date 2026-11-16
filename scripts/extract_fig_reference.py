"""Extract saved MATLAB FIG properties without executing MATLAB callbacks."""

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from scipy.io import loadmat

from reference_common import ORIGINAL, REFERENCE, ROOT, sha256, write_json

PANELS = ('uibgTabMaps', 'uibgTabLengths', 'uibgTabAngles', 'uibgTabFluid',
          'uibgTabWavelets', 'uibgTabGraphs')


def serializable(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: serializable(item) for key, item in value.items()}
    if isinstance(value, np.ndarray):
        if value.dtype == object and value.size == 1:
            return serializable(value.item())
        return serializable(value.tolist())
    if hasattr(value, '_fieldnames'):
        return {key: serializable(getattr(value, key))
                for key in value._fieldnames}
    if isinstance(value, (list, tuple)):
        return [serializable(item) for item in value]
    if isinstance(value, np.generic):
        return serializable(value.item())
    if isinstance(value, complex):
        return {'real': value.real, 'imag': value.imag}
    if isinstance(value, float) and not np.isfinite(value):
        return {'nonfinite': str(value)}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f'Unsupported MAT property type: {type(value)}')


def extract(source: Path) -> dict:
    figure = loadmat(source, simplify_cells=True)['hgS_070000']
    objects = []

    def visit(node: dict, parent: str | None, parent_rect: list[float],
              effective_parent_rect: list[float]) -> None:
        props = serializable(node['properties'])
        tag = props.get('Tag') or f'untagged_{len(objects):03d}'
        position = props.get('Position', [])
        normalized = None
        effective = None
        if node['type'] == 'figure':
            normalized = effective = [0., 0., 1., 1.]
        elif props.get('Units') == 'normalized' and len(position) == 4:
            x, y, w, h = position

            def compose(rect: list[float]) -> list[float]:
                px, py, pw, ph = rect
                return [px + x * pw, py + y * ph, w * pw, h * ph]

            normalized = compose(parent_rect)
            if source.name == 'guiFracPaQ2D.fig' and tag in PANELS[1:]:
                maps = next(o for o in objects if o['tag'] == PANELS[0])
                effective = maps['normalized_figure_rect']
            else:
                effective = compose(effective_parent_rect)
        objects.append({
            'tag': tag, 'type': node['type'], 'parent': parent,
            'saved_properties': props,
            'normalized_figure_rect': normalized,
            'opening_normalized_figure_rect': effective,
        })
        children = node.get('children', [])
        if isinstance(children, dict):
            children = [children]
        for child in children:
            visit(child, tag, normalized or parent_rect,
                  effective or effective_parent_rect)

    visit(figure, None, [0., 0., 1., 1.], [0., 0., 1., 1.])
    return {
        'schema_version': 1, 'source': str(source.relative_to(ROOT)),
        'source_sha256': sha256(source),
        'coordinate_convention': 'MATLAB: bottom-left; normalized to parent. '
                                 'Figure rectangles compose parent rectangles, '
                                 'without native panel insets.',
        'missing_properties': 'Não salvas: dependem dos defaults MATLAB. '
                              'Não inferir valores como se estivessem no FIG.',
        'object_counts': dict(Counter(o['type'] for o in objects)),
        'objects': objects,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path,
                        default=REFERENCE / 'gui')
    args = parser.parse_args()
    for name in ('guiFracPaQ2D', 'guiWaveletDialog'):
        data = extract(ORIGINAL / f'{name}.fig')
        write_json(args.output_dir / f'{name}.json', data)
        print(f"{name}: {len(data['objects'])} objetos extraídos.")


if __name__ == '__main__':
    main()
