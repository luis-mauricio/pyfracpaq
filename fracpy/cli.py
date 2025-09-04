from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from .io import read_segments_txt
from .stats import orientations_deg, lengths
from .plots import plot_tracemap, plot_rose


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="FracPy: quick fracture analysis CLI")
    p.add_argument("input", type=Path, help="Path to input TXT file (x1 y1 x2 y2 per line)")
    p.add_argument("--bins", type=int, default=18, help="Number of bins for rose diagram")
    p.add_argument("--show", action="store_true", help="Show plots interactively")
    p.add_argument("--save-prefix", type=Path, default=None, help="Prefix path to save figures")
    args = p.parse_args(argv)

    segments = read_segments_txt(args.input)
    if not segments:
        print("No valid segments found.")
        return 1

    ang = orientations_deg(segments)
    lens = lengths(segments)
    print(f"Segments: {len(segments)}; mean length = {lens.mean():.3f}; median = {lens.median() if hasattr(lens, 'median') else None}")

    # Trace map
    ax_map = plot_tracemap(segments)

    # Rose diagram
    import numpy as np
    ax_rose = plot_rose(ang, bins=args.bins)

    if args.save_prefix is not None:
        prefix = Path(args.save_prefix)
        ax_map.figure.savefig(prefix.with_suffix("_tracemap.png"))
        ax_rose.figure.savefig(prefix.with_suffix("_rose.png"))

    if args.show or args.save_prefix is None:
        plt.show()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

