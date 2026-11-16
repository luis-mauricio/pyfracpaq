"""Record analytical geometry validation; no MATLAB parity claim is made."""

import argparse
from dataclasses import asdict
import importlib.metadata as metadata
import json
from pathlib import Path
import platform
import tempfile

import numpy as np

from pyfracpaq.geometry import segment_intersection
from pyfracpaq.domain import Dataset
from pyfracpaq.io import NodeFileError, read_txt
from reference_common import ORIGINAL, REFERENCE, ROOT, sha256, write_json


def measured(dataset: Dataset) -> dict:
    arrays = dataset.as_arrays()
    return {
        'traces': dataset.n_traces,
        'segments': dataset.n_segments,
        'nodes': dataset.n_nodes,
        'segment_lengths': arrays.segment_lengths.tolist(),
        'raw_angles_degrees': arrays.raw_angles.tolist(),
        'segment_midpoints': arrays.segment_midpoints.tolist(),
        'trace_lengths': arrays.trace_lengths.tolist(),
        'trace_midpoints': arrays.trace_midpoints.tolist(),
        'euclidean_lengths': [t.euclidean_length for t in dataset.traces],
        'bounds_xyxy': [dataset.bounds.x_min, dataset.bounds.y_min,
                        dataset.bounds.x_max, dataset.bounds.y_max],
        'area': dataset.area,
        'diagonal': dataset.bounds.diagonal,
        'length_unit': dataset.length_unit,
        'diagnostics': [asdict(d) for d in dataset.diagnostics],
    }


def analytic_results() -> list[dict]:
    cases = json.loads((ROOT / 'tests/fixtures/analytic_cases.json').read_text())['cases']
    results = []
    for case in cases:
        if case['family'] != 'geometry':
            continue
        source = ROOT / case['input']['file']
        dataset = read_txt(source, pixels_per_metre=case['input'].get('scale'))
        actual = measured(dataset)
        comparable = dict(actual)
        comparable['trace_length'] = dataset.traces[0].total_length
        comparable['trace_halfway_point'] = dataset.traces[0].midpoint
        errors = {}
        for key, expected in case['expected'].items():
            if key == 'units':
                assert expected == actual['length_unit']
                continue
            value = comparable[key]
            if key in ('traces', 'segments', 'nodes'):
                assert value == expected
            else:
                length_scale = max(dataset.bounds.width, dataset.bounds.height)
                characteristic = (360 if 'angles' in key else
                                  length_scale ** 2 if key == 'area'
                                  else length_scale)
                np.testing.assert_allclose(
                    value, expected, rtol=1e-10,
                    atol=1e-12 * max(1, characteristic),
                )
                errors[key] = float(np.max(np.abs(np.asarray(value) - expected)))
        results.append({
            'id': case['id'], 'input': case['input'], 'input_sha256': sha256(source),
            'measured': actual, 'max_absolute_errors': errors, 'status': 'passed',
        })
    return results


def real_results() -> list[dict]:
    examples = json.loads((REFERENCE / 'examples.json').read_text())
    results = []
    with tempfile.TemporaryDirectory(prefix='pyfracpaq-sprint1-') as temporary:
        for entry in examples:
            if entry.get('delimiter') != 'TAB':
                continue
            source = ROOT / entry['path']
            excluded = entry['degenerate_trace_lines']
            result = {'source': entry['path'], 'source_sha256': sha256(source)}
            if excluded:
                try:
                    read_txt(source)
                except NodeFileError as error:
                    assert [issue.line for issue in error.issues] == excluded
                    result['original_status'] = 'rejected_degenerate_traces'
                    result['issues'] = [asdict(issue) for issue in error.issues]
                else:
                    raise AssertionError(f'Degenerate example unexpectedly accepted: {source}')
                lines = source.read_text().splitlines()
                prepared = Path(temporary) / source.name
                prepared.write_text('\n'.join(
                    '' if i in excluded else line
                    for i, line in enumerate(lines, 1)
                ) + '\n')
                dataset = read_txt(prepared)
                result['preparation'] = 'Excluded lines replaced by empty lines in a temporary copy.'
                result['prepared_sha256'] = sha256(prepared)
                result['excluded_lines'] = excluded
            else:
                dataset = read_txt(source)
                result['original_status'] = 'accepted'
            result['counts'] = {
                'traces': dataset.n_traces, 'segments': dataset.n_segments,
                'nodes': dataset.n_nodes,
            }
            assert dataset.n_traces == entry['records'] - len(excluded)
            assert dataset.n_nodes == dataset.n_segments + dataset.n_traces
            result['area'] = dataset.area
            result['total_length'] = dataset.total_length
            result['duplicates_removed'] = len(dataset.diagnostics)
            results.append(result)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=REFERENCE / 'sprint1/numerical.json')
    args = parser.parse_args()
    analytical = analytic_results()
    real = real_results()
    intersections = []
    for first, second, expected in [
        ([0, 0, 4, 0], [2, -1, 2, 1], 'point'),
        ([0, 0, 4, 0], [2, 0, 6, 0], 'overlap'),
        ([0, 0, 4, 0], [0, 1, 4, 1], 'none'),
    ]:
        result = segment_intersection(first, second)
        assert result.kind == expected
        intersections.append({'first': first, 'second': second,
                              'measured': asdict(result)})
    files = sorted((ROOT / 'pyfracpaq').rglob('*.py'))
    write_json(args.output, {
        'schema_version': 1,
        'scope': 'Python versus analytical oracles; MATLAB execution unavailable.',
        'environment': {'python': platform.python_version(),
                        'os': platform.platform(), 'numpy': metadata.version('numpy')},
        'code_sha256': {str(path.relative_to(ROOT)): sha256(path) for path in files},
        'original_manifest_sha256': sha256(REFERENCE / 'source_manifest.json'),
        'analytical': analytical, 'real_examples': real,
        'intersections': intersections,
        'matlab_comparison': 'pending',
    })
    print(f'{len(analytical)} casos analíticos, {len(real)} exemplos reais e '
          f'{len(intersections)} relações geométricas: OK.')


if __name__ == '__main__':
    main()
