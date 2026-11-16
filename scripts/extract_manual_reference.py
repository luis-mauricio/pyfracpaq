"""Obtain supporting manual images; never label them as MATLAB golden files."""

import argparse
import logging
import os
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import LimitReachedError

from reference_common import ORIGINAL, REFERENCE, ROOT, sha256, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path,
                        default=REFERENCE / 'manual')
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    logging.getLogger('pypdf').setLevel(logging.ERROR)
    source = ORIGINAL / 'FracPaQ User Guide v2.8.pdf'
    reader = PdfReader(source)
    entries = []
    skipped = []
    text = []
    for page_number, page in enumerate(reader.pages, 1):
        text.append(f'--- Página {page_number} ---\n{page.extract_text()}')
        for index in range(len(page.images)):
            try:
                entry = page.images[index]
            except LimitReachedError as error:
                skipped.append({'page': page_number, 'image_index': index,
                                'reason': str(error)})
                continue
            image = entry.image
            # The small recurring header logo is already preserved upstream.
            if image.width < 400 or image.height < 150:
                continue
            name = f'page-{page_number:02d}-image-{index:02d}.png'
            path = args.output_dir / name
            image.save(path)
            entries.append({'path': name, 'page': page_number,
                            'pdf_image_name': entry.name,
                            'size': list(image.size), 'sha256': sha256(path),
                            'role': 'Apoio documental; parâmetros/ambiente '
                                    'originais não informados. Não é golden.'})
    (args.output_dir / 'text.txt').write_text('\n\n'.join(text), encoding='utf-8')

    # Poppler is absent on the initial host. QtPdf is already supplied by PySide6.
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PySide6.QtCore import QSize
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtPdf import QPdfDocument

    app = QGuiApplication.instance() or QGuiApplication([])
    document = QPdfDocument()
    error = document.load(str(source))
    if error != QPdfDocument.Error.None_:
        raise RuntimeError(f'QtPdf failed to read manual: {error}')
    for page_number in sorted({4, 5} | {s['page'] for s in skipped}):
        size = document.pagePointSize(page_number - 1)
        image = document.render(page_number - 1,
                                QSize(round(size.width() * 2),
                                      round(size.height() * 2)))
        path = args.output_dir / f'page-{page_number:02d}.png'
        if not image.save(str(path)):
            raise RuntimeError(f'Cannot save {path}')
        from PIL import Image
        with Image.open(path) as rendered:
            rgba = rendered.convert('RGBA')
            background = Image.new('RGBA', rgba.size, 'white')
            background.alpha_composite(rgba)
            background.convert('RGB').save(path)
    write_json(args.output_dir / 'manifest.json', {
        'source': str(source.relative_to(ROOT)), 'source_sha256': sha256(source),
        'pages': len(reader.pages), 'images': entries,
        'unextracted_images': skipped,
        'page_rendering': 'QtPdf, 144 dpi; páginas 4, 5 e imagens que excedem '
                          'o limite de memória do extrator.',
        'missing': 'Capturas reais controladas da GUI 2.8 e PNG/arrays MATLAB.',
    })
    document.close()
    app.processEvents()
    print(f'{len(entries)} imagens de apoio extraídas de {len(reader.pages)} páginas.')


if __name__ == '__main__':
    main()
