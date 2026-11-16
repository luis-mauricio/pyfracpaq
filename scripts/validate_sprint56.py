"""SVG/Hough evidence, full diagnostic meshes and prior-family integration."""

import argparse
from dataclasses import asdict, replace
import gc
import json
from pathlib import Path
import platform
import shutil
import tempfile

from defusedxml import ElementTree as ET
import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np
from PIL import Image

from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.analysis.hough import HoughParameters
from pyfracpaq.domain import TraceInput, build_dataset
from pyfracpaq.domain.execution import RunContext
from pyfracpaq.io.images import ImageInputError, read_grayscale, read_image
from pyfracpaq.io.svg import SvgInputError, convert_svg, read_svg
from pyfracpaq.io import read_txt
from pyfracpaq.io.figures import export_png
from pyfracpaq.plots.hough import render_hough
from reference_common import ROOT, sha256, write_json
from source_manifest import verify
from sprint3_reference import reference_config

SELECTED = ('MAP-01', 'MAP-04', 'MAP-05', 'MAP-06', 'LEN-02', 'LEN-03',
            'LEN-06', 'ANG-01', 'ANG-02')


def save_figure(output, tag: str, folder: Path) -> dict:
    FigureCanvasAgg(output.figure).draw()
    target = export_png(output.figure, output.basename, tag, folder)
    with Image.open(target) as image:
        size, dpi = image.size, image.info['dpi']
        thumbnail = image.copy()
        thumbnail.thumbnail((800, 800))
        preview = target.with_name('qa-' + target.name)
        thumbnail.save(preview)
    output.figure.clear()
    gc.collect()
    return {'path': target.name, 'sha256': sha256(target), 'size': size, 'dpi': dpi,
            'qa': preview.name, 'qa_sha256': sha256(preview)}


def analyses(dataset, folder: Path, tag: str, *, selected=SELECTED, **values) -> tuple[list, dict]:
    is_image = dataset.input_mode == 'image'
    values = {'radiobutton_image': is_image, 'radiobutton_node': not is_image, **values}
    cfg = replace(reference_config(selected, **values), tag=tag,
                  input=replace(reference_config().input, path=dataset.source or Path('synthetic'),
                                kind='image' if is_image else 'node',
                                pixels_per_metre=dataset.pixels_per_metre))
    registry = AnalysisRegistry()
    results = registry.execute(dataset, RunContext(cfg, folder, folder, tag),
                               lambda *a: None, lambda: False)
    figures = []
    for result in results:
        spec = next(s for s in registry.specs if s.id == result.analysis_id)
        for output in spec.render(result.data, cfg):
            figures.append({'id': result.analysis_id, **save_figure(output, tag, folder)})
    return figures, asdict(cfg)


def svg_validation(folder: Path) -> dict:
    inputs = folder / 'inputs'
    inputs.mkdir(parents=True, exist_ok=True)
    cases, arrays, converted = [], {}, []
    for name in ('simple', 'multicolour'):
        source = ROOT / 'tests/fixtures/svg' / (name + '.svg')
        target = inputs / source.name
        shutil.copyfile(source, target)
        result = convert_svg(target)
        dataset = result.dataset
        cases.append({'case': name, 'input': str(source.relative_to(ROOT)),
                      'input_sha256': sha256(source), 'traces': dataset.n_traces,
                      'segments': dataset.n_segments, 'nodes': dataset.n_nodes,
                      'colours': dataset.colours})
        arrays[name + '_nodes'] = dataset.as_arrays().node_coordinates
        arrays[name + '_colours'] = dataset.as_arrays().trace_colours
        for table in result.tables:
            converted.append({'path': str(table.path.relative_to(folder)),
                              'sha256': sha256(table.path), 'colour': table.colour_hex,
                              'rows': len(table.elements)})
    dataset = read_svg(inputs / 'multicolour.svg').dataset
    figures, cfg = analyses(dataset, folder, 'SVG', checkbox_shownodes=True)
    red = read_txt(inputs / 'multicolour_colourFF0000_converted.txt')
    extra, red_cfg = analyses(red, folder, 'red', selected=('LEN-02', 'ANG-01', 'ANG-02'),
                              checkbox_rosecolour=False)
    figures.extend(extra)
    audit = []
    for source in sorted((ROOT / 'fracpaq-matlab').glob('*.svg')):
        try:
            result = read_svg(source)
            status = f'accepted: {result.dataset.n_traces} traces'
        except (SvgInputError, ValueError) as error:
            status = str(error)
        audit.append({'input': str(source.relative_to(ROOT)), 'sha256': sha256(source),
                      'result': status})
    write_json(folder / 'original_svg_audit.json', audit)
    # Explicit preparation of a COPY: discard only the three known wholly
    # degenerate traces. No product reader silently drops these records.
    original = ROOT / 'fracpaq-matlab/map1_edit.svg'
    root = ET.parse(original).getroot()
    removed = 0
    for parent in root.iter():
        for element in list(parent):
            tag = element.tag.split('}')[-1]
            if tag == 'line':
                values = [float(element.get(n, '0')) for n in ('x1', 'y1', 'x2', 'y2')]
                points = [tuple(values[:2]), tuple(values[2:])]
            elif tag == 'polyline':
                values = [float(s) for s in element.get('points', '').replace(',', ' ').split()]
                points = list(zip(values[::2], values[1::2]))
            else:
                continue
            if points and all(point == points[0] for point in points):
                parent.remove(element)
                removed += 1
    assert removed == 3
    prepared = inputs / 'map1_prepared.svg'
    import xml.etree.ElementTree as StandardET
    StandardET.ElementTree(root).write(prepared, encoding='utf-8', xml_declaration=True)
    result = read_svg(prepared)
    assert result.dataset.n_traces == 2120
    prepared_case = {'original': str(original.relative_to(ROOT)),
                     'original_sha256': sha256(original),
                     'prepared': str(prepared.relative_to(folder)),
                     'prepared_sha256': sha256(prepared), 'removed_degenerate': removed,
                     'traces': result.dataset.n_traces, 'segments': result.dataset.n_segments}
    np.savez_compressed(folder / 'arrays.npz', **arrays)
    (folder / 'parameters.json').write_text(json.dumps([cfg, red_cfg], default=str, indent=2) + '\n')
    return {'scope': 'Python SVG/colour implementation; native MATLAB parity pending.',
            'cases': cases, 'converted': converted, 'figures': figures,
            'prepared_real_example': prepared_case,
            'arrays_sha256': sha256(folder / 'arrays.npz'),
            'parameters_sha256': sha256(folder / 'parameters.json'),
            'audit_sha256': sha256(folder / 'original_svg_audit.json')}


def image_validation(folder: Path) -> dict:
    records, arrays, figures = [], {}, []
    parameters = HoughParameters()  # Frozen GUI defaults, including 1000 peaks.
    for source, tag in [
        (ROOT / 'tests/fixtures/images/directional.tif', 'directional'),
        (ROOT / 'tests/fixtures/images/rectangular.tif', 'rectangular'),
        (ROOT / 'fracpaq-matlab/MacduffBinary.tif', 'Macduff'),
        (ROOT / 'fracpaq-matlab/Orkney1aBinary.tif', 'Orkney'),
    ]:
        imported = read_image(source, parameters)
        data, hough = imported.dataset, imported.hough
        figures.append(save_figure(render_hough(hough), tag, folder))
        for name in ('image', 'binary', 'accumulator', 'theta', 'rho', 'peaks', 'endpoints'):
            arrays[tag + '_' + name] = getattr(hough, name)
        for name in ('segment_lengths', 'raw_angles', 'segment_midpoints', 'end_lengths'):
            arrays[tag + '_' + name] = getattr(data.as_arrays(), name)
        assert data.n_segments == data.n_traces and data.n_nodes == data.n_traces * 2
        assert all(t.segments[0].midpoint == t.midpoint for t in data.traces)
        records.append({'case': tag, 'input': str(source.relative_to(ROOT)),
                        'input_sha256': sha256(source),
                        'metadata': {**asdict(imported.metadata),
                                     'path': str(source.relative_to(ROOT))},
                        'accumulator_shape': hough.accumulator.shape,
                        'max_votes': int(hough.accumulator.max()), 'threshold': hough.threshold,
                        'peaks': len(hough.peaks), 'traces': data.n_traces,
                        'nodes': data.n_nodes, 'bounds': asdict(data.bounds),
                        'total_length': data.total_length})
    data = read_image(ROOT / 'tests/fixtures/images/rectangular.tif', parameters,
                       pixels_per_metre=2).dataset
    extra, cfg = analyses(data, folder, 'image', checkbox_shownodes=True,
                           edit_degfromnorth='10')
    figures.extend(extra)
    rejected = []
    for name in ('Macduff.tiff', 'Orkney1a.tiff'):
        try:
            read_grayscale(ROOT / 'fracpaq-matlab' / name)
        except ImageInputError as error:
            rejected.append({'input': name, 'message': str(error),
                             'metadata': {**asdict(error.metadata),
                                          'path': str(error.metadata.path.relative_to(ROOT))}})
        else:
            raise AssertionError('Original RGBA images must not be converted silently.')
    np.savez_compressed(folder / 'arrays.npz', **arrays)
    (folder / 'parameters.json').write_text(json.dumps({'hough': asdict(parameters),
                                                       'analysis': cfg}, default=str, indent=2) + '\n')
    return {'scope': 'Python deterministic Hough; no native MATLAB comparison.',
            'cases': records, 'rejected_originals': rejected, 'figures': figures,
            'arrays_sha256': sha256(folder / 'arrays.npz'),
            'parameters_sha256': sha256(folder / 'parameters.json')}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference-root', type=Path, default=ROOT / 'tests/reference')
    args = parser.parse_args()
    for number, operation in ((5, svg_validation), (6, image_validation)):
        directory = args.reference_root / f'sprint{number}'
        directory.mkdir(parents=True, exist_ok=True)
        report = operation(directory)
        report.update({'date': '2026-11-14', 'python': platform.python_version(),
                       'platform': platform.platform(), 'numpy': np.__version__,
                       'matplotlib': matplotlib.__version__, 'matlab_comparison': 'pending'})
        txt = [{'path': str(p.relative_to(directory)), 'sha256': sha256(p)}
               for p in sorted(directory.rglob('*.txt'))]
        report['txt'] = txt
        write_json(directory / 'validation.json', report)
        print(f"Sprint {number}: {len(report['figures'])} PNGs, {len(txt)} TXT, arrays saved.", flush=True)
    verify()


if __name__ == '__main__':
    main()
