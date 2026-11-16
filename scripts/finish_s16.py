"""Final S16 candidates; native SD11A references and previous runs stay intact.

Compute cache is a locally created, checksummed temporary pickle, never an
input format of the application. Renderers always execute production code.
"""

import argparse
from dataclasses import replace
import gc
import json
from pathlib import Path
import pickle
import time

import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np
from PIL import Image

from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.analysis.lengths import compute_lengths
from pyfracpaq.domain.execution import RunContext
from pyfracpaq.io import read_txt
from pyfracpaq.io.figures import export_png
from compare_sd11a import configuration, SOURCE, SEED, structure
from reference_common import ROOT, REFERENCE, sha256, write_json
from audit_sprint16 import integrity

FOLDER=REFERENCE/'sprint16/final'
CACHE=Path('/tmp/pyfracpaq-s16-compute.pkl')


def manifest():
    return {str(p.relative_to(ROOT)):sha256(p) for directory in ('analysis','domain','geometry','io')
            for p in sorted((ROOT/'pyfracpaq'/directory).rglob('*.py'))}


def compute():
    integrity();p,cfg=configuration();data=read_txt(SOURCE)
    out=FOLDER/'python';out.mkdir(parents=True,exist_ok=True)
    def seeded(*args,**kwargs):return compute_lengths(*args,**kwargs,mle_seed=SEED)
    registry=AnalysisRegistry([replace(s,compute=seeded) if s.cache_key=='lengths' else s
                               for s in AnalysisRegistry().specs])
    start=time.perf_counter()
    results=registry.execute(data,RunContext(cfg,out,out,'s16-final'),lambda *_:None,lambda:False)
    CACHE.write_bytes(pickle.dumps(results,protocol=pickle.HIGHEST_PROTOCOL))
    write_json(CACHE.with_suffix('.json'),{'cache_sha256':sha256(CACHE),'implementation':manifest(),
                                          'input_sha256':sha256(SOURCE),'seconds':time.perf_counter()-start})
    arrays={};schema={'geometry':structure(data.as_arrays(),arrays,'geometry')};seen=set()
    for result in results:
        spec=next(s for s in registry.specs if s.id==result.analysis_id);key=spec.cache_key or spec.id
        if key not in seen:schema[key]=structure(result.data,arrays,key);seen.add(key)
    np.savez_compressed(out/'arrays.npz',**arrays);write_json(out/'arrays-schema.json',schema)
    print('Computed',len(results),'routes.',flush=True)


def render(ids):
    meta=json.loads(CACHE.with_suffix('.json').read_text())
    assert meta['cache_sha256']==sha256(CACHE) and meta['implementation']==manifest()
    assert meta['input_sha256']==sha256(SOURCE)
    results=pickle.loads(CACHE.read_bytes());p,cfg=configuration();registry=AnalysisRegistry()
    folder=FOLDER/'python';records=[];seen=set()
    for result in results:
        if ids and result.analysis_id not in ids:continue
        spec=next(s for s in registry.specs if s.id==result.analysis_id)
        for output in spec.render(result.data,cfg):
            if output.basename in seen:output.figure.clear();continue
            seen.add(output.basename);fig=output.figure
            canvas=FigureCanvasAgg(fig);canvas.draw();path=export_png(fig,output.basename,p['tag'],folder)
            old=fig.dpi;fig.set_dpi(600);canvas.draw();renderer=canvas.get_renderer()
            records.append({'id':result.analysis_id,'path':path.name,'sha256':sha256(path),
                'axes':[{'bbox':list(a.get_window_extent(renderer).extents),
                         'title':a.get_title(),'xlabel':a.get_xlabel(),'ylabel':a.get_ylabel(),
                         'xlim':list(a.get_xlim()),'ylim':list(a.get_ylim()),
                         'xticks':np.asarray(a.get_xticks()).tolist(),'yticks':np.asarray(a.get_yticks()).tolist(),
                         'colourbar':hasattr(a,'_colorbar'),
                         'texts':[{'text':t.get_text(),'bbox':list(t.get_window_extent(renderer).extents)}
                                  for t in [a.title,a.xaxis.label,a.yaxis.label]
                                  if t.get_text() and t.get_visible()]}
                        for a in fig.axes]})
            fig.set_dpi(old)
            with Image.open(path) as im:
                thumb=im.convert('RGB');thumb.thumbnail((800,800));thumb.save(folder/('qa-'+path.name))
            fig.clear();gc.collect();print(path.name,flush=True)
    target=folder/'validation.json'
    previous=json.loads(target.read_text()) if target.exists() else []
    updated={x['path']:x for x in previous};updated.update({x['path']:x for x in records})
    write_json(target,list(updated.values()))


def preview(names):
    # Thumbnails are exclusively for human inspection.
    from PIL import ImageDraw
    records=json.loads((FOLDER/'python/validation.json').read_text())
    records=[r for r in records if not names or r['id'] in names]
    for start in range(0,len(records),5):
        group=records[start:start+5];canvas=Image.new('RGB',(1200,len(group)*630),'white');d=ImageDraw.Draw(canvas)
        for i,record in enumerate(group):
            d.text((10,i*630+4),record['path'],fill='black')
            for j,base in enumerate((REFERENCE/'sprint16/sd11a/native',FOLDER/'python')):
                d.text((j*600+10,i*630+18),'MATLAB' if j==0 else 'Python',fill='black')
                with Image.open(base/record['path']) as im:
                    thumb=im.convert('RGB');thumb.thumbnail((595,595));canvas.paste(thumb,(j*600,i*630+30))
        canvas.save(FOLDER/f'preview-{start//5+1}.png')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=['compute','render','preview']);parser.add_argument('--ids',nargs='*')
    a=parser.parse_args()
    if a.phase=='compute':compute()
    elif a.phase=='render':render(a.ids)
    else:preview(a.ids)
