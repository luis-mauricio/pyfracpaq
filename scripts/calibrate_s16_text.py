"""Evaluate free-font outline painting on an independent native TeX scene."""

import gc
from pathlib import Path

import numpy as np
from PIL import Image
from matplotlib.backends.backend_agg import FigureCanvasAgg
from skimage.metrics import structural_similarity

from pyfracpaq.plots.style import figure_axes,matlab_style,title
from pyfracpaq.plots import tex
from reference_common import REFERENCE,ROOT,sha256,write_json


def main():
    source=REFERENCE/'sprint16/final/native-grid-primitives/mixed_text_primitive.png'
    with Image.open(source) as im:expected=np.array(im.convert('RGB'))[:440,700:4300]
    records=[]
    for stroke in (None,0,.02,.04,.06,.08,.10,.12):
        tex.ARIAL_OUTLINE_STROKE=stroke
        with matlab_style():
            figure,axes=figure_axes((.13,.11,.775,.815));axes.set_box_aspect(1)
            axes.set(xlim=(0,1),ylim=(0,1),xlabel='X, pixels',ylabel='Y, pixels')
            title(axes,r'Normalised slip tendency for $\sigma_1$=100 MPa, $\sigma_2$=50 MPa, $\theta$=0°')
        figure.set_dpi(600);canvas=FigureCanvasAgg(figure);canvas.draw()
        actual=np.asarray(canvas.buffer_rgba())[:440,700:4300,:3]
        score=float(structural_similarity(expected,actual,channel_axis=2,data_range=255))
        records.append({'stroke_points':stroke,'ssim_rgb':score})
        print(records[-1],flush=True);figure.clear();gc.collect()
    write_json(REFERENCE/'sprint16/final/text-outline-calibration.json',{
        'native_sha256':sha256(source),'script_sha256':sha256(ROOT/'scripts/calibrate_s16_text.py'),
        'region_xyxy':[700,0,4300,440],'records':records})


if __name__=='__main__':main()
