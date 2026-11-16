"""Run with python -m pyfracpaq.tools --help; all destinations are explicit."""

import argparse
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    pre = commands.add_parser('preprocess', help='Prepare an RGB/grayscale photograph for Hough.')
    pre.add_argument('input', type=Path)
    pre.add_argument('output', type=Path)
    pre.add_argument('--panel', required=True, type=Path, help='Explicit path for the six-stage PNG.')
    move = commands.add_parser('move', help='Convert ASCII Move objects to tabulated nodes.')
    move.add_argument('input', type=Path)
    move.add_argument('output', type=Path)
    move.add_argument('--x-column', type=int, default=1)
    move.add_argument('--y-column', type=int, default=3)
    move.add_argument('--skip-header', type=int, default=0)
    wave = commands.add_parser('wavelet-dialog', help='Open the complementary dialog on an existing raster.')
    wave.add_argument('input', type=Path)
    wave.add_argument('--output-directory', type=Path, default=Path.cwd())
    wave.add_argument('--tag', default='Run1')
    args = parser.parse_args(argv)
    if args.command == 'move':
        from pyfracpaq.io.move import convert_move
        convert_move(args.input, args.output, x_column=args.x_column,
                     y_column=args.y_column, skip_header=args.skip_header)
    elif args.command == 'preprocess':
        import numpy as np
        from PIL import Image
        from pyfracpaq.analysis.preprocess import preprocess_image
        from pyfracpaq.io.wavelets import _atomic
        from pyfracpaq.plots.preprocess import render_preprocess
        if len({args.input.resolve(), args.output.resolve(), args.panel.resolve()}) != 3:
            parser.error('Input, TIFF output and panel output must be distinct paths.')
        if args.output.suffix.lower() not in ('.tif', '.tiff') or args.panel.suffix.lower() != '.png':
            parser.error('Choose a TIFF output and a PNG panel.')
        with Image.open(args.input) as image:
            if image.mode not in ('L', 'RGB'):
                parser.error('Preprocessing requires an eight-bit grayscale or RGB image.')
            result = preprocess_image(np.asarray(image))
        _atomic(args.output.resolve(), lambda stream: Image.fromarray(result.processed.astype(np.uint8) * 255).save(stream, format='TIFF'))
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        output = render_preprocess(result)
        FigureCanvasAgg(output.figure).draw()
        _atomic(args.panel.resolve(), lambda stream: output.figure.savefig(stream, format='png', dpi=150))
        output.figure.clear()
    else:
        from PySide6.QtWidgets import QApplication
        from pyfracpaq.app import configure_application
        from pyfracpaq.gui.wavelet_dialog import WaveletDialog
        app = QApplication.instance() or QApplication([])
        configure_application(app)
        dialog = WaveletDialog(args.input, directory=args.output_directory, tag=args.tag)
        dialog.show()
        return app.exec()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
