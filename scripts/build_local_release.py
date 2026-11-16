"""Package the audited local candidate, exact original baseline and offline wheels."""

import argparse
import json
from pathlib import Path
import shutil
import tempfile
import zipfile

from reference_common import ROOT, sha256, write_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheelhouse',type=Path,required=True)
    args=parser.parse_args()
    dist=ROOT/'dist';dist.mkdir(exist_ok=True)
    wheel=dist/'pyfracpaq-0.1.0rc1-py3-none-any.whl'
    assert wheel.is_file(),'Build the wheel before packaging.'
    offline=dist/'wheelhouse-macos-arm64';offline.mkdir(exist_ok=True)
    packages=[]
    for source in sorted(args.wheelhouse.glob('*.whl')):
        target=offline/source.name
        if not target.exists() or sha256(target)!=sha256(source):shutil.copyfile(source,target)
        packages.append({'name':target.name,'bytes':target.stat().st_size,'sha256':sha256(target)})
    assert len(packages)==32, 'Expected the actually resolved32 pinned dependency wheels.'
    (offline/'SHA256SUMS').write_text(''.join(f"{p['sha256']}  {p['name']}\n" for p in packages))
    names=['pyfracpaq','scripts','tests','docs','examples','.vscode', '.gitignore',
           'AGENTS.md','PRD.md','FUNCIONALIDADES_FRACPAQ.md','README.md','CHANGELOG.md',
           'LICENSE','THIRD_PARTY_NOTICES.md','pyproject.toml','requirements.txt',
           'requirements-dev.txt','run_gui.py']
    paths=[]
    for name in names:
        path=ROOT/name
        paths.extend(p for p in path.rglob('*') if p.is_file()) if path.is_dir() else paths.append(path)
    paths=[p for p in paths if '__pycache__' not in p.parts and '.pytest_cache' not in p.parts
           and p.name!='.DS_Store' and not p.name.startswith('.env') and p.suffix!='.pyc']
    manifest=json.loads((ROOT/'tests/reference/source_manifest.json').read_text())['files']
    for entry in manifest:
        path=ROOT/'fracpaq-matlab'/entry['path'];assert sha256(path)==entry['sha256'];paths.append(path)
    target=dist/'pyfracpaq-0.1.0rc1-source.zip'
    with tempfile.NamedTemporaryFile(prefix='.pyfracpaq-release-',suffix='.zip',dir=dist,delete=False) as f:
        temporary=Path(f.name)
    try:
        with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as archive:
            for path in sorted(set(paths)):
                info=zipfile.ZipInfo('pyfracpaq-0.1.0rc1/'+str(path.relative_to(ROOT)),date_time=(2026,11,14,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
                archive.writestr(info,path.read_bytes())
        with zipfile.ZipFile(temporary) as archive:assert archive.testzip() is None
        temporary.replace(target)
    finally:
        if temporary.exists():temporary.unlink()
    artifacts=[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha256(p)} for p in (wheel,target)]
    write_json(dist/'release-manifest.json',{'version':'0.1.0rc1','reference':'FracPaQ2.8',
       'status':'Local release candidate; full visual parity and stable release remain unapproved.',
       'platform':'macOS arm64 / CPython3.13.18; Windows/Linux deferred by user',
       'artifacts':artifacts,'dependencies':packages,'original_baseline_files':len(manifest),
       'user_outputs_included':False,'notes':'Source archive includes the exact164 original reference files, '
       'test evidence and docs. Excludes venvs, secrets, caches, root user outputs and eight extra original-folder outputs. '
       'Offline wheels are distributed separately in wheelhouse-macos-arm64.'})
    (dist/'SHA256SUMS').write_text(''.join(f"{p['sha256']}  {Path(p['path']).name}\n" for p in artifacts))
    print(f'Local candidate: {len(paths)} source files; {len(packages)} dependency wheels. Manifest saved.')


if __name__=='__main__':main()
