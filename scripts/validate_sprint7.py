"""Reproducible circular sampling evidence; no native MATLAB execution claimed."""

import argparse
from dataclasses import asdict, replace
import json
from math import hypot, pi
from pathlib import Path
import platform

import matplotlib
matplotlib.use('Agg')
import numpy as np

from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.analysis.circular import sample_circles
from pyfracpaq.analysis.hough import HoughParameters
from pyfracpaq.geometry.circles import circle_counts
from pyfracpaq.io import read_txt
from pyfracpaq.io.images import read_image
from pyfracpaq.io.svg import read_svg
from pyfracpaq.domain.execution import RunContext
from reference_common import ROOT, sha256, write_json
from source_manifest import verify
from sprint3_reference import reference_config
from validate_sprint56 import save_figure


def emulate_legacy(segment, centre, radius) -> tuple[int, int]:
    """Static translation of pattern.m predicates, NOT executed MATLAB output."""
    x1, y1, x2, y2 = np.array(segment, dtype=float) - np.tile(centre, 2)
    a, b = hypot(x1, y1) < radius, hypot(x2, y2) < radius
    m = int(a) + int(b)
    if m:
        return int(m == 1), m
    dx, dy = x2 - x1, y2 - y1
    determinant = x1 * y2 - x2 * y1
    delta = radius ** 2 * (dx ** 2 + dy ** 2) - determinant ** 2
    sign_x = (x1 < 0 and x2 >= 0) or (x2 < 0 and x1 >= 0)
    sign_y = (y1 < 0 and y2 >= 0) or (y2 < 0 and y1 >= 0)
    return (2 if delta > 0 and sign_x and sign_y else 0), 0


def q20_cases() -> dict:
    cases = []
    fixtures = json.loads((ROOT / 'tests/fixtures/analytic_cases.json').read_text())['cases']
    for case in fixtures:
        if case['family'] != 'circles':
            continue
        data = case['input']
        line = np.array(data['segment']).reshape(4)
        n, m = circle_counts([line], data['centre'], data['radius'])
        old_n, old_m = emulate_legacy(line, data['centre'], data['radius'])
        r = data['radius']
        cases.append({'id': case['id'], 'input': data,
                      'legacy_static': {'n': old_n, 'm': old_m, 'P21': old_n / (4 * r),
                                        'P20': old_m / (2 * pi * r * r)},
                      'corrected': {'n': int(n[0]), 'm': int(m[0]), 'P21': float(n[0] / (4 * r)),
                                    'P20': float(m[0] / (2 * pi * r * r))}})
    return {'scope': 'Analytic cases vs static predicate translation; not native MATLAB results.',
            'approval': {'date': '2026-11-14', 'user': 'Corrigir a contagem geométrica',
                         'decision': 'Finite closed segment: distinct circle points per segment; '
                                     'tangent=1, boundary endpoints included in n, strict interior m.'},
            'source': 'fracpaq-matlab/guiFracPaQ2Dpattern.m',
            'source_sha256': sha256(ROOT / 'fracpaq-matlab/guiFracPaQ2Dpattern.m'),
            'cases': cases}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=ROOT / 'tests/reference/sprint7')
    args = parser.parse_args()
    folder = args.directory
    folder.mkdir(parents=True, exist_ok=True)
    records, arrays, figures, configs = [], {}, [], []
    sources = [('TXT', ROOT / 'tests/fixtures/nodes/mixed.txt'),
               ('SVG', ROOT / 'tests/fixtures/svg/multicolour.svg'),
               ('Hough', ROOT / 'tests/fixtures/images/rectangular.tif')]
    for tag, source in sources:
        scale = 2 if tag == 'Hough' else None
        data = (read_txt(source) if tag == 'TXT' else read_svg(source).dataset if tag == 'SVG'
                else read_image(source, HoughParameters(), pixels_per_metre=scale).dataset)
        cfg = replace(reference_config(('MAP-07', 'MAP-08'), edit_numscancircles='3',
                                        checkbox_showcircles=True), tag=tag,
                      input=replace(reference_config().input, path=source,
                                    kind='image' if tag == 'Hough' else 'node',
                                    pixels_per_metre=scale))
        configs.append(asdict(cfg))
        registry = AnalysisRegistry()
        results = registry.execute(data, RunContext(cfg, folder, folder, tag),
                                   lambda *a: None, lambda: False)
        assert results[0].data is results[1].data
        result = results[0].data
        for key in ('intersections', 'endpoints_inside', 'intensity', 'density'):
            arrays[tag + '_' + key] = getattr(result, key)
        arrays[tag + '_centres'] = result.grid.centres
        arrays[tag + '_segment_coordinates'] = data.as_arrays().segment_coordinates
        arrays[tag + '_trace_colours'] = data.as_arrays().trace_colours
        for entry in results:
            spec = next(s for s in registry.specs if s.id == entry.analysis_id)
            for output in spec.render(entry.data, cfg):
                figures.append({'input_mode': tag, **save_figure(output, tag, folder)})
        records.append({'input_mode': tag, 'input': str(source.relative_to(ROOT)),
                        'input_sha256': sha256(source), 'scale': scale,
                        'bounds': asdict(data.bounds), 'segments': data.n_segments,
                        'grid_shape': result.grid.shape, 'dx': result.grid.dx, 'dy': result.grid.dy,
                        'radius': result.grid.radius, 'image_extent': result.grid.extent,
                        'global_P21': result.global_intensity, 'global_P20': result.global_density,
                        'mean_local_P21': float(result.intensity.mean()),
                        'mean_local_P20': float(result.density.mean())})
    # Real Hough-origin examples supplement the small, fully rendered fixtures.
    for name in ('MacduffBinary.tif', 'Orkney1aBinary.tif'):
        source = ROOT / 'fracpaq-matlab' / name
        data = read_image(source).dataset
        result = sample_circles(data, 12)
        for key in ('intersections', 'endpoints_inside', 'intensity', 'density'):
            arrays[name + '_' + key] = getattr(result, key)
        arrays[name + '_centres'] = result.grid.centres
        records.append({'input_mode': 'Hough', 'input': str(source.relative_to(ROOT)),
                        'input_sha256': sha256(source), 'segments': data.n_segments,
                        'grid_shape': result.grid.shape, 'radius': result.grid.radius,
                        'global_P21': result.global_intensity, 'global_P20': result.global_density})
    np.savez_compressed(folder / 'arrays.npz', **arrays)
    (folder / 'parameters.json').write_text(json.dumps(configs, default=str, indent=2) + '\n')
    write_json(folder / 'q20_static_reproduction.json', q20_cases())
    report = {'scope': 'Python Sprint 7; corrected geometry approved by user; native MATLAB parity pending.',
              'date': '2026-11-14', 'python': platform.python_version(),
              'platform': platform.platform(), 'numpy': np.__version__,
              'matplotlib': matplotlib.__version__, 'matlab_comparison': 'pending',
              'cases': records, 'figures': figures,
              'txt': [{'path': p.name, 'sha256': sha256(p)} for p in sorted(folder.glob('*.txt'))],
              'arrays_sha256': sha256(folder / 'arrays.npz'),
              'parameters_sha256': sha256(folder / 'parameters.json'),
              'q20_sha256': sha256(folder / 'q20_static_reproduction.json')}
    write_json(folder / 'validation.json', report)
    verify()
    print(f'Sprint 7: {len(figures)} PNGs, {len(report["txt"])} TXT, {len(records)} cases.')


if __name__ == '__main__':
    main()
