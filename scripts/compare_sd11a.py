"""Paired FracPaQ/Python evidence for the user-selected, unmodified SD11A.txt.

Phases run independently. Native outputs are produced only by MATLAB's
capture_sd11a.m; presence of a capture never declares visual acceptance.
"""

import argparse
from dataclasses import asdict, fields, is_dataclass, replace
import gc
import json
import math
from pathlib import Path
import resource
import time

import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np
from PIL import Image, ImageDraw
from scipy.io import loadmat, savemat

from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.analysis.lengths import compute_lengths
from pyfracpaq.analysis.mle import survival
from pyfracpaq.domain.execution import RunContext
from pyfracpaq.geometry.profiles import ProfileLine
from pyfracpaq.io import read_txt
from pyfracpaq.io.figures import export_png
from reference_common import ROOT, REFERENCE, sha256, write_json
from sprint3_reference import reference_config
from audit_sprint16 import integrity

FOLDER = REFERENCE/'sprint16/sd11a'
SOURCE = ROOT/'fracpaq-matlab/SD11A.txt'
SEED = 20261115


def prepare():
    integrity()
    dataset=read_txt(SOURCE)
    b=dataset.bounds
    values=reference_config().values
    parameters={
        'input':str(SOURCE.relative_to(ROOT)), 'input_sha256':sha256(SOURCE),
        'bytes':SOURCE.stat().st_size, 'traces':dataset.n_traces,
        'segments':dataset.n_segments,'nodes':dataset.n_nodes,'bounds':asdict(b),
        'unit':'pixels','pixels_per_metre':0,'north':0,'flip_x':False,'flip_y':False,
        'length_bins':20,'angle_bins':20,'rose_bins':10,'show_nodes':True,
        'show_circles':True,'rose_mean':True,'rose_colour':True,'rose_weighted':False,
        'censor':False,'lower_cut':0,'upper_cut':0,'circles':12,'blocks':12,
        'tolerance':float(f'{max(b.width,b.height)/1000:.2f}'),
        'sigma1':100,'sigma2':50,'stress_azimuth':0,'cohesion':0,'pore_pressure':0,'friction':.6,
        'fixed_aperture':.001,'lambda':1,'graph_circles':12,
        'graph_x':[b.x_min,b.x_max],'graph_y':[(b.y_min+b.y_max)/2]*2,
        'wavelet_a':[32],'wavelet_L':[2],'wavelet_step':90,'wavelet_morlet':True,
        'mle_seed_python':SEED,'mle_seed_matlab':SEED,'tag':'SD11A',
        'source_gui_defaults':dict(values),
        'scope':'All applicable TXT routes. Output selectors and show-nodes/circles/mean enabled for inspection. '
                'No physical scale supplied: pixels. Graph line explicitly chosen at mid-height. '
                'Wavelet a32/L2/90degrees is a controlled first case, not the full GUI default grid. '
                'Same entered parameters in original/Python; both GUI paths convert L to1/L. '
                'Same RNG seed across libraries is not stochastic parity.'}
    write_json(FOLDER/'parameters.json',parameters)
    print(f'SD11A: {dataset.n_traces} traces, {dataset.n_segments} segments, {dataset.n_nodes} nodes; input intact.')


def configuration():
    p=json.loads((FOLDER/'parameters.json').read_text())
    assert sha256(SOURCE)==p['input_sha256']
    registry=AnalysisRegistry()
    values={s.checkbox:True for s in registry.specs}
    values.update(checkbox_shownodes=True,checkbox_showcircles=True,checkbox_showrosemean=True,
        checkbox_rosecolour=True,checkbox_roselengthweighted=False,checkbox_censor=False,
        edit_degfromnorth='0',edit_numscancircles='12',edit_numblocksmap='12',
        edit_numscancirclesgraph='12',edit_numpixelsItoY=str(p['tolerance']),
        edit_aString='32',edit_LString='2',edit_DegString='90')
    cfg=replace(reference_config(tuple(s.id for s in registry.specs),**values),
        tag=p['tag'],input=replace(reference_config().input,path=SOURCE),
        profile_line=ProfileLine(tuple([p['graph_x'][0],p['graph_y'][0]]),
                                 tuple([p['graph_x'][1],p['graph_y'][1]])))
    return p,cfg


def structure(value, arrays, prefix):
    """Lossless scientific arrays plus a JSON schema; omit duplicate Dataset refs."""
    if isinstance(value,np.ndarray):
        arrays[prefix]=value
        return {'array':prefix,'shape':value.shape,'dtype':str(value.dtype)}
    if is_dataclass(value):
        return {f.name:structure(getattr(value,f.name),arrays,prefix+'_'+f.name)
                for f in fields(value) if f.name!='dataset'}
    if isinstance(value,dict):return {str(k):structure(v,arrays,prefix+'_'+str(k)) for k,v in value.items()}
    if isinstance(value,(tuple,list)):
        return [structure(v,arrays,prefix+'_'+str(i)) for i,v in enumerate(value)]
    if isinstance(value,np.generic):value=value.item()
    if isinstance(value,float) and not math.isfinite(value):return {'nonfinite':str(value)}
    if isinstance(value,Path):return str(value)
    return value


def python_run():
    integrity();p,cfg=configuration();data=read_txt(SOURCE)
    folder=FOLDER/'python';folder.mkdir(parents=True,exist_ok=True)
    registry=AnalysisRegistry()
    def seeded(*args,**kwargs):return compute_lengths(*args,**kwargs,mle_seed=SEED)
    # Audit-only RNG injection through the existing public keyword. Production
    # defaults are unchanged; all real calculations/exporters still execute.
    registry=AnalysisRegistry([replace(s,compute=seeded) if s.cache_key=='lengths' else s
                               for s in registry.specs])
    start=time.perf_counter();events=[]
    def progress(percent,message):
        if not events or message!=events[-1]['message']:
            events.append({'seconds':time.perf_counter()-start,'percent':percent,'message':message})
    results=registry.execute(data,RunContext(cfg,folder,folder,'sd11a'),progress,lambda:False)
    arrays={};schema={'geometry':structure(data.as_arrays(),arrays,'geometry')}
    seen_data=set();specs={s.id:s for s in registry.specs};figures=[];seen_outputs=set()
    for result in results:
        spec=specs[result.analysis_id];key=spec.cache_key or spec.id
        if key not in seen_data:
            schema[key]=structure(result.data,arrays,key);seen_data.add(key)
        for output in spec.render(result.data,cfg):
            if output.basename in seen_outputs:output.figure.clear();continue
            seen_outputs.add(output.basename)
            canvas=FigureCanvasAgg(output.figure);canvas.draw()
            target=export_png(output.figure,output.basename,p['tag'],folder)
            # Export geometry at the actual print dimensions/DPI. No resizing
            # of the reference PNG or alignment translations for comparisons.
            old_dpi=output.figure.dpi;output.figure.set_dpi(600);canvas.draw()
            axes=[]
            for ax in output.figure.axes:
                renderer=canvas.get_renderer()
                texts=[{'text':t.get_text(),'bbox':list(t.get_window_extent(renderer).extents)}
                       for t in [ax.title,ax.xaxis.label,ax.yaxis.label]
                       if t.get_visible() and t.get_text()]
                axes.append({'bbox':list(ax.get_window_extent(renderer).extents),
                    'position':list(ax.get_position().bounds),'title':ax.get_title(),
                    'xlabel':ax.get_xlabel(),'ylabel':ax.get_ylabel(),
                    'xlim':list(ax.get_xlim()),'ylim':list(ax.get_ylim()),'texts':texts,
                    'colourbar':hasattr(ax,'_colorbar')})
            output.figure.set_dpi(old_dpi)
            with Image.open(target) as im:
                dimensions=im.size;dpi=im.info.get('dpi');thumb=im.copy();thumb.thumbnail((800,800))
                thumb.save(folder/('qa-'+target.name))
            figures.append({'id':result.analysis_id,'path':target.name,'sha256':sha256(target),
                            'size':dimensions,'dpi':dpi,'axes':axes})
            output.figure.clear();gc.collect()
        print(result.analysis_id+': captured',flush=True)
    np.savez_compressed(folder/'arrays.npz',**arrays)
    write_json(folder/'arrays-schema.json',schema)
    write_json(folder/'configuration.json',json.loads(json.dumps(asdict(cfg),default=str)))
    write_json(folder/'validation.json',{'input_sha256':sha256(SOURCE),'parameters_sha256':sha256(FOLDER/'parameters.json'),
        'analysis_ids':[r.analysis_id for r in results],'figures':figures,'progress':events,
        'seconds':time.perf_counter()-start,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'arrays_sha256':sha256(folder/'arrays.npz'),'schema_sha256':sha256(folder/'arrays-schema.json'),
        'scope':'Production calculations/renderers/exporters on unchanged user-selected TXT; '
                'RNG controlled only in audit. This records functionality, not blanket MATLAB parity.'})
    print(f'{len(figures)} real PNGs captured.',flush=True)


def numeric_comparison(candidate_folder=None,report_path=None):
    candidate_folder=Path(candidate_folder) if candidate_folder is not None else FOLDER/'python'
    p,_=configuration();actual=np.load(candidate_folder/'arrays.npz')
    native=loadmat(FOLDER/'native/geometry.mat',simplify_cells=True)['geometry']
    comparisons=[]
    def compare(name,a,b,*,rtol=1e-10,atol=2e-9,exact=False,approved=None):
        a,b=np.asarray(a),np.asarray(b)
        if b.size==a.size:b=b.reshape(a.shape)
        same_shape=a.shape==b.shape
        mask=same_shape and all(np.array_equal(test(a),test(b)) for test in
                               (np.isfinite,np.isnan,np.isposinf,np.isneginf))
        passed=mask and (np.array_equal(a,b) if exact else np.allclose(a[np.isfinite(a)],b[np.isfinite(b)],rtol=rtol,atol=atol))
        err=float(np.max(np.abs(a[np.isfinite(a)]-b[np.isfinite(b)]))) if mask and np.isfinite(a).any() else None
        comparisons.append({'name':name,'python_shape':a.shape,'native_shape':b.shape,'same_finite_mask':mask,
            'passed':bool(passed),'maximum_absolute_error':err,'rtol':0 if exact else rtol,
            'atol':0 if exact else atol,'approved_difference':approved})
    for name in ['node_coordinates','segment_coordinates','segment_lengths','raw_angles','trace_lengths',
                 'segment_midpoints','trace_midpoints','start_lengths','end_lengths']:
        compare('geometry.'+name,actual['geometry_'+name],native[name],atol=3.6e-10 if name=='raw_angles' else 2e-9)
    core=loadmat(FOLDER/'native/core.mat',simplify_cells=True)['core']
    for population in ('trace','segment'):
        for name in ('centres','frequencies'):
            compare(population+'_histogram_'+name,actual[f'lengths_{population}_histogram_{name}'],
                    core[population+'_histogram'][name],exact=name=='frequencies')
        for name in ('centres','frequencies','complementary'):
            compare(population+'_complementary_'+name,actual[f'lengths_{population}_complementary_{name}'],
                    core[population+'_complementary'][name],exact=name!='centres')
    for name,other in [('angles','angles'),('centres','angle_centres'),('frequencies','angle_frequencies')]:
        compare('angles.'+name,actual['angles_'+name],core[other],exact=True)
    for rank in (2,4,8):
        compare(f'tensor.F{rank}',actual[f'angles_crack_ranks_{(2,4,8).index(rank)}_components'],core[f'F{rank}'],rtol=1e-8,atol=1e-12*max(1,float(core['F0'])))
        compare(f'tensor.polar{rank}',actual[f'angles_crack_ranks_{(2,4,8).index(rank)}_polar'],core[f'polar{rank}'],rtol=1e-8,atol=1e-12*max(1,float(core['F0'])))
    for name in ['p','k','polar']:
        compare('permeability.'+name,actual['FLO-09_'+name],core['permeability'][name],rtol=1e-8,atol=1e-12*float(np.abs(core['permeability'][name]).max()))
    def cells(value):return [value] if isinstance(value,dict) else list(value)
    def figures(family):
        return cells(loadmat(FOLDER/f'native/{family}_figures.mat',simplify_cells=True)['figures_data'])
    def axis(figure):return cells(figure['axes'])[0]
    circular=figures('circular')
    for index,name in ((1,'intensity'),(2,'density')):
        image=cells(axis(circular[index])['images'])[0]
        compare('circular.'+name,actual['circular_'+name],image['values'],
                approved='Q20 finite segment/circle intersections' if name=='intensity' else None)
        for direction in ('x','y'):
            compare('circular.grid_'+direction,actual['circular_grid_'+direction],image[direction])
    graphs=figures('graphs')
    keys=[('graphs_along_distances','graphs_along_trace_lengths'),
          ('graphs_along_distances','graphs_along_segment_lengths'),
          ('graphs_along_distances','graphs_along_raw_angles'),None,
          ('graphs_circles_distances','graphs_circles_intensity'),
          ('graphs_circles_distances','graphs_circles_density'),
          ('graphs_trace_distances','geometry_trace_lengths'),
          ('graphs_segment_distances','geometry_segment_lengths'),
          ('graphs_segment_distances','geometry_raw_angles')]
    for i,keys_for_figure in enumerate(keys):
        if keys_for_figure is None:continue
        # findall returns children in reverse creation order; reverse once to
        # retain source observation order. No value-based sorting/matching.
        lines=cells(axis(graphs[i])['lines'])[::-1]
        xy=np.asarray([[float(line['x']),float(line['y'])] for line in lines])
        for j,key in enumerate(keys_for_figure):
            compare(f'graphs.figure{i}.{key}',actual[key],xy[:,j],
                    approved='Q20 finite counts/P20 normalisation' if i in (4,5) and j==1 else None)
    line=cells(axis(figures('variogram')[0])['lines'])[0]
    for name,coordinate in (('distance','x'),('values','y')):
        compare('variogram.'+name,actual['lengths_variogram_'+name],line[coordinate],rtol=1e-8,atol=1e-8)
    line=cells(axis(figures('slip')[0])['lines'])[1]
    for name,coordinate in (('normal','x'),('shear','y')):
        compare('mohr.'+name,actual['stability_mohr_'+name],line[coordinate])
    schema=json.loads((candidate_folder/'arrays-schema.json').read_text())
    for i,figure in enumerate(figures('mle')):
        population=('trace','segment')[i//3];model=i%3
        fit=schema['lengths']['mle'][population][model]['fit']
        observed=np.unique(actual[f'lengths_mle_{population}_{model}_fit_sample_original'])
        tail=actual[f'lengths_mle_{population}_{model}_fit_tail']
        frequency=np.arange(len(observed),0,-1)/len(observed)
        estimated=survival(tail,fit['kind'],fit['xmin'],fit['parameters'])*frequency[np.searchsorted(observed,fit['xmin'])]
        lines=cells(axis(figure)['lines'])
        for label,x,y,line in [('observed',observed,frequency,lines[3]),('estimated',tail,estimated,lines[2])]:
            for coordinate,values in (('x',x),('y',y)):
                compare(f'mle.{population}.{fit["kind"]}.{label}.{coordinate}',values,line[coordinate],
                        approved='Q15 candidate-specific lognormal tail' if population=='segment' and model==2 and label=='estimated' else None)
    # The halfway-point contract is already required by S01-04. Keep the native
    # defect visible, with exact input records and its propagated FROM error.
    mismatch=np.flatnonzero(np.any(~np.isclose(actual['geometry_trace_midpoints'],native['trace_midpoints'],rtol=1e-10,atol=2e-9),axis=1))
    dataset=read_txt(SOURCE)
    midpoint_cases=[{'source_line':int(i)+1,'nodes':[node.point for node in dataset.traces[i].nodes],
        'trace_length':float(actual['geometry_trace_lengths'][i]),
        'python_midpoint':actual['geometry_trace_midpoints'][i].tolist(),
        'native_midpoint':native['trace_midpoints'][i].tolist()} for i in mismatch]
    blocks=figures('blocks');centroids=cells(axis(blocks[0])['lines'])[0]
    block_comparison={'native_count':int(np.asarray(centroids['x']).size),
                      'python_count':int(actual['lengths_blocks_areas'].size),'approved_difference':'Q14 raster/exterior/calibration'}
    # Scientific changes approved earlier stay visible, with both populations.
    source_counts={line.split()[0]:int(line.split()[1]) for line in (FOLDER/'native/FracPaQ2Dconnectivity_SD11A.txt').read_text().splitlines()}
    python_counts={line.split()[0]:int(line.split()[1]) for line in (candidate_folder/'FracPaQ2Dconnectivity_SD11A.txt').read_text().splitlines()}
    file_checks=[]
    for basename in ['FracPaQ2Dsegmentlengths','FracPaQ2Dtracelengths','FracPaQ2Dsegmentangleslengths','FracPaQ2DEZROSE']:
        a=candidate_folder/f'{basename}_SD11A.txt';b=FOLDER/'native'/a.name
        file_checks.append({'name':a.name,'bytes_exact':a.read_bytes()==b.read_bytes(),
                            'python_sha256':sha256(a),'native_sha256':sha256(b)})
    write_json(Path(report_path) if report_path is not None else FOLDER/'numeric-comparison.json',{'comparisons':comparisons,'files':file_checks,
        'connectivity_Q11':{'native':source_counts,'python':python_counts,'approved':True},
        'blocks_Q14':block_comparison,'trace_halfway_cases':midpoint_cases,
        'halfway_contract':'S01-04 already requires half the path; Python implementation unchanged. '
                           'Native source incorrectly displaces upward on downward vertical segments.',
        'scope':'Comparisons keep masks/shapes/order. Explicit scientific changes are not asserted identical. '
                'No generic equal_nan or relaxed tolerances. Remaining families retain raw arrays/plots for review.'})
    print('Numeric:',sum(v['passed'] for v in comparisons),'/',len(comparisons),'passed.',flush=True)


def images_comparison():
    from skimage.metrics import structural_similarity
    report=json.loads((FOLDER/'python/validation.json').read_text());records=[]
    previous={v['name']:v for v in json.loads((FOLDER/'image-comparison.json').read_text())} if (FOLDER/'image-comparison.json').exists() else {}
    for entry in report['figures']:
        name=entry['path'];a=FOLDER/'python'/name;b=FOLDER/'native'/name
        if not b.exists():
            records.append({'name':name,'status':'Native output absent; inspect native_calls.json'});continue
        old=previous.get(name,{})
        if old.get('python_sha256')==sha256(a) and old.get('native_sha256')==sha256(b):
            records.append(old);print(name+': reused verified hashes',flush=True);continue
        with Image.open(a) as im:pa=np.array(im.convert('RGB'))
        with Image.open(b) as im:ma=np.array(im.convert('RGB'))
        if pa.shape!=ma.shape:
            records.append({'name':name,'status':'Different original dimensions','python_shape':pa.shape,'matlab_shape':ma.shape});continue
        h,w=pa.shape[:2]
        # Full axes panels and colourbar boxes in their original absolute
        # positions, without image resampling or per-object translations.
        # Native bbox coordinates after printing are not reliable across HG
        # print internals: these Python-anchored ROIs remain diagnostic only.
        regions={'full_canvas':(0,0,w,h)}
        for i,ax in enumerate(entry['axes']):
            x0,y0,x1,y1=ax['bbox'];pad=3
            box=(max(0,int(x0)-pad),max(0,h-int(y1)-pad),min(w,math.ceil(x1)+pad),min(h,h-math.floor(y0)+pad))
            regions[('colourbar' if ax['colourbar'] else 'panel')+str(i)]=box
            for j,text in enumerate(ax['texts']):
                x0,y0,x1,y1=text['bbox']
                box=(max(0,int(x0)-8),max(0,h-int(y1)-8),min(w,math.ceil(x1)+8),min(h,h-math.floor(y0)+8))
                if box[2]-box[0]>=7 and box[3]-box[1]>=7:regions[f'text{i}_{j}']=box
        scores={}
        for key,(x0,y0,x1,y1) in regions.items():
            if x1-x0<7 or y1-y0<7:continue
            scores[key]=float(structural_similarity(pa[y0:y1,x0:x1],ma[y0:y1,x0:x1],channel_axis=2,data_range=255))
        difference=np.abs(pa.astype(np.int16)-ma.astype(np.int16)).astype(np.uint8)
        target=FOLDER/'differences'/name;target.parent.mkdir(exist_ok=True);Image.fromarray(difference).save(target)
        records.append({'name':name,'status':'Compared; not homologated','python_sha256':sha256(a),'native_sha256':sha256(b),
            'regions_xyxy':regions,'ssim_rgb_data_range255':scores,'threshold':.98,
            'difference':str(target.relative_to(ROOT)),'scope':'Diagnostic ROIs can overlap and are Python-anchored; '
                'not the independent semantic region partition required for final acceptance. Approved Q changes remain separate.'})
        del pa,ma,difference;gc.collect()
        print(name+': compared',flush=True)
    write_json(FOLDER/'image-comparison.json',records)


def gallery():
    """Human review thumbnails; never used as inputs to the pixel metrics."""
    records=json.loads((FOLDER/'image-comparison.json').read_text())
    lines=['# SD11A — galeria pareada', '',
           'MATLAB à esquerda e Python à direita nas folhas. Miniaturas reduzidas somente para navegação; '
           'SSIM e diferenças foram calculados nos PNG originais, sem redimensionamento. '
           'As métricas são diagnósticas e incluem diferenças científicas aprovadas. Não representam homologação.', '']
    for start in range(0,len(records),6):
        group=records[start:start+6]
        canvas=Image.new('RGB',(1000,len(group)*535),'white');draw=ImageDraw.Draw(canvas)
        for i,entry in enumerate(group):
            draw.text((10,i*535+4),entry['name'],fill='black')
            for j,folder in enumerate(('native','python')):
                path=FOLDER/folder/entry['name']
                draw.text((j*500+10,i*535+20),'MATLAB' if j==0 else 'Python',fill='black')
                if path.exists():
                    with Image.open(path) as im:
                        thumb=im.convert('RGB');thumb.thumbnail((495,495));canvas.paste(thumb,(j*500,i*535+35))
                else:draw.text((j*500+50,i*535+200),'No native export; see native_calls.json',fill='red')
        name=f'paired-sheet-{start//6+1:02}.png';canvas.save(FOLDER/name)
        lines.append(f'- [Folha {start//6+1}: figuras {start+1}–{start+len(group)}]({name})')
    lines+=['','| Figura | MATLAB | Python | Diferença | SSIM global |','| --- | --- | --- | --- | --- |']
    for entry in records:
        name=entry['name'];score=entry.get('ssim_rgb_data_range255',{}).get('full_canvas')
        links=[f'[PNG]({folder}/{name})' if (FOLDER/folder/name).exists() else 'Ausente' for folder in ('native','python','differences')]
        lines.append('| '+name+' | '+' | '.join(links)+' | '+(f'{score:.6f}' if score is not None else '—')+' |')
    (FOLDER/'gallery.md').write_text('\n'.join(lines)+'\n')


def shared_wavelet():
    """Separate CWT parity on identical native pixels from approved raster changes."""
    from pyfracpaq.analysis.wavelets import analyse_wavelet_image, WaveletParameters
    p,_=configuration()
    figure=loadmat(FOLDER/'native/wavelets_figures.mat',simplify_cells=True)['figures_data']
    if not isinstance(figure,dict):figure=figure[0]
    axes=figure['axes'];axes=[axes] if isinstance(axes,dict) else list(axes)
    images={}
    for ax in axes:
        objects=ax['images'];objects=[objects] if isinstance(objects,dict) else list(objects)
        if objects:images['binary' if 'Binary image' in str(ax['title']) else 'coefficients']=objects[0]['values']
    parameters=WaveletParameters(tuple(np.atleast_1d(p['wavelet_a']).tolist()),
                                 tuple(np.atleast_1d(p['wavelet_L']).tolist()),p['wavelet_step'],'morlet')
    start=time.perf_counter()
    shared=analyse_wavelet_image(images['binary'],parameters).scales[0]
    native=images['coefficients'];native_selected=native>native.max()*.5
    native_angles=np.loadtxt(FOLDER/'native/FracPaQ2Dwavelet_theta_a32_SD11A.txt')
    production=np.load(FOLDER/'python/arrays.npz')
    image=production['WAV-01_image'];wc=production['WAV-01_scales_0_coefficients']
    checks={
        'coefficients_within_tolerance':bool(np.allclose(shared.coefficients,native,rtol=1e-10,atol=1e-12)),
        'maximum_absolute_error':float(np.max(np.abs(shared.coefficients-native))),
        'selected_pixels_exact':bool(np.array_equal(shared.selected,native_selected)),
        'doubled_angles_exact':bool(np.array_equal(shared.doubled_degrees,native_angles)),
        'rtol':1e-10,'atol':1e-12,'selected_count_native':int(native_selected.sum()),
        'selected_count_shared_python':int(shared.selected.sum())}
    np.savez_compressed(FOLDER/'wavelet-shared-native-raster.npz',coefficients=shared.coefficients,
                        selected=shared.selected,doubled_degrees=shared.doubled_degrees)
    write_json(FOLDER/'wavelet-comparison.json',{
        'parameters':asdict(parameters),'native_ratio':(1/np.asarray(p['wavelet_L'])).tolist(),
        'shared_native_pixels':checks,
        'production_raster_Q12':{'different_pixel_fraction':float(np.mean(image!=images['binary'])),
            'mean_absolute_gray_error_255':float(np.mean(np.abs(image-images['binary']))*255),
            'maximum_absolute_coefficient_error':float(np.max(np.abs(wc-native))),
            'native_maximum':float(native.max()),'python_maximum':float(wc.max()),
            'native_angle_count':int(native_angles.size),
            'python_angle_count':int(production['WAV-01_scales_0_doubled_degrees'].size)},
        'seconds':time.perf_counter()-start,
        'scope':'Additional diagnostic on identical native pixels, not a substitution for the actual Python Run/raster. '
                'Both native and Python GUI invert the entered L factor. Production raster difference is Q12.'})
    print(checks,flush=True)


def provenance():
    integrity();p,_=configuration()
    outputs=[]
    for path in sorted((FOLDER/'native').rglob('*')):
        if path.is_file():outputs.append({'path':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,'sha256':sha256(path)})
    write_json(FOLDER/'native-provenance.json',{'input':p['input'],'input_sha256':sha256(SOURCE),
       'script':'scripts/capture_sd11a.m','script_sha256':sha256(ROOT/'scripts/capture_sd11a.m'),
       'parameters_sha256':sha256(FOLDER/'parameters.json'),'outputs':outputs,
       'scope':'Actual supplied MATLAB functions; originals unchanged; separate batch process. '
               'Native Q defects remain in their outputs. No fake goldens or fallback figures.'})
    outputs=[]
    for path in sorted((FOLDER/'python').rglob('*')):
        if path.is_file():outputs.append({'path':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,'sha256':sha256(path)})
    implementation=[{'path':str(path.relative_to(ROOT)),'sha256':sha256(path)}
                    for path in sorted((ROOT/'pyfracpaq').rglob('*.py'))]
    write_json(FOLDER/'python-provenance.json',{'input_sha256':sha256(SOURCE),
        'script':'scripts/compare_sd11a.py','script_sha256':sha256(ROOT/'scripts/compare_sd11a.py'),
        'parameters_sha256':sha256(FOLDER/'parameters.json'),'implementation':implementation,'outputs':outputs,
        'scope':'Implementation manifest recorded after paired run; original production compute/render/export, audit-only seed. '
                'Initial direct-L2 native diagnostic is excluded from the paired native manifest.'})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=['prepare','python','numeric','images','provenance','gallery','wavelet'])
    args=parser.parse_args()
    {'prepare':prepare,'python':python_run,'numeric':numeric_comparison,
     'images':images_comparison,'provenance':provenance,'gallery':gallery,'wavelet':shared_wavelet}[args.phase]()
