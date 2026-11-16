"""Freeze the stipple material from isolated, data-free grid primitives.

The raster backend's phase has discontinuities along a long printed line.
This is a one-dimensional graphic material, never a scientific plot crop.
It is used only for the captured 20 cm/600 dpi square-ruler viewport; other
viewports retain procedural stippling.
"""

import json
import numpy as np
from PIL import Image
from scipy.ndimage import label

from reference_common import ROOT,REFERENCE,sha256,write_json


def main():
    folder=REFERENCE/'sprint16/final/native-grid-primitives'
    capture=json.loads((folder/'capture.json').read_text());patterns={};sources=[]
    for viewport in ('square','rectangular'):
        for direction in ('vertical','horizontal'):
            suffix='' if viewport=='square' else '_rectangular'
            path=folder/f'grid_{direction}{suffix}_primitive.png'
            image=np.array(Image.open(path).convert('RGB'))
            mask=np.all(image==198,axis=2)
            axis=0 if direction=='vertical' else 1
            components,n=label(mask.sum(axis=axis)>500)
            centres=[int(round(np.flatnonzero(components==i).mean())) for i in range(1,n+1)]
            strips=[mask[:,c] if axis==0 else mask[c,:] for c in centres]
            assert len(strips)>20
            patterns[viewport+'_'+direction]=np.sum(strips,axis=0)>len(strips)/2
            sources.append({'path':str(path.relative_to(ROOT)),'sha256':sha256(path),
                            'strip_centres':centres})
    target=ROOT/'pyfracpaq/resources/matlab_grids.npz'
    np.savez_compressed(target,**patterns)
    write_json(ROOT/'pyfracpaq/resources/matlab_grids.json',{
        **capture,'resource_sha256':sha256(target),'sources':sources,
        'script':'scripts/capture_s16_grid_primitives.m',
        'script_sha256':sha256(ROOT/'scripts/capture_s16_grid_primitives.m'),
        'viewports_xyxy_image_pixels':{'square':[613,448,4275,4109],'rectangular':[613,353,4275,4204]},
        'rectangular_script_sha256':sha256(ROOT/'scripts/capture_s16_text_and_rect.m'),
        'scope':'One-dimensional opaque-grid stipple material from independent primitives; no scientific data.'})
    print(target.name,target.stat().st_size,'bytes')


if __name__=='__main__':main()
