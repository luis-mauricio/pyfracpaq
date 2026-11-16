"""Native array comparisons, production 1944x1944 wavelets and utility evidence."""

from dataclasses import replace
import json
import resource
import time

import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
import numpy as np
from PIL import Image
from scipy.io import loadmat

from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.analysis.auxiliary import crack_tensor16, probe_plane
from pyfracpaq.analysis.palettes import cmocean
from pyfracpaq.analysis.preprocess import preprocess_image
from pyfracpaq.analysis.roses import linear_rose, historical_rose
from pyfracpaq.analysis.wavelets import cwt2, analyse_wavelet_image, WaveletParameters
from pyfracpaq.domain import TraceInput, build_dataset
from pyfracpaq.domain.execution import RunContext
from pyfracpaq.geometry.primitives import Bounds
from pyfracpaq.plots.preprocess import render_preprocess
from pyfracpaq.plots.roses import draw_historical_rose
from pyfracpaq.plots.auxiliary import plot_ellipse, plot_arc, centered_axes, ternary_frame, ternary_points
from reference_common import ROOT, REFERENCE, ORIGINAL, sha256, write_json
from sprint3_reference import reference_config
from validate_sprint56 import save_figure

APPROVAL = {'id': 'Q-12', 'author': 'user', 'date': '2026-11-14', 'statement': 'Aprovo a Q-12.',
    'scope': 'Deterministic 1944x1944/72dpi raster with source margins/thicknesses; ny-by-nx rectangular arrays; '
             'integer angular divisor of180; stable first L/theta within rtol1e-12/atol1e-14 while retaining actual maximum WC.'}


def integrity():
    manifest = json.loads((REFERENCE / 'source_manifest.json').read_text())['files']
    extras = json.loads((REFERENCE / 'sprint13/native_provenance.json').read_text())['extra_original_folder_files_preserved']
    assert all(sha256(ORIGINAL / p['path']) == p['sha256'] for p in (*manifest, *extras))
    return manifest, extras


def compare():
    source = loadmat(REFERENCE / 'sprint14/native/cwt_arrays.mat', simplify_cells=True)
    comparison = {}
    for kind, keys in [('morlet', ('wm', 'em', 'sm', 'esm')), ('mexican', ('wh', 'eh', 'sh', 'esh'))]:
        errors = {name: 0. for name in ('coefficients', 'eta', 'self', 'self_eta')}
        for ai, a in enumerate(source['a']):
            for ti, theta in enumerate(source['theta']):
                for li, ratio in enumerate(source['L']):
                    result = cwt2(source['data'], a, theta, ratio, kind)
                    actual = (result.coefficients, result.eta, result.self_coefficients, result.self_eta)
                    native = (source[keys[0]][:, :, ai, ti, li], source[keys[1]][ai, ti, li],
                              source[keys[2]][:, :, ai, ti, li], source[keys[3]][ai, ti, li])
                    for name, x, y in zip(errors, actual, native):
                        errors[name] = max(errors[name], float(np.max(np.abs(x - y))))
        comparison[kind] = errors
    gui = loadmat(REFERENCE / 'sprint14/native/gui_arrays.mat', simplify_cells=True)['details']
    for kind in ('morlet', 'mexican'):
        result = analyse_wavelet_image(gui[kind]['binary'], WaveletParameters((2,), (2, 1), 45, kind)).scales[0]
        expected = np.loadtxt(REFERENCE / f'sprint14/native/{kind}/FracPaQ2Dwavelet_theta_a2.txt')
        comparison[kind].update(gui_map_error=float(np.max(np.abs(result.coefficients - gui[kind]['wc']))),
            native_maximum=float(gui[kind]['wc'].max()),
            changed_theta_entries=int(np.count_nonzero(result.doubled_degrees != expected)))
    write_json(REFERENCE / 'sprint14/native_comparison.json', comparison)
    folder = REFERENCE / 'sprint15/native'
    m = loadmat(folder / 'preprocess_arrays.mat', simplify_cells=True)
    with Image.open(folder / 'MacduffColourCropped.jpg') as image:
        prepared = preprocess_image(np.asarray(image))
    errors = {name: int(np.count_nonzero(getattr(prepared, name) != m[key]))
        for name, key in [('grayscale', 'gray'), ('median', 'median'), ('difference', 'difference'),
                          ('edges', 'edges'), ('closed', 'closed'), ('processed', 'processed')]}
    native = loadmat(folder / 'aux_arrays.mat', simplify_cells=True)
    tensor = crack_tensor16([2, 3], [30, 110], 20)
    probe = probe_plane(1, Bounds(0, 0, 10, 10), native['segments'], 8)
    details = loadmat(folder / 'details_arrays.mat', simplify_cells=True)
    errors.update(tensor16_error=float(np.max(np.abs(tensor.components - native['tensor16']))),
        tensor16_polar_error=float(np.max(np.abs(tensor.polar - native['polar16']))),
        probe_mq_error=float(np.max(np.abs(probe.mq - native['probe_mq']))),
        pivot_palette_error=float(np.max(np.abs(cmocean('balance', pivot=1, limits=(-2, 5)) - details['balance']))))
    write_json(REFERENCE / 'sprint15/native_comparison.json', errors)
    return prepared


def captures(prepared):
    dataset = build_dataset([TraceInput(((0, 0), (100, 0), (100, 60))), TraceInput(((20, 10), (40, 30)))])
    records = []
    for kind in ('morlet', 'mexican'):
        folder = REFERENCE / f'sprint14/production/{kind}';folder.mkdir(parents=True, exist_ok=True)
        cfg = replace(reference_config(('WAV-01',), edit_aString='32', edit_LString='2',
            edit_DegString='90', radiobutton_Morlet=kind == 'morlet'), tag=kind)
        registry = AnalysisRegistry();start = time.perf_counter()
        results = registry.execute(dataset, RunContext(cfg, folder, folder, kind),
            lambda percent, message: print(f'{kind} {percent}% {message}', flush=True), lambda: False)
        result = results[0].data
        output, = next(s for s in registry.specs if s.id == 'WAV-01').render(result, cfg)
        figure = save_figure(output, cfg.tag, folder)
        np.savez_compressed(folder / 'arrays.npz', image=result.image, wc=result.scales[0].coefficients,
            theta=result.scales[0].optimum_theta, ratio=result.scales[0].optimum_ratio,
            selected=result.scales[0].selected, eta=result.scales[0].eta, self_eta=result.scales[0].self_eta)
        records.append({'kernel': kind, 'shape_yx': result.image.shape, 'scale': 32,
            'L_input': [2], 'angular_step': 90, 'seconds': time.perf_counter() - start,
            'maximum_wc': float(result.scales[0].coefficients.max()),
            'selected': int(result.scales[0].selected.sum()), 'figure': figure})
    write_json(REFERENCE / 'sprint14/validation.json', {'approval': APPROVAL,
        'role': 'Actual full production raster/FFT/default-registry runs, not reduced UI fixtures.',
        'cases': records, 'process_peak_rss_native_units': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'rss_note': 'macOS ru_maxrss reports bytes; process peak includes both runs, rendering and compression.'})
    folder = REFERENCE / 'sprint15/production';folder.mkdir(parents=True, exist_ok=True)
    figures = [save_figure(render_preprocess(prepared), 'steps', folder)]
    Image.fromarray(prepared.processed.astype(np.uint8) * 255).save(folder / 'processed.tif')
    figure = Figure(figsize=(8, 8));axes = figure.subplots(2, 2)
    values = [0, 10, 20, 90, 180, 270, 350]
    draw_historical_rose(axes[0, 0], linear_rose(values, 30))
    draw_historical_rose(axes[0, 1], historical_rose(values, 12))
    plot_ellipse(axes[1, 0], 4, 2, 30);plot_arc(axes[1, 0], 2, 0, 180)
    ternary_frame(axes[1, 1]);ternary_points(axes[1, 1], [[30, 30, 40]])
    from pyfracpaq.plots.results import FigureOutput
    figures.append(save_figure(FigureOutput('FracPaQ2D_auxiliary_apis', figure), 'apis', folder))
    write_json(REFERENCE / 'sprint15/validation.json', {'role': 'Complementary utilities; no new main GUI controls.',
        'figures': figures, 'tensor16_components': 65536, 'advanced_variogram': 'Already ported in Sprint12; preserved API.',
        'dialog': 'guiWaveletDialog .fig defaults/objects replicated; async Run/Cancel regression tested.'})


def provenance():
    baseline, extras = integrity()
    for sprint in (14, 15):
        folder = REFERENCE / f'sprint{sprint}'
        outputs = []
        for path in sorted((folder / 'native').rglob('*')):
            if path.is_file():
                outputs.append({'path': str(path.relative_to(ROOT)), 'sha256': sha256(path),
                    'role': 'Genuine MATLAB calls or supplied-script execution; provenance in capture scripts.'})
        write_json(folder / 'native_provenance.json', {'native_version': 'MATLAB R2024b Update9',
            'date': '2026-11-14', 'scripts': {p: sha256(ROOT / p) for p in
                ('scripts/capture_native_s1415.m', 'scripts/capture_native_s1415_details.m')},
            'original_files_sha256_verified': len(baseline),
            'extra_original_folder_files_preserved': extras, 'outputs': outputs,
            'limitations': 'Native wavelet2 square panels/arrays plus original integrated raster-only stage. '
                           'Full integrated FFT not attributed to MATLAB; Python full runs are separate production evidence. '
                           'Legacy cmocean pivot parser ignores requested levels; reference pivot palette has256 levels.'})
    write_json(REFERENCE / 'sprint14/approval.json', APPROVAL)


if __name__ == '__main__':
    integrity();prepared = compare();captures(prepared);provenance()
    print('Sprint 14/15 comparisons, full production runs and utility evidence saved.')
