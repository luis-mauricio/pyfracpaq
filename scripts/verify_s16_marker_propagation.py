"""Attribute remaining marker-update pixels without altering SSIM or its ROIs.

The original map passed its RGB gate; the two Graphs title bands were already
accepted. Check that their later changes are entirely inside live marker
footprints from the globally requested standard-geometry replacement.
"""

import gc
import hashlib
from io import BytesIO
import json
import pickle
import subprocess

import numpy as np
from PIL import Image
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.transforms import Affine2D

from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.io.figures import PRINT_DPI,PRINT_SIZE_INCHES
from compare_sd11a import configuration,SOURCE
from finish_s16 import CACHE,manifest
from reference_common import ROOT,REFERENCE,sha256,write_json

FOLDER=REFERENCE/'sprint16/final'
TARGETS={'FracPaQ2D_tracemap_SD11A.png':'plot',
         'guiFracPaQ2D_intensityalonggraph_SD11A.png':'title',
         'guiFracPaQ2D_densityalonggraph_SD11A.png':'title'}


def marker_boxes(figure,name,height,width):
    axis=figure.axes[0];boxes=[]
    if name.startswith('FracPaQ2D_tracemap'):
        collection=axis.collections[1]
        points=collection.get_offset_transform().transform(collection.get_offsets())
        paths=collection.get_paths();sizes=collection.get_sizes();weights=collection.get_linewidths()
        for i,point in enumerate(points):
            transform=Affine2D().scale(np.sqrt(sizes[i%len(sizes)])*PRINT_DPI/72)
            extent=paths[i%len(paths)].get_extents(transform)
            boxes.append((point,extent,weights[i%len(weights)]))
    else:
        for line in axis.lines:
            marker=line._marker
            extent=marker.get_path().get_extents(marker.get_transform()+Affine2D().scale(line.get_markersize()*PRINT_DPI/72))
            for point in line.get_transform().transform(line.get_xydata()):
                boxes.append((point,extent,line.get_markeredgewidth()))
    result=[]
    for (x,y),extent,weight in boxes:
        # Stroke half-width plus 3 device pixels bounds antialias coverage,
        # the former atlas's rounded centre and its one-pixel row offset.
        pad=weight*PRINT_DPI/144+3
        result.append([max(0,int(np.floor(x+extent.x0-pad))),
                       max(0,int(np.floor(height-(y+extent.y1+pad)))),
                       min(width,int(np.ceil(x+extent.x1+pad))),
                       min(height,int(np.ceil(height-(y+extent.y0-pad))))])
    return result


def main():
    change=json.loads((FOLDER/'marker-change.json').read_text())
    meta=json.loads(CACHE.with_suffix('.json').read_text())
    assert sha256(CACHE)==meta['cache_sha256'] and manifest()==meta['implementation']
    assert sha256(SOURCE)==meta['input_sha256'] and change['scientific_modules_unchanged']
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    prior=json.loads(subprocess.check_output(['git','show',revision+':tests/reference/sprint16/final/region-comparison.json'],cwd=ROOT))
    prior={r['name']:r for r in prior}
    current={r['name']:r for r in json.loads((FOLDER/'region-comparison.json').read_text())}
    previous_acceptances={(r['figure'],r['region']):r for r in change['before_visual_acceptance']['accepted_regions']}
    results=pickle.loads(CACHE.read_bytes());_,config=configuration();registry=AnalysisRegistry();records=[]
    for result in results:
        if result.analysis_id not in ('MAP-01','GRA-06'):continue
        spec=next(s for s in registry.specs if s.id==result.analysis_id)
        for output in spec.render(result.data,config):
            name=output.basename+'_SD11A.png';figure=output.figure
            if name not in TARGETS:figure.clear();continue
            region=next(r for r in current[name]['regions'] if r['name']==TARGETS[name])
            before_bytes=subprocess.check_output(['git','show',revision+':tests/reference/sprint16/final/python/'+name],cwd=ROOT)
            before_sha=hashlib.sha256(before_bytes).hexdigest()
            assert before_sha==change['before_primary_images'][name]==prior[name]['candidate_sha256']
            with Image.open(BytesIO(before_bytes)) as im:before=np.array(im.convert('RGB'))
            with Image.open(FOLDER/'python'/name) as im:after=np.array(im.convert('RGB'))
            assert before.shape==after.shape
            figure.set_size_inches(PRINT_SIZE_INCHES,PRINT_SIZE_INCHES);figure.set_dpi(PRINT_DPI)
            FigureCanvasAgg(figure).draw();height,width=before.shape[:2]
            boxes=marker_boxes(figure,name,height,width);covered=np.zeros((height,width),dtype=bool)
            for x0,y0,x1,y1 in boxes:covered[y0:y1,x0:x1]=True
            x0,y0,x1,y1=region['xyxy'];changed=np.any(before[y0:y1,x0:x1]!=after[y0:y1,x0:x1],axis=2)
            outside=int(np.count_nonzero(changed&~covered[y0:y1,x0:x1]))
            old_region=next(r for r in prior[name]['regions'] if r['name']==TARGETS[name])
            accepted=previous_acceptances.get((name,TARGETS[name]))
            prior_satisfied=old_region['passed'] is True or (accepted is not None and accepted['candidate_sha256']==before_sha and accepted['native_sha256']==current[name]['native_sha256'])
            record={'figure':name,'region':TARGETS[name],'xyxy':region['xyxy'],
                    'native_sha256':current[name]['native_sha256'],'before_candidate_sha256':before_sha,
                    'candidate_sha256':sha256(FOLDER/'python'/name),'marker_count':len(boxes),
                    'changed_pixel_count':int(changed.sum()),'changed_pixels_outside_marker_footprints':outside,
                    'prior_gate_satisfied':bool(prior_satisfied),'prior_ssim_rgb':old_region['ssim_rgb'],
                    'current_ssim_rgb':region['ssim_rgb'],'passed':outside==0 and bool(prior_satisfied)}
            records.append(record);print(name,record['changed_pixel_count'],outside,record['passed'],flush=True)
            figure.clear();gc.collect()
    assert len(records)==3
    write_json(FOLDER/'marker-propagation-proof.json',{
        'method':'Before/after RGB difference attribution inside actual marker artist footprints, including stroke/AA/old centre rounding. This is NOT an SSIM mask: original scores and frozen full ROIs stay unchanged.',
        'before_git_revision':revision,'authorized_global_instruction':change['user_instruction'],
        'implementation':{str(p.relative_to(ROOT)):sha256(p) for p in sorted((ROOT/'pyfracpaq').rglob('*.py'))},
        'records':records,'passed':all(r['passed'] for r in records)})


if __name__=='__main__':main()
