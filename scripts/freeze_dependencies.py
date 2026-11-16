"""Freeze the resolved CPython 3.13 host environment, including transitives."""

import argparse
import importlib.metadata as metadata
import json
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from reference_common import REFERENCE, ROOT, sha256, write_json

RUNTIME = ['PySide6', 'matplotlib', 'numpy', 'scipy', 'scikit-image',
           'Pillow', 'defusedxml']
DEVELOPMENT = ['pytest', 'pytest-qt', 'pypdf', 'setuptools']


def closure(roots: list[str]) -> dict[str, str]:
    result = {}
    pending = list(roots)
    while pending:
        name = pending.pop()
        key = canonicalize_name(name)
        if key in result:
            continue
        dist = metadata.distribution(name)
        result[key] = dist.version
        for text in dist.requires or []:
            req = Requirement(text)
            if req.marker is None or req.marker.evaluate({'extra': ''}):
                pending.append(req.name)
    return dict(sorted(result.items()))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pip-report', action='append', type=Path, required=True,
                        help='Relatório pip --report da resolução a congelar; repetível.')
    args = parser.parse_args()
    runtime = closure(RUNTIME)
    dev = {key: version for key, version in closure(DEVELOPMENT).items()
           if key not in runtime}
    for name, packages in [('requirements.txt', runtime), ('requirements-dev.txt', dev)]:
        header = '# Resolvido em CPython 3.13.18 / macOS arm64; ver docs/decisions/0001-environment.md.\n'
        if name == 'requirements-dev.txt':
            header += '-r requirements.txt\n\n'
        (ROOT / name).write_text(header + ''.join(f'{key}=={version}\n'
                                                 for key, version in packages.items()))
    entries = []
    notices = ROOT / 'docs' / 'licenses' / 'dependencies'
    for key in sorted(runtime.keys() | dev.keys()):
        dist = metadata.distribution(key)
        licenses = []
        for item in dist.files or []:
            if '.dist-info/' not in str(item):
                continue
            parts = Path(str(item)).parts
            relative = (str(Path(*parts[1:])) if parts[0].endswith('.dist-info')
                        else str(Path('vendored') / Path(str(item))))
            if not any(part.upper().startswith(('LICENSE', 'COPYING', 'NOTICE'))
                       for part in Path(relative).parts):
                continue
            path = Path(dist.locate_file(item))
            destination = notices / key / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(path.read_bytes())
            licenses.append({'path': str(destination.relative_to(ROOT)),
                             'wheel_path': str(item),
                             'sha256': sha256(destination)})
        entries.append({'name': key, 'version': dist.version,
                        'role': 'runtime' if key in runtime else 'development',
                        'license_expression': dist.metadata.get('License-Expression'),
                        'license_metadata': dist.metadata.get('License'),
                        'license_classifiers': [v for v in dist.metadata.get_all('Classifier', [])
                                                if v.startswith('License')],
                        'notices_status': 'copied_from_wheel' if licenses else
                                          'no_notice_file_in_wheel; license metadata preserved',
                        'notices': licenses})
    license_manifest = REFERENCE / 'dependency_licenses.json'
    if license_manifest.exists():
        previous = json.loads(license_manifest.read_text())
        old_paths = {n['path'] for d in previous for n in d['notices']}
        new_paths = {n['path'] for d in entries for n in d['notices']}
        for path in old_paths - new_paths:
            stale = ROOT / path
            if stale.is_relative_to(notices) and stale.is_file():
                stale.unlink()
    write_json(license_manifest, entries)
    # Only public wheel URLs and digests, never local paths or credentials.
    downloads = []
    for path in args.pip_report:
        report = json.loads(path.read_text())
        for entry in report['install']:
            downloads.append({'name': entry['metadata']['name'],
                              'version': entry['metadata']['version'],
                              'download': entry['download_info']})
    write_json(REFERENCE / 'dependency_resolution.json', {
        'python': '3.13.18', 'platform': 'macOS arm64',
        'runtime_roots': RUNTIME, 'development_roots': DEVELOPMENT,
        'downloads': downloads,
        'scope': 'Resolução verificada neste host; outros SOs ainda não validados.',
    })
    print(f'{len(runtime)} pins de execução; {len(dev)} pins de desenvolvimento.')


if __name__ == '__main__':
    main()
