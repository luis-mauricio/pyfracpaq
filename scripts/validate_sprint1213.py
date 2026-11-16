"""Capture approved default Run outputs and compare genuine MATLAB arrays.

The historical candidate paths are retained; approval metadata distinguishes the
promoted production results from the unchanged native MATLAB references.
"""

from dataclasses import replace
import json

import matplotlib
matplotlib.use('Agg')
import numpy as np
from PIL import Image
from scipy.io import loadmat

from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.analysis.blocks import white_components
from pyfracpaq.analysis.profiles import ALONG, CIRCULAR, FROM
from pyfracpaq.analysis.variogram import experimental_variogram
from pyfracpaq.domain.execution import RunContext
from reference_common import ROOT, REFERENCE, ORIGINAL, sha256, write_json
from sprint1213_reference import block_dataset, configuration, graph_dataset
from validate_sprint56 import save_figure

APPROVAL = {'author': 'user', 'date': '2026-11-14',
    'statement': 'Aprovo ambos Q-14 e Extensão Q-20.',
    'decisions': ['Q-14', 'Q-20 Graphs P20 normalization extension'],
    'scope': 'Enclosed white 8-connected blocks, fixed unscaled raster and calibrated areas/centres; '
             'Graphs P20=m/(2*pi*r^2), retaining the previously approved finite counts.'}


def production_run(dataset, cfg, folder):
    registry = AnalysisRegistry()
    results = registry.execute(dataset, RunContext(cfg, folder, folder, cfg.tag),
                               lambda *_: None, lambda: False)
    specs = {spec.id: spec for spec in registry.specs}
    figures = [(result.analysis_id, output) for result in results
               for output in specs[result.analysis_id].render(result.data, cfg)]
    return results, figures


def maximum_error(actual, expected):
    a, b = np.asarray(actual, float), np.asarray(expected, float)
    if a.shape != b.shape or not np.array_equal(np.isnan(a), np.isnan(b)):
        raise AssertionError('Native comparison shape/NaN pattern differs.')
    valid = np.isfinite(a) & np.isfinite(b)
    difference = float(np.max(np.abs(a[valid] - b[valid]))) if valid.any() else 0.
    if difference > 1e-10:
        raise AssertionError(f'Native values differ by {difference}.')
    return difference


def native_comparisons():
    source = loadmat(REFERENCE / 'sprint12/native/variogram_arrays.mat', simplify_cells=True)
    comparisons = {}
    for name, options in [('default', {'nrbins': 30}),
        ('gamma', {}), ('cloud1', {'kind': 'cloud1'}), ('cloud2', {'kind': 'cloud2'}),
        ('anisotropic', {'anisotropy': True}),
        ('anisotropic40', {'anisotropy': True, 'thetastep': 40})]:
        args = {'nrbins': 4, 'maxdist': 3, **options}
        if name == 'default':
            args.pop('maxdist')
        result = experimental_variogram(source['x'], source['values'], **args)
        expected = source['variograms'][name]
        comparisons[name] = {'distance_max_error': maximum_error(result.distance, expected['distance']),
            'gamma_max_error': maximum_error(result.values, expected['val']),
            'pair_count': result.pair_count}
        if result.counts is not None:
            comparisons[name]['counts_max_error'] = maximum_error(result.counts, expected['num'])
    for n in (999, 1000):
        coords = np.column_stack((np.arange(n), np.zeros(n)))
        result = experimental_variogram(coords, np.arange(n) % 5, nrbins=3, maxdist=1.1)
        expected = source['variograms'][f'n{n}']
        comparisons[f'n{n}'] = {'gamma_max_error': maximum_error(result.values, expected['val']),
            'counts_max_error': maximum_error(result.counts, expected['num']),
            'pair_count': result.pair_count, 'includes_self': result.includes_self}
    for name in ('separate', 'nested', 'oblique', 'scaled'):
        folder = REFERENCE / 'sprint12/native' / name
        expected = loadmat(folder / 'raster_arrays.mat', simplify_cells=True)
        with Image.open(folder / 'FracPaQ2D_blocksize.bmp') as bitmap:
            result = white_components(np.asarray(bitmap))
        np.testing.assert_array_equal(result.binary, expected['binary'])
        np.testing.assert_array_equal(result.touches_border, expected['touches'])
        comparisons['raster_' + name] = {
            'pixel_areas_max_error': maximum_error(result.pixel_areas, expected['area']),
            'pixel_centroids_max_error': maximum_error(result.pixel_centroids, expected['centroids']),
            'threshold_error': abs(result.threshold - expected['threshold']),
            'scope': 'Identical native input bitmap; does not assert renderer equality.'}
    write_json(REFERENCE / 'sprint12/native_comparison.json', comparisons)


def integrity():
    baseline = json.loads((REFERENCE / 'source_manifest.json').read_text())['files']
    for entry in baseline:
        assert sha256(ORIGINAL / entry['path']) == entry['sha256']
    previous = json.loads((REFERENCE / 'sprint11/native_provenance.json').read_text())
    for entry in previous['extra_original_folder_files_preserved']:
        assert sha256(ORIGINAL / entry['path']) == entry['sha256']
    return baseline, previous['extra_original_folder_files_preserved']


def provenance():
    baseline, extras = integrity()
    for sprint in (12, 13):
        outputs = []
        for path in sorted((REFERENCE / f'sprint{sprint}/native').rglob('*')):
            if not path.is_file():
                continue
            record = {'path': str(path.relative_to(ROOT)), 'sha256': sha256(path),
                'bytes': path.stat().st_size, 'role': 'Actual supplied MATLAB source execution output'}
            if path.suffix in ('.bmp', '.png'):
                with Image.open(path) as image:
                    record.update(size=image.size, mode=image.mode, dpi=image.info.get('dpi'))
            outputs.append(record)
        write_json(REFERENCE / f'sprint{sprint}/native_provenance.json', {
            'date': '2026-11-14', 'native_version': '24.2.0.3212159 (R2024b) Update 9',
            'capture_script': 'scripts/capture_native_s1213.m',
            'capture_script_sha256': sha256(ROOT / 'scripts/capture_native_s1213.m'),
            'source_manifest_sha256': sha256(REFERENCE / 'source_manifest.json'),
            'original_files_sha256_verified': len(baseline),
            'extra_original_folder_files_preserved': extras, 'outputs': outputs,
            'limitations': 'Native outputs are preserved. Approved Q-14/P20 differences are recorded separately; renderer pixel identity is not claimed.'})


def captures():
    folder = REFERENCE / 'sprint12/candidate'
    figures, arrays = [], {}
    for tag, scale in (('unscaled', None), ('scaled10', 10)):
        target = folder / tag
        target.mkdir(parents=True, exist_ok=True)
        cfg = replace(configuration(('LEN-13', 'LEN-15')), tag=tag)
        dataset = block_dataset(scale=scale)
        results, outputs = production_run(dataset, cfg, target)
        result = results[0].data
        assert all(item.data is result for item in results)
        for _, output in outputs:
            figures.append({'tag': tag, **save_figure(output, tag, target)})
        for name in ('areas', 'centroids', 'raster'):
            arrays[tag + '_' + name] = getattr(result.blocks, name)
        arrays[tag + '_gamma'] = result.variogram.values
        arrays[tag + '_pairs_per_bin'] = result.variogram.counts
    np.savez_compressed(folder / 'arrays.npz', **arrays)
    target = folder / 'native_style'
    target.mkdir(exist_ok=True)
    cfg = replace(configuration(('LEN-15',)), tag='native_style')
    _, outputs = production_run(graph_dataset(), cfg, target)
    figures.append({'tag': 'native_style', **save_figure(outputs[0][1], cfg.tag, target)})
    write_json(folder / 'validation.json', {
        'role': 'Approved Q-14 production outputs through the default registry; historical candidate paths retained.',
        'approval': APPROVAL, 'production_registry': ['LEN-13', 'LEN-15'],
        'generator': 'scripts/validate_sprint1213.py', 'figures': figures,
        'area_definition': 'White 8-connected enclosed raster components, excluding line ink; not vector polygon area.',
        'export': 'Three PNG blocks + one variogram, three Lengths TXT, fixed FracPaQ2D_blocksize.bmp.'})
    folder = REFERENCE / 'sprint13/candidate'
    folder.mkdir(parents=True, exist_ok=True)
    cfg = configuration((*ALONG, *CIRCULAR, *FROM))
    results, outputs = production_run(graph_dataset(), cfg, folder)
    result = results[0].data
    assert all(item.data is result for item in results)
    native = loadmat(REFERENCE / 'sprint13/native/graph_arrays.mat', simplify_cells=True)['graphs']
    comparisons = {}
    for key, x, y in [('trace_along', result.along.distances, result.along.trace_lengths),
        ('segment_along', result.along.distances, result.along.segment_lengths),
        ('angle_along', result.along.distances, result.along.raw_angles),
        ('trace_from', result.trace_distances, result.dataset.as_arrays().trace_lengths),
        ('segment_from', result.segment_distances, result.dataset.as_arrays().segment_lengths),
        ('angle_from', result.segment_distances, result.dataset.as_arrays().raw_angles),
        ('intensity', result.circles.distances, result.circles.intensity)]:
        comparisons[key] = {'x_max_error': maximum_error(x, native[key]['x']),
                            'y_max_error': maximum_error(y, native[key]['y'])}
    write_json(REFERENCE / 'sprint13/native_comparison.json', comparisons)
    figures = []
    for key, output in outputs:
        figures.append({'id': key, **save_figure(output, cfg.tag, folder)})
    np.savez_compressed(folder / 'arrays.npz', along_distances=result.along.distances,
        trace_lengths=result.along.trace_lengths, segment_lengths=result.along.segment_lengths,
        raw_angles=result.along.raw_angles, trace_from=result.trace_distances,
        segment_from=result.segment_distances, circle_centres=result.circles.centres,
        circle_distances=result.circles.distances, intensity=result.circles.intensity,
        density=result.circles.density, n=result.circles.intersections, m=result.circles.endpoints_inside)
    available = [s.id for s in AnalysisRegistry().specs if s.available and s.id.startswith('GRA-')]
    write_json(folder / 'validation.json', {'generator': 'scripts/validate_sprint1213.py',
        'role': 'All nine Graphs production figures through the default registry; Q-20 extension approved.',
        'approval': APPROVAL,
        'production_registry': available, 'figures': figures, 'graphs_txt': []})


if __name__ == '__main__':
    integrity()
    native_comparisons()
    captures()
    provenance()
    for sprint in (12, 13):
        write_json(REFERENCE / f'sprint{sprint}/approval.json', APPROVAL)
    print('Sprint 12/13: native comparisons passed; approved default Run PNG/arrays/files captured.')
