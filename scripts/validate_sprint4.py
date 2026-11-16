"""Record Lengths arrays, legacy differences and actual PNG/TXT exports."""

import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
import platform
import tempfile

import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib import font_manager
import numpy as np
from PIL import Image

from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.analysis.lengths import select_lengths
from pyfracpaq.domain import TraceInput, build_dataset
from pyfracpaq.domain.execution import FieldError, RunContext
from pyfracpaq.io.figures import export_png
from pyfracpaq.io import read_txt
from reference_common import ROOT, sha256, write_json
from source_manifest import verify
from sprint4_reference import INPUT, edge_dataset, emulate_legacy_censor, length_config


def validate_examples(directory: Path) -> list[dict]:
    records = []
    with tempfile.TemporaryDirectory(prefix='pyfracpaq-sprint4-examples-') as name:
        folder = Path(name)
        for index, filename in enumerate(('IYXtest1_converted.txt',
                                           'IYXtest2_converted.txt', 'Souter_Blue.txt')):
            path = ROOT / 'fracpaq-matlab' / filename
            dataset = read_txt(path)
            config = replace(length_config(), tag=f'example{index}')
            results = AnalysisRegistry().execute(
                dataset, RunContext(config, folder, folder, str(index)),
                lambda *a: None, lambda: False)
            result = results[0].data
            assert result.segment_histogram.frequencies.sum() == dataset.n_segments
            assert result.trace_complementary.frequencies.sum() == dataset.n_traces
            records.append({
                'input': str(path.relative_to(ROOT)), 'sha256': sha256(path),
                'traces': asdict(result.trace_statistics),
                'segments': asdict(result.segment_statistics),
                'domain_diagonal': result.domain_diagonal,
                'scope': 'Python computation and three TXT exports; '
                         'no native MATLAB comparison.',
            })
    write_json(directory / 'examples.json', records)
    return records


def validate(directory: Path) -> dict:
    directory.mkdir(parents=True, exist_ok=True)
    data, registry = edge_dataset(), AnalysisRegistry()
    repeated = build_dataset([TraceInput(((0, 0), (2, 0))),
                              TraceInput(((0, 2), (2, 2)))])
    variants = [
        ('pixels', data, replace(length_config(), tag='pixels')),
        ('censored_metres', data.with_scale(2), replace(length_config(
            checkbox_censor=True, edit_degfromnorth='10', popupmenu_histolengthbins='30'),
            tag='censored_metres', flip_x=True)),
        ('repeated', repeated, replace(length_config(), tag='repeated')),
    ]
    records, arrays, statistics, parameters = [], {}, {}, []
    for name, dataset, config in variants:
        parameters.append({'case': name, 'config': asdict(config),
                           'pixels_per_metre': dataset.pixels_per_metre,
                           'input_points': [[n.point for n in t.nodes] for t in dataset.traces]})
        context = RunContext(config, directory, directory, name)
        results = registry.execute(dataset, context, lambda *a: None, lambda: False)
        result = results[0].data
        statistics[name] = {
            'traces': asdict(result.trace_statistics),
            'segments': asdict(result.segment_statistics),
            'excluded_traces': result.sample.excluded_traces,
            'excluded_segments': result.sample.excluded_segments,
            'domain_diagonal': result.domain_diagonal,
            'maximum_possible_length': result.maximum_possible_length,
        }
        for field in ('trace_keep', 'segment_keep', 'trace_ids', 'segment_ids',
                      'trace_lengths', 'segment_lengths', 'raw_angles'):
            arrays[name + '_' + field] = getattr(result.sample, field)
        for field in ('cross_angles', 'cross_lengths'):
            arrays[name + '_' + field] = getattr(result, field)
        for subject in ('trace', 'segment'):
            histogram = getattr(result, subject + '_histogram')
            cumulative = getattr(result, subject + '_complementary')
            arrays[name + '_' + subject + '_hist_centres'] = histogram.centres
            arrays[name + '_' + subject + '_hist_counts'] = histogram.frequencies
            arrays[name + '_' + subject + '_cumulative_centres'] = cumulative.centres
            arrays[name + '_' + subject + '_cumulative_counts'] = cumulative.frequencies
            arrays[name + '_' + subject + '_complementary'] = cumulative.complementary
        for analysis in results:
            spec = next(s for s in registry.specs if s.id == analysis.analysis_id)
            for output in spec.render(analysis.data, config):
                FigureCanvasAgg(output.figure).draw()
                path = export_png(output.figure, output.basename, config.tag, directory)
                with Image.open(path) as image:
                    size, dpi = image.size, image.info['dpi']
                    preview = directory / ('qa-' + path.name)
                    thumb = image.copy()
                    thumb.thumbnail((800, 800))
                    thumb.save(preview)
                records.append({'case': name, 'id': analysis.analysis_id,
                                'path': path.name, 'sha256': sha256(path),
                                'size': size, 'dpi': dpi,
                                'qa': preview.name, 'qa_sha256': sha256(preview)})
                output.figure.clear()
    baseline = emulate_legacy_censor(data)
    corrected = select_lengths(data, censor=True)
    baseline['corrected_trace_keep'] = corrected.trace_keep.tolist()
    baseline['corrected_segment_keep'] = corrected.segment_keep.tolist()
    baseline['corrected_angles'] = corrected.raw_angles.tolist()
    baseline['corrected_lengths'] = corrected.segment_lengths.tolist()
    baseline['source'] = 'fracpaq-matlab/guiFracPaQ2Dlength.m'
    baseline['source_sha256'] = sha256(ROOT / baseline['source'])
    write_json(directory / 'q05_static_reproduction.json', baseline)
    before = {p.name: sha256(p) for p in directory.glob('*.txt')}
    try:
        cfg = replace(length_config(checkbox_censor=True), tag='empty')
        registry.execute(repeated, RunContext(cfg, directory, directory, 'empty'),
                         lambda *a: None, lambda: False)
    except FieldError as error:
        empty = {'field': error.field, 'message': str(error)}
    else:
        raise AssertionError('An empty censored sample must fail.')
    assert before == {p.name: sha256(p) for p in directory.glob('*.txt')}
    np.savez_compressed(directory / 'arrays.npz', **arrays)
    (directory / 'parameters.json').write_text(
        json.dumps(parameters, default=str, indent=2) + '\n')
    txt = [{'path': path.name, 'sha256': sha256(path),
            'lines': len(path.read_text().splitlines())}
           for path in sorted(directory.glob('*.txt'))]
    validate_examples(directory)
    verify()
    report = {
        'scope': 'Python Lengths implementation; MATLAB execution/visual parity pending.',
        'python': platform.python_version(), 'platform': platform.platform(),
        'numpy': np.__version__, 'matplotlib': matplotlib.__version__,
        'font': font_manager.FontProperties(family='Arial').get_name(),
        'input': str(INPUT.relative_to(ROOT)), 'input_sha256': sha256(INPUT),
        'figures': records, 'txt': txt, 'statistics': statistics,
        'empty_censored_sample': empty, 'empty_preserved_txt': True,
        'arrays_sha256': sha256(directory / 'arrays.npz'),
        'parameters_sha256': sha256(directory / 'parameters.json'),
        'q05_reproduction_sha256': sha256(directory / 'q05_static_reproduction.json'),
        'examples_sha256': sha256(directory / 'examples.json'),
        'original_source_unchanged': True,
        'matlab_comparison': 'pending',
    }
    write_json(directory / 'validation.json', report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path,
                        default=ROOT / 'tests/reference/sprint4')
    args = parser.parse_args()
    report = validate(args.output_dir.resolve())
    print(f"Sprint 4: {len(report['figures'])} PNGs + {len(report['txt'])} TXT; "
          'amostra vazia e reprodução estática de Q-05 registradas; MATLAB pendente.')


if __name__ == '__main__':
    main()
