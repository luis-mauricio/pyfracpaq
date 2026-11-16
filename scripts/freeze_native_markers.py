"""Freeze transparent primitive materials from the independent MATLAB atlas.

Only the two material coverage channels are stored, not scientific plots or
reference data. Black edges/blue faces on white allow exact alpha separation.
"""

import json
from pathlib import Path

import numpy as np
from PIL import Image

from reference_common import ROOT, REFERENCE, sha256, write_json


def main():
    folder=REFERENCE/'sprint16/final/native-marker-atlas'
    spec=json.loads((folder/'atlas.json').read_text())
    source=folder/'marker_primitives_atlas.png';image=np.asarray(Image.open(source).convert('RGB'))
    height,width=image.shape[:2];arrays={};records=[]
    for entry in spec['entries']:
        x=entry['x'];y=entry['y']
        x0=int((x-.5)*width/8);x1=int((x+.5)*width/8)
        y0=int((7.5-y)*height/8);y1=int((8.5-y)*height/8)
        cell=image[y0:y1,x0:x1];ink=cell[:,:,0]<128;yy,xx=np.where(ink)
        assert xx.size,'Empty glyph cell'
        cx=int(round((int(xx.min())+int(xx.max()))/2))+x0
        cy=int(round((int(yy.min())+int(yy.max()))/2))+y0
        pad=int(np.ceil((entry['size_points']/2+entry['linewidth_points']+2)*600/72))
        tile=image[cy-pad:cy+pad+1,cx-pad:cx+pad+1].astype(np.int16)
        assert tile.shape==(pad*2+1,pad*2+1,3)
        # R=G=remaining white background; B=background+blue face.
        assert np.array_equal(tile[:,:,0],tile[:,:,1])
        edge=255-tile[:,:,2];face=tile[:,:,2]-tile[:,:,0]
        assert np.all((edge>=0)&(face>=0)&(edge+face<=255))
        if not entry['filled']:assert not face.any()
        coverage=np.stack((edge,face),axis=2).astype(np.uint8)
        assert not coverage[[0,-1]].any() and not coverage[:,[0,-1]].any()
        key=f'{entry["shape"]}_{entry["size_points"]:g}_{entry["linewidth_points"]:g}_{int(entry["filled"])}'
        arrays[key]=coverage
        records.append({**entry,'key':key,'centre_xy':[cx,cy],'pad':pad,
                        'strong_bbox_xyxy':[int(xx.min())+x0,int(yy.min())+y0,int(xx.max())+x0,int(yy.max())+y0]})
    target=ROOT/'pyfracpaq/resources/matlab_markers.npz';np.savez_compressed(target,**arrays)
    write_json(target.with_suffix('.json'),{
        'native_version':spec['native_version'],'dpi':600,'sha256':sha256(target),
        'capture_script_sha256':sha256(ROOT/'scripts/capture_s16_marker_atlas.m'),
        'primitive_capture_sha256':sha256(source),
        'glyphs':[{k:entry[k] for k in ('key','shape','size_points','linewidth_points','filled','pad')}
                  for entry in records],
        'scope':'Independent basic-graphics primitive materials; no scientific images, observations, or MATLAB code.'})
    write_json(folder/'provenance.json',{'native_version':spec['native_version'],'source':str(source.relative_to(ROOT)),
        'source_sha256':sha256(source),'script':'scripts/capture_s16_marker_atlas.m',
        'script_sha256':sha256(ROOT/'scripts/capture_s16_marker_atlas.m'),
        'resource':str(target.relative_to(ROOT)),'resource_sha256':sha256(target),'glyphs':records,
        'scope':'Independent primitive rendering assets. Scientific goldens remain separate and unchanged.'})
    print('Frozen',len(records),'glyph materials;',target.stat().st_size,'bytes.')


if __name__=='__main__':main()
