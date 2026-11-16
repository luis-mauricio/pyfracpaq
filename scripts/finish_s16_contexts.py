"""Production and identical-raster CWT comparisons for both integrated kernels."""

from dataclasses import replace
import gc
import json
from pathlib import Path
import argparse
import pickle
import time

import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np
from scipy.io import loadmat

from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.analysis.wavelets import WaveletParameters, analyse_wavelet_image
from pyfracpaq.domain.execution import RunContext
from pyfracpaq.io import read_txt
from pyfracpaq.io.figures import export_png
from compare_sd11a import configuration, SOURCE
from reference_common import ROOT, REFERENCE, sha256, write_json

FOLDER=REFERENCE/'sprint16/final'


def seq(value):return [value] if isinstance(value,dict) else list(value)


def cells(value):
    if hasattr(value,'_fieldnames'):
        return {name:cells(getattr(value,name)) for name in value._fieldnames}
    if isinstance(value,dict):return {k:cells(v) for k,v in value.items()}
    if isinstance(value,np.ndarray) and value.dtype==object:return [cells(v) for v in value]
    return value


def main(render_only=False):
    _,base=configuration();data=read_txt(SOURCE);registry=AnalysisRegistry()
    context=json.loads((FOLDER/'native-contexts/contexts.json').read_text())
    assert context['records']['morlet']['success'] and context['records']['mexican']['success']
    records=[]
    for kind in ('morlet','mexican'):
        native=FOLDER/'native-contexts'/kind;folder=FOLDER/'python-contexts'/kind
        folder.mkdir(parents=True,exist_ok=True);start=time.perf_counter()
        cfg=replace(base,selected=('WAV-01',),tag='context',values=tuple({**dict(base.values),
            'edit_aString':'16 32','edit_LString':'2 4','edit_DegString':'30',
            'radiobutton_Morlet':kind=='morlet','radiobutton_Mexican':kind=='mexican'}.items()))
        cache=Path('/tmp')/f'pyfracpaq-s16-cwt-{kind}.pkl'
        if render_only:
            metadata=json.loads(cache.with_suffix('.json').read_text())
            from finish_s16 import manifest
            assert metadata['sha256']==sha256(cache) and metadata['implementation']==manifest()
            production,shared=pickle.loads(cache.read_bytes())
        else:
            production=registry.execute(data,RunContext(cfg,folder,folder,'context'),lambda *_:None,lambda:False)[0].data
        spec=next(s for s in registry.specs if s.id=='WAV-01')
        files=[]
        for figure in spec.render(production,cfg):
            FigureCanvasAgg(figure.figure).draw();path=export_png(figure.figure,figure.basename,'context',folder)
            files.append({'path':str(path.relative_to(ROOT)),'sha256':sha256(path)})
            figure.figure.clear();gc.collect()
        panels=cells(loadmat(native/'panels.mat',simplify_cells=True)['capture'])
        expected={};histograms={};image=None
        for figure in panels:
            for ax in seq(figure):
                title=str(ax['title']);images=ax['images']
                if 'Binary image' in title:image=np.asarray(images)
                elif 'WC map, a=' in title:
                    scale=16 if 'a=16' in title else 32;expected[scale]=np.asarray(images)
                elif 'WC histogram, a=' in title:
                    scale=16 if 'a=16' in title else 32;histograms[scale]=ax['bars']
        assert image is not None and image.shape==(1944,1944)
        if not render_only:
            shared=analyse_wavelet_image(image,WaveletParameters((16,32),(2,4),30,kind))
            cache.write_bytes(pickle.dumps((production,shared),protocol=pickle.HIGHEST_PROTOCOL))
            from finish_s16 import manifest
            write_json(cache.with_suffix('.json'),{'sha256':sha256(cache),'implementation':manifest()})
        shared_folder=FOLDER/'shared-native-pixels'/kind
        shared_folder.mkdir(parents=True,exist_ok=True)
        shared_files=[]
        for figure in spec.render(shared,cfg):
            FigureCanvasAgg(figure.figure).draw()
            path=export_png(figure.figure,figure.basename,'context',shared_folder)
            shared_files.append({'path':str(path.relative_to(ROOT)),'sha256':sha256(path)})
            figure.figure.clear();gc.collect()
        comparisons=[]
        for i,scale in enumerate(shared.scales):
            source=expected[scale.scale];selected=source>source.max()*.5
            angles=np.loadtxt(native/f'FracPaQ2Dwavelet_theta_a{scale.scale}_context.txt')
            candidate=production.scales[i]
            histogram=histograms[scale.scale]
            if isinstance(histogram,list):histogram=histogram[0]
            comparisons.append({'scale':scale.scale,
                'coefficients_pass':bool(np.allclose(scale.coefficients,source,rtol=1e-6,atol=1e-8)),
                'maximum_absolute_error':float(np.max(np.abs(scale.coefficients-source))),
                'selection_exact':bool(np.array_equal(scale.selected,selected)),
                'doubled_angles_exact':bool(np.array_equal(scale.doubled_degrees,angles)),
                'histogram_centres_pass':bool(np.allclose(scale.histogram_centres,histogram['x'],rtol=1e-6,atol=1e-8)),
                'histogram_log_counts_pass':bool(np.allclose(np.log10(scale.histogram_counts),histogram['y'],rtol=1e-6,atol=1e-8)),
                'native_angle_count':int(angles.size),'shared_angle_count':int(scale.doubled_degrees.size),
                'production_angle_count':int(candidate.doubled_degrees.size),
                'production_native_maximum_coefficient_difference':float(np.max(np.abs(candidate.coefficients-source))),
                'production_native_raster_difference_fraction':float(np.mean(production.image!=image))})
        records.append({'kernel':kind,'input_sha256':sha256(SOURCE),'parameters':context['wavelets'],
                        'comparisons':comparisons,'production_pngs':files,'shared_native_pixels_pngs':shared_files,
                        'seconds':time.perf_counter()-start,
                        'scope':'Shared native pixels test CWT independently; production Run retains the approved Q12 raster.'})
        write_json(FOLDER/'wavelet-context-comparison.json',records)
        print(kind,comparisons,flush=True)
        del production,shared;gc.collect()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render-only',action='store_true')
    main(parser.parse_args().render_only)
