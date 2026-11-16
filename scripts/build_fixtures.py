"""Build small analytical inputs, separate from MATLAB execution evidence."""

import math
from pathlib import Path

from PIL import Image, ImageDraw

from reference_common import ORIGINAL, REFERENCE, ROOT, sha256, write_json

FIXTURES = ROOT / 'tests' / 'fixtures'


def main() -> None:
    cases = []

    def add(name: str, family: str, inputs: dict, expected: dict,
            issues: list[str] | None = None) -> None:
        cases.append({'id': name, 'family': family, 'input': inputs,
                      'expected': expected, 'issues': issues or [],
                      'oracle': 'Analítico; não executado em MATLAB.'})

    geometry = [
        ('horizontal', [[0, 0], [4, 0]], [4], [90], [2, 0]),
        ('vertical', [[0, 0], [0, 3]], [3], [0], [0, 1.5]),
        ('oblique', [[0, 0], [3, 4]], [5], [36.86989764584402], [1.5, 2]),
        ('polyline', [[1, 2], [4, 2], [4, 6]], [3, 4], [90, 0], [4, 2.5]),
        ('negative', [[-9, -8], [-6, -8], [-6, -4]], [3, 4], [90, 0], [-6, -7.5]),
        ('duplicate', [[1, 2], [1, 2], [4, 2], [4, 6]], [3, 4], [90, 0], [4, 2.5]),
    ]
    node_dir = FIXTURES / 'nodes'
    node_dir.mkdir(parents=True, exist_ok=True)
    for name, points, lengths, angles, centre in geometry:
        path = node_dir / f'{name}.txt'
        path.write_text('\t'.join(str(v) for p in points for v in p) + '\n')
        clean = [p for i, p in enumerate(points) if i == 0 or p != points[i - 1]]
        add(name, 'geometry', {'file': str(path.relative_to(ROOT)), 'scale': None}, {
            'traces': 1, 'segments': len(lengths), 'nodes': len(clean),
            'segment_lengths': lengths, 'raw_angles_degrees': angles,
            'trace_length': sum(lengths), 'trace_halfway_point': centre,
            'bounds_xyxy': [min(p[0] for p in clean), min(p[1] for p in clean),
                            max(p[0] for p in clean), max(p[1] for p in clean)],
            'segment_midpoints': [[(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]
                                  for a, b in zip(clean, clean[1:])],
        }, ['Q-07'] if name == 'duplicate' else ['Q-08'] if name == 'negative' else [])
    (node_dir / 'mixed.txt').write_text('0\t0\t4\t0\n1\t2\t4\t2\t4\t6\n')
    add('mixed', 'geometry', {'file': 'tests/fixtures/nodes/mixed.txt'},
        {'traces': 2, 'segments': 3, 'nodes': 5, 'trace_lengths': [4, 7],
         'bounds_xyxy': [0, 0, 4, 6], 'area': 24})
    add('scaled', 'geometry', {'file': 'tests/fixtures/nodes/polyline.txt', 'scale': 2},
        {'segment_lengths': [1.5, 2], 'trace_length': 3.5,
         'bounds_xyxy': [.5, 1, 2, 3], 'area': 3,
         'trace_halfway_point': [2, 1.25], 'units': 'metres'}, ['Q-21'])
    for name, content in {'empty': '', 'incomplete': '0\t0\t1\n',
                          'degenerate': '1\t1\t1\t1\n',
                          'nonfinite': '0\t0\tnan\t1\n',
                          'comma': '0,0,1,1\n'}.items():
        (node_dir / f'{name}.txt').write_text(content)
        add(name, 'invalid_input', {'file': f'tests/fixtures/nodes/{name}.txt'},
            {'valid': False, 'partial_import': False}, ['Q-02', 'Q-07'])

    add('histogram_centres', 'histograms',
        {'samples': [0, 1, 2, 2, 3, 4], 'centres': [1, 2, 3]},
        {'counts': [2, 2, 2], 'percent': [100 / 3] * 3,
         'note': 'Centros explícitos; caudas nos bins externos, não bordas NumPy.'})
    add('histogram_ties', 'histograms',
        {'samples': [1.5, 2.5], 'centres': [1, 2, 3]},
        {'tie_rule': 'Confirmar no MATLAB antes de congelar contagens de empates.',
         'matlab_counts': None})
    add('matlab_round', 'angles', {'values': [-1.5, -.5, .5, 1.5]},
        {'rounded': [-2, -1, 1, 2]})
    for fx, fy, expected in [(False, False, [20, 200]), (True, False, [160, 340]),
                             (False, True, [160, 340]), (True, True, [20, 200])]:
        add(f'angles_flip_{int(fx)}{int(fy)}', 'angles',
            {'raw': [30], 'north': 10, 'flip_x': fx, 'flip_y': fy},
            {'sorted_axial_directions': expected}, ['Q-10'])

    circle_lines = [
        ('horizontal', [[-2, 0], [2, 0]], 2, 0),
        ('vertical', [[0, -2], [0, 2]], 2, 0),
        ('oblique', [[-2, -2], [2, 2]], 2, 0),
        ('internal', [[-.5, 0], [.5, 0]], 0, 2),
        ('one_inside', [[0, 0], [2, 0]], 1, 1),
        ('outside', [[2, 2], [3, 3]], 0, 0),
    ]
    for offset in ([0, 0], [7, -11]):
        for name, endpoints, n, m in circle_lines:
            points = [[x + offset[0], y + offset[1]] for x, y in endpoints]
            add(f'circle_{name}_{offset[0]}', 'circles',
                {'centre': offset, 'radius': 1, 'segment': points},
                {'boundary_intersections': n, 'endpoints_inside': m,
                 'p21_geometric': n / 4, 'p20_geometric': m / (2 * math.pi),
                 'matlab_result': None}, ['Q-20'])
    add('circle_tangent', 'circles',
        {'centre': [0, 0], 'radius': 1, 'segment': [[-2, 1], [2, 1]]},
        {'unique_boundary_points': 1, 'endpoints_inside': 0,
         'estimator_tangent_policy': 'Pendente Q-20; não contar como secante automaticamente.'},
        ['Q-20'])

    topology = [
        ('isolated', [[[-1, 0], [1, 0]]], {'I': 2, 'Y': 0, 'X': 0}),
        ('cross', [[[-2, 0], [2, 0]], [[0, -2], [0, 2]]], {'I': 4, 'Y': 0, 'X': 1}),
        ('tee', [[[-2, 0], [2, 0]], [[0, 0], [0, 2]]], {'I': 3, 'Y': 1, 'X': 0}),
        ('no_crossing', [[[-2, -1], [2, -1]], [[-2, 1], [2, 1]]],
         {'I': 4, 'Y': 0, 'X': 0}),
    ]
    for name, traces, counts in topology:
        add(name, 'topology', {'traces': traces, 'domain': [-3, -3, 3, 3],
                                 'tolerance': 0},
            {'geometric_node_counts_before_border_cleanup': counts,
             'border_policy': 'Domínio explícito: todos os endpoints são interiores.',
             'matlab_counts': None}, ['Q-11'])
    for name, y in [('undershoot', .1), ('overshoot', -.1)]:
        add(name, 'topology', {'traces': [[[-2, 0], [2, 0]], [[0, y], [0, 2]]],
                              'tolerance': .2},
            {'endpoint_distance_to_horizontal': .1,
             'exact_intersections': 0 if y > 0 else 1,
             'snap_classification': None}, ['Q-11'])

    add('directional_tensor', 'tensors', {'lengths': [2], 'pole_degrees': [0],
                                       'area': 4, 'aperture': .001, 'lambda': 1},
        {'F0': 1, 'F2': [[1, 0], [0, 0]], 'F4_xxxx': 1, 'F8_xxxxxxxx': 1,
         'P': [[5e-10, 0], [0, 0]], 'K': [[0, 0], [0, 5e-10 / 12]],
         'double_aperture_K_ratio': 8, 'lambda_zero_K': [[0, 0], [0, 0]]})
    add('isotropic_tensor', 'tensors', {'lengths': [1] * 8,
                                      'pole_degrees': [22.5 * i for i in range(8)],
                                      'area': 8},
        {'F0': 1, 'F2': [[.5, 0], [0, .5]], 'F4_xxxx': 3 / 8,
         'F4_xxyy': 1 / 8, 'F8_xxxxxxxx': 35 / 128})
    add('scaled_apertures', 'tensors', {'lengths': [1, 4], 'a': .001, 'b': .5},
        {'apertures': [.001, .002]})

    for name, kernel_at_origin in [('morlet', [1, 0]), ('mexicanhat', [2, 0])]:
        add(f'{name}_kernel', 'wavelets',
            {'x': [-1, 0, 1], 'y': [-1, 0, 1], 'A': [[1, 0], [0, 1]],
             'C': [[1, 0], [0, 1]], 'k': [0, 0]},
            {'centre_real_imag': kernel_at_origin,
             'at_1_0_real': math.exp(-.5),
             'at_1_1_real': math.exp(-1) if name == 'morlet' else 0})
    image_dir = FIXTURES / 'images'
    image_dir.mkdir(exist_ok=True)
    for name, size, mode in [('directional', (32, 32), 'L'),
                             ('rectangular', (48, 24), 'L'),
                             ('rgb_invalid', (32, 32), 'RGB')]:
        image = Image.new(mode, size, 'white')
        ImageDraw.Draw(image).line((4, size[1] // 2, size[0] - 5, size[1] // 2),
                                   fill='black', width=1)
        image.save(image_dir / f'{name}.tif')
    add('rectangular_cwt', 'wavelets',
        {'file': 'tests/fixtures/images/rectangular.tif', 'a': [2, 4],
         'L': [2, 4], 'theta_increment': 20, 'kernels': ['Morlet', 'Mexican Hat']},
        {'image_shape_yx': [24, 48], 'input_L_reciprocals': [.5, .25],
         'normalised_coefficients_matlab': None, 'optima_matlab': None}, ['Q-12'])
    add('bad_wavelet_step', 'invalid_input', {'theta_increment': 181},
        {'policy': 'Pendente Q-12; não promover amostragem alterada a padrão.'}, ['Q-12'])
    svg_dir = FIXTURES / 'svg'
    svg_dir.mkdir(exist_ok=True)
    (svg_dir / 'simple.svg').write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" version="1.1">\n'
        '<line x1="0" y1="0" x2="4" y2="0" stroke="#000000"/>\n'
        '<polyline points="1,2 4,2 4,6" stroke="#000000" fill="none"/>\n</svg>\n')
    (svg_dir / 'multicolour.svg').write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" version="1.1">\n'
        '<line x1="0" y1="0" x2="4" y2="0" stroke="#FF0000"/>\n'
        '<path d="M 1,2 L 4,2 L 4,6" stroke="#0000FF" fill="none"/>\n</svg>\n')
    write_json(FIXTURES / 'analytic_cases.json', {
        'schema_version': 1, 'license': 'MIT (LICENSE na raiz)',
        'origin': 'Criado neste projeto; equações conferidas nos fontes. '
                  'Campos MATLAB nulos são referências ainda indisponíveis.',
        'cases': cases,
    })

    selected = []
    for name in ('IYXtest1_converted.txt', 'IYXtest2_converted.txt',
                 'map1_edit_converted.txt', 'map7_edit_converted.txt',
                 'Souter_Blue.txt', 'souter_all_colour24378D.txt'):
        path = ORIGINAL / name
        lines = [line.strip() for line in path.read_text().splitlines() if line.strip()]
        delimiter = '\t' if '\t' in lines[0] else ','
        records = [[float(v) for v in line.split(delimiter) if v.strip()] for line in lines]
        valid = all(len(r) >= 4 and len(r) % 2 == 0 and
                    all(math.isfinite(v) for v in r) for r in records)
        degenerate_lines = [
            i for i, record in enumerate(records, 1)
            if len(set(zip(record[::2], record[1::2]))) < 2
        ]
        selected.append({'path': str(path.relative_to(ROOT)), 'sha256': sha256(path),
                         'records': len(records), 'delimiter': 'TAB' if delimiter == '\t' else 'comma',
                         'coordinate_columns_min_max': [min(map(len, records)),
                                                        max(map(len, records))],
                         'valid_numeric_pairs': valid,
                         'tab_delimited_numeric_pairs': valid and delimiter == '\t',
                         'degenerate_trace_lines': degenerate_lines,
                         'direct_gui_txt': valid and delimiter == '\t' and not degenerate_lines,
                         'license': 'MIT, fracpaq-matlab/LICENSE; atribuição aos '
                                    'FracPaQ Contributors, sem autoria de campo adicional presumida.'})
        assert valid, name
    for name in ('Macduff.tiff', 'MacduffBinary.tif', 'Orkney1a.tiff', 'Orkney1aBinary.tif'):
        path = ORIGINAL / name
        with Image.open(path) as image:
            selected.append({'path': str(path.relative_to(ROOT)), 'sha256': sha256(path),
                             'mode': image.mode, 'size': list(image.size),
                             'direct_gui_8bit_grayscale': image.mode == 'L',
                             'license': 'MIT, fracpaq-matlab/LICENSE; imagem fornecida no pacote.'})
    write_json(REFERENCE / 'examples.json', selected)
    print(f'{len(cases)} casos analíticos; {len(selected)} exemplos reais inspecionados.')


if __name__ == '__main__':
    main()
