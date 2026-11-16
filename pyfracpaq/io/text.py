"""Explicit generic readtext API, independent of the stricter TXT node reader.

Contract inspired by Peder Axensten's supplied readtext (2006–2007). Quotes
are retained; delimiters inside them are protected. No expression evaluation.
"""

from dataclasses import dataclass
from pathlib import Path
import re

import numpy as np


@dataclass(frozen=True, slots=True)
class TextTable:
    data: np.ndarray
    minimum_columns: int
    maximum_columns: int
    rows: int
    number_mask: np.ndarray
    empty_mask: np.ndarray
    string_mask: np.ndarray
    quote_count: int

    @property
    def number(self):
        return int(self.number_mask.sum())

    @property
    def empty(self):
        return int(self.empty_mask.sum())

    @property
    def string(self):
        return int(self.string_mask.sum())


def readtext(source: Path | str, delimiter: str = ',', comment: str = '',
             quotes: str = '', *, textsource: bool = False, mode: str = 'mixed',
             empty: str = 'default', regex: bool = False) -> TextTable:
    if not delimiter or len(comment) > 1 or len(quotes) > 2 \
            or mode not in ('mixed', 'numeric', 'textual') or empty not in ('default', 'zero', 'nan'):
        raise ValueError('Invalid text delimiter, comment, quotes, mode or empty policy.')
    text = str(source) if textsource else Path(source).read_text(encoding='utf-8-sig')
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    if comment:
        text = re.sub(r'(?m)^' + re.escape(comment) + r'[^\n]*\n?', '', text)
        text = re.sub(re.escape(comment) + r'[^\n]*', '', text)
    pattern = re.compile(delimiter if regex else re.escape(delimiter))
    if pattern.match('') is not None:
        raise ValueError('Delimiter cannot match an empty string.')
    rows, row, field = [], [], []
    opening, closing = (quotes[0], quotes[-1]) if quotes else (None, None)
    depth = quote_count = i = 0
    while i < len(text):
        char = text[i]
        if quotes and char == closing and depth:
            depth -= 1
            quote_count += 1
        elif quotes and char == opening:
            depth += 1
            quote_count += 1
        elif not depth and (char == '\n' or (match := pattern.match(text, i))):
            row.append(''.join(field).strip())
            field = []
            if char == '\n':
                rows.append(row)
                row = []
                i += 1
            else:
                i = match.end()
            continue
        field.append(char)
        i += 1
    if depth:
        raise ValueError('Opening and closing quotes do not match.')
    if field or row:
        rows.append([*row, ''.join(field).strip()])
    columns = max(map(len, rows), default=0)
    shape = len(rows), columns
    if shape[0] * shape[1] * 128 > 256 * 1024 ** 2:
        raise MemoryError('Generic text table exceeds the 256 MiB working memory budget.')
    values = np.empty(shape, dtype=object)
    number_mask, empty_mask, string_mask = (np.zeros(shape, bool) for _ in range(3))
    for r, row in enumerate(rows):
        for c in range(columns):
            token = row[c] if c < len(row) else ''
            empty_mask[r, c] = not token
            number = None
            if token and mode != 'textual':
                try:
                    if re.fullmatch(r'[+-]?(?:(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?|[iI][nN][fF]|NaN)', token) is None:
                        raise ValueError('Not a numeric literal.')
                    number = float(token)
                except ValueError:
                    # Numeric complex literals only; never eval/str2num.
                    compact = re.sub(r'\s+', '', token).replace('i', 'j')
                    if re.fullmatch(r'[0-9eEj.+\-]+', compact):
                        try:
                            number = complex(compact)
                        except ValueError:
                            reversed_complex = re.fullmatch(r'(.+)j([+\-].+)', compact)
                            if reversed_complex is not None:
                                try:
                                    number = complex(float(reversed_complex[2]), float(reversed_complex[1]))
                                except ValueError:
                                    pass
                if number is not None and np.isnan(number) and token != 'NaN':
                    number = None
            number_mask[r, c] = number is not None
            string_mask[r, c] = bool(token) and number is None
            if not token:
                if mode == 'textual':
                    values[r, c] = '0' if empty == 'zero' else 'NaN' if empty == 'nan' else ''
                else:
                    values[r, c] = 0. if empty == 'zero' else np.nan if empty == 'nan' or mode == 'numeric' else None
            elif number is not None:
                values[r, c] = number
            else:
                values[r, c] = np.nan if mode == 'numeric' else token
    # Source removes all-empty trailing rows/columns before building masks.
    last_r, last_c = shape
    while last_r and empty_mask[last_r - 1].all():
        last_r -= 1
    while last_c and empty_mask[:, last_c - 1].all():
        last_c -= 1
    data = values[:last_r, :last_c].copy()
    number_mask, empty_mask, string_mask = (a[:last_r, :last_c].copy()
                                            for a in (number_mask, empty_mask, string_mask))
    if mode == 'numeric':
        data = data.astype(complex if any(isinstance(v, complex) for v in data.ravel()) else float)
    for array in (data, number_mask, empty_mask, string_mask):
        array.setflags(write=False)
    return TextTable(data, min(map(len, rows), default=0) if last_r and last_c else 0,
                      columns if last_r and last_c else 0, last_r,
                      number_mask, empty_mask, string_mask, quote_count // 2)
