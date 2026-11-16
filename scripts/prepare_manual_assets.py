"""Prepare documented copies of approved scientific figures for the LaTeX manual.

Original reference PNGs are read-only. UI captures come from capture_sprint2.py
on the unchanged SD11A example; cropped panels improve printed legibility.
"""
import hashlib,json,re,shutil
from pathlib import Path
from PIL import Image
from reference_common import ROOT,sha256,write_json


def main():
    output=ROOT/'docs/manual/assets';output.mkdir(parents=True,exist_ok=True)
    tex='\n'.join(p.read_text() for p in (ROOT/'docs/manual').rglob('*.tex'))
    used=set(re.findall(r'\\(?:plotfig|uifig)\{([^}]+\.png)\}',tex))
    used.update(re.findall(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+\.png)\}',tex))
    accepted=json.loads((ROOT/'tests/reference/sprint16/delivery/point-2/summary.json').read_text())
    records=[]
    for item in accepted['figures']:
        source=ROOT/item['accepted_reference'];assert sha256(source)==item['reference_sha256']
        stem=re.sub(r'^(gui)?FracPaQ2D_?', '', source.stem)
        stem=re.sub(r'_(SD11A|extra)$','',stem)
        path=output/(stem+'.png')
        if path.name not in used:continue
        with Image.open(source) as image:
            image=image.convert('RGB');image.thumbnail((1700,1700),Image.Resampling.LANCZOS)
            image.save(path,optimize=True)
        records.append({'asset':path.name,'source':str(source.relative_to(ROOT)),'source_sha256':sha256(source),'sha256':sha256(path),'operation':'1700px maximum, RGB; full uncropped scientific canvas'})
    ui=Path('/tmp/pyfracpaq-manual-ui')
    for name in ('initial','preview','maps','lengths','angles','fluid','wavelets','graphs'):
        if 'ui-'+name+'.png' not in used:continue
        source=ui/(name+'.png')
        with Image.open(source) as image:
            crop=image if name in ('initial','preview') else image.crop((783,72,1247,554))
            path=output/('ui-'+name+'.png');crop.save(path,optimize=True)
        records.append({'asset':path.name,'source':'capture_sprint2.py --input examples/SD11A.txt --width 1250 --height 739','source_sha256':sha256(source),'sha256':sha256(path),'operation':'Full window' if name in ('initial','preview') else 'Analysis panel crop; original controls unchanged'})
    source=ROOT/'pyfracpaq/resources/pyfracpaq-logo.png';shutil.copyfile(source,output/'logo.png')
    source=ROOT/'tests/reference/sprint16/auxiliary/preprocess.png'
    with Image.open(source) as image:
        image=image.convert('RGB');image.thumbnail((1700,1700));image.save(output/'preprocess.png',optimize=True)
    write_json(ROOT/'docs/manual/figure-provenance.json',{'scope':'Manual-only image copies; approved scientific originals preserved. UI: Qt offscreen actual widgets, illustration viewport1250x739.', 'input_sha256':sha256(ROOT/'examples/SD11A.txt'),'figures':records,'extra_assets':['logo.png (resource copy)','preprocess.png (approved auxiliary preprocessing panel)']})
    print('Prepared',len(records)+2,'manual assets without altering references.')

if __name__=='__main__':main()
