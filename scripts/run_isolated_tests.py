"""Run the strict suite in a snapshot containing exactly the original164 files.

Existing user outputs alongside the MATLAB sources are preserved in place;
the manifest verifier is not relaxed or monkeypatched.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from reference_common import ROOT, sha256, write_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python',type=Path,default=Path(os.sys.executable))
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    stage=Path(tempfile.mkdtemp(prefix='pyfracpaq-s16-tests-'))
    ignored=shutil.ignore_patterns('.venv','venv','env','.git','.codex','.agents','.aws','.env*',
        '__pycache__','.pytest_cache','build','dist','*.egg-info','fracpaq-matlab','.DS_Store','FracPaQ2D*')
    shutil.copytree(ROOT,stage,dirs_exist_ok=True,ignore=ignored)
    baseline=json.loads((ROOT/'tests/reference/source_manifest.json').read_text())['files']
    # The broad root output pattern above is intentionally restored for tests'
    # golden files: ignore it only at the project root, not inside references.
    shutil.copytree(ROOT/'tests',stage/'tests',dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__','.pytest_cache'))
    for entry in baseline:
        source=ROOT/'fracpaq-matlab'/entry['path'];assert sha256(source)==entry['sha256']
        target=stage/'fracpaq-matlab'/entry['path'];target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
    junit=stage/'junit.xml';start=__import__('time').perf_counter()
    result=subprocess.run([str(args.python.absolute()),'-m','pytest','-q',f'--junitxml={junit}'],cwd=stage,
        env={**os.environ,'QT_QPA_PLATFORM':'offscreen','MPLCONFIGDIR':'/tmp/pyfracpaq-matplotlib'},
        capture_output=True,text=True)
    preserved=args.report.absolute().with_suffix('.xml')
    preserved.parent.mkdir(parents=True,exist_ok=True)
    if junit.exists():shutil.copyfile(junit,preserved)
    report={'stage':str(stage),'interpreter':str(args.python.absolute()),'exit_code':result.returncode,
        'seconds':__import__('time').perf_counter()-start,'stdout':result.stdout,'stderr':result.stderr,
        'junit':str(preserved) if junit.exists() else None,
        'junit_sha256':sha256(junit) if junit.exists() else None,
        'source_manifest':'Exact164 originals; all user extras remain untouched in the working folder.'}
    write_json(args.report,report)
    print(result.stdout);print(result.stderr)
    raise SystemExit(result.returncode)


if __name__=='__main__':main()
