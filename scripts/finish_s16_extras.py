from dataclasses import replace
import gc
import numpy as np
from scipy.io import loadmat
from matplotlib.backends.backend_agg import FigureCanvasAgg
from PIL import Image,ImageDraw
from pyfracpaq.io.svg import read_svg
from pyfracpaq.io.images import read_image
from pyfracpaq.io.figures import export_png
from pyfracpaq.plots.maps import render_multicolour
from pyfracpaq.plots.hough import render_hough
from reference_common import ROOT,REFERENCE,sha256,write_json
from compare_sd11a import configuration
folder=REFERENCE/'sprint16/final';out=folder/'python-extra';out.mkdir(exist_ok=True)
_,cfg=configuration();source=folder/'inputs/multicolour/network.svg';data=read_svg(source).dataset
native=loadmat(folder/'native-extra/multicolour_geometry.mat',simplify_cells=True)['alltraces']
checks=[]
for i,(trace,original) in enumerate(zip(data.traces,native,strict=True)):
 nodes=original['Node'];points=np.array([[n['x'],n['y']] for n in nodes]);colour=original['Colour']
 checks.append({'trace':i,'nodes_exact':bool(np.array_equal(points,[n.point for n in trace.nodes])),
  'colour_exact':bool(np.array_equal(colour,trace.colour)),
  'lengths_match':bool(np.allclose(original['segmentLength'],[s.length for s in trace.segments],rtol=1e-6,atol=1e-8)),
  'angles_match':bool(np.allclose(original['segmentAngle'],[s.raw_angle for s in trace.segments],rtol=1e-6,atol=1e-8))})
write_json(out/'multicolour-data.json',checks)
for output in (render_multicolour(data,cfg),render_hough(read_image(ROOT/'tests/fixtures/images/tensor_network.tif').hough)):
 FigureCanvasAgg(output.figure).draw();p=export_png(output.figure,output.basename,'extra',out)
 page=Image.new('RGB',(1200,625),'white');draw=ImageDraw.Draw(page)
 for j,base in enumerate((folder/'native-extra',out)):
  draw.text((j*600,2),'MATLAB' if j==0 else 'Python',fill='black')
  with Image.open(base/p.name) as im:
   thumb=im.convert('RGB');thumb.thumbnail((595,595));page.paste(thumb,(j*600,25))
 page.save(out/('qa-'+p.name));output.figure.clear();gc.collect();print(p.name,flush=True)
