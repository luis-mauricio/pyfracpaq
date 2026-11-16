"""Generate tensor/stability figures, arrays and files through the default registry."""

from dataclasses import asdict, replace
import json

import matplotlib
matplotlib.use('Agg')
import numpy as np
from scipy.io import loadmat

from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.analysis.stability import KINDS
from pyfracpaq.analysis.tensors import crack_tensors, permeability_tensor
from pyfracpaq.domain.execution import RunContext
from pyfracpaq.io import read_txt
from pyfracpaq.io.images import read_image
from pyfracpaq.io.svg import read_svg
from reference_common import ROOT, sha256, write_json
from sprint3_reference import reference_config
from sprint1011_reference import uniform_dataset
from validate_sprint56 import save_figure

APPROVAL = {'id': 'Q-17', 'author': 'user', 'date': '2026-11-14',
            'statement': 'Aprovo a correção Q-17.',
            'scope': 'Correct stability normalization, colour lookup, inclusive CSF and contextual validation; retain legacy length-map colour convention.'}


def configuration(selected, tag, *, scale=None, north=12.5, theta=30, flip=True, **changes):
    cfg = reference_config(selected, edit_degfromnorth=str(north), edit_sigma1='100',
        edit_sigma2='50', edit_thetasigma1=str(theta), edit_C0='2', edit_Pf='10', edit_mu='.6',
        edit_lambda='.7', edit_fixedaperture='.001', edit_aperturefactor='.01',
        edit_apertureexponent='.75', **changes)
    return replace(cfg, tag=tag, flip_x=flip, input=replace(cfg.input, pixels_per_metre=scale))


def run(dataset, cfg, folder):
    registry = AnalysisRegistry()
    results = registry.execute(dataset, RunContext(cfg, folder, folder, cfg.tag),
                               lambda *_: None, lambda: False)
    specs = {s.id: s for s in registry.specs}
    figures = []
    for result in results:
        for output in specs[result.analysis_id].render(result.data, cfg):
            figures.append({'id': result.analysis_id, **save_figure(output, cfg.tag, folder)})
    return results, figures


def tensor_evidence(cases):
    folder = ROOT / 'tests/reference/sprint10'
    folder.mkdir(parents=True, exist_ok=True)
    figures, arrays, records = [], {}, []
    for tag, dataset, cfg in cases:
        results, produced = run(dataset, cfg, folder)
        figures.extend(produced)
        crack, perm = results[0].data.crack, results[1].data
        arrays[tag + '_poles_crack'] = crack.poles
        arrays[tag + '_F0'] = crack.zero
        for rank in crack.ranks:
            arrays[f'{tag}_F{rank.order}'] = rank.components
            arrays[f'{tag}_F{rank.order}_polar'] = rank.polar
        for name in ('p', 'k', 'eigenvalues', 'polar', 'apertures', 'poles'):
            arrays[tag + '_' + name] = getattr(perm, name)
        records.append({'tag': tag, 'input_mode': str(dataset.input_mode),
            'trace_envelope_area': perm.area, 'domain_area': dataset.area, 'unit': perm.unit,
            'Kmin': float(perm.eigenvalues[0]), 'Kmax': float(perm.eigenvalues[-1]),
            'parameters': json.loads(json.dumps(asdict(cfg), default=str))})
    native = loadmat(folder / 'native/tensor_arrays.mat', simplify_cells=True)
    comparisons = {}
    for name, expected in native['tensor_refs'].items():
        result = crack_tensors(expected['lengths'], expected['angles'], expected['area'])
        comparisons[name] = {f'F{rank.order}_max_error': float(np.max(np.abs(
            rank.components - expected[f'F{rank.order}']))) for rank in result.ranks}
        comparisons[name].update({f'polar{rank.order}_max_error': float(np.max(np.abs(
            rank.polar - expected[f'polar{rank.order}']))) for rank in result.ranks})
    for name, expected in native['permeability_refs'].items():
        result = permeability_tensor(expected['lengths'], expected['poles'], expected['area'],
                                      expected['apertures'], expected['lambda'])
        comparisons[name] = {'K_max_error': float(np.max(np.abs(result.k - expected['K']))),
                            'polar_max_error': float(np.max(np.abs(result.polar - expected['polar'])))}
    np.savez_compressed(folder / 'arrays.npz', **arrays)
    write_json(folder / 'parameters.json', records)
    write_json(folder / 'native_comparison.json', comparisons)
    write_json(folder / 'validation.json', {
        'scope': 'Default Run tensors/permeability, genuine native arrays and visual references; full visual homologation remains pending.',
        'figures': figures, 'cases': records, 'arrays_sha256': sha256(folder / 'arrays.npz'),
        'parameters_sha256': sha256(folder / 'parameters.json'),
        'native_comparison_sha256': sha256(folder / 'native_comparison.json'),
        'txt': [{'path': p.name, 'sha256': sha256(p)} for p in sorted(folder.glob('*.txt'))],
    })
    print(f'Sprint 10: {len(figures)} PNG/QA, tensors, eigenvalues and EZROSE saved.', flush=True)


def stability_evidence(cases):
    folder = ROOT / 'tests/reference/sprint11'
    figures, arrays, records = [], {}, []
    for tag, dataset, cfg in cases:
        results, produced = run(dataset, cfg, folder)
        figures.extend(produced)
        result = results[0].data
        for name in ('normal_stress', 'shear_stress', 'strikes', 'doubled_angles'):
            arrays[tag + '_' + name] = getattr(result, name)
        arrays[tag + '_rose_counts'] = result.rose.counts
        arrays[tag + '_rose_vertices'] = result.rose.vertices
        for field in result.fields:
            for name in ('values', 'normalized', 'rose_values', 'rose_normalized', 'map_indices', 'rose_indices'):
                arrays[tag + '_' + field.kind + '_' + name] = getattr(field, name)
        records.append({'tag': tag, 'input_mode': str(dataset.input_mode),
            'parameters': json.loads(json.dumps(asdict(cfg), default=str)),
            'fields': [{'kind': f.kind, 'range': f.colour_range,
                        'raw_min': float(f.values.min()), 'raw_max': float(f.values.max()),
                        'saturated_rose_bins': int(np.sum((f.rose_normalized < 0) | (f.rose_normalized > 1)))}
                       for f in result.fields]})
    np.savez_compressed(folder / 'arrays.npz', **arrays)
    write_json(folder / 'parameters.json', records)
    before = json.loads((folder / 'candidate/q17_comparison.json').read_text())
    before['decision'] = APPROVAL
    before['native']['degenerate_calls'] = json.loads((folder / 'native/native_calls.json').read_text())
    write_json(folder / 'q17_comparison.json', before)
    write_json(folder / 'validation.json', {
        'scope': 'Approved Q-17 stability, active in default Run; full native visual homologation remains pending.',
        'scientific_approval': APPROVAL, 'figures': figures, 'cases': records,
        'arrays_sha256': sha256(folder / 'arrays.npz'),
        'parameters_sha256': sha256(folder / 'parameters.json'),
        'q17_sha256': sha256(folder / 'q17_comparison.json'),
        'txt': [{'path': p.name, 'sha256': sha256(p)} for p in sorted(folder.glob('*.txt'))],
    })
    print(f'Sprint 11: {len(figures)} PNG/QA, stresses, fields, roses and segmentdata saved.', flush=True)


def main():
    txt = read_txt(ROOT / 'tests/fixtures/nodes/mixed.txt')
    svg = read_svg(ROOT / 'tests/fixtures/svg/multicolour.svg').dataset
    hough = read_image(ROOT / 'tests/fixtures/images/tensor_network.tif', pixels_per_metre=2).dataset
    uniform = uniform_dataset()
    tensors = []
    for tag, data in (('TXT', txt), ('SVG', svg), ('Hough', hough), ('native_style', uniform), ('zero', txt)):
        cfg = configuration(('FLO-08', 'FLO-09'), tag, scale=data.pixels_per_metre,
            north=12 if tag == 'native_style' else 12.5,
            radiobutton_fixedaperture=tag != 'SVG')
        if tag == 'zero':
            values = dict(cfg.values)
            values.update(edit_lambda='0', edit_fixedaperture='0')
            cfg = replace(cfg, values=tuple(values.items()))
        tensors.append((tag, data, cfg))
    tensor_evidence(tensors)
    stability = [(tag, data, configuration(tuple(KINDS), tag, scale=data.pixels_per_metre,
                    north=0 if tag == 'native_style' else 12.5,
                    theta=0 if tag == 'native_style' else 30, flip=tag != 'native_style'))
                 for tag, data in (('TXT', txt), ('SVG', svg), ('Hough', hough), ('native_style', uniform))]
    constant = configuration(('MAP-13',), 'constant')
    values = dict(constant.values)
    values['edit_sigma2'] = '100'
    stability.append(('constant', txt, replace(constant, values=tuple(values.items()))))
    stability_evidence(stability)


if __name__ == '__main__':
    main()
