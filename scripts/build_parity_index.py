"""Generate the initial traceability matrix and static source catalog."""

import json
import re
from collections import Counter

from reference_common import ORIGINAL, REFERENCE, ROOT, sha256, write_json

SOURCE = {
    'UI': 'guiFracPaQ2D.m', 'IN': 'guiFracPaQ2Dlist.m, guiFracPaQ2Dimage.m, convertSVG2txt_colour2.m',
    'MAP': 'guiFracPaQ2Dtracemap.m, guiFracPaQ2Dpattern.m',
    'LEN': 'guiFracPaQ2Dlength.m', 'ANG': 'guiFracPaQ2Dangle.m',
    'FLO': 'getConnectivity.m, guiFracPaQ2Dtensor.m, guiFracPaQ2Dcracktensor.m',
    'WAV': 'guiFracPaQ2Dwavelet.m', 'GRA': 'guiFracPaQ2Dgraphs.m',
    'EXP': 'guiPrint.m', 'AUX': 'Apêndice 15 do inventário',
    'Q': 'docs/parity/divergences.md',
}
FIXTURE = {'UI': 'mixed; negative; scaled', 'IN': 'horizontal; polyline; duplicate; rectangular_cwt',
           'MAP': 'circle_*; angles_flip_*; mixed', 'LEN': 'histogram_centres; mixed; negative',
           'ANG': 'angles_flip_*; matlab_round; histogram_centres',
           'FLO': 'isolated; tee; cross; directional_tensor; isotropic_tensor',
           'WAV': 'morlet_kernel; mexicanhat_kernel; rectangular_cwt',
           'GRA': 'polyline; negative; no_crossing; circle_*',
           'EXP': 'mixed; rectangular_cwt; captura com tag Run1',
           'AUX': 'examples.json; analytic_cases.json', 'Q': 'casos e decisões em divergences.md'}
MODULE = {'UI': 'gui/', 'IN': 'io/, domain/', 'MAP': 'analysis/, plots/',
          'LEN': 'analysis/, plots/', 'ANG': 'compatibility/, analysis/, plots/',
          'FLO': 'geometry/, analysis/, plots/', 'WAV': 'analysis/, plots/',
          'GRA': 'geometry/, analysis/, plots/', 'EXP': 'io/',
          'AUX': 'tools/, compatibility/, plots/', 'Q': 'ver sprint responsável'}
CONTROLS = {
    'UI': ['figure_main', 'text19 axes_icon axes_logo text4', 'edit_filename', 'pushbutton_browse',
           'radiobutton_image radiobutton_node', 'pushbutton_preview', 'axes_tracemap', 'label_stats',
           'pushbutton_flipx pushbutton_flipy', 'pbMapsTab pbLengthsTab pbAnglesTab pbFluidTab pbWaveletsTab pbGraphsTab',
           'pushbutton_run', 'pushbutton_run', 'pushbutton_exit', 'text_message', 'text_message',
           'edit_FilenameTag', 'axes_tracemap', 'text_message', 'uibgTabMaps'],
    'IN': ['radiobutton_node edit_filename', 'pushbutton_preview', 'pushbutton_preview',
           'edit_scaling', 'pushbutton_preview', 'pushbutton_preview', 'pushbutton_preview',
           'pushbutton_preview', 'pushbutton_preview', 'axes_tracemap', 'edit_filename',
           'radiobutton_image', 'pushbutton_preview', 'pushbutton_preview',
           'edit_houghpeaks edit_houghthreshold edit_fillgap edit_minlength',
           'pushbutton_preview', 'pushbutton_preview', 'pushbutton_preview'],
    'MAP': ['checkbox_tracemap', 'checkbox_shownodes', 'checkbox_tracemap', 'checkbox_tracemaplength',
            'checkbox_segmentmaplength', 'checkbox_segmentmapstrike', 'checkbox_intensitymap',
            'checkbox_densitymap', 'checkbox_showcircles edit_numscancircles', 'checkbox_intensitymap',
            'checkbox_sliptendency', 'checkbox_dilationtendency', 'checkbox_fracsuscep', 'checkbox_CSF',
            'edit_sigma1 edit_sigma2 edit_thetasigma1 edit_C0 edit_Pf edit_mu',
            'checkbox_sliptendency', 'checkbox_sliptendency', 'checkbox_intensitymap checkbox_densitymap'],
    'LEN': ['checkbox_histolength', 'checkbox_histolength popupmenu_histolengthbins',
            'checkbox_logloglength', 'checkbox_logloglength', 'checkbox_censor', 'checkbox_crossplot',
            'checkbox_mle', 'checkbox_mle', 'checkbox_mle', 'edit_lc edit_uc', 'checkbox_mle',
            'checkbox_mle', 'checkbox_blocksize', 'checkbox_blocksize', 'checkbox_seglenvariogram', 'checkbox_histolength'],
    'ANG': ['checkbox_histoangle popupmenu_histoanglebins', 'checkbox_rose', 'popupmenu_rosebins',
            'checkbox_roselengthweighted', 'checkbox_showrosemean', 'checkbox_rosecolour',
            'edit_degfromnorth', 'pushbutton_flipx pushbutton_flipy', 'checkbox_rose'],
    'FLO': ['checkbox_triangle', 'edit_numpixelsItoY', 'checkbox_triangle', 'checkbox_triangle',
            'checkbox_triangle', 'edit_numblocksmap', 'checkbox_triangle', 'checkbox_cracktensor',
            'checkbox_permellipse', 'radiobutton_fixedaperture edit_fixedaperture',
            'radiobutton_scaledaperture edit_aperturefactor edit_apertureexponent',
            'edit_lambda', 'checkbox_permellipse'],
    'WAV': ['checkbox_wavelet', 'radiobutton_Morlet radiobutton_Mexican', 'edit_aString',
            'edit_LString', 'edit_DegString', 'checkbox_wavelet', 'checkbox_wavelet',
            'checkbox_wavelet', 'checkbox_wavelet', 'checkbox_wavelet', 'checkbox_wavelet',
            'pushbutton_flipx pushbutton_flipy'],
    'GRA': ['pushbutton_selectgraphendpoints', 'pushbutton_selectgraphendpoints',
            'checkbox_tracelengthgraphalong', 'checkbox_segmentlengthgraphalong',
            'checkbox_segmentstrikegraphalong', 'checkbox_intensitygraphalong',
            'checkbox_densitygraphalong', 'edit_numscancirclesgraph', 'pushbutton_selectgraphendpoints',
            'checkbox_tracelengthgraphfrom', 'checkbox_segmentlengthgraphfrom',
            'checkbox_segmentanglegraphfrom', 'pushbutton_run'],
}
AUX_DISPOSITION = {
    1: 'Complemento CLI', 2: 'Complemento CLI', 3: 'Biblioteca de entrada',
    4: 'Biblioteca geométrica', 5: 'API complementar de variograma', 6: 'API complementar de tensor 16',
    7: 'API histórica/experimentos de rosas', 8: 'Biblioteca de paletas', 9: 'Experimento preservado',
    10: 'Biblioteca de desenho', 11: 'API complementar probePlane',
    12: 'Diálogo complementar Run/Cancel', 13: 'Variantes: portar só dependências do diálogo',
    14: 'Legado 2.2 preservado; fora do entrypoint', 15: 'Demonstrações preservadas; não são testes',
    16: 'Exemplos válidos preparados/auditados; originais preservados',
    17: 'Manual local Python e manual de referência preservado',
    18: 'Instalação, créditos/licenças e referências atualizados',
    19: 'Site histórico preservado; sem hospedagem nem configuração analítica',
}


def outputs_for(key: str, groups: dict[str, list[str]]) -> str:
    """Describe per-feature outputs without inventing new export triggers."""
    prefix, suffix = key.split('-')
    number = int(suffix)
    selected: list[str] = []
    if prefix == 'IN':
        if 5 <= number <= 10:
            return 'nome_converted.txt / nome_colourHHHHHH_converted.txt (junto ao SVG)'
        if number >= 12:
            selected = groups['Diagnóstico Hough']
        else:
            return 'Sem arquivo obrigatório no Preview TXT; saídas das análises selecionadas'
    elif prefix == 'MAP':
        if number <= 6:
            selected = [groups['Mapa básico e cores'][[0, 0, 1, 2, 3, 4][number - 1]]]
        elif number in (7, 8, 9, 18):
            selected = ([groups['P21/P20'][number - 6]] if number in (7, 8)
                        else [groups['P21/P20'][0]] if number == 9 else [])
            return (', '.join(selected) + '{tag}.png; ' if selected else '') + \
                'FracPaQ2Dintensity{tag}.txt + FracPaQ2Ddensity{tag}.txt quando P21 ou P20'
        elif number == 10:
            return 'Console: P21/P20 globais, sem TXT próprio'
        elif number in (11, 12, 13, 14):
            start = 1 + 2 * (number - 11)
            selected = groups['Estabilidade e Mohr'][start:start + 2] + [groups['Estabilidade e Mohr'][0]]
            if number == 11:
                return ', '.join(selected) + '{tag}.png; FracPaQ2Dsegmentdata{tag}.txt'
        elif number == 16:
            selected = [groups['Estabilidade e Mohr'][0]]
        else:
            selected = groups['Estabilidade e Mohr']
    elif prefix == 'LEN':
        if number == 1:
            return 'Console de comprimentos; TXT comuns ao despachar Lengths (RF-09.2)'
        if number == 2:
            selected = groups['Histogramas de comprimento']
        elif number == 3:
            selected = [n for n in groups['Log-log'] if n.endswith('density')]
        elif number == 4:
            selected = [n for n in groups['Log-log'] if not n.endswith('density')]
        elif number == 5:
            return 'Filtra arrays de Lengths conforme decisão Q-05; sem arquivo próprio'
        elif number == 6:
            selected = groups['Cross-plot']
        elif number in (7, 8, 9):
            selected = [n for n in groups['MLE'] if n.endswith(['PowerLaw', 'Exponential', 'LogNormal'][number - 7])]
        elif number in (10, 11, 12):
            selected = groups['MLE']
        elif number in (13, 14):
            return ', '.join(groups['Blocos e variograma'][:3]) + '{tag}.png; FracPaQ2D_blocksize.bmp'
        elif number == 15:
            selected = [groups['Blocos e variograma'][3]]
        else:
            return 'FracPaQ2Dsegmentlengths{tag}.txt; FracPaQ2Dtracelengths{tag}.txt; FracPaQ2Dsegmentangleslengths{tag}.txt'
    elif prefix == 'ANG':
        if number == 1:
            selected = [groups['Ângulos'][1]]
        elif number == 9:
            return 'FracPaQ2DEZROSE{tag}.txt (também por crack tensor)'
        else:
            selected = [groups['Ângulos'][0]]
    elif prefix == 'FLO':
        if number in (1, 2, 3):
            selected = groups['Conectividade']
        elif number == 4:
            selected = [groups['Conectividade'][3]]
        elif number == 5:
            selected = [groups['Conectividade'][0]]
        elif number == 6:
            selected = groups['Conectividade'][1:3]
        elif number == 7:
            return 'FracPaQ2Dconnectivity{tag}.txt; console I/X/Y'
        elif number == 8:
            return 'FracPaQ2D_cracktensor{tag}.png; FracPaQ2DEZROSE{tag}.txt'
        else:
            selected = [groups['Tensores'][0]]
    elif prefix == 'WAV':
        return 'FracPaQ2Dwavelet_a{a}{tag}.png; FracPaQ2Dwavelet_theta_a{a}{tag}.txt; FracPaQ2D_wavelet_traces.png'
    elif prefix == 'GRA':
        if number <= 2 or number == 9:
            selected = [groups['Graphs FROM e mapa'][3]]
        elif number in (3, 4, 5):
            selected = [groups['Graphs ALONG'][number - 3]]
        elif number in (6, 7, 8):
            selected = groups['Graphs ALONG'][3:5] + [groups['Graphs FROM e mapa'][3]]
        elif number in (10, 11, 12):
            selected = [groups['Graphs FROM e mapa'][number - 10]]
        else:
            selected = groups['Graphs ALONG'] + groups['Graphs FROM e mapa']
    elif prefix == 'Q':
        return 'Entrada/saídas da reprodução em divergences.md'
    elif prefix == 'AUX':
        return 'Conforme destinação AUX / apêndice 15; não adicionar saída GUI'
    elif prefix == 'EXP':
        return 'Catálogo RF-09 completo; EXP-05 legado, EXP-06 extensão futura'
    else:
        return 'Sem arquivo próprio; efeitos de seleção conforme RF-09'
    return ', '.join(n + '{tag}.png' for n in selected)


def inventory_rows() -> dict[str, list[str]]:
    rows = {}
    for line in (ROOT / 'docs/planning/FUNCIONALIDADES_FRACPAQ.md').read_text().splitlines():
        match = re.match(r'^\| ((?:UI|IN|MAP|LEN|ANG|FLO|WAV|GRA|EXP|AUX|Q)-\d{2}) \|', line)
        if match:
            key = match[1]
            if key in rows:
                raise ValueError(f'Duplicate ID: {key}')
            rows[key] = [cell.strip() for cell in line.strip('|').split('|')]
    if len(rows) != 164:
        raise ValueError(f'Expected 164 IDs, got {len(rows)}')
    return rows


def main() -> None:
    rows = inventory_rows()
    directory = ROOT / 'docs' / 'parity'
    directory.mkdir(parents=True, exist_ok=True)
    implementation_path = directory / 'implementation.json'
    implementations = (json.loads(implementation_path.read_text())['items']
                       if implementation_path.exists() else {})
    prd = (ROOT / 'docs/planning/PRD.md').read_text()
    figure_section = prd.split('### RF-09.1')[1].split('### RF-09.2')[0]
    figures = []
    groups = {}
    for line in figure_section.splitlines():
        if line.startswith('|') and '`' in line:
            group = line.split('|')[1].strip()
            names = re.findall(r'`([^`]+)`', line)
            groups[group] = names
            for name in names:
                figures.append({'name': name + '{tag}.png', 'group': group,
                                'matlab_png': None, 'matlab_arrays': None,
                                'status': 'Pendente captura MATLAB controlada'})
    data_section = prd.split('### RF-09.2')[1].split('## RF-10')[0]
    data = []
    for line in data_section.splitlines():
        if line.startswith('| `'):
            cells = [c.strip() for c in line.strip('|').split('|')]
            data.append({'name': cells[0].strip('`'), 'trigger': cells[1],
                         'content': cells[2], 'matlab_file': None})
    screens = [{'name': n, 'status': 'Pendente captura MATLAB controlada'}
               for n in ['initial', 'preview', 'Maps', 'Lengths', 'Angles',
                         'Fluid flow', 'Wavelets', 'Graphs']]
    evidence_path = REFERENCE / 'sprint16/evidence-index.json'
    if evidence_path.exists():
        evidence = json.loads(evidence_path.read_text())
        for section, items in [('screens', screens), ('figures', figures),
                               ('data_and_intermediates', data)]:
            for item in items:
                entry = evidence.get(section, {}).get(item['name'])
                if entry:
                    # Availability and acceptance are separate. Validate every
                    # linked capture before regenerating the catalog.
                    for capture in entry.get('native', []) + entry.get('python', []):
                        assert sha256(ROOT / capture['path']) == capture['sha256']
                    item['evidence'] = entry
                    item['status'] = entry['status']
                    native = entry.get('native', [])
                    item['matlab_png' if section != 'data_and_intermediates'
                         else 'matlab_file'] = native[0]['path'] if native else None
    write_json(REFERENCE / 'capture_catalog.json', {
        'schema_version': 1, 'status': 'Paridade não demonstrada',
        'screens': screens,
        'figures': figures, 'data_and_intermediates': data,
        'auxiliary': ['Diálogo wavelet Run/Cancel', 'Pré-processamento: seis etapas',
                      'APIs e experimentos: destinação AUX na matriz'],
    })
    matrix = [
        '# Matriz de paridade — acompanhamento das sprints', '',
        '164 IDs funcionais: 118 GUI + 6 EXP + 19 AUX + 21 Q. A distribuição '
        'também possui 164 arquivos; são contagens diferentes.', '',
        'A coluna Python distingue módulos implementados de destinos planejados. '
        'Os estados implementados vêm de [implementation.json](implementation.json) '
        'e dos relatórios de sprint; os demais caminhos são **destinos planejados**. '
        'Fixtures referem-se a `tests/fixtures/analytic_cases.json` e `tests/reference/examples.json`. '
        'PNGs, TXT e seus gatilhos exatos estão em [capture_catalog.json](../../tests/reference/capture_catalog.json) '
        'e RF-09 do PRD. A [auditoria S16](sprint-16.md) distingue execução funcional, '
        'comparações nativas, diferenças autorizadas e homologação visual ainda aberta.', '',
        '| ID | Recurso / controle ou entrada | Classe / destinação | Fonte MATLAB | Python implementado / planejado | Fixture / cenário | Arquivos esperados | Estado / Q |',
        '| --- | --- | --- | --- | --- | --- | --- | --- |',
    ]
    control_ids = {}
    for prefix, values in CONTROLS.items():
        for number, tags in enumerate(values, 1):
            for tag in tags.split():
                control_ids.setdefault(tag, []).append(f'{prefix}-{number:02d}')
    for key, cells in rows.items():
        prefix, number_text = key.split('-')
        number = int(number_text)
        category = 'GUI obrigatória'
        title = cells[1]
        if prefix in ('AUX', 'EXP', 'Q'):
            title = cells[2]
            category = (AUX_DISPOSITION[number] if prefix == 'AUX' else
                        'Exportação obrigatória' if prefix == 'EXP' and number <= 4 else
                        'Saída de legado' if prefix == 'EXP' and number == 5 else
                        'Extensão futura fora da GUI' if prefix == 'EXP' else 'Questão de paridade')
        tags = CONTROLS.get(prefix, [])
        control = tags[number - 1] if number <= len(tags) else 'entrada/API; ver inventário'
        issues = sorted(set(re.findall(r'Q-\d{2}', ' '.join(cells))))
        status = 'Planejado; paridade pendente'
        if prefix == 'Q':
            status = 'Registrada; decisão pendente na sprint responsável'
        if key in ('AUX-16', 'AUX-18'):
            status = 'Preparação S0 concluída; integração/documentação final pendentes'
        outputs = outputs_for(key, groups)
        fixture = FIXTURE[prefix]
        if prefix == 'IN' and 5 <= number <= 11:
            fixture = 'svg/simple.svg; svg/multicolour.svg; examples.json'
        if prefix == 'IN' and number >= 12:
            fixture = 'images/directional.tif; images/rectangular.tif; images/rgb_invalid.tif'
        implementation = implementations.get(key, {})
        module = implementation.get('python', MODULE[prefix])
        fixture = implementation.get('fixture', fixture)
        status = implementation.get('status', status)
        matrix.append(f'| {key} | {title}<br>`{control}` | {category} | {SOURCE[prefix]} | '
                      f'`{module}` | {fixture} | {outputs} | '
                      f'{status}; {", ".join(issues) or "—"} |')
    (directory / 'matrix.md').write_text('\n'.join(matrix) + '\n')

    fig = json.loads((REFERENCE / 'gui' / 'guiFracPaQ2D.json').read_text())
    objects = {o['tag']: o for o in fig['objects']}

    def ids_for(tag: str) -> list[str]:
        if tag in control_ids:
            return control_ids[tag]
        alternate = tag.replace('label_', 'edit_').replace('text_histo', 'popupmenu_histo')
        if alternate in control_ids:
            return control_ids[alternate]
        node = objects[tag]
        parent = node['parent']
        return ids_for(parent) if parent else ['UI-02']

    controls = ['# Controles e grupos do FIG', '',
                'Todos os objetos com Tag estão relacionados abaixo. Propriedades completas, callbacks, '
                'hierarquia e posições: [JSON principal](../../tests/reference/gui/guiFracPaQ2D.json). '
                'Associação a IDs é rastreabilidade de referência, não cobertura Qt implementada. '
                'Propriedades ausentes no arquivo dependem dos defaults MATLAB; confirmar em captura real.', '',
                '| Tag / objectName futuro | Tipo | Grupo pai | IDs relacionados |',
                '| --- | --- | --- | --- |']
    for obj in fig['objects']:
        if obj['tag'].startswith('untagged_'):
            continue
        controls.append(f'| `{obj["tag"]}` | {obj["saved_properties"].get("Style", obj["type"])} | '
                        f'`{obj["parent"]}` | {", ".join(ids_for(obj["tag"]))} |')
    (directory / 'controls.md').write_text('\n'.join(controls) + '\n')

    code = []
    names = {p.stem for p in ORIGINAL.glob('*.m')}
    for path in sorted(ORIGINAL.glob('*.m')):
        try:
            text = path.read_text(encoding='utf-8')
            encoding = 'utf-8'
        except UnicodeDecodeError:
            text = path.read_text(encoding='latin-1')
            encoding = 'latin-1'
        code.append({'path': str(path.relative_to(ROOT)), 'sha256': sha256(path),
                     'decoding': encoding,
                     'lines': len(text.splitlines()),
                     'functions': [line.strip() for line in text.splitlines()
                                   if re.match(r'^\s*function\b', line)],
                     'local_call_candidates': sorted(set(re.findall(r'\b(\w+)\s*\(',
                                                                    re.sub(r'%[^\n]*', '', text))) & names),
                     'export_statements': [line.strip() for line in text.splitlines()
                                           if re.search(r'\b(guiPrint|fprintf|imwrite|print)\s*\(', line)
                                           and not line.lstrip().startswith('%')]})
    write_json(REFERENCE / 'source_catalog.json', code)
    print(f'{len(rows)} IDs, {len(controls) - 6} linhas de controles; '
          f'{len(figures)} nomes de figuras; {len(code)} fontes MATLAB.')


if __name__ == '__main__':
    main()
