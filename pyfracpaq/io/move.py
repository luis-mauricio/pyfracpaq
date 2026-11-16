"""Explicit ASCII Move conversion; header and EOF handling are never inferred."""

from pathlib import Path

from pyfracpaq.domain import TraceInput, build_dataset
from pyfracpaq.io.wavelets import _atomic


def convert_move(source, destination, *, x_column: int = 1, y_column: int = 3,
                  skip_header: int = 0):
    if any(isinstance(v, bool) or not isinstance(v, int) for v in (x_column, y_column, skip_header)) \
            or x_column < 1 or y_column < 1 or x_column == y_column or skip_header < 0:
        raise ValueError('Use distinct positive one-based columns and a nonnegative header count.')
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if source == destination:
        raise ValueError('Move input and output must be distinct files.')
    traces, points = [], []
    lines = source.read_text(encoding='utf-8-sig').splitlines()
    if skip_header > len(lines):
        raise ValueError('Header count exceeds the input line count.')
    for row, line in enumerate(lines[skip_header:], skip_header + 1):
        if not line.strip():
            if points:
                traces.append(TraceInput(tuple(points)))
                points = []
            continue
        try:
            coordinates = [float(field) for field in line.split()]
            points.append((coordinates[x_column - 1], coordinates[y_column - 1]))
        except (ValueError, IndexError) as error:
            raise ValueError(f'Move line {row}: expected finite numeric coordinates in selected columns.') from error
    if points:
        traces.append(TraceInput(tuple(points)))
    dataset = build_dataset(traces, source=source)
    # Four decimals follow the source. Revalidate rounded geometry before writing.
    text = ''.join(''.join(f'{value:.4f}\t' for point in trace.points for value in point) + '\n'
                    for trace in dataset.source_traces)
    rounded = [TraceInput(tuple((float(f'{x:.4f}'), float(f'{y:.4f}')) for x, y in trace.points))
               for trace in dataset.source_traces]
    build_dataset(rounded)
    _atomic(destination, lambda stream: stream.write(text.encode('ascii')))
    return dataset
