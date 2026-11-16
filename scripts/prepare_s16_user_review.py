"""Prepare the seven requested visual comparisons from unchanged PNGs.

Crops and reduced contact sheets are review aids only. They do not replace
the original quantitative comparisons, alter source images or rerun analyses.
"""

import html
import json

from PIL import Image,ImageChops,ImageDraw,ImageFont

from reference_common import ROOT,REFERENCE,sha256,write_json

BASE=REFERENCE/'sprint16/final'
OUT=BASE/'user-review'
LABELS=[
    ('Dilatação','dilatacao'),
    ('Suscetibilidade de fraturas','suscetibilidade'),
    ('CSF','csf'),
    ('Graphs — intensidade P21','p21'),
    ('Graphs — densidade P20','p20'),
    ('Hough — vista lateral ρ','hough-rho'),
    ('Hough — vista lateral θ','hough-theta'),
]


def font(size):
    return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',size)


def pair_sheet(a,b,heading,*,width=1600,stacked=False):
    per_width=width-32 if stacked else (width-48)//2
    scale=min(1,per_width/a.width)
    dims=(round(a.width*scale),round(a.height*scale))
    views=[im.resize(dims,Image.Resampling.LANCZOS) for im in (a,b)]
    height=90+(dims[1]+38)*2 if stacked else 90+dims[1]
    sheet=Image.new('RGB',(width,height),'white');draw=ImageDraw.Draw(sheet)
    draw.text((16,10),heading,font=font(25),fill='#172033')
    for i,(label,view) in enumerate(zip(('MATLAB','Python'),views,strict=True)):
        x=16 if stacked else 16+i*(width//2)
        y=54+i*(dims[1]+38) if stacked else 54
        draw.text((x,y),label,font=font(20),fill='#485164')
        sheet.paste(view,(x,y+29))
    return sheet


def main():
    OUT.mkdir(exist_ok=True)
    status=json.loads((BASE/'status.json').read_text());records=[];title_sheets=[];hough_sheets=[]
    for index,(case,(label,slug)) in enumerate(zip(status['failed_comparable_regions'],LABELS,strict=True),1):
        is_hough=index>5
        native=(BASE/'native-extra' if is_hough else REFERENCE/'sprint16/sd11a/native')/case['figure']
        candidate=(BASE/'python-extra' if is_hough else BASE/'python')/case['figure']
        with Image.open(native) as im:a=im.convert('RGB')
        with Image.open(candidate) as im:b=im.convert('RGB')
        audited_box=case['xyxy'];original_a=a.crop(audited_box);original_b=b.crop(audited_box)
        # A common crop in original coordinates. The P20 left ruler remains in
        # the full audited strip; central close-ups do not call it title text.
        box=audited_box.copy()
        if not is_hough:
            search=[900 if index>=4 else 0,0,4200 if index>=4 else 4724,audited_box[3]]
            bounds=[]
            for im in (a,b):
                q=im.crop(search);ink=ImageChops.difference(q,Image.new('RGB',q.size,'white')).getbbox()
                bounds.append([ink[0]+search[0],ink[1],ink[2]+search[0],ink[3]])
            box=[max(search[0],min(q[0] for q in bounds)-28),max(0,min(q[1] for q in bounds)-20),
                 min(search[2],max(q[2] for q in bounds)+28),min(audited_box[3],max(q[3] for q in bounds)+20)]
        crop_a=a.crop(box);crop_b=b.crop(box)
        stem=f'{index:02d}-{slug}'
        crop_a.save(OUT/f'{stem}-matlab.png');crop_b.save(OUT/f'{stem}-python.png')
        sheet=pair_sheet(crop_a,crop_b,f'{index}. {label} — SSIM da faixa: {case["ssim_rgb"]:.6f}',stacked=not is_hough)
        sheet.save(OUT/f'{stem}-comparacao.png')
        (hough_sheets if is_hough else title_sheets).append(sheet)
        original_a.save(OUT/f'{stem}-faixa-matlab.png');original_b.save(OUT/f'{stem}-faixa-python.png')
        records.append({'index':index,'label':label,'slug':slug,'stem':stem,
                        'native':str(native.relative_to(ROOT)),'candidate':str(candidate.relative_to(ROOT)),
                        'native_sha256':sha256(native),'candidate_sha256':sha256(candidate),
                        'audited_xyxy':audited_box,'display_crop_xyxy':box,'ssim_rgb':case['ssim_rgb'],
                        'title_or_panel':'panel' if is_hough else 'title'})
    for name,sheets in [('cinco-titulos',title_sheets),('duas-vistas-hough',hough_sheets)]:
        board=Image.new('RGB',(1600,sum(s.height for s in sheets)+20*(len(sheets)-1)),'#e6e9ed');y=0
        for sheet in sheets:board.paste(sheet,(0,y));y+=sheet.height+20
        board.save(OUT/f'{name}.png')
    write_json(OUT/'manifest.json',{'source_status_sha256':sha256(BASE/'status.json'),
        'method':'Lossless common-coordinate crops of unchanged PNGs. Reduced contact sheets are review only; SSIM values retain the full original audited regions.',
        'records':records})
    sections=[];md=['# Avaliação dos sete casos','',
        'MATLAB primeiro; Python depois. As notas se referem às regiões originais da auditoria. '
        'Os recortes centrais e miniaturas são apenas recursos de inspeção, sem alterar as métricas.', '',
        '**P20:** a faixa original inclui parte do tick `0,08` do eixo Y. A escala dessa análise muda com a correção Q20 aprovada; esse tick não é parte do título. '
        'Em Graphs, marcadores próximos ao topo também podem aparecer na faixa.','',
        '[Comparador com zoom e alternância](index.html) · [Procedência e coordenadas](manifest.json)','']
    for r in records:
        stem=r['stem'];label=html.escape(r['label'])
        sections.append(f'''<section id="case-{r['index']}" data-stem="{stem}">
<h2>{r['index']}. {label}</h2><p>SSIM da região original: <strong>{r['ssim_rgb']:.6f}</strong> · referência: 0,980000</p>
<div class="controls"><button data-mode="pair">Lado a lado</button><button data-mode="blink">Alternar MATLAB/Python</button>
<button data-mode="matlab">Só MATLAB</button><button data-mode="python">Só Python</button>
<button class="actual">Pixels originais (1:1)</button><button class="fit">Ajustar à tela</button>
<label>Zoom <input type="range" min="25" max="200" value="100" step="25" class="zoom"><output>100%</output></label>
<label><input type="checkbox" class="full"> Faixa original completa</label></div>
<div class="panes"><figure><figcaption>MATLAB</figcaption><div class="viewport"><img class="native" src="{stem}-matlab.png" alt="{label}: MATLAB"></div></figure>
<figure><figcaption>Python</figcaption><div class="viewport"><img class="candidate" src="{stem}-python.png" alt="{label}: Python"></div></figure></div>
<p><a href="../../../../../{r['native']}">PNG MATLAB completo</a> · <a href="../../../../../{r['candidate']}">PNG Python completo</a> · <a href="{stem}-comparacao.png">Prancha comparativa</a></p>
</section>''')
        md.extend([f'## {r["index"]}. {r["label"]}', '',f'SSIM da faixa original: **{r["ssim_rgb"]:.6f}**.', '',
                   f'![Comparação MATLAB e Python]({stem}-comparacao.png)','',
                   f'[MATLAB — recorte 1:1]({stem}-matlab.png) · [Python — recorte 1:1]({stem}-python.png) · '
                   f'[MATLAB — faixa completa]({stem}-faixa-matlab.png) · [Python — faixa completa]({stem}-faixa-python.png)',''])
    page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>S16-04 — revisão dos sete casos</title><style>
body{font:16px/1.5 system-ui,sans-serif;color:#172033;background:#f1f3f6;margin:0;padding:24px}main{max-width:1700px;margin:auto}
section,header{background:white;border-radius:10px;padding:22px;margin:0 0 24px}h1,h2{line-height:1.2}a{color:#1459a5}nav a{display:inline-block;margin-right:18px}
.controls{display:flex;flex-wrap:wrap;gap:12px;align-items:center;margin:18px 0}button{padding:8px 12px;cursor:pointer}label{display:flex;align-items:center;gap:8px}
.panes{display:flex;gap:18px}figure{margin:0;flex:1;min-width:0}figcaption{font-weight:700;margin:0 0 8px}.viewport{overflow:auto;border:1px solid #cbd1db;background:white;max-height:75vh}
img{display:block;width:100%;max-width:none;height:auto}.single figure:nth-child(2){display:none}.single figure:first-child{flex-basis:100%}output{min-width:48px}
@media(max-width:850px){body{padding:10px}.panes{flex-direction:column}}
</style><main><header><h1>Revisão dos sete casos</h1><p>Os PNGs originais não foram alterados. Use o zoom ou a alternância para inspecionar os mesmos recortes, nas mesmas coordenadas.</p>
<p>As notas SSIM pertencem às faixas completas da auditoria; não foram recalculadas nos recortes centrais. O valor de referência é 0,98.</p>
<p><strong>Atenção ao P20:</strong> a faixa auditada contém parte do tick <code>0,08</code> do eixo Y, cuja escala muda com Q20. Esse trecho não pertence ao título. Em Graphs, também podem aparecer marcadores próximos ao topo.</p>
<nav>'''+''.join(f'<a href="#case-{r["index"]}">{r["index"]}. {html.escape(r["label"])}</a>' for r in records)+'''</nav></header>'''+''.join(sections)+'''</main><script>
document.querySelectorAll('section').forEach(section=>{
 const panes=section.querySelector('.panes'),figs=section.querySelectorAll('figure'),views=section.querySelectorAll('.viewport');
 const native=section.querySelector('.native'),candidate=section.querySelector('.candidate');let timer=null,mode='pair',blink=false,sync=false;
 const source=kind=>section.dataset.stem+(section.querySelector('.full').checked?'-faixa-':'-')+kind+'.png';
 const paint=()=>{native.src=source(mode==='python'||mode==='blink'&&blink?'python':'matlab');candidate.src=source('python');
  figs[0].querySelector('figcaption').textContent=mode==='python'||mode==='blink'&&blink?'Python':'MATLAB';panes.classList.toggle('single',mode!=='pair');};
 section.querySelectorAll('[data-mode]').forEach(button=>button.onclick=()=>{clearInterval(timer);mode=button.dataset.mode;blink=false;paint();
  if(mode==='blink')timer=setInterval(()=>{blink=!blink;paint()},800);});
 section.querySelector('.full').onchange=paint;
 [native,candidate].forEach(im=>im.addEventListener('load',()=>{if(section.querySelector('output').textContent==='1:1')im.style.width=im.naturalWidth+'px';}));
 section.querySelector('.actual').onclick=()=>{[native,candidate].forEach(im=>im.style.width=im.naturalWidth+'px');section.querySelector('output').textContent='1:1';};
 section.querySelector('.fit').onclick=()=>{[native,candidate].forEach(im=>im.style.width='100%');section.querySelector('.zoom').value=100;section.querySelector('output').textContent='100%';};
 section.querySelector('.zoom').oninput=e=>{section.querySelector('output').textContent=e.target.value+'%';[native,candidate].forEach(im=>im.style.width=e.target.value+'%');};
 views.forEach((view,i)=>view.addEventListener('scroll',()=>{if(sync)return;sync=true;views[1-i].scrollLeft=view.scrollLeft;views[1-i].scrollTop=view.scrollTop;requestAnimationFrame(()=>sync=false);}));
});</script></html>'''
    (OUT/'index.html').write_text(page);(OUT/'LEIA-ME.md').write_text('\n'.join(md))
    print('Prepared',len(records),'cases in',OUT.relative_to(ROOT))


if __name__=='__main__':main()
