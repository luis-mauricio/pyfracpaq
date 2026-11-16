"""Evidence for Sprints 8/9 and the Q-15/Q-11 corrections approved by the user."""

from dataclasses import asdict
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import numpy as np
from scipy.io import loadmat

from pyfracpaq.analysis.lengths import compute_lengths
from pyfracpaq.analysis.mle import fit_tail
from pyfracpaq.analysis.connectivity import classify_connectivity,connectivity_maps
from pyfracpaq.domain import TraceInput,build_dataset
from pyfracpaq.domain.execution import RunContext
from pyfracpaq.geometry import Bounds
from pyfracpaq.io import read_txt
from pyfracpaq.io.svg import read_svg
from pyfracpaq.io.images import read_image
from pyfracpaq.io.connectivity import export_connectivity
from pyfracpaq.plots.mle import render_mle
from pyfracpaq.plots.connectivity import render_connectivity
from reference_common import ROOT,sha256,write_json
from sprint3_reference import reference_config
from validate_sprint56 import save_figure


BLUE=(0.,0.,1.)


def mle_evidence():
    folder=ROOT/'tests/reference/sprint8/candidate';folder.mkdir(parents=True,exist_ok=True)
    values=np.array([1,2,3,4,6,10,18,40.])
    data=build_dataset([TraceInput(((0,float(y)),(float(x),float(y))),BLUE) for y,x in enumerate(values)])
    cfg=reference_config(('LEN-07',),checkbox_logloglength=True)
    result=compute_lengths(data,RunContext(cfg,folder,folder,'mle-review'),lambda *a:None,mle_seed=20261114)
    figures=[save_figure(output,'review',folder) for output in render_mle(result,cfg)]
    arrays={};records=[]
    for population,models in (('trace',result.mle.trace),('segment',result.mle.segment)):
        for model in models:
            fit=model.fit;prefix=population+'_'+fit.kind
            for name,array in (('tail',fit.tail),('candidates',fit.candidates),('distances',fit.distances),
                               ('ks_D',model.goodness.distances),('ks_p',model.goodness.pvalues)):
                arrays[prefix+'_'+name]=array
            records.append({'population':population,'model':fit.kind,'xmin':fit.xmin,
                            'parameters':dict(fit.parameters),'tail_size':len(fit.tail),
                            'search_distance':fit.search_distance,'alpha':model.goodness.alpha,
                            'non_rejection_percent':model.goodness.non_rejection_percent,
                            'p_above_005_percent':model.goodness.above_005_percent})
    np.savez_compressed(folder/'arrays.npz',**arrays)
    native=json.loads((ROOT/'tests/reference/sprint8/native/native_fits.json').read_text())
    corrected={kind:{'xmin':(fit:=fit_tail(values,kind,lower=20,upper=10)).xmin,
                      'parameters':dict(fit.parameters),'selected':fit.sample.retained.tolist(),
                      'tail':fit.tail.tolist(),'distances':fit.distances.tolist()}
               for kind in ('power_law','exponential','lognormal')}
    write_json(folder/'q15_comparison.json',{'input':values.tolist(),'lower_percent':20,'upper_percent':10,
                                            'native_original':native,'proposed_correction':corrected,
                                            'approval':'Q-15 approved by user on 2026-11-14: Aprovo as Q-15 e a Q-11.'})
    write_json(folder/'parameters.json',{'values':dict(cfg.values),'selected':cfg.selected,
                                        'seed':result.mle.seed,'unit':result.unit,'raw_lengths':values.tolist()})
    write_json(folder/'validation.json',{'scope':'Approved Q-15 implementation, active in production Run; full visual homologation pending.',
        'figures':figures,'records':records,'arrays_sha256':sha256(folder/'arrays.npz'),
        'parameters_sha256':sha256(folder/'parameters.json'),
        'q15_sha256':sha256(folder/'q15_comparison.json'),
        'txt':[{'path':p.name,'sha256':sha256(p)} for p in sorted(folder.glob('*.txt'))]})


def topology_evidence():
    folder=ROOT/'tests/reference/sprint9/candidate';folder.mkdir(parents=True,exist_ok=True)
    cases=[];arrays={};figures=[]
    native=json.loads((ROOT/'tests/reference/sprint9/native/native_topology.json').read_text())
    proposed={}
    for name in ('isolated','tee_zero','tee','cross','undershoot','overshoot','kink_cross'):
        if name=='isolated':points=[[[-1,0],[1,0]]]
        elif name=='kink_cross':points=[[[-2,0],[0,0],[2,0]],[[0,-2],[0,2]]]
        else:
            gap={'cross':-2,'undershoot':.1,'overshoot':-.1}.get(name,0)
            points=[[[-2,0],[2,0]],[[0,gap],[0,2]]]
        tolerance=0 if name=='tee_zero' else .2
        data=build_dataset([TraceInput(tuple(map(tuple,p)),BLUE) for p in points],source_bounds=Bounds(-3,-3,3,3))
        result=classify_connectivity(data,tolerance)
        proposed[name]={'I_Y_X':result.counts,'i':result.i_nodes.coordinates.tolist(),
                        'y':result.y_nodes.coordinates.tolist(),'x':result.x_nodes.coordinates.tolist(),
                        'snaps':[asdict(snap) for snap in result.snaps]}
    write_json(folder/'q11_comparison.json',{'native_original':native,'proposed_correction':proposed,
                                            'approval':'Q-11 approved by user on 2026-11-14: Aprovo as Q-15 e a Q-11.'})
    cfg=reference_config(('FLO-01',),edit_numblocksmap='3',edit_numpixelsItoY='.2')
    sources=[('TXT',read_txt(ROOT/'tests/fixtures/nodes/mixed.txt')),
             ('SVG',read_svg(ROOT/'tests/fixtures/svg/multicolour.svg').dataset),
             ('Hough',read_image(ROOT/'tests/fixtures/images/rectangular.tif').dataset),
             ('zero',build_dataset([TraceInput(((-1,-1),(1,-1),(1,1),(-1,1),(-1,-1)),BLUE)],
                                    source_bounds=Bounds(-3,-3,3,3)))]
    for tag,data in sources:
        result=connectivity_maps(classify_connectivity(data,.2),3)
        export_connectivity(result.topology.counts,tag,folder)
        for name,nodes in (('I',result.topology.i_nodes),('Y',result.topology.y_nodes),('X',result.topology.x_nodes)):
            arrays[tag+'_'+name]=nodes.coordinates
        arrays[tag+'_XY_grid']=result.xy_heatmap.values;arrays[tag+'_I_grid']=result.i_heatmap.values
        for output in render_connectivity(result,cfg):figures.append(save_figure(output,tag,folder))
        cases.append({'tag':tag,'input_mode':str(data.input_mode),'bounds':asdict(data.bounds),
                      'counts_I_Y_X':result.topology.counts,'grid_shape':result.xy_heatmap.values.shape,
                      'common_colour_maximum':result.maximum})
    np.savez_compressed(folder/'arrays.npz',**arrays)
    write_json(folder/'parameters.json',{'values':dict(cfg.values),'cases':cases})
    write_json(folder/'validation.json',{'scope':'Approved Q-11 implementation, active in production Run; full visual homologation pending.',
        'figures':figures,'cases':cases,'arrays_sha256':sha256(folder/'arrays.npz'),
        'q11_sha256':sha256(folder/'q11_comparison.json'),
        'txt':[{'path':p.name,'sha256':sha256(p)} for p in sorted(folder.glob('*.txt'))]})


if __name__=='__main__':
    mle_evidence();topology_evidence()
    print('Approved implementation: 6 MLE figures, 16 topology figures, arrays/TXT and native Q comparisons saved.')
