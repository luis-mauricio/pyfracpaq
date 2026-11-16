"""Review scientific meaning independently of the accepted raster styling.

Uses captured native axes/colourbars, unchanged production artists, native
PNG palette samples, and explicit prior scientific decisions. No exports or
scientific results are regenerated or overwritten.
"""

import gc
import json
import pickle
import re
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.io import loadmat
from matplotlib.colors import to_rgba

from pyfracpaq.analysis import AnalysisRegistry
from compare_sd11a import configuration,SOURCE
from finish_s16 import CACHE,manifest
from reference_common import ROOT,REFERENCE,sha256,write_json
from audit_s16_details import frames

FOLDER=REFERENCE/'sprint16/final'
NATIVE=REFERENCE/'sprint16/sd11a/native'


def seq(value):return [value] if isinstance(value,dict) else list(value)


def text(value):
    if isinstance(value,str):return value
    if isinstance(value,np.ndarray):return ' '.join(text(v) for v in value.flat)
    return ''


def canonical(value):
    value=text(value).replace('$','').replace('\\circ','°')
    for command in ('it','rm','bf'):value=value.replace('\\'+command,'')
    value=re.sub(r'\\(?:mathit|mathrm|mathdefault|mathregular|mathbf)(?=\{)','',value)
    value=value.replace('\\log','log').replace('\\DeltaP','\\Delta P')
    value=value.replace('\\ ', ' ')
    return re.sub(r'\s+','',value.replace('{','').replace('}',''))


def title_key(value,*,generalize=False):
    value=canonical(value).lower()
    if generalize:value=re.sub(r'\d+(?:\.\d+)?','#',value)
    return value


def native_index():
    entries=[]
    for path in sorted(NATIVE.glob('*_figures.mat')):
        for index,figure in enumerate(seq(loadmat(path,simplify_cells=True)['figures_data'])):
            entries.append({'family':path.stem.replace('_figures',''),'index':index,
                            'path':str(path.relative_to(ROOT)),'data':figure})
    return entries


def match_native(figure,index,name):
    titled=next(a for a in figure.axes if not hasattr(a,'_colorbar') and a.get_title())
    heading=titled.get_title();generalize=any(s in heading for s in ('Block ','I-nodes','(X+Y)-nodes','Connectivity'))
    matches=[]
    for item in index:
        for axis in seq(item['data']['axes']):
            if title_key(axis.get('title',''),generalize=generalize)==title_key(heading,generalize=generalize):
                matches.append(item);break
    # Disambiguate ALONG and FROM, whose titles are intentionally identical.
    preferred=[item for item in matches if any(canonical(a.get('XLabel',''))==canonical(titled.get_xlabel())
                                               for a in seq(item['data']['axes']))]
    if preferred:matches=preferred
    # Block histogram and CCDF share both title and X label. Their Y units
    # distinguish them; choosing the first title match compares two plots.
    if len(matches)>1:
        preferred=[item for item in matches if any(canonical(a.get('YLabel',''))==canonical(titled.get_ylabel())
                                                   for a in seq(item['data']['axes']))]
        if preferred:matches=preferred
    if len(matches)>1 and ('scancircle' in name or 'graphtracemap' in name):
        family='circular' if 'scancircle' in name else 'graphs'
        matches=[item for item in matches if item['family']==family]
    if len(matches)>1 and 'Mohrplot' in name:
        # Every stability call emits the same Mohr scene for this stress case.
        matches=[item for item in matches if item['family']=='slip']
    assert len(matches)==1,(heading,[(m['family'],m['index']) for m in matches])
    assert matches,heading
    return matches[0]


def native_frames(image,vertical=False):
    # Rectangle topology is identical to the independent detail-frame detector;
    # vertical colourbars need a taller allowed height and a narrower width.
    if not vertical:return [b for b in frames(image,38) if (b[2]-b[0])/(b[3]-b[1])>8]
    from scipy.ndimage import label,find_objects
    mask=(image.max(2)-image.min(2)<=1)&(abs(image[:,:,0].astype(int)-38)<=1)
    labels,_=label(mask);boxes=[]
    for sl in find_objects(labels):
        yy,xx=sl;w=xx.stop-xx.start;h=yy.stop-yy.start
        if 60<w<250 and h>600:
            cell=mask[sl]
            if min(cell[:4].any(0).mean(),cell[-4:].any(0).mean(),cell[:,:4].any(1).mean(),cell[:,-4:].any(1).mean())>.65:
                boxes.append([xx.start,yy.start,xx.stop,yy.stop])
    return boxes


def palette_check(image,bar,box):
    x0,y0,x1,y1=box;fraction=(np.arange(64)+.5)/64
    if bar.orientation=='horizontal':
        xx=np.rint(x0+4+fraction*(x1-x0-8)).astype(int);yy=np.full(64,(y0+y1)//2)
    else:
        yy=np.rint(y1-4-fraction*(y1-y0-8)).astype(int);xx=np.full(64,(x0+x1)//2)
    samples=image[yy,xx,:3].astype(int)
    table=np.floor(bar.cmap(np.linspace(0,1,bar.cmap.N))[:,:3]*255).astype(int)
    errors=np.max(abs(samples[:,None,:]-table[None,:,:]),axis=2)
    error=errors.min(1);closest=[];previous=0;monotonic=True
    for row,minimum in zip(errors,error,strict=True):
        # A cyclic palette can repeat its first RGB at the final index.
        # Resolve tied nearest colours in order, preserving every sample.
        choices=np.flatnonzero((row==minimum)&(np.arange(len(row))>=previous))
        if not len(choices):monotonic=False;choices=np.flatnonzero(row==minimum)
        previous=int(choices[0]);closest.append(previous)
    return {'maximum_rgb_distance':int(error.max()),'palette_indices':closest,
            'passed':bool(error.max()<=2 and monotonic)}


def legend_contract(name):
    if 'Fitting' in name:return [('Observed Data','blue'),('Estimated Data','black'),('Upper cut-off','red'),('Lower cut-off','red')]
    if 'Mohrplot' in name:return [('Stress','black'),('Sliding or Failure','red')]
    if 'IYXnodes' in name:return [('I','blue'),('X','red'),('Y','lime')]
    if 'cracktensor' in name:return [(r'$0^{th}$','magenta'),(r'$2^{nd}$','blue'),(r'$4^{th}$','red'),(r'$8^{th}$','lime')]
    if 'graphtracemap' in name:return [('Point 1','cyan'),('Point 2','lime')]
    return None


def main():
    metadata=json.loads(CACHE.with_suffix('.json').read_text())
    assert sha256(CACHE)==metadata['cache_sha256'] and manifest()==metadata['implementation']
    assert sha256(SOURCE)==metadata['input_sha256']
    baseline=json.loads((FOLDER/'status.json').read_text())
    assert all(sha256(ROOT/path)==checksum for path,checksum in baseline['production_modules'].items())
    results=pickle.loads(CACHE.read_bytes());_,config=configuration();registry=AnalysisRegistry()
    frozen={r['path']:r for r in json.loads((FOLDER/'python/validation.json').read_text())}
    index=native_index();seen=set();records=[]
    def check(checks,field,native,candidate,passed,reason=None):
        checks.append({'field':field,'native':native,'candidate':candidate,
                       'status':'passed' if passed else 'documented_difference' if reason else 'issue','reason':reason})
    for result in results:
        spec=next(s for s in registry.specs if s.id==result.analysis_id)
        for output in spec.render(result.data,config):
            name=output.basename+'_SD11A.png';figure=output.figure
            if name in seen:figure.clear();continue
            seen.add(name);assert sha256(FOLDER/'python'/name)==frozen[name]['sha256']
            native=match_native(figure,index,name);checks=[];axes=[a for a in figure.axes if not hasattr(a,'_colorbar')]
            native_axes=seq(native['data']['axes'])
            for axis in axes:
                if not axis.get_title():continue  # The right yyaxis is checked as a figure-level label below.
                possible=[a for a in native_axes if title_key(a.get('title',''),generalize=True)==title_key(axis.get_title(),generalize=True)]
                assert possible,(name,axis.get_title())
                original=possible[0];heading=text(original['title'])
                decision='Q14 corrected block population' if native['family']=='blocks' else 'Q11 corrected node populations' if native['family']=='connectivity' else None
                check(checks,'title',heading,axis.get_title(),canonical(heading)==canonical(axis.get_title()),decision)
                for field,native_field,getter in [('xlabel','XLabel',axis.get_xlabel),('ylabel','YLabel',axis.get_ylabel)]:
                    if native_field not in original:continue
                    expected=text(original[native_field]);actual=getter()
                    labels=[a.get_xlabel() if field=='xlabel' else a.get_ylabel() for a in axes]
                    check(checks,field,expected,actual,any(canonical(expected)==canonical(v) for v in labels))
                for field,native_field,getter in [('xlim','XLim',axis.get_xlim),('ylim','YLim',axis.get_ylim)]:
                    if native_field not in original:continue
                    # yyaxis capture stores the right percentage limits.
                    expected=np.asarray(original[native_field],float);actual=np.asarray(getter(),float)
                    if field=='ylim' and 'histo' in name:
                        actual=np.asarray(axes[-1].get_ylim(),float)
                    reason=decision
                    if 'loglogplot' in name and 'density' not in name and field=='xlim':
                        reason='Q08/S01-04: ceil of translation-invariant envelope diagonal (2818), rather than absolute-coordinate diagonal (2819)'
                    if 'rose' in name and field in ('xlim','ylim'):
                        radius=50*np.sqrt(10)
                        sampled=-radius+np.floor(2*radius/.0005)*.0005
                        if np.allclose(expected,[-sampled,sampled],rtol=0,atol=1e-10) and np.allclose(actual,[-radius,radius],rtol=0,atol=1e-10):
                            reason='Display-only circle extent: native -r:0.0005:r ends before r; Python uses exact r=50*sqrt(10). Frequencies, angles and units unchanged.'
                    if 'densityalong' in name:reason='Q20 corrected P20 normalisation'
                    if 'wavelet' in name:reason='Q12 production raster changes WC/angle populations and auto limits'
                    check(checks,field,expected.tolist(),actual.tolist(),bool(np.allclose(expected,actual,rtol=1e-10,atol=1e-10)),reason)
            contract=legend_contract(name)
            if contract:
                legend=next(a.get_legend() for a in axes if a.get_legend() is not None)
                actual=[t.get_text() for t in legend.get_texts()]
                check(checks,'legend_labels',[v[0] for v in contract],actual,
                      [canonical(v[0]) for v in contract]==[canonical(v) for v in actual])
                colors=[]
                for line,(label_name,color) in zip(legend.get_lines(),contract,strict=True):
                    actual_color=line.get_markerfacecolor() if 'graphtracemap' in name else line.get_color()
                    colors.append({'label':label_name,'passed':bool(np.allclose(to_rgba(actual_color),to_rgba(color)))})
                check(checks,'legend_data_roles',None,colors,all(c['passed'] for c in colors))
            # Explicit left/right frequency units, not equality of the active
            # MATLAB yyaxis metadata with the left Matplotlib axes alone.
            if 'histo' in name and len(axes)==2:
                labels=[a.get_ylabel() for a in axes]
                check(checks,'dual_frequency_units',['Frequency','Frequency, %'],labels,labels==['Frequency','Frequency, %'])
            if 'Fitting' in name:
                native_parameters={
                    'tracelengthsFittingPowerLaw':[2.5373,93.0562],
                    'tracelengthsFittingExponential':[.0028398],
                    'tracelengthsFittingLogNormal':[4.5301,.81414],
                    'segmentlengthsFittingPowerLaw':[4.3613,83.6212],
                    'segmentlengthsFittingExponential':[.030679],
                    'segmentlengthsFittingLogNormal':[3.8925,.55553]}
                key=next(k for k in native_parameters if k in name)
                actual=[float(v) for v in re.findall(r'(?<!=)[-+]?\d*\.\d+|\d+',figure.texts[0].get_text())]
                reason='Q15: lognormal segment tail selection; native mu/sigma 3.8925/0.55553, corrected 3.9241/0.51722' if key=='segmentlengthsFittingLogNormal' else None
                check(checks,'parameter_annotation_values',native_parameters[key],actual,actual==native_parameters[key],reason)
            expected_annotations=None
            if 'rose' in name or 'wavelet' in name:
                expected_annotations=['1%','5%','10%']+(['20%','30%','50%'] if 'wavelet' in name else [])
                if 'tendencyrose' in name or 'fracsusceprose' in name or 'CSFrose' in name:
                    expected_annotations+=['Azimuth $\\sigma_1$']
            if 'IYXtriangle' in name:expected_annotations=['Y','X','I','$C_L = 2$','$C_L = 3.57$']
            if expected_annotations is not None:
                actual=[t.get_text() for a in axes for t in a.texts]
                check(checks,'annotation_meanings',expected_annotations,actual,
                      [canonical(t) for t in expected_annotations]==[canonical(t) for t in actual])
            bars=[a._colorbar for a in figure.axes if hasattr(a,'_colorbar')]
            native_bars=seq(native['data']['colourbars'])
            check(checks,'colourbar_count',len(native_bars),len(bars),len(native_bars)==len(bars))
            if bars:
                with Image.open(NATIVE/name) as im:image=np.array(im.convert('RGB'))
                boxes=native_frames(image,vertical=bars[0].orientation=='vertical')
                boxes=sorted(boxes,key=lambda b:b[0])
                ordered=sorted(bars,key=lambda b:b.ax.get_figure().bbox.x0+b.ax.get_position().x0)
                assert len(boxes)==len(bars),(name,boxes)
                for bar,box in zip(ordered,boxes,strict=True):
                    label_text=bar.ax.get_xlabel() or bar.ax.get_ylabel()
                    expected=[b for b in native_bars if canonical(b['label'])==canonical(label_text)]
                    assert expected,(name,label_text)
                    original=expected[0]
                    limits=[bar.norm.vmin,bar.norm.vmax];reason=None
                    if 'intensityP21' in name:reason='Q20 finite circle/segment intersections'
                    if native['family']=='connectivity':reason='Q11 corrected node populations'
                    if 'fracsuscep' in name:reason='Q17: observed corrected-strike susceptibility bounds, instead of preliminary raw-angle bounds'
                    check(checks,'colourbar_label',text(original['label']),label_text,True)
                    check(checks,'colourbar_limits',np.asarray(original['limits']).tolist(),limits,
                          bool(np.allclose(original['limits'],limits,rtol=1e-10,atol=1e-10)),reason)
                    palette=palette_check(image,bar,box)
                    check(checks,'colourbar_palette_and_direction',None,palette,palette['passed'])
            records.append({'figure':name,'id':result.analysis_id,'candidate_sha256':frozen[name]['sha256'],
                            'native_sha256':sha256(NATIVE/name),'native_metadata':native['path'],
                            'native_metadata_sha256':sha256(ROOT/native['path']),
                            'native_figure_index':native['index'],'checks':checks,
                            'axis_annotations':[[t.get_text() for t in a.texts] for a in axes],
                            'figure_annotations':[t.get_text() for t in figure.texts]})
            figure.clear();gc.collect()
    assert len(records)==51,len(records)
    write_json(FOLDER/'semantic-comparison.json',{
        'method':'Native metadata comparison with explicit prior scientific decisions. Production artists constructed from the verified computation cache; no exports changed. Palette samples use 64 interior native PNG samples, nearest exact production LUT entry and monotonic direction (RGB distance <=2).',
        'implementation':baseline['production_modules'],
        'annotation_reference':'Six MLE value boxes transcribed from native PNGs, independently reviewed in detail-review; rose/ternary labels checked against native source and paired previews.',
        'records':records,'issues':[{'figure':r['figure'],**c} for r in records for c in r['checks'] if c['status']=='issue']})
    for r in records:
        for c in r['checks']:
            if c['status']=='issue':print(r['figure'],c,flush=True)
    print('Semantic figures:',len(records),'; issues:',sum(c['status']=='issue' for r in records for c in r['checks']),flush=True)


if __name__=='__main__':main()
