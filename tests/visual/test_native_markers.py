"""Native marker assets validated against a separate, held-out MATLAB scene."""

import json

import numpy as np
from PIL import Image
import pytest

from pyfracpaq.plots.markers import glyph
from reference_common import REFERENCE, ROOT, sha256


@pytest.mark.parametrize('shape,centre', [('o',1346),('s',2078)])
def test_native_glyph_matches_independent_scene_at_print_dpi(shape, centre):
    source=REFERENCE/'sprint16/final/native-contexts/markers_context.png'
    rgba,pad=glyph(shape,50 if shape=='o' else 40,600/72*.5,(1,0,0,1),None,600)
    alpha=rgba[:,:,3:4]/255
    actual=np.rint(rgba[:,:,:3]*alpha+255*(1-alpha)).astype(np.uint8)
    with Image.open(source) as im:
        expected=np.asarray(im.convert('RGB'))[2279-pad:2279+pad+1,centre-pad:centre+pad+1]
    np.testing.assert_array_equal(actual,expected)


def test_atlas_provenance_and_transparent_materials_are_valid():
    record=json.loads((REFERENCE/'sprint16/final/native-marker-atlas/provenance.json').read_text())
    assert sha256(ROOT/record['resource'])==record['resource_sha256']
    with np.load(ROOT/record['resource']) as data:
        assert len(data.files)==48
        for key in data.files:
            material=data[key]
            assert material.shape[0]==material.shape[1]
            assert material.shape[0]%2==1 and material.shape[2]==2
            assert np.all(material.astype(int).sum(axis=2)<=255)
            assert not material[[0,-1]].any() and not material[:,[0,-1]].any()


def test_raster_asset_resizes_with_dpi_and_api_fallback_remains_available():
    large,pad=glyph('o',50,600/72*.5,(0,0,0,1),None,600)
    small,small_pad=glyph('o',50/6,100/72*.5,(0,0,0,1),None,100)
    assert small.shape[0]<large.shape[0] and small_pad<pad
    custom,custom_pad=glyph('o',37.2,2.3,(.2,.4,.7,1),(.9,.1,.3,1),137)
    assert custom.shape==(2*custom_pad+1,2*custom_pad+1,4)
    assert custom[:,:,3].any()
