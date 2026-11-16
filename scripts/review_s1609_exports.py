"""Bounded S16-09.2 audit; never rewrites accepted scientific references.

Reuse only the locally generated, checksummed SD11A computation cache after
verifying every scientific module and source hash. Current renderers and real
exporters execute again. PNG copies live in a temporary directory; their file
and RGB hashes are retained alongside the persistent small data exports.
"""

from dataclasses import replace
import argparse
import gc
import json
from pathlib import Path
import pickle
import shutil
import tempfile
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np
from PIL import Image
import hashlib

from pyfracpaq import __version__
from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.domain.execution import RunContext
from pyfracpaq.io import read_txt
from pyfracpaq.io.angles import export_ezrose
from pyfracpaq.io.block_raster import export_block_raster
from pyfracpaq.io.circular import export_circular
from pyfracpaq.io.connectivity import export_connectivity
from pyfracpaq.io.figures import export_png
from pyfracpaq.io.images import read_image
from pyfracpaq.io.lengths import export_lengths
from pyfracpaq.io.stability import export_segmentdata
from pyfracpaq.io.svg import read_svg, write_conversion
from pyfracpaq.io.wavelets import export_wavelets, rasterize_wavelets
from pyfracpaq.plots.hough import render_hough
from pyfracpaq.plots.maps import render_multicolour
from pyfracpaq.tools.__main__ import main as tools_main
from audit_sprint16 import integrity
from compare_sd11a import SOURCE, configuration
from finish_s16 import CACHE, manifest
from reference_common import ROOT, REFERENCE, sha256, write_json

FOLDER = REFERENCE / 'sprint16/delivery/point-2'
ACCEPTED = REFERENCE / 'sprint16/final'


def relative(path):
    return str(path.relative_to(ROOT))


def run(png_directory=None):
    integrity()
    metadata = json.loads(CACHE.with_suffix('.json').read_text())
    assert metadata['cache_sha256'] == sha256(CACHE)
    assert metadata['input_sha256'] == sha256(SOURCE)
    assert metadata['implementation'] == manifest()
    results = pickle.loads(CACHE.read_bytes())  # verified local cache, not application input
    data = {type(result.data).__name__: result.data for result in results}
    _, cfg = configuration()
    registry = AnalysisRegistry()
    specs = {spec.id: spec for spec in registry.specs}
    dataset = read_txt(SOURCE)
    FOLDER.mkdir(parents=True, exist_ok=True)
    products = FOLDER / 'data'
    products.mkdir(exist_ok=True)
    temp = png_directory or Path(tempfile.mkdtemp(prefix='pyfracpaq-s1609-exports-'))
    report = {'version': __version__, 'input_sha256': sha256(SOURCE),
              'cache_sha256': sha256(CACHE), 'scientific_implementation': manifest(),
              'current_implementation': {relative(p): sha256(p) for p in
                  sorted((ROOT / 'pyfracpaq').rglob('*.py'))},
              'scope': 'Export/file audit using verified previously approved scientific results; no new scientific or visual acceptance.',
              'temporary_png_directory': str(temp), 'figures': [], 'data': [], 'units': []}
    seen = set()

    def figure(output, tag, baseline):
        fig = output.figure
        if output.basename in seen:
            fig.clear()
            return
        seen.add(output.basename)
        original_size = fig.get_size_inches().copy()
        path = temp / f'{output.basename}_{tag}.png'
        if not png_directory or not path.exists():
            path = export_png(fig, output.basename, tag, temp)
        np.testing.assert_array_equal(fig.get_size_inches(), original_size)
        with Image.open(path) as current, Image.open(baseline) as accepted:
            assert current.size == (4724, 4724)
            assert all(abs(dpi - 600) < .01 for dpi in current.info['dpi'])
            assert current.info['Software'] == f'PyFracPaQ {__version__}; FracPaQ 2.8 reference'
            rgb = np.asarray(current.convert('RGB'))
            np.testing.assert_array_equal(rgb, np.asarray(accepted.convert('RGB')))
            record = {'name': path.name, 'sha256': sha256(path),
                      'accepted_reference': relative(baseline), 'reference_sha256': sha256(baseline),
                      'rgb_sha256': hashlib.sha256(rgb.tobytes()).hexdigest(),
                      'rgb_exact': True, 'size': list(current.size), 'dpi': list(current.info['dpi']),
                      'software': current.info['Software'],
                      'labels': [{'x': ax.get_xlabel(), 'y': ax.get_ylabel()} for ax in fig.axes]}
        report['figures'].append(record)
        fig.clear()
        gc.collect()
        print(f"PNG {len(report['figures'])}: {path.name} exact RGB", flush=True)

    for result in results:
        for output in specs[result.analysis_id].render(result.data, cfg):
            figure(output, 'SD11A', ACCEPTED / 'python' / f'{output.basename}_SD11A.png')
    multi_source = ACCEPTED / 'inputs/multicolour/network.svg'
    for output in (render_multicolour(read_svg(multi_source).dataset, cfg),
                   render_hough(read_image(ROOT / 'tests/fixtures/images/tensor_network.tif').hough)):
        figure(output, 'extra', ACCEPTED / 'python-extra' / f'{output.basename}_extra.png')
    catalog = json.loads((REFERENCE / 'capture_catalog.json').read_text())
    expected = {entry['name'].removesuffix('{tag}.png').replace('{a}', '32').rstrip('_')
                for entry in catalog['figures']}
    assert {name.rstrip('_') for name in seen} == expected
    assert len(report['figures']) == 53

    lengths = data['LengthResult'].sample
    circular = data['CircularResult']
    raster = rasterize_wavelets(dataset)

    def tables(tag, folder):
        paths = list(export_lengths(lengths.trace_lengths, lengths.segment_lengths,
                                    lengths.raw_angles, tag, folder))
        paths.append(export_ezrose(data['AngularResult'].angles, tag, folder))
        paths.extend(export_circular(circular.grid.centres, circular.intensity.ravel(order='F'),
                                     circular.density.ravel(order='F'), tag, folder))
        paths.append(export_connectivity(data['ConnectivityResult'].topology.counts, tag, folder))
        paths.append(export_segmentdata(dataset, tag, folder))
        paths.append(export_block_raster(data['LengthResult'].blocks.raster, folder))
        paths.extend(export_wavelets(data['WaveletResult'], tag, folder, raster=raster))
        return paths

    outputs = tables('SD11A', products)
    for path in outputs:
        baseline = ACCEPTED / 'python' / path.name
        assert path.read_bytes() == baseline.read_bytes(), path.name
        report['data'].append({'name': path.name, 'sha256': sha256(path),
                               'reference': relative(baseline), 'bytes_exact': True})
    assert len(outputs) == 11  # nine TXT, fixed BMP and wavelet raster
    # Real replacement: damaged targets are repaired, unrelated files preserved.
    sentinel = products / 'unrelated.keep'
    sentinel.write_bytes(b'preserve unrelated files\n')
    hashes = {p.name: sha256(p) for p in outputs}
    for path in outputs:
        path.write_bytes(b'old export\n')
    assert {p.name: sha256(p) for p in tables('SD11A', products)} == hashes
    assert sentinel.read_bytes() == b'preserve unrelated files\n'
    report['replacement'] = {'all_11_main_data_files_replaced': True, 'unrelated_preserved': True}

    for tag in ('', 'Execução 1 – São Paulo'):
        folder = products / ('empty-tag' if not tag else 'pasta com espaços e acentos')
        folder.mkdir(exist_ok=True)
        tagged = tables(tag, folder)
        for path in tagged:
            if path.suffix == '.txt':
                assert path.name.endswith(f'_{tag}.txt')
                baseline = path.name.removesuffix(f'_{tag}.txt') + '_SD11A.txt'
            else:
                baseline = path.name
            assert sha256(path) == hashes[baseline]
    aux = products / 'auxiliary'
    aux.mkdir(exist_ok=True)
    theta, = export_wavelets(data['WaveletResult'], 'ignored', aux, auxiliary=True)
    assert theta.name == 'FracPaQ2Dwavelet_theta_a32.txt'
    assert sha256(theta) == hashes['FracPaQ2Dwavelet_theta_a32_SD11A.txt']
    report['tags'] = {'empty': True, 'unicode_spaces': True, 'auxiliary_untagged_theta': True}

    report['svg'] = []
    for stem in ('simple', 'multicolour'):
        src = products / f'{stem}.svg'
        original = ROOT / f'tests/fixtures/svg/{stem}.svg'
        shutil.copyfile(original, src)
        imported = read_svg(src)
        write_conversion(imported)
        for table in imported.tables:
            baseline = original.parent / table.path.name
            if baseline.exists():
                assert table.path.read_bytes() == baseline.read_bytes()
            else:
                assert stem == 'simple'
                assert table.path.read_bytes() == b'  1.00000000\t  2.00000000\t  4.00000000\t  2.00000000\t  4.00000000\t  6.00000000\t\r\n  0.00000000\t  0.00000000\t  4.00000000\t  0.00000000'
            converted = read_txt(table.path)
            assert converted.n_traces == len(table.elements)
            for trace, element in zip(converted.traces, table.elements):
                np.testing.assert_array_equal([n.point for n in trace.nodes], element.points)
            previous = sha256(table.path)
            table.path.write_bytes(b'old conversion\n')
            write_conversion(imported)
            assert sha256(table.path) == previous
            report['svg'].append({'name': table.path.name, 'sha256': previous, 'bytes_exact': True})
        assert sha256(src) == sha256(original)

    tif = aux / 'FracPaQ2D_Example1_processed.tif'
    panel = aux / 'preprocess.png'
    source = REFERENCE / 'sprint15/native/MacduffColourCropped.jpg'
    tools_main(['preprocess', str(source), str(tif), '--panel', str(panel)])
    baseline = REFERENCE / 'sprint16/auxiliary' / tif.name
    with Image.open(tif) as current, Image.open(baseline) as accepted:
        np.testing.assert_array_equal(np.asarray(current), np.asarray(accepted))
        assert current.mode == 'L' and current.format == 'TIFF'
    report['preprocess'] = {'name': tif.name, 'sha256': sha256(tif), 'pixels_exact': True,
                            'panel_sha256': sha256(panel)}

    # Fresh registry runs independently verify physical scale in values/labels.
    for scale in (None, 2.):
        scaled = dataset.with_scale(scale)
        folder = products / ('units-pixels' if scale is None else 'units-metres')
        folder.mkdir(exist_ok=True)
        config = replace(cfg, selected=('LEN-02',), tag='units',
                         input=replace(cfg.input, pixels_per_metre=scale))
        result, = registry.execute(scaled, RunContext(config, folder, folder, 'export-units'),
                                  lambda *_: None, lambda: False)
        expected_lengths = lengths.segment_lengths / (scale or 1.)
        np.testing.assert_allclose(result.data.sample.segment_lengths, expected_lengths, atol=1e-12)
        expected_txt = np.array(sorted(expected_lengths))
        np.testing.assert_allclose(np.loadtxt(folder / 'FracPaQ2Dsegmentlengths_units.txt'),
                                   expected_txt, atol=.00501, rtol=0)
        assert result.data.unit == ('pixels' if scale is None else 'metres')
        labels = []
        for output in specs['LEN-02'].render(result.data, config):
            FigureCanvasAgg(output.figure).draw()
            labels.extend(ax.get_xlabel() for ax in output.figure.axes)
            output.figure.clear()
        assert any(result.data.unit in label for label in labels)
        report['units'].append({'pixels_per_metre': scale, 'unit': result.data.unit,
                                'values_and_labels_correct': True, 'labels': labels})
    assert not list(products.rglob('.pyfracpaq-*'))
    integrity()
    checks = FOLDER / 'export-checks.xml'
    suites = list(ET.parse(checks).getroot().iter('testsuite'))
    totals = {key: sum(int(suite.get(key, 0)) for suite in suites)
              for key in ('tests', 'failures', 'errors', 'skipped')}
    assert totals == {'tests': 282, 'failures': 0, 'errors': 0, 'skipped': 0}
    report['tests'] = {**totals, 'path': relative(checks), 'sha256': sha256(checks)}
    report['covered_data_templates'] = list(json.loads(
        (REFERENCE / 'sprint16/output-contract.json').read_text())['data_templates'])
    report['complete'] = True
    write_json(FOLDER / 'summary.json', report)
    print('COMPLETE: 53 PNGs, 11 primary data files, SVG, auxiliary TIFF/theta, tags, units, replacement.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--png-directory', type=Path,
                        help='Resume PNGs exported by an earlier pass of this same audit; recheck all pixels/metadata.')
    run(parser.parse_args().png_directory)
