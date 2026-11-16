"""Native-defined, disjoint figure regions and unmodified RGB SSIM evidence.

Freeze regions from the native PNG alone before comparing the candidate.
Scientific/layout exceptions retain both their raw scores and their reason;
they never turn a failed comparable region into a pass.
"""

import argparse
import gc
import json

import numpy as np
from PIL import Image
from scipy.ndimage import label
from skimage.metrics import structural_similarity

from reference_common import ROOT,REFERENCE,sha256,write_json

FOLDER=REFERENCE/'sprint16/final'
NATIVE=REFERENCE/'sprint16/sd11a/native'


def row_groups(image):
    grey=(image.max(axis=2)-image.min(axis=2)<=1)&(image[:,:,0]>=37)&(image[:,:,0]<=39)
    scores=grey.sum(axis=1)
    components,n=label(scores>max(300,float(scores.max())*.7))
    rows=[np.flatnonzero(components==i) for i in range(1,n+1)]
    return grey,rows


def define_regions(name,image):
    height,width=image.shape[:2];grey,rows=row_groups(image)
    if 'wavelet_a' in name:
        # Positions inspected in the native four-panel capture. Vertical bar
        # containers deliberately retain their user-approved layout override.
        return [
            ('binary_panel',[0,0,1870,2362],'Q12_production_raster'),
            ('binary_colourbar',[1870,0,2362,2362],'user_colourbar_geometry'),
            ('coefficient_panel',[2362,0,3945,2362],'Q12_production_raster'),
            ('coefficient_colourbar',[3945,0,width,2362],'user_colourbar_geometry'),
            ('rose_panel',[0,2362,2362,height],'Q12_production_raster'),
            ('histogram_panel',[2362,2362,width,height],'Q12_production_raster')]
    if 'rose' in name:
        boundary=int(rows[-2][0])-2 if len(rows)>=2 else height
        return [('rose_title_and_annotations',[0,0,width,boundary],None),
                ('colourbar_container',[0,boundary,width,height],'user_colourbar_geometry')]
    if 'polar' in name or 'cracktensor' in name:
        if 'cracktensor' in name:
            return [('polar_plot_and_rulers',[0,0,width,4300],None),
                    ('legend_container',[0,4300,width,height],None)]
        return [('polar_plot_title_and_rulers',[0,0,width,height],None)]
    if 'IYXtriangle' in name:
        return [('ternary_plot_title_and_annotations',[0,0,width,height],'Q11_topology')]
    if len(rows)<2:raise ValueError(f'No independent native frame: {name}')
    top=int(rows[0][0])-2;bottom=int(rows[1][-1])+3
    edge_x=np.flatnonzero(grey[rows[0][len(rows[0])//2]])
    left=max(0,int(edge_x.min())-2);right=min(width,int(edge_x.max())+3)
    data_exception=None
    if any(s in name for s in ('blocksize','IYXnodes','XYnodes','Inodes')):
        data_exception='Q14_blocks' if 'blocksize' in name else 'Q11_topology'
    elif any(s in name for s in ('intensityP21','intensityalong','densityalong')):
        data_exception='Q20_finite_circles'
    elif 'segmentlengthsFittingLogNormal' in name:data_exception='Q15_fitted_tail'
    elif 'tracelengthfrom' in name:data_exception='Q07_halfway_centres'
    regions=[('title',[0,0,width,top],data_exception if data_exception in ('Q14_blocks','Q11_topology') else None),
             ('plot',[left,top,right,bottom],data_exception),
             ('left_ruler',[0,top,left,bottom],
              data_exception if data_exception=='Q14_blocks' or 'densityalong' in name else None),
             ('right_ruler',[right,top,width,bottom],None)]
    if len(rows)>=4:
        boundary=int(rows[2][0])-4
        regions.extend([('x_ruler',[0,bottom,width,boundary],None),
                        ('colourbar_container',[0,boundary,width,height],'user_colourbar_geometry')])
    else:
        regions.append(('x_ruler_and_footer',[0,bottom,width,height],data_exception if data_exception=='Q14_blocks' else None))
    return regions


def freeze():
    records=[]
    names=[r['path'] for r in json.loads((FOLDER/'python/validation.json').read_text())]
    for name in names:
        path=NATIVE/name
        with Image.open(path) as im:image=np.array(im.convert('RGB'))
        regions=define_regions(name,image)
        # Coverage/disjointness includes whitespace and approved exceptions.
        coverage=np.zeros(image.shape[:2],dtype=np.uint8)
        for _,(x0,y0,x1,y1),_ in regions:
            assert 0<=x0<x1<=image.shape[1] and 0<=y0<y1<=image.shape[0],name
            coverage[y0:y1,x0:x1]+=1
        assert np.all(coverage==1),name
        records.append({'name':name,'native_sha256':sha256(path),
                        'regions':[{'name':r,'xyxy':box,'exception':exc} for r,box,exc in regions]})
    write_json(FOLDER/'regions-native.json',{'method':'Native PNG frames plus explicit native panel/legend containers. '
               'All regions are disjoint and cover the complete canvas; candidate pixels do not define regions.',
               'records':records})
    print('Frozen native regions for',len(records),'figures.',flush=True)


def compare():
    definitions=json.loads((FOLDER/'regions-native.json').read_text())
    previous=FOLDER/'region-comparison.json'
    prior={r['name']:r for r in json.loads(previous.read_text())} if previous.exists() else {}
    records=[]
    for entry in definitions['records']:
        name=entry['name'];native=NATIVE/name;candidate=FOLDER/'python'/name
        assert sha256(native)==entry['native_sha256']
        candidate_hash=sha256(candidate)
        old=prior.get(name)
        if old and old['native_sha256']==entry['native_sha256'] and old['candidate_sha256']==candidate_hash and old['definitions_sha256']==sha256(FOLDER/'regions-native.json'):
            comparable=[r for r in old['regions'] if r['passed'] is not None]
            old['comparable_region_count']=len(comparable)
            old['comparable_regions_pass']=all(r['passed'] for r in comparable) if comparable else None
            records.append(old);continue
        with Image.open(native) as im:a=np.array(im.convert('RGB'))
        with Image.open(candidate) as im:b=np.array(im.convert('RGB'))
        assert a.shape==b.shape
        comparisons=[]
        for region in entry['regions']:
            x0,y0,x1,y1=region['xyxy']
            score=float(structural_similarity(a[y0:y1,x0:x1],b[y0:y1,x0:x1],channel_axis=2,data_range=255))
            comparisons.append({**region,'ssim_rgb':score,'threshold':.98,
                                'passed':score>=.98 if region['exception'] is None else None})
        comparable=[r for r in comparisons if r['passed'] is not None]
        record={'name':name,'native_sha256':entry['native_sha256'],'candidate_sha256':candidate_hash,
                'definitions_sha256':sha256(FOLDER/'regions-native.json'),'regions':comparisons,
                'comparable_region_count':len(comparable),
                'comparable_regions_pass':all(r['passed'] for r in comparable) if comparable else None}
        records.append(record);write_json(previous,records)
        print(name,[(r['name'],round(r['ssim_rgb'],5)) for r in comparisons if r['passed'] is False],flush=True)
        del a,b;gc.collect()
    write_json(previous,records)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('phase',choices=('freeze','compare'))
    phase=parser.parse_args().phase
    freeze() if phase=='freeze' else compare()
