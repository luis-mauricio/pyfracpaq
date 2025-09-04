FracPy (early scaffold)
======================

A minimal Python scaffold inspired by the MATLAB FracPaQ toolkit. It focuses on:

- Loading fracture traces from simple text files (x1 y1 x2 y2 per line)
- Computing basic statistics (lengths, orientations)
- Plotting trace maps and rose diagrams

Status: early prototype — not feature-complete vs FracPaQ.

Quick start
-----------

1) Place a TXT file with one segment per line: `x1 y1 x2 y2` (whitespace- or comma-separated). Lines beginning with `#` are ignored.

2) Run the CLI:

   python -m fracpy.cli path/to/traces.txt --bins 18 --show

   - `--bins`: number of bins for the rose diagram (default 18 → 10° bins)
   - `--show`: display plots interactively
   - `--save-prefix out/figs`: save `*_tracemap.png` and `*_rose.png`

Package layout
--------------

- `fracpy/types.py`: `Segment`, `Trace`, `TraceMap` dataclasses
- `fracpy/io/txt.py`: loader for text files
- `fracpy/stats/`: angles and lengths utilities
- `fracpy/plots/`: trace map and rose diagram plotting
- `fracpy/cli.py`: simple command-line interface

Roadmap
-------

- Connectivity analysis (nodes/links, I-Y-X classification)
- Length/angle distributions and distribution fitting
- Wavelet-based analysis
- Crack density tensors (F2, F4, F8, F16)
- GUI (e.g., PySide6/Qt or a browser-based Dash app)

Notes
-----

- This scaffold aims to be a clean-room reimplementation; no MATLAB code is copied. Algorithms will follow standard published formulations.
- Dependencies used now: `numpy`, `matplotlib`. Additional features may add optional `scipy`, `networkx`, `pywavelets`, etc.

