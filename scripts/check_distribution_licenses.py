"""Check notices and reviewed assets in a public source ZIP, without network.

This checks the recorded distribution policy, not ownership or legal compliance
of arbitrary code. Invoke again after assembling the exact file to be delivered.
"""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

from pyfracpaq import __version__
from reference_common import ROOT


MANIFEST = 'docs/licenses/manifest.json'
FORBIDDEN_PARTS = {
    'fracpaq-matlab', 'tests', 'scripts', '.git', '.venv', '.aws', '.codex',
    '.agents', '__pycache__', 'wheelhouse', 'dist', 'build',
}
FORBIDDEN_SUFFIXES = {
    '.m', '.fig', '.whl', '.dylib', '.dll', '.so', '.pyd', '.pyc', '.pyo',
    '.exe', '.msi', '.pkg', '.dmg', '.ttf', '.otf', '.pfb', '.pfa', '.woff', '.woff2',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(content):
    return hashlib.sha256(content).hexdigest()


def validate_notices(read, names):
    """Accept a byte reader and relative file names for either a tree or a ZIP."""
    required = {'LICENSE', 'THIRD_PARTY_NOTICES.md', MANIFEST, 'requirements.txt',
                'docs/licenses/fracpaq/LICENSE',
                'docs/licenses/README.md', 'pyfracpaq/resources/cmocean_LICENSE.txt'}
    require(required <= names, f'Missing distribution notices: {sorted(required - names)}')
    data = json.loads(read(MANIFEST))
    require(data['version'] == __version__, 'License inventory has a different project version.')
    original = read('docs/licenses/fracpaq/LICENSE')
    require(original.strip() in read('LICENSE'), 'Original FracPaQ license was not retained.')
    notices = data['notice_files'] + data['dependency_notice_files']
    for notice in notices:
        path = notice['path']
        require(path in names, f'Missing notice: {path}')
        require(digest(read(path)) == notice['sha256'], f'Changed notice: {path}')
    assets = {entry['path']: entry for entry in data['assets']}
    require(len(assets) == len(data['assets']), 'Duplicate asset in license inventory.')
    resource_names = {name for name in names if name.startswith('pyfracpaq/resources/')
                      and not name.endswith('.py') and '__pycache__' not in PurePosixPath(name).parts}
    reviewed_resources = {name for name in assets if name.startswith('pyfracpaq/resources/')}
    require(resource_names == reviewed_resources,
            f'Resource inventory differs: {sorted(resource_names ^ reviewed_resources)}')
    example_names = {name for name in names if name.startswith('examples/')
                     and PurePosixPath(name).suffix not in ('.md', '.json')}
    reviewed_examples = {name for name in assets if name.startswith('examples/')}
    require(example_names == reviewed_examples,
            f'Example inventory differs: {sorted(example_names ^ reviewed_examples)}')
    manual_names = {name for name in names if name.startswith('docs/manual/assets/')}
    reviewed_manual = {name for name in assets if name.startswith('docs/manual/assets/')}
    require(manual_names == reviewed_manual,
            f'Manual image inventory differs: {sorted(manual_names ^ reviewed_manual)}')
    dependency_notices = {name for name in names if name.startswith('docs/licenses/dependencies/')}
    reviewed_notices = {entry['path'] for entry in data['dependency_notice_files']}
    require(dependency_notices == reviewed_notices, 'Dependency notice inventory differs.')
    for path, entry in assets.items():
        require(path in names, f'Missing reviewed asset: {path}')
        require(digest(read(path)) == entry['sha256'], f'Asset needs license/provenance review: {path}')
        require(bool(entry['basis']), f'No recorded license basis: {path}')
    # Pin source supplements to the dependency versions actually being delivered.
    pins = {}
    for line in read('requirements.txt').decode('utf-8').splitlines():
        if line.strip() and not line.lstrip().startswith('#') and '==' in line:
            key, version = line.strip().split('==', 1)
            pins[key.lower().replace('_', '-')] = version
    for dependency, version in data['qt_dependency_versions'].items():
        require(pins.get(dependency) == version,
                f'Qt dependency version needs review: {dependency}')
    actual_qt = {name for name in pins if name.startswith(('pyside6', 'shiboken6'))}
    require(actual_qt == set(data['qt_dependency_versions']), 'Qt dependency inventory differs.')
    return {'notice_files': len(notices), 'upstream_supplements': len(data['notice_files']),
            'reviewed_assets': len(assets)}


def validate_repository(root=ROOT):
    """Check the working tree; development references are allowed outside the ZIP."""
    names = {str(path.relative_to(root)) for base in ('pyfracpaq', 'docs/licenses', 'examples', 'docs/manual')
             for path in (root / base).rglob('*') if path.is_file()
             and '__pycache__' not in path.parts}
    names.update({'LICENSE', 'THIRD_PARTY_NOTICES.md', 'requirements.txt'})
    return validate_notices(lambda name: (root / name).read_bytes(), names)


def validate_archive(path):
    prefix = f'pyfracpaq-{__version__}'
    with zipfile.ZipFile(path) as archive:
        require(archive.testzip() is None, 'ZIP checksum failure.')
        entries = archive.namelist()
        require(len(entries) == len(set(entries)), 'Duplicate path in public ZIP.')
        names = set()
        for name in entries:
            parts = PurePosixPath(name).parts
            require(parts and parts[0] == prefix and '..' not in parts and '\\' not in name,
                    f'Unexpected archive path: {name}')
            relative = PurePosixPath(*parts[1:])
            require(not FORBIDDEN_PARTS.intersection(parts[1:]), f'Private/development content: {name}')
            require(relative.suffix.lower() not in FORBIDDEN_SUFFIXES,
                    f'Binary or original MATLAB file in public ZIP: {name}')
            require(not any(part.startswith(('.env', 'wheelhouse')) for part in parts[1:]),
                    f'Unexpected environment/dependency content: {name}')
            # Unix symlink file type encoded in the upper mode bits.
            require((archive.getinfo(name).external_attr >> 16) & 0o170000 != 0o120000,
                    f'Symlink in public ZIP: {name}')
            if not name.endswith('/'):
                names.add(str(relative))
        report = validate_notices(lambda name: archive.read(f'{prefix}/{name}'), names)
    return {'version': __version__, 'files': len(names), **report,
            'matlab_distribution_included': False, 'bundled_dependencies_included': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, help='Exact public source ZIP to check.')
    args = parser.parse_args()
    result = validate_archive(args.archive) if args.archive else validate_repository()
    print(json.dumps(result, ensure_ascii=False))
