"""Consolidate unmodified-RGB comparison evidence, without declaring acceptance."""

import gc
import json
import platform

import matplotlib
import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity

from audit_sprint16 import integrity
from reference_common import ROOT,REFERENCE,sha256,write_json

FOLDER=REFERENCE/'sprint16/final'


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
    records=main+additional
    failures=[{'figure':r['name'],**s} for r in records for s in r['regions'] if s['passed'] is False]
    write_json(FOLDER/'status.json',{
        'S16-04_complete':False,'S16-09_complete':False,
        'scope':'Evidence only. Final semantic partitions/review and all comparable visual gates are required for acceptance.',
        'primary_figures':len(main),'primary_figures_passing_current_regions':sum(r['comparable_regions_pass'] is True for r in main),
        'primary_figures_without_comparable_regions':sum(r['comparable_regions_pass'] is None for r in main),
        'additional_figures':len(additional),'additional_figures_passing_current_regions':sum(r['comparable_regions_pass'] is True for r in additional),
        'failed_comparable_regions':failures,'threshold':.98,
        'numeric_checks':len(numeric['comparisons']),'numeric_passed':sum(c['passed'] for c in numeric['comparisons']),
        'txt_byte_exact':all(f['bytes_exact'] for f in numeric['files']),
        'original_files_verified':len(sources),'preexisting_outputs_verified':len(extras),
        'python':platform.python_version(),'matplotlib':matplotlib.__version__,
        'production_modules':{str(p.relative_to(ROOT)):sha256(p) for p in sorted((ROOT/'pyfracpaq').rglob('*.py'))},
        'resources':{str(p.relative_to(ROOT)):sha256(p) for p in sorted((ROOT/'pyfracpaq/resources').glob('*')) if p.is_file()},
        'comparison_files':{p.name:sha256(p) for p in [FOLDER/'regions-native.json',FOLDER/'region-comparison.json',FOLDER/'additional-region-comparison.json',FOLDER/'numeric-comparison.json',FOLDER/'wavelet-context-comparison.json']}})
    print('Current failures:',len(failures),'; S16-04 remains open.',flush=True)


if __name__=='__main__':main()
