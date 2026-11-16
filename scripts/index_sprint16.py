"""Index genuine audit evidence, all output templates, and all functional IDs."""

import json
from pathlib import Path
import re

from build_parity_index import CONTROLS, inventory_rows
from reference_common import ROOT, REFERENCE, sha256, write_json

FOLDER=REFERENCE/'sprint16'

TESTS={
 'UI':['gui/test_main_window.py','gui/test_reference_layout.py','gui/test_entrypoints.py'],
 'IN':['numerical/test_nodes.py','numerical/test_svg.py','numerical/test_hough.py','numerical/test_sprint16_hough.py','gui/test_main_window.py'],
 'MAP':['numerical/test_angles.py','numerical/test_circular.py','numerical/test_stability.py','visual/test_sprint3_figures.py','visual/test_sprint7_figures.py','gui/test_sprint1011_run.py'],
 'LEN':['numerical/test_lengths.py','numerical/test_mle.py','numerical/test_blocks.py','numerical/test_variogram.py','visual/test_sprint4_figures.py','gui/test_sprint89_run.py','gui/test_sprint1213_run.py'],
 'ANG':['numerical/test_angles.py','visual/test_sprint3_figures.py','gui/test_main_window.py'],
 'FLO':['numerical/test_connectivity.py','numerical/test_tensors.py','gui/test_sprint89_run.py','gui/test_sprint1011_run.py'],
 'WAV':['numerical/test_wavelets.py','visual/test_wavelet_figures.py','gui/test_sprint1415_run.py'],
 'GRA':['numerical/test_profiles.py','visual/test_sprint1213_figures.py','gui/test_sprint1213_run.py'],
 'EXP':['numerical/test_execution_contract.py','numerical/test_lengths.py','numerical/test_svg.py','numerical/test_blocks.py','numerical/test_wavelets.py'],
 'AUX':['numerical/test_auxiliary.py','gui/test_sprint1415_run.py','reference/test_sprint1415_reference.py']}


def file_record(path):
 return {'path':str(path.relative_to(ROOT)),'sha256':sha256(path)}


def evidence_index():
 catalog=json.loads((REFERENCE/'capture_catalog.json').read_text())
 native=[p for p in REFERENCE.glob('sprint*/native/**/*.png') if p.is_file()]
 native_txt=[p for p in REFERENCE.glob('sprint*/native/**/*') if p.is_file()]
 candidates=[p for p in (FOLDER/'all-outputs').iterdir() if p.is_file()]
 candidates.extend((FOLDER/'candidate').glob('FracPaQ2D_Houghstuff*.png'))
 # SVG conversion, all three colour groups and the auxiliary untagged theta
 # already have actual outputs; keep their original provenance.
 data_candidates=candidates+[p for s in ('sprint5','sprint15') for p in (REFERENCE/s).rglob('*')
                             if p.is_file() and 'native' not in p.parts]
 data_candidates.extend((FOLDER/'auxiliary').glob('*'))
 index={'screens':{},'figures':{},'data_and_intermediates':{}}
 for section,source,python in [('figures',native,candidates),('data_and_intermediates',native_txt,data_candidates)]:
  for item in catalog[section]:
   name=item['name']
   # PRD templates use {tag} for a suffix including the underscore.
   expression=re.escape(name)
   for key in ('tag','a','nome','HHHHHH'):
    expression=expression.replace(re.escape('{'+key+'}'),'.*')
   if name.startswith('nome'):
    expression=expression.replace('nome','.*').replace('HHHHHH','[0-9A-Fa-f]{6}')
   matched=[p for p in source if re.fullmatch(expression,p.name)]
   produced=[p for p in python if re.fullmatch(expression,p.name)]
   index[section][name]={'native': [file_record(p) for p in sorted(matched)],
                       'python':[file_record(p) for p in sorted(produced)],
                       'status':'Captura disponível; homologação numérica/visual por contexto permanece independente.' if matched else 'Pendente captura MATLAB controlada'}
 for label,suffix in [('initial','initial'),('preview','preview'),('Maps','maps'),('Lengths','lengths'),
                      ('Angles','angles'),('Fluid flow','fluid'),('Wavelets','wavelets'),('Graphs','graphs')]:
  path=FOLDER/'native/details'/('gui_'+suffix+'.png')
  index['screens'][label]={'native':[file_record(path)],'geometry':file_record(path.with_suffix('.mat')),
                           'status':'Captura MATLAB por print e propriedades em pixels; comparação desktop/DPI pendente.'}
 write_json(FOLDER/'evidence-index.json',index)
 missing=[k for k,v in index['figures'].items() if not v['python']]
 write_json(FOLDER/'output-contract.json',{'png_templates':len(index['figures']),
   'png_templates_executed':len(index['figures'])-len(missing),'missing_python_png':missing,
   'data_templates':index['data_and_intermediates'],
   'scope':'Names/triggers covered by real production outputs plus shared exporter tests. '
           'No equality of scientific corrections or pixel acceptance inferred from name matches.'})


def matrix():
 implementation_path=ROOT/'docs/parity/implementation.json'
 implementation=json.loads(implementation_path.read_text())
 ledger=[]
 questions=(ROOT/'docs/parity/divergences.md').read_text()
 for key,cells in inventory_rows().items():
  prefix,number=key.split('-');i=int(number)
  old=implementation['items'].get(key,{})
  if prefix=='Q':
   block=re.search(r'^## '+key+r' .*?(?=^## Q-|\Z)',questions,re.M|re.S)[0]
   decision=next(l[2:] for l in block.splitlines() if l.startswith('- Estado:'))
   evidence=['docs/parity/divergences.md']
   status=decision
  else:
   evidence=['tests/'+p for p in TESTS[prefix]]
   assert all((ROOT/p).is_file() for p in evidence)
   if prefix=='AUX':
    evidence.append('docs/parity/legacy.md')
    status='Destinação auditada na S16; biblioteca/ferramenta ou legado explicitamente classificado, sem novos controles GUI.'
   elif key in ('EXP-05','EXP-06'):
    status='Destinação auditada: legado/extensão fora da GUI2.8; nenhuma saída obrigatória omitida por isso.'
   else:
    evidence.append('tests/reference/sprint16/all-outputs/validation.json')
    status='S16: implementação/integração auditadas; 30 rotas disponíveis. Paridade numérica, visual e de arquivos avaliadas separadamente; sem homologação visual geral.'
  implementation['items'][key]={**old,'python':old.get('python', 'docs/parity/legacy.md' if prefix=='AUX' else 'pyfracpaq/'),
      'status':status,'fixture':'; '.join(evidence),
      'audit':'tests/reference/sprint16/functional-matrix.json'}
  ledger.append({'id':key,'controls':CONTROLS.get(prefix,['']*max(i,1))[i-1].split(),
       'evidence':evidence,'status':status,'functional':'audited' if prefix!='Q' else 'decision reviewed',
       'numeric':'See family reports and accepted Q differences',
       'visual':'Not homologated across all contexts','files':'See output-contract.json; schema/order/atomicity regression suite'})
 write_json(implementation_path,implementation)
 write_json(FOLDER/'functional-matrix.json',{'ids':len(ledger),'gui_ids':118,'export_ids':6,'aux_ids':19,'questions':21,
    'method':'Source/control mapping review + complete regression suite + all30 production compute/render routes. '
             'Grouped test evidence is shared, not a claim of one independent test per functional ID.',
    'items':ledger})


if __name__=='__main__':evidence_index();matrix()
