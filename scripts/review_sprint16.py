"""Create review sheets and a per-family evidence map, preserving failed gates."""

import json
from pathlib import Path
import textwrap

from PIL import Image,ImageDraw
from reference_common import ROOT,REFERENCE,sha256,write_json

FOLDER=REFERENCE/'sprint16'


def main():
    report=json.loads((FOLDER/'all-outputs/validation.json').read_text())
    rows=report['figures']+[{'path':'../candidate/FracPaQ2D_Houghstuff_audit.png',
                            'qa':'../candidate/qa-FracPaQ2D_Houghstuff_audit.png'}]
    pages=[]
    for page,start in enumerate(range(0,len(rows),12),1):
        canvas=Image.new('RGB',(1600,1320),'white');draw=ImageDraw.Draw(canvas)
        for index,row in enumerate(rows[start:start+12]):
            x,y=index%4*400,index//4*440
            path=FOLDER/'all-outputs'/row['qa']
            with Image.open(path) as image:
                thumb=image.convert('RGB');thumb.thumbnail((400,400));canvas.paste(thumb,(x,y))
            draw.text((x+8,y+400),'\n'.join(textwrap.wrap(Path(row['path']).stem,48)),fill='black')
        target=FOLDER/f'review-sheet-{page}.png';canvas.save(target)
        pages.append({'path':str(target.relative_to(ROOT)),'sha256':sha256(target)})
    families={
       'Geometria/TXT':('sprint16/numeric-comparison.json','Native lengths/angles/centres match; Q07 distance deliberately corrected.'),
       'SVG':('sprint16/svg-comparison.json','Native converter emits NaN/omissions; XML correction Q09 is explicit.'),
       'Hough':('sprint16/hough_comparison.json','All seven stage arrays/threshold exact in five cases, including real rasters.'),
       'Mapas básicos/Angles/Lengths':('sprint16/candidate/validation.json','Paired native context; exact four TXT and distribution arrays.13 exploratory SSIM comparisons fail some regions.'),
       'Circular P21/P20':('sprint7/validation.json','Analytic finite geometry Q20 approved; S16 adds native Maps arrays/TXT. Corrected counts intentionally differ.'),
       'MLE/K-S':('sprint8/native_ks_comparison.json','7500 shared-vector K-S comparisons; scientific Q15 approved. S16 adds six original GUI-function PNGs; new stochastic Run is functional evidence.'),
       'I-Y-X':('sprint9/native/native_topology.json','Seven native cases plus S16 triangle/TXT. Endpoint tolerance/classification Q11 approved; not identity of defective classifications.'),
       'Crack tensors/permeabilidade':('sprint10/native_comparison.json','Native tensors/polar/K comparisons, dimensional tolerances and shared regression tests.'),
       'Estabilidade/Mohr':('sprint11/q17_comparison.json','Native defects, corrected physical values/normalization/palette and inclusive CSF; Q17 approved.'),
       'Blocos/variograma':('sprint12/native_comparison.json','Native raster/components/variogram/helper arrays; Q14 population/area correction approved.'),
       'Graphs ALONG/FROM':('sprint13/native_comparison.json','Native intersections/signed distances/profiles; circular geometry and P20 normalization explicitly approved.'),
       'Wavelets2D':('sprint14/native_comparison.json','Native kernel/FFT/helper panels and integrated raster; full production Python separately. Q12 approved. Catalog PNG is wavelet2 variant; full integrated primary MATLAB visual context still missing.'),
       'Utilitários/paletas':('sprint15/native_comparison.json','Native preprocess stages, tensor16/probe/palettes; legacy destinations audited separately.')}
    records=[]
    for name,(path,scope) in families.items():
        target=REFERENCE/path;assert target.is_file(),target
        records.append({'family':name,'evidence':str(target.relative_to(ROOT)),'sha256':sha256(target),
                        'scope':scope,'visual_acceptance':'Open; see fixed thresholds and per-context limitations.'})
    write_json(FOLDER/'family-audit.json',{'families':records,'review_sheets':pages,
       'scope':'Sheets are scaled previews for human review, never used for SSIM. '
               'The available53 native names include explicitly identified auxiliary variants; no claim that all primary GUI contexts were captured.'})
    lines=['# Galeria da auditoria S16','','53 nomes de figuras Python; miniaturas para revisão. '
           'Não são imagens usadas no cálculo de SSIM. Capturas nativas/contextos e limites estão no catálogo e family-audit.json.','']
    for page in pages:lines.append(f"![Revisão de figuras](../../{page['path']})\n")
    (ROOT/'docs/parity/sprint-16-gallery.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':main()
