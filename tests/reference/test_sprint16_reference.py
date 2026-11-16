"""Audit provenance and delivery evidence; capture presence is not visual acceptance."""

import json

from build_parity_index import inventory_rows
from pyfracpaq import __version__
from pyfracpaq.analysis import AnalysisRegistry
from reference_common import REFERENCE, ROOT, sha256

FOLDER=REFERENCE/'sprint16'


def read(name):return json.loads((FOLDER/name).read_text())


def test_sprint16_matrix_covers_all_ids_and_production_routes():
    ledger=read('functional-matrix.json')
    assert {item['id'] for item in ledger['items']}==inventory_rows().keys()
    assert len(ledger['items'])==164 and ledger['gui_ids']==118
    production=read('all-outputs/validation.json')
    specs=AnalysisRegistry().specs
    assert len(specs)==30 and all(s.available and s.render for s in specs)
    assert production['analysis_ids']==[s.id for s in specs]
    assert len(production['figures'])==52
    assert production['mle_root_seed']>0
    for item in ledger['items']:
        for path in item['evidence']:assert (ROOT/path).is_file()


def test_all_capture_templates_have_separate_authentic_evidence():
    index=read('evidence-index.json')
    assert len(index['figures'])==53 and len(index['data_and_intermediates'])==14
    for section in ('figures','data_and_intermediates'):
        for entry in index[section].values():
            assert entry['native'] and entry['python']
            for implementation,records in ((True,entry['python']),(False,entry['native'])):
                for record in records:
                    path=ROOT/record['path']
                    assert sha256(path)==record['sha256']
                    assert ('native' not in path.parts) if implementation else ('native' in path.parts)
    provenance=read('native_provenance.json')
    for path,digest in provenance['scripts'].items():assert sha256(ROOT/path)==digest
    for capture in provenance['outputs']:assert sha256(ROOT/capture['path'])==capture['sha256']


def test_local_install_uses_installed_wheel_with_network_denied():
    result=read('clean-install.json')
    assert {r['mode'] for r in result['entrypoints']}=={'script','module'}
    for record in result['entrypoints']:
        assert record['exit_code']==0 and record['version']==__version__
        assert 'site-packages' in record['module']
        assert record['network']=='socket connect/DNS denied'
        assert record['readers']==['TXT','SVG','Hough']
        assert 'MAIN_WINDOW_OBSERVED' in record['stdout']


def test_current_dpi_captures_have_no_text_fit_violations():
    for scale in (100,125,150,200):
        manifest=read(f'gui/dpi-{scale}/manifest.json')
        assert len(manifest['captures'])==8
        assert manifest['text_fit_violations']==[]
        assert manifest['font']=='Helvetica'
        for capture in manifest['captures']:
            assert sha256(FOLDER/f'gui/dpi-{scale}'/capture['path'])==capture['sha256']
