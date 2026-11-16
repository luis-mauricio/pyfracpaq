"""Independent native-frame checks for legends and MLE parameter annotations.

These additional checks preserve the complete primary partition. No pixels
are removed, masked or realigned; the added regions intentionally overlap
their parent panels to inspect the text and legend separately.
"""

import json
from pathlib import Path

import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.ndimage import label,find_objects
from skimage.metrics import structural_similarity

from reference_common import ROOT,REFERENCE,sha256,write_json

FOLDER=REFERENCE/'sprint16/final'
NATIVE=REFERENCE/'sprint16/sd11a/native'


def frames(image,ink):
    mask=(image.max(2)-image.min(2)<=1)&(abs(image[:,:,0].astype(int)-ink)<=1)
    components,_=label(mask);result=[]
    for slices in find_objects(components):
        yy,xx=slices;width=xx.stop-xx.start;height=yy.stop-yy.start
        if width<250 or not 70<=height<700:continue
        cell=mask[slices]
        edges=[cell[:4].any(0).mean(),cell[-4:].any(0).mean(),
               cell[:,:4].any(1).mean(),cell[:,-4:].any(1).mean()]
        if min(edges)>.65:result.append([xx.start,yy.start,xx.stop,yy.stop])
    return result


def main():
    out=FOLDER/'detail-review';out.mkdir(exist_ok=True)
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',22)
    records=[];pages=[];catalog=[];expected=0
    names=[r['path'] for r in json.loads((FOLDER/'python/validation.json').read_text())]
    for name in names:
        if not any(k in name for k in ('Fitting','Mohrplot','cracktensor','IYXnodes','graphtracemap')):continue
        native=NATIVE/name;candidate=FOLDER/'python'/name
        with Image.open(native) as im:a=np.array(im.convert('RGB'))
        with Image.open(candidate) as im:b=np.array(im.convert('RGB'))
        regions=[];crops=[('legend',38)]
        if 'Fitting' in name:crops.append(('parameter_annotation',0))
        for kind,ink in crops:
            boxes=frames(a,ink);assert len(boxes)==1,(name,kind,boxes)
            box=boxes[0]
            # Two-point-scale whitespace around the independently found frame.
            x0,y0,x1,y1=box;box=[max(0,x0-16),max(0,y0-16),min(a.shape[1],x1+16),min(a.shape[0],y1+16)]
            x0,y0,x1,y1=box;left=a[y0:y1,x0:x1];right=b[y0:y1,x0:x1]
            score=float(structural_similarity(left,right,channel_axis=2,data_range=255))
            region={'name':kind,'xyxy':box,'ssim_rgb':score,'threshold':.98,
                    'passed':score>=.98,'exception':None,'native_frame_detection_ink':ink}
            regions.append(region);expected+=1
            stem=f'{expected:02d}-{kind}-{name[:-4]}'
            # Wider native-defined context for review, so a displaced candidate
            # frame is fully visible. Quantitative ROI/score stays unchanged.
            bx0,by0,bx1,by1=boxes[0]
            display=[max(0,bx0-80),max(0,by0-80),min(a.shape[1],bx1+80),min(a.shape[0],by1+80)]
            dx0,dy0,dx1,dy1=display
            view_left=a[dy0:dy1,dx0:dx1];view_right=b[dy0:dy1,dx0:dx1]
            width=max(1200,view_left.shape[1]+32);height=100+view_left.shape[0]*2+44
            sheet=Image.new('RGB',(width,height),'white');draw=ImageDraw.Draw(sheet)
            draw.text((16,8),f'{expected}. {kind} — SSIM {score:.6f}',font=font,fill='black')
            draw.text((16,40),'MATLAB',font=font,fill='black');sheet.paste(Image.fromarray(view_left),(16,70))
            draw.text((16,86+view_left.shape[0]),'Python',font=font,fill='black');sheet.paste(Image.fromarray(view_right),(16,116+view_left.shape[0]))
            path=out/(stem+'.png');sheet.save(path)
            catalog.append({'index':expected,'figure':name,'region':kind,'path':str(path.relative_to(ROOT)),
                            'ssim_rgb':score,'passed':score>=.98,'xyxy':box,'display_xyxy':display})
            if score<.98:pages.append(f'<h2>{expected}. {name} — {kind}</h2><p>SSIM: {score:.6f}; referência 0,98.</p><a href="{path.name}"><img src="{path.name}"></a>')
        records.append({'name':name,'native_sha256':sha256(native),'candidate_sha256':sha256(candidate),
                        'regions':regions,'comparable_regions_pass':all(r['passed'] for r in regions)})
    assert expected==16,expected
    write_json(FOLDER/'detail-region-comparison.json',{
        'method':'Native-only rectangular-frame detection, 16-pixel margin; unchanged RGB SSIM. Supplementary regions retain the complete primary partition and intentionally overlap its panels.',
        'records':records,'catalog':catalog})
    marker_note='<p><strong>Marcadores atualizados:</strong> quadrados e círculos geométricos normais, conforme solicitado. <a href="../marker-review/index.html">Veja o antes/depois.</a> Consulte o <a href="../user-visual-acceptance.json">registro de aceites</a>, vinculado aos hashes das imagens e aos recortes atuais.</p>' if (FOLDER/'marker-change.json').exists() else ''
    (out/'index.html').write_text('<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Legendas e anotações — S16</title><style>body{font:16px system-ui;max-width:1300px;margin:30px auto;padding:16px}img{max-width:100%;height:auto;border:1px solid #ddd}h2{margin-top:48px}</style><h1>Legendas e caixas de parâmetros</h1>'+marker_note+'<p>MATLAB acima; Python abaixo. Mesmas coordenadas nos dois PNGs, sem alinhamento ou alteração. Clique para abrir os pixels originais. As notas pertencem aos recortes quantitativos; a prancha inclui contexto maior para mostrar eventuais deslocamentos.</p><p><strong>O que avaliar:</strong> fonte, espaçamento, tamanho dos símbolos e posição das molduras. Na legenda Graphs (caso 16), as cores dos pequenos traços também diferem; os quadrados continuam identificando corretamente os dois pontos.</p><p><strong>Caso 12:</strong> a mudança de μ/σ no ajuste lognormal de segmentos decorre da correção científica Q15 já aprovada. Essa diferença numérica não é uma nova proposta; aqui se avalia a apresentação da caixa.</p>'+''.join(pages)+'</html>')
    (out/'LEIA-ME.md').write_text('# Legendas e caixas de parâmetros\n\n[Galeria das diferenças visuais](index.html)\n\n'+ '\n'.join(f'- {r["index"]}. [{r["figure"]} — {r["region"]}]({Path(r["path"]).name}): SSIM {r["ssim_rgb"]:.6f}.' for r in catalog)+'\n')
    print('Regions:',expected,'; below threshold:',sum(not r['passed'] for r in catalog))
    for r in catalog:print(r['index'],r['figure'],r['region'],round(r['ssim_rgb'],6),flush=True)


if __name__=='__main__':main()
