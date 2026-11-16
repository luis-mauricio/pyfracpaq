"""Export reproducible Python evidence for Sprint 3, never MATLAB goldens."""

import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
import platform

import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib import font_manager
import numpy as np
from PIL import Image

from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.domain.execution import RunContext
from pyfracpaq.io.figures import export_png
from reference_common import ROOT, sha256, write_json
from sprint3_reference import directional_dataset, reference_config


def validate(directory: Path) -> dict:
    directory.mkdir(parents=True, exist_ok=True)
    dataset, registry = directional_dataset(), AnalysisRegistry()
    cfg = reference_config(checkbox_shownodes=True, checkbox_rosecolour=False,
                           checkbox_showrosemean=True)
    variants = [
        ('base', dataset, cfg),
        ('weighted', dataset, replace(reference_config(
            ('ANG-02',), checkbox_roselengthweighted=True, checkbox_rosecolour=False,
            checkbox_showrosemean=True, popupmenu_rosebins='5'), tag='weighted')),
        ('strike_colour', dataset, replace(reference_config(
            ('ANG-02',), checkbox_roselengthweighted=True, checkbox_rosecolour=True,
            checkbox_showrosemean=True, popupmenu_rosebins='20'), tag='strike_colour')),
        ('north_flips_metres', dataset.with_scale(2), replace(reference_config(
            ('MAP-06', 'ANG-01', 'ANG-02'), edit_degfromnorth='10',
            checkbox_roselengthweighted=False, checkbox_rosecolour=True,
            checkbox_showrosemean=True, popupmenu_rosebins='30'),
            tag='north_flips_metres', flip_x=True, flip_y=True)),
    ]
    figures, arrays, numerical, parameters = [], {}, {}, []
    for name, data, config in variants:
        context = RunContext(config, directory, directory, name)
        results = registry.execute(data, context, lambda *a: None, lambda: False)
        parameters.append({'name': name, 'config': asdict(config),
                           'scale': data.pixels_per_metre})
        for result in results:
            if result.analysis_id.startswith('ANG-'):
                angular = result.data
                arrays[name + '_angles'] = angular.angles
                arrays[name + '_lengths'] = angular.lengths
                if angular.centres is not None:
                    arrays[name + '_hist_centres'] = angular.centres
                    arrays[name + '_hist_frequencies'] = angular.frequencies
                if angular.rose is not None:
                    for field in ('raw_counts', 'counts', 'length_sums', 'percentages',
                                  'radii', 'vertices'):
                        arrays[name + '_rose_' + field] = getattr(angular.rose, field)
                numerical[name] = asdict(angular.statistics)
            elif result.data.colour_indices is not None:
                arrays[name + '_' + result.analysis_id] = result.data.colour_indices
            spec = next(s for s in registry.specs if s.id == result.analysis_id)
            for output in spec.render(result.data, config):
                figure = output.figure
                canvas = FigureCanvasAgg(figure)
                canvas.draw()
                path = export_png(figure, output.basename, config.tag, directory)
                # QA thumbnail from the same exported pixels; not an alternate export.
                with Image.open(path) as image:
                    size, dpi = image.size, image.info['dpi']
                    thumbnail = image.copy()
                    thumbnail.thumbnail((800, 800))
                    preview = directory / ('qa-' + path.name)
                    thumbnail.save(preview)
                figures.append({'case': name, 'id': result.analysis_id,
                                'path': path.name, 'sha256': sha256(path),
                                'size': size, 'dpi': dpi, 'qa': preview.name,
                                'qa_sha256': sha256(preview)})
                figure.clear()
    np.savez_compressed(directory / 'arrays.npz', **arrays)
    # Path values are metadata only and must not accidentally become JSON strings
    # inside numeric fixtures.
    (directory / 'parameters.json').write_text(
        json.dumps(parameters, default=str, indent=2) + '\n')
    txt = [{'path': p.name, 'sha256': sha256(p), 'lines': len(p.read_text().splitlines())}
           for p in sorted(directory.glob('*.txt'))]
    result = {
        'scope': 'Python Agg exports; source/manual audit only; MATLAB unavailable.',
        'matlab_comparison': 'pending', 'numpy': np.__version__,
        'python': platform.python_version(), 'platform': platform.platform(),
        'matplotlib': matplotlib.__version__,
        'font': font_manager.FontProperties(family='Arial').get_name(),
        'figures': figures, 'txt': txt, 'statistics': numerical,
        'arrays_sha256': sha256(directory / 'arrays.npz'),
        'parameters_sha256': sha256(directory / 'parameters.json'),
        'source_unchanged': True,
    }
    from source_manifest import verify
    verify()
    write_json(directory / 'validation.json', result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path,
                        default=ROOT / 'tests/reference/sprint3')
    args = parser.parse_args()
    result = validate(args.output_dir.resolve())
    print(f"Sprint 3: {len(result['figures'])} PNGs + {len(result['txt'])} EZROSE TXT; "
          'comparação MATLAB pendente.')


if __name__ == '__main__':
    main()
