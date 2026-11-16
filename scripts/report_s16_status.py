"""Consolidate evidence and require every closure gate, including user decisions."""

import gc
import json
import platform
import xml.etree.ElementTree as ET

import matplotlib
import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity

from audit_sprint16 import integrity
from reference_common import ROOT,REFERENCE,sha256,write_json

FOLDER=REFERENCE/'sprint16/final'


def visual_acceptances(records,decisions):
    """Accept only identified regions of the exact reviewed image pair."""
    current={}
    for record in records:
        for region in record['regions']:
            current[(record['name'],region['name'])]=(record,region)
    accepted=[]
    for decision in decisions.get('accepted_regions',[]):
        pair=current.get((decision['figure'],decision['region']))
        if pair is None:continue
        record,region=pair
        if not all(record[k]==decision[k] for k in ('native_sha256','candidate_sha256')):continue
        if 'xyxy' in decision and decision['xyxy']!=region['xyxy']:continue
        accepted.append(decision)
    keys={(r['figure'],r['region']) for r in accepted}
    pending=[{'figure':r['name'],**s} for r in records for s in r['regions']
             if s['passed'] is False and (r['name'],s['name']) not in keys]
    return accepted,pending


def junit_passed(path,count):
    root=ET.parse(path).getroot()
    suites=[root] if root.tag=='testsuite' else list(root.findall('testsuite'))
    return (sum(int(s.get('tests',0)) for s in suites)==count
            and all(int(s.get(k,0))==0 for s in suites for k in ('failures','errors','skipped')))


def authorized_marker_propagation(records,accepted,decisions,proof,implementation):
    """Resolve only proved consequences of the explicitly requested global style.

    These are technical dispositions, never additional claimed user approvals.
    Raw SSIM and the frozen full comparison regions remain unchanged.
    """
    if not proof or not proof.get('passed') or proof.get('implementation')!=implementation:return []
    if {r.get('detail_case') for r in accepted if r.get('detail_case')}!=set(range(1,17)):return []
    instruction=decisions.get('renderer_change_authorized',{}).get('user_statement')
    if not instruction or instruction!=proof.get('authorized_global_instruction'):return []
    allowed={('FracPaQ2D_tracemap_SD11A.png','plot'),
             ('guiFracPaQ2D_intensityalonggraph_SD11A.png','title'),
             ('guiFracPaQ2D_densityalonggraph_SD11A.png','title')}
    current={(r['name'],s['name']):(r,s) for r in records for s in r['regions']}
    resolved=[]
    for item in proof['records']:
        key=(item['figure'],item['region'])
        if key not in allowed or key not in current:continue
        record,region=current[key]
        if not item.get('passed') or not item.get('prior_gate_satisfied'):continue
        if item.get('changed_pixels_outside_marker_footprints')!=0:continue
        if item['xyxy']!=region['xyxy']:continue
        if not all(item[k]==record[k] for k in ('native_sha256','candidate_sha256')):continue
        resolved.append({**item,'basis':'Verified propagation of explicitly authorized global geometric markers; not a new visual approval.'})
    return resolved


def comparisons():
    target=FOLDER/'additional-region-comparison.json'
    previous={r['name']:r for r in json.loads(target.read_text())} if target.exists() else {}
    definitions=[
        ('binary_panel',[0,0,1870,2362],None),
        ('binary_colourbar',[1870,0,2362,2362],'user_colourbar_geometry'),
        ('coefficient_panel',[2362,0,3945,2362],None),
        ('coefficient_colourbar',[3945,0,4724,2362],'user_colourbar_geometry'),
        ('rose_panel',[0,2362,2362,4724],None),
        ('histogram_panel',[2362,2362,4724,4724],None)]
    pairs=[]
    for kernel in ('morlet','mexican'):
        for scale in (16,32):
            name=f'FracPaQ2Dwavelet_a{scale}_context.png'
            pairs.append((f'shared-native-pixels/{kernel}/{name}',
                          FOLDER/'native-contexts'/kernel/name,
                          FOLDER/'shared-native-pixels'/kernel/name,definitions))
    name='FracPaQ2D_Houghstuff_extra.png'
    pairs.append((name,FOLDER/'native-extra'/name,FOLDER/'python-extra'/name,[
        ('raw_panel',[0,0,2362,2362],None),('rho_panel',[2362,0,4724,2362],None),
        ('plan_panel',[0,2362,2362,4724],None),('theta_panel',[2362,2362,4724,4724],None)]))
    name='FracPaQ2D_tracemap_multicolour_extra.png'
    native=FOLDER/'native-extra'/name
    from audit_s16_figures import define_regions
    with Image.open(native) as im:regions=define_regions(name,np.array(im.convert('RGB')))
    pairs.append((name,native,FOLDER/'python-extra'/name,regions))
    records=[]
    for name,native,candidate,regions in pairs:
        geometry=[{'name':n,'xyxy':b,'exception':e} for n,b,e in regions]
        nh,ch=sha256(native),sha256(candidate);old=previous.get(name)
        if old and old['native_sha256']==nh and old['candidate_sha256']==ch and old['definitions']==geometry:
            records.append(old);continue
        with Image.open(native) as im:a=np.array(im.convert('RGB'))
        with Image.open(candidate) as im:b=np.array(im.convert('RGB'))
        assert a.shape==b.shape
        coverage=np.zeros(a.shape[:2],dtype=np.uint8);scores=[]
        for region in geometry:
            x0,y0,x1,y1=region['xyxy'];coverage[y0:y1,x0:x1]+=1
            score=float(structural_similarity(a[y0:y1,x0:x1],b[y0:y1,x0:x1],channel_axis=2,data_range=255))
            scores.append({**region,'ssim_rgb':score,'threshold':.98,
                           'passed':score>=.98 if region['exception'] is None else None})
        assert np.all(coverage==1),name
        records.append({'name':name,'native_sha256':nh,'candidate_sha256':ch,
                        'native':str(native.relative_to(ROOT)),'candidate':str(candidate.relative_to(ROOT)),
                        'definitions':geometry,'regions':scores,
                        'comparable_regions_pass':all(s['passed'] for s in scores if s['passed'] is not None)})
        write_json(target,records);print(name,[(s['name'],round(s['ssim_rgb'],6)) for s in scores if s['passed'] is False],flush=True)
        del a,b;gc.collect()
    write_json(target,records)
    return records


def main():
    additional=comparisons()
    main=json.loads((FOLDER/'region-comparison.json').read_text())
    sources,extras=integrity()
    numeric=json.loads((FOLDER/'numeric-comparison.json').read_text())
    details=json.loads((FOLDER/'detail-region-comparison.json').read_text())
    semantics=json.loads((FOLDER/'semantic-comparison.json').read_text())
    review=json.loads((FOLDER/'semantic-review.json').read_text())
    records=main+additional
    failures=[{'figure':r['name'],**s} for r in records for s in r['regions'] if s['passed'] is False]
    decision_path=FOLDER/'user-visual-acceptance.json'
    decisions=json.loads(decision_path.read_text()) if decision_path.exists() else {}
    accepted,pending=visual_acceptances(records+details['records'],decisions)
    production={str(p.relative_to(ROOT)):sha256(p) for p in sorted((ROOT/'pyfracpaq').rglob('*.py'))}
    proof_path=FOLDER/'marker-propagation-proof.json'
    proof=json.loads(proof_path.read_text()) if proof_path.exists() else None
    propagated=authorized_marker_propagation(records,accepted,decisions,proof,production)
    propagated_keys={(r['figure'],r['region']) for r in propagated}
    pending=[r for r in pending if (r['figure'],r['name']) not in propagated_keys]
    resources={str(p.relative_to(ROOT)):sha256(p) for p in sorted((ROOT/'pyfracpaq/resources').glob('*')) if p.is_file()}
    numerical_dispositions={c['name']:c.get('approved_difference') for c in numeric['comparisons'] if not c['passed']}
    for name in ('geometry.trace_midpoints','graphs.figure6.graphs_trace_distances'):
        if name in numerical_dispositions:numerical_dispositions[name]='S01-04/Q07: centres at half the accumulated polyline length, propagated to FROM distances; ADR0002/0004/0015.'
    wavelets=json.loads((FOLDER/'wavelet-context-comparison.json').read_text())
    regression=review['regression_basis'].get('current_full_suite','tests/reference/sprint16/final/checks.json')
    checks=json.loads((ROOT/regression).read_text())
    # Reports may be moved with the repository; the companion XML is local.
    regression_xml=(ROOT/regression).with_suffix('.xml')
    regression_count=review['regression_basis'].get('current_full_suite_passed',709)
    semantic_names={r['figure'] for r in semantics['records']}
    detail_regions=[s for r in details['records'] for s in r['regions']]
    image_hashes_current=all(sha256(ROOT/path)==digest for path,digest in review['reviewed_images'].items())
    image_hashes_current &= all(
        sha256(FOLDER/'python'/r['name'])==r['candidate_sha256'] and
        sha256(REFERENCE/'sprint16/sd11a/native'/r['name'])==r['native_sha256'] for r in main)
    image_hashes_current &= all(sha256(ROOT/r[k])==r[k+'_sha256'] for r in additional for k in ('native','candidate'))
    semantic_hashes_current=all(
        sha256(FOLDER/'python'/r['figure'])==r['candidate_sha256'] and
        sha256(REFERENCE/'sprint16/sd11a/native'/r['figure'])==r['native_sha256'] and
        sha256(ROOT/r['native_metadata'])==r['native_metadata_sha256'] for r in semantics['records'])
    primary_by_name={r['name']:r for r in main}
    detail_hashes_current=all(all(r[k]==primary_by_name[r['name']][k] for k in ('native_sha256','candidate_sha256')) for r in details['records'])
    hough=json.loads((REFERENCE/'sprint16/hough_comparison.json').read_text())
    svg=json.loads((FOLDER/'python-extra/multicolour-data.json').read_text())
    gates={
        'paired_primary_and_additional_coverage':len(main)==51 and len(additional)==6,
        'semantic_review':len(semantic_names)==51 and semantic_names=={r['name'] for r in main} and not semantics['issues'] and review['completed'],
        'independent_legend_annotation_coverage':len(details['records'])==10 and len(detail_regions)==16 and sum(s['name']=='legend' for s in detail_regions)==10,
        'visual_comparisons_or_explicit_user_acceptance':not pending,
        'numerical_comparisons_or_documented_decisions':len(numeric['comparisons'])==81 and len(numerical_dispositions)==7 and all(numerical_dispositions.values()),
        'txt_byte_exact':len(numeric['files'])==4 and all(f['bytes_exact'] for f in numeric['files']),
        'shared_pixel_wavelet_contexts':len(wavelets)==2 and all(len(k['comparisons'])==2 and all(all(c[key] for key in ('coefficients_pass','selection_exact','doubled_angles_exact','histogram_centres_pass','histogram_log_counts_pass')) for c in k['comparisons']) for k in wavelets),
        'hough_and_svg_numeric_controls':len(hough)==5 and all(all(r['exact_checks'].values()) for r in hough) and len(svg)==6 and all(all(r[k] for k in ('nodes_exact','colour_exact','lengths_match','angles_match')) for r in svg),
        'original_files_preserved':len(sources)==164 and len(extras)==8,
        'evidence_matches_reviewed_images_and_code':bool(image_hashes_current and semantic_hashes_current and detail_hashes_current and semantics['implementation']==production and review['production_modules']==production and review['resources']==resources),
        'recorded_regressions_pass':checks['exit_code']==0 and sha256(regression_xml)==checks['junit_sha256'] and junit_passed(regression_xml,regression_count) and checks.get('production_modules',production)==production and checks.get('resources',resources)==resources and junit_passed(FOLDER/'renderer-contracts.xml',5) and junit_passed(FOLDER/'audit-contracts.xml',5) and (not proof or junit_passed(FOLDER/'acceptance-contracts.xml',7)),
    }
    complete=all(gates.values())
    write_json(FOLDER/'status.json',{
        'S16-04_complete':complete,'S16-09_complete':False,'closure_gates':gates,
        'scope':'S16-04 evidence for the captured native contexts and documented scientific decisions. S16-09 release/screens remain separate; raw SSIM failures are retained.',
        'primary_figures':len(main),'primary_figures_passing_current_regions':sum(r['comparable_regions_pass'] is True for r in main),
        'primary_figures_without_comparable_regions':sum(r['comparable_regions_pass'] is None for r in main),
        'additional_figures':len(additional),'additional_figures_passing_current_regions':sum(r['comparable_regions_pass'] is True for r in additional),
        'failed_comparable_regions':failures,'threshold':.98,
        'independent_detail_figures':len(details['records']),'independent_detail_regions':len(detail_regions),
        'failed_independent_detail_regions':[{'figure':r['name'],**s} for r in details['records'] for s in r['regions'] if s['passed'] is False],
        'semantic_figures':len(semantic_names),'semantic_issues':semantics['issues'],
        'current_regression_report':regression,'current_regression_test_count':regression_count,
        'numerical_difference_dispositions':numerical_dispositions,
        'user_accepted_visual_regions':accepted,
        'authorized_marker_propagation_regions':propagated,
        'marker_propagation_proof_sha256':sha256(proof_path) if proof_path.exists() else None,
        'pending_visual_regions_after_user_acceptance':pending,
        'visual_acceptance_record_sha256':sha256(decision_path) if decision_path.exists() else None,
        'numeric_checks':len(numeric['comparisons']),'numeric_passed':sum(c['passed'] for c in numeric['comparisons']),
        'txt_byte_exact':all(f['bytes_exact'] for f in numeric['files']),
        'original_files_verified':len(sources),'preexisting_outputs_verified':len(extras),
        'python':platform.python_version(),'matplotlib':matplotlib.__version__,
        'production_modules':production,'resources':resources,
        'comparison_files':{str(p.relative_to(ROOT)):sha256(p) for p in [FOLDER/name for name in ('regions-native.json','region-comparison.json','additional-region-comparison.json','numeric-comparison.json','wavelet-context-comparison.json','detail-region-comparison.json','semantic-comparison.json','semantic-review.json','python-extra/multicolour-data.json','checks.json','checks.xml','renderer-contracts.xml','audit-contracts.xml')]+[ROOT/regression,regression_xml,REFERENCE/'sprint16/hough_comparison.json']+([proof_path,FOLDER/'acceptance-contracts.xml'] if proof else [])}})
    print('Raw SSIM failures:',len(failures),'; user-accepted regions:',len(accepted),
          '; pending regions:',len(pending),'; S16-04 complete:',complete,'; gates:',gates,flush=True)


if __name__=='__main__':main()
