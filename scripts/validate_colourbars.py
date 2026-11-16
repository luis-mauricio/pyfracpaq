"""Audit every implemented colourbar at different aspect ratios and at 600 dpi."""

from dataclasses import asdict
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.colors import Normalize
from matplotlib.transforms import Bbox
import numpy as np
from PIL import Image

from pyfracpaq.analysis import AnalysisRegistry
from pyfracpaq.domain import TraceInput, build_dataset
from pyfracpaq.domain.execution import RunContext
from pyfracpaq.io.figures import export_png
from pyfracpaq.plots.colourbars import colourbar
from reference_common import ROOT, sha256, write_json
from sprint3_reference import directional_dataset, reference_config

FAMILIES = ('MAP-04', 'MAP-05', 'MAP-06', 'ANG-02', 'MAP-07', 'MAP-08')
SIZES = (('square', (6, 6)), ('wide', (10, 4)), ('tall', (4, 9)),
         ('small', (3.4, 2.8)), ('large', (14, 10)))


def measure(host, bar, renderer) -> dict:
    plot, scale = host.get_window_extent(renderer), bar.ax.get_window_extent(renderer)
    expected, actual = ((plot.x0, plot.x1), (scale.x0, scale.x1)) if bar.orientation == 'horizontal' else (
        (plot.y0, plot.y1), (scale.y0, scale.y1))
    error = max(abs(a - b) for a, b in zip(expected, actual))
    assert error < 1e-8, (expected, actual)
    axis = host.xaxis if bar.orientation == 'horizontal' else host.yaxis
    text = axis.get_tightbbox(renderer) if host.axison else None
    facing = Bbox.union([plot, text]) if text is not None else plot
    gap = (facing.y0 - scale.y1 if bar.orientation == 'horizontal' else scale.x0 - facing.x1)
    gap_points = gap / renderer.points_to_pixels(1)
    assert abs(gap_points - 25) < 1e-8, gap_points
    return {'plot_endpoints_px': expected, 'bar_endpoints_px': actual,
            'maximum_deviation_px': error, 'orientation': bar.orientation,
            'label_clearance_points': gap_points}


def capture(figure, host, bar, name, folder) -> list:
    canvas = FigureCanvasAgg(figure)
    rows = []
    for label, size in SIZES:
        figure.set_size_inches(*size)
        target = folder / f'{name}_{label}.png'
        observations = []
        connection = canvas.mpl_connect('draw_event', lambda event: observations.append(
            measure(host, bar, event.renderer)))
        figure.savefig(target, dpi=110)
        canvas.mpl_disconnect(connection)
        assert observations
        rows.append({'path': target.name, 'sha256': sha256(target), 'inches': size,
                     'dpi': 110, 'geometry': observations[-1]})
    # Common export changes the figure to 20x20 cm, renders at 600 dpi and restores
    # the previous on-screen size. Observe that actual draw, rather than a mock.
    observations = []
    connection = canvas.mpl_connect('draw_event', lambda event: observations.append(
        measure(host, bar, event.renderer)))
    old_size = figure.get_size_inches().copy()
    target = export_png(figure, name, '600dpi', folder)
    canvas.mpl_disconnect(connection)
    np.testing.assert_array_equal(figure.get_size_inches(), old_size)
    assert observations
    with Image.open(target) as image:
        assert image.size == (4724, 4724)
        preview = image.copy()
        preview.thumbnail((800, 800))
        preview.save(folder / f'qa-{target.name}')
    canvas.draw()
    measure(host, bar, canvas.get_renderer())
    rows.append({'path': target.name, 'sha256': sha256(target), 'size': [4724, 4724],
                 'dpi': 600, 'geometry': observations[-1]})
    figure.clear()
    return rows


def main() -> None:
    folder = ROOT / 'tests/reference/colourbar-spacing'
    folder.mkdir(parents=True, exist_ok=True)
    source = directional_dataset()
    dataset = build_dataset([TraceInput(tuple((n.x * 2, n.y) for n in t.nodes)) for t in source.traces])
    cfg = reference_config(FAMILIES, checkbox_rosecolour=True, edit_numscancircles='3')
    write_json(folder / 'parameters.json', {'selected': FAMILIES, 'bounds': asdict(dataset.bounds),
                                          'sizes': SIZES, 'circles_on_short_side': 3,
                                          'rose_colour': True, 'tag': cfg.tag,
                                          'control_values': dict(cfg.values),
                                          'traces': [[n.point for n in t.nodes] for t in dataset.traces]})
    registry = AnalysisRegistry()
    results = registry.execute(dataset, RunContext(cfg, folder, folder, 'layout'),
                               lambda *a: None, lambda: False)
    rows = []
    for result in results:
        spec = next(s for s in registry.specs if s.id == result.analysis_id)
        output = spec.render(result.data, cfg)[0]
        figure = output.figure
        host, scale = figure.axes
        rows.append({'analysis_id': result.analysis_id,
                     'figures': capture(figure, host, scale._colorbar, output.basename, folder)})
    # No implemented scientific family currently has a vertical colourbar. This
    # explicitly labelled geometry example verifies the shared future contract.
    figure = Figure()
    host = figure.add_axes((.18, .15, .6, .7))
    host.set_box_aspect(1)
    host.plot([0, 1], [0, 1])
    host.set_xlabel('X coordinate')
    host.set_ylabel('Y coordinate')
    host.yaxis.set_label_position('right')
    host.yaxis.tick_right()
    host.set_title('Vertical colourbar')
    bar = colourbar(host, location='right', norm=Normalize(0, 1))
    bar.set_label('Layout scale')
    rows.append({'analysis_id': 'vertical_layout_example',
                 'figures': capture(figure, host, bar, 'vertical_layout', folder)})
    # Users may add native MATLAB output files next to the supplied sources.
    # Verify all immutable baseline bytes and report extras without deleting,
    # moving or treating those additional files as controlled parity goldens.
    original = ROOT / 'fracpaq-matlab'
    manifest = json.loads((ROOT / 'tests/reference/source_manifest.json').read_text())
    names = {entry['path'] for entry in manifest['files']}
    for entry in manifest['files']:
        assert sha256(original / entry['path']) == entry['sha256'], entry['path']
    extras = [{'path': str(p.relative_to(original)), 'sha256': sha256(p)}
              for p in sorted(original.rglob('*'))
              if p.is_file() and str(p.relative_to(original)) not in names]
    write_json(folder / 'validation.json', {
        'date': '2026-11-14', 'scope': 'Fixed label clearance and responsive colourbar length; no scientific change.',
        'families': FAMILIES, 'cases': rows, 'all_endpoints_deviation_below_px': 1e-8,
        'fixed_label_clearance_points': 25, 'clearance_tolerance_points': 1e-8,
        'png': sum(len(r['figures']) for r in rows), 'original_files_unchanged': 164,
        'additional_workspace_reference_files_preserved': extras,
        'parameters_sha256': sha256(folder / 'parameters.json'),
        'data_files': [{'path': p.name, 'sha256': sha256(p)} for p in sorted(folder.glob('*.txt'))]})
    print('Six implemented families + vertical example: 35 resize PNGs and 7 common 600-dpi exports; fixed 25-point clearance.')


if __name__ == '__main__':
    main()
