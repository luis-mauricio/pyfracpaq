"""Reproducible local audit; records evidence without declaring visual parity.

Run each phase separately to isolate peak RSS. Native captures are generated
only by capture_native_s16*.m, never by this Python script.
"""

import argparse
from dataclasses import asdict, replace
import gc
import json
import platform
import resource
import time
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import numpy as np
from PIL import Image
from scipy.io import loadmat

from build_parity_index import CONTROLS, inventory_rows
from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.analysis.hough import HoughParameters, extract_hough
from pyfracpaq.domain import TraceInput, build_dataset
from pyfracpaq.domain.execution import RunContext
from pyfracpaq.geometry.profiles import ProfileLine
from pyfracpaq.io import read_txt
from pyfracpaq.io.images import read_grayscale
from reference_common import ORIGINAL, REFERENCE, ROOT, sha256, write_json
from sprint3_reference import reference_config
from validate_sprint56 import analyses, save_figure

FOLDER = REFERENCE / 'sprint16'


def integrity():
    baseline = json.loads((REFERENCE / 'source_manifest.json').read_text())['files']
    for entry in baseline:
        assert sha256(ORIGINAL / entry['path']) == entry['sha256']
    previous = json.loads((REFERENCE / 'sprint11/native_provenance.json').read_text())
    extras = previous['extra_original_folder_files_preserved']
    for entry in extras:
        assert sha256(ORIGINAL / entry['path']) == entry['sha256']
    return baseline, extras


def native():
    baseline, extras = integrity()
    records = []
    for case in ('directional', 'rectangular', 'tensor_network', 'MacduffBinary', 'Orkney1aBinary'):
        real = case.endswith('Binary')
        source = (ORIGINAL if real else ROOT / 'tests/fixtures/images') / f'{case}.tif'
        native_path = FOLDER / 'native' / ('details/hough_real.mat' if real else 'hough_arrays.mat')
        expected = loadmat(native_path, simplify_cells=True)['hough_real' if real else 'hough_refs'][case]
        start = time.perf_counter()
        actual = extract_hough(read_grayscale(source)[0], HoughParameters())
        checks = {field: np.array_equal(getattr(actual, field), expected[other])
                  for field, other in [('binary', 'binary'), ('accumulator', 'H'),
                                       ('theta', 'theta'), ('rho', 'rho'), ('endpoints', 'endpoints')]}
        checks['peaks'] = np.array_equal(actual.peaks + 1, expected['peaks'])
        checks['threshold'] = actual.threshold == expected['threshold']
        assert all(checks.values()), (case, checks)
        records.append({'case': case, 'input': str(source.relative_to(ROOT)), 'input_sha256': sha256(source),
                        'reference': str(native_path.relative_to(ROOT)), 'reference_sha256': sha256(native_path),
                        'parameters': asdict(actual.parameters), 'seconds': time.perf_counter() - start,
                        'peaks': len(actual.peaks), 'segments': len(actual.endpoints), 'exact_checks': checks})
    write_json(FOLDER / 'hough_comparison.json', records)
    from pyfracpaq.analysis.compatibility import double_angles
    dataset = read_txt(FOLDER/'inputs/directional.txt')
    arrays = dataset.as_arrays()
    original = loadmat(FOLDER/'native/geometry_arrays.mat', simplify_cells=True)['traces']
    checks = {}
    for field, expected in {
        'trace_lengths': [t['totalLength'] for t in original],
        'segment_lengths': np.concatenate([np.atleast_1d(t['segmentLength']) for t in original]),
        'raw_angles': np.concatenate([np.atleast_1d(t['segmentAngle']) for t in original]),
        'trace_midpoints': [[t['midpointX'], t['midpointY']] for t in original],
    }.items():
        error = float(np.max(np.abs(getattr(arrays,field)-expected)))
        assert np.allclose(getattr(arrays,field),expected,rtol=1e-10,atol=8e-12)
        checks[field]={'maximum_absolute_error':error,'rtol':1e-10,'atol':8e-12}
    angular=loadmat(FOLDER/'native/angular_conventions.mat',simplify_cells=True)['angular']
    for name,entry in angular.items():
        for flip,label in [(False,'doubled'),(True,'flipped')]:
            actual=double_angles(entry['raw'],entry['north'],flip_x=flip)
            assert np.array_equal(actual,entry[label])
            checks[name+'_'+label]={'exact':True}
    checks['Q07_euclidean']={'native':[float(t['euclideanLength']) for t in original],
       'python':[t.euclidean_length for t in dataset.traces],
       'status':'Intentional technical correction authorized by PRD; vertical source distance0 becomes8.'}
    from pyfracpaq.analysis.lengths import length_histogram, complementary_distribution
    line_arrays=loadmat(FOLDER/'native/length_arrays.mat',simplify_cells=True)['arrays']
    for key, data in [('figure3_axes1',length_histogram(arrays.trace_lengths,20)),
                      ('figure4_axes1',complementary_distribution(arrays.trace_lengths)),
                      ('figure5_axes1',length_histogram(arrays.segment_lengths,20)),
                      ('figure6_axes1',complementary_distribution(arrays.segment_lengths))]:
        line=next(line for line in line_arrays[key]['lines'] if np.size(line['x'])>2)
        values=data.complementary if hasattr(data,'complementary') else data.frequencies
        assert np.array_equal(values,line['y'])
        assert np.allclose(data.centres,line['x'],rtol=1e-10,atol=8e-12)
        checks[key]={'frequencies_exact':True,
                     'centres_maximum_absolute_error':float(np.max(np.abs(data.centres-line['x'])))}
    checks['input']={'path':str((FOLDER/'inputs/directional.txt').relative_to(ROOT)),
                     'sha256':sha256(FOLDER/'inputs/directional.txt')}
    write_json(FOLDER/'numeric-comparison.json',checks)
    outputs = []
    for path in sorted((FOLDER / 'native').rglob('*')):
        if path.is_file():
            entry = {'path': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size, 'sha256': sha256(path)}
            if path.suffix == '.png':
                with Image.open(path) as image:
                    entry.update(size=image.size, dpi=image.info.get('dpi'), mode=image.mode)
            outputs.append(entry)
    write_json(FOLDER / 'native_provenance.json', {
        'date': '2026-11-14', 'native_version': 'MATLAB R2024b Update9',
        'scripts': {name: sha256(ROOT / name) for name in
                    ('scripts/capture_native_s16.m', 'scripts/capture_native_s16_details.m',
                     'scripts/capture_native_s16_exports.m')},
        'original_files_sha256_verified': len(baseline), 'extra_original_folder_files_preserved': extras,
        'outputs': outputs,
        'scope': 'Actual calls to the supplied sources/toolbox. GUI images are print renders at100dpi, not OS screenshots. '
                 'The first absolute-path GUI call fails (Q04); the separate relative-path session succeeds. '
                 'Capture availability does not certify SSIM, platform support or accepted scientific changes.'})


def baseline_figures():
    """Same directional input and parameters as native capture, excluding corrected Q20."""
    folder = FOLDER / 'candidate';folder.mkdir(parents=True, exist_ok=True)
    dataset = read_txt(FOLDER / 'inputs/directional.txt')
    selected = ('MAP-01', 'MAP-04', 'MAP-05', 'MAP-06', 'LEN-02', 'LEN-03', 'LEN-06', 'ANG-01', 'ANG-02')
    figures, cfg = analyses(dataset, folder, 'audit', selected=selected,
        checkbox_shownodes=True, edit_degfromnorth='12', checkbox_roselengthweighted=False,
        checkbox_showrosemean=True, checkbox_rosecolour=True)
    from pyfracpaq.plots.hough import render_hough
    hough = extract_hough(read_grayscale(ROOT/'tests/fixtures/images/tensor_network.tif')[0], HoughParameters())
    save_figure(render_hough(hough), 'audit', folder)
    write_json(folder / 'parameters.json', json.loads(json.dumps(cfg, default=str)))
    comparisons = []
    from skimage.metrics import structural_similarity
    for record in figures:
        path = folder / record['path'];native_path = FOLDER / 'native' / path.name
        if not native_path.is_file():
            continue
        with Image.open(path) as image: a = np.array(image.convert('RGB'))
        with Image.open(native_path) as image: b = np.array(image.convert('RGB'))
        assert a.shape == b.shape
        # Fixed, nonoverlapping physical image regions. No resizing, masks or
        # antialiasing exclusions; these exploratory regions do not replace
        # the per-family semantic review required for acceptance.
        h, w = a.shape[:2]
        regions = {'title': (0, 0, w, round(.1*h)), 'body': (0, round(.1*h), w, round(.85*h)),
                   'bottom': (0, round(.85*h), w, h)}
        scores = {}
        for name, (x0, y0, x1, y1) in regions.items():
            scores[name] = float(structural_similarity(a[y0:y1,x0:x1], b[y0:y1,x0:x1],
                                channel_axis=2, data_range=255))
        delta = np.abs(a.astype(np.int16) - b.astype(np.int16)).astype(np.uint8)
        difference = path.with_name('diff-' + path.name);Image.fromarray(delta).save(difference)
        comparisons.append({'python': str(path.relative_to(ROOT)), 'python_sha256': sha256(path),
            'matlab': str(native_path.relative_to(ROOT)), 'matlab_sha256': sha256(native_path),
            'regions_xyxy': regions, 'ssim_rgb_data_range255': scores, 'threshold': .98,
            'exploratory_regions_pass': all(v >= .98 for v in scores.values()),
            'difference': str(difference.relative_to(ROOT)),
            'acceptance': 'Not homologated: semantic/data review and independent regions required.'})
        del a,b,delta;gc.collect()
    files=[]
    for name in ('FracPaQ2Dsegmentlengths_audit.txt','FracPaQ2Dtracelengths_audit.txt',
                 'FracPaQ2Dsegmentangleslengths_audit.txt','FracPaQ2DEZROSE_audit.txt'):
        native_path=FOLDER/'native'/name;path=folder/name
        assert path.read_bytes()==native_path.read_bytes(), name
        files.append({'name':name,'bytes_exact':True,'sha256':sha256(path),
                      'matlab_sha256':sha256(native_path)})
    write_json(folder / 'validation.json', {'figures': figures, 'comparisons': comparisons,'files_comparison':files,
        'scope': 'Same source input/flags. Quantitative exploratory images; no whole-family parity claim.'})


def full_run():
    """Execute every registry route and its real exporter, without UI mocks."""
    folder = FOLDER / 'all-outputs';folder.mkdir(parents=True, exist_ok=True)
    traces = []
    for i in range(48):
        x,y = 5 + i%8*10, 5 + i//8*10
        length = 1.2 + (i+1)**.8
        angle = np.deg2rad(i*137.5)
        traces.append(TraceInput(((x,y),(x+length*np.cos(angle),y+length*np.sin(angle))),
                                colour=(0,0,1) if i%2 else (1,0,0)))
    for x,y,size in ((0,0,100),(10,10,5),(30,30,10)):
        traces.append(TraceInput(((x,y),(x+size,y),(x+size,y+size),(x,y+size),(x,y))))
    dataset = build_dataset(traces)
    registry = AnalysisRegistry();assert all(spec.available and spec.render for spec in registry.specs)
    values = {spec.checkbox: True for spec in registry.specs}
    cfg = replace(reference_config(tuple(spec.id for spec in registry.specs), **values,
            checkbox_shownodes=True, checkbox_showcircles=True, checkbox_censor=False,
            edit_degfromnorth='12', edit_numscancircles='3', edit_numscancirclesgraph='3',
            edit_numblocksmap='4', edit_aString='32', edit_LString='2', edit_DegString='90'),
            tag='audit_all', profile_line=ProfileLine((0,0),(100,100)))
    write_json(folder / 'parameters.json', json.loads(json.dumps(asdict(cfg), default=str)))
    write_json(folder / 'input.json', [{'nodes': t.points, 'colour': t.colour} for t in traces])
    events=[];start = time.perf_counter()
    results = registry.execute(dataset, RunContext(cfg, folder, folder, cfg.tag),
        lambda percent,message: events.append({'percent':percent,'message':message,'seconds':time.perf_counter()-start}),
        lambda: False)
    figures=[];seen=set()
    for result in results:
        spec = next(s for s in registry.specs if s.id == result.analysis_id)
        for output in spec.render(result.data, cfg):
            # Coupled figure families deliberately share outputs. Match GUI
            # presentation: export a basename once, retaining all triggers.
            if output.basename not in seen:
                seen.add(output.basename)
                figures.append({'id': result.analysis_id, **save_figure(output,cfg.tag,folder)})
            else:
                output.figure.clear()
        print(f'{result.analysis_id}: rendered', flush=True)
    files=[{'name':p.name,'sha256':sha256(p),'bytes':p.stat().st_size} for p in sorted(folder.iterdir())
           if p.suffix in ('.png','.txt','.bmp') and not p.name.startswith('qa-')]
    mle=next(r.data.mle for r in results if r.analysis_id=='LEN-07')
    write_json(folder / 'validation.json', {'analysis_ids':[r.analysis_id for r in results],
        'mle_root_seed':mle.seed,'mle_rng':'PCG64;6 streams;2500 comparisons/model',
        'figures':figures,'files':files,'progress':events,'seconds':time.perf_counter()-start,
        'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'rss_unit': 'bytes on this macOS host; rerun separately on other OS',
        'dataset':{'traces':dataset.n_traces,'segments':dataset.n_segments},
        'scope':'All production compute/render routes with real resolution/exporters; synthetic audit input. '
                'Stochastic MLE runs are functionality evidence, not shared-RNG parity.'})


def benchmark(case):
    """Original real datasets, explicitly preparing known wholly degenerate rows."""
    name = {'map1':'map1_edit_converted.txt','map7':'map7_edit_converted.txt'}[case]
    source=ORIGINAL/name;folder=FOLDER/'benchmarks';folder.mkdir(parents=True,exist_ok=True)
    rows=[];removed=[]
    for index,line in enumerate(source.read_text().splitlines(),1):
        if not line.strip():continue
        values=np.array([float(v) for v in line.split()]).reshape(-1,2)
        if np.all(values==values[0]):removed.append(index)
        else:rows.append(line)
    target=folder/(case+'_prepared.txt');target.write_text('\n'.join(rows)+'\n')
    start=time.perf_counter();dataset=read_txt(target);read_seconds=time.perf_counter()-start
    cfg=reference_config(('MAP-01','LEN-02','ANG-01'))
    start=time.perf_counter()
    results=AnalysisRegistry().execute(dataset,RunContext(cfg,folder,folder,case),lambda *a:None,lambda:False)
    write_json(folder/(case+'.json'),{'platform':platform.platform(),'python':platform.python_version(),
        'source':str(source.relative_to(ROOT)),'source_sha256':sha256(source),'prepared':str(target.relative_to(ROOT)),
        'prepared_sha256':sha256(target),'removed_degenerate_lines_1based':removed,
        'traces':dataset.n_traces,'segments':dataset.n_segments,'read_seconds':read_seconds,
        'compute_seconds':time.perf_counter()-start,'analysis_ids':[r.analysis_id for r in results],
        'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'scope':'Fresh process; macOS bytes. Imports included in peak; rendering/export excluded. '
                'Production readers refuse degenerate rows; preparation here is explicit on a copy.'})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=['native','baseline','all','map1','map7'])
    phase=parser.parse_args().phase
    integrity()
    if phase in ('map1','map7'):benchmark(phase)
    else:{'native':native,'baseline':baseline_figures,'all':full_run}[phase]()
