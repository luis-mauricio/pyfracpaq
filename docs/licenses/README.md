# Licences and distribution scope

Review dated 16 November 2026 for PyFracPaQ 0.9.0rc1. The intended delivery is
Python source code, executed from a folder obtained by cloning the repository or
extracting the usage ZIP. Dependencies are installed separately from
`requirements.txt`; this delivery includes no MATLAB runtime, installer, Qt
libraries or wheelhouse.

## FracPaQ and contributions to the port

[LICENSE](../../LICENSE) preserves the 2017 copyright of the FracPaQ Contributors,
David Healy and Roberto Rizzo, alongside the copyright of the port's contributors.
An unchanged copy of the supplied licence is in [fracpaq/LICENSE](fracpaq/LICENSE).
MIT permits modification and redistribution under its conditions; preserve these
notices in every distribution and when extracting substantial portions.

PyFracPaQ is an independently maintained port with its own modifications, rather
than an official publication by the FracPaQ authors. The scientific reference
remains Healy et al. (2017), DOI
[10.1016/j.jsg.2016.12.003](https://doi.org/10.1016/j.jsg.2016.12.003).
Scientific citation supplements the licence notices.

## Third-party routines consulted

The MATLAB originals are not needed to run the application and are excluded
from the usage ZIP. Review of the Python modules confirmed the recorded treatment:

| Reference | Treatment in the port and evidence |
| --- | --- |
| distancePoints / distancePointEdge — David Legland; Copyright 2009 INRA - Cepia Software Platform; Copyright 2016 INRA - BIA-BIBS | `geometry/primitives.py` uses NumPy, `hypot` and scalar projection. Matching reference statements were confirmed at the official matGeom commit that includes BSD-2-Clause; the full text is in [matGeom-BSD-2-Clause.txt](fracpaq/matGeom-BSD-2-Clause.txt), with historical credits retained. These routines are not reclassified as MIT. |
| lineSegmentIntersect — U. Murat Erdem, April 2010 | `geometry/intersections.py` implements rational predicates with `Fraction`, degenerate cases and overlap, without copying the MATLAB matrix implementation. The two-clause BSD notice obtained from the official version 1.1.0 page is in [lineSegmentIntersect-BSD-2-Clause.txt](fracpaq/lineSegmentIntersect-BSD-2-Clause.txt). |
| variogram — Wolfgang Schwanghart, January 2013; parseargs — Malcolm Wood | `analysis/variogram.py` accumulates streaming pairs with explicit Python arguments; the MATLAB parser is not incorporated. The official version 1.4.0 notice is in [variogram-BSD-2-Clause.txt](fracpaq/variogram-BSD-2-Clause.txt). |
| readtext — Peder Axensten, Copyright 2006–2007 in the supplied file | `io/text.py` has a project Python parser without the MATLAB/eval parser. The official archive contains the same supplied M-file, byte-identical, alongside the BSD-2-Clause licence with a 2009 copyright. The [exact archive notice](fracpaq/readtext-BSD-2-Clause.txt) and both copyright records are retained. |
| centax2 / CENTAXES — John L. Galenski III, December 1995; Copyright The MathWorks, Inc., All Rights Reserved | `plots/auxiliary.py:centered_axes` uses Matplotlib spines and ticks in place of the original line/text objects. Author credits and the header's express permission to edit/distribute are preserved in [centax2-permission.txt](fracpaq/centax2-permission.txt); this is not treated as MIT. |
| Morlet/CWT — Kaye L. Powell and Roseanna M. Neupauer, University of Virginia, 2004; Mexican Hat — Dave Healy; triplot/tripts — Gerry Middleton, 1995, modified by Dave Healy, 2017 | The supplied files contain MIT permission text. Credits and the full text are in [wavelets-and-ternary.txt](fracpaq/wavelets-and-ternary.txt). The Python implementations follow the documented equations and conventions. |

Downloaded notices do not replace historical headers. The confirmed correspondence
for Legland's two utilities and readtext, the treatment of centax2 and the limits
of the comparison are described in the [specific review](third-party-review.md).
A notice alone does not prove identity between versions of other components.
These M-files are not redistributed in the public candidate. Copying their bodies
in future requires preserving the applicable terms.

On page 37, the legacy manual describes the lineSegmentIntersect, readtext,
cmocean and variogram contributions as "public domain". That informal summary
does not replace the BSD/MIT licences obtained from their respective publishers.
Inspection of the text on all 39 pages did not identify an individual licence for
each image; it is not a visual or ownership verification of every photograph.

## Resources and documentation

The original logos/icon, SD11A example and layouts derived from FIG files have
recorded provenance and are treated under the MIT licence of the supplied
FracPaQ distribution, without exclusive attribution to the port. No separate
notice restricting the package licence was found in those resources; this grants
neither author endorsement nor additional trademark rights. The PyFracPaQ logo
was supplied by the maintainer. The cmocean colour maps retain
[their full notices](../../pyfracpaq/resources/cmocean_LICENSE.txt).

The PyFracPaQ manual PDFs use project-generated figures and interface screenshots;
[figure-provenance.json](../manual/figure-provenance.json) records their sources.
The original MATLAB manual, its extracted photographs and reference/test
materials are excluded from the usage ZIP. The full clone still retains documentary
evidence in `tests/reference/`, with attribution to the original package;
excluding this directory from the ZIP does not remove it from Git history.
Individual review of photograph/font rights in that archive remains necessary
if it is redistributed outside the recorded documentary scope. Do not describe
the entire archive as cleared solely on the basis of this ZIP review.

Locally generated MATLAB RGB tables and elementary graphical scenes have their
own manifests; they are data/results without incorporated toolbox code. No
Arial/Helvetica font or MATLAB runtime is included in the usage ZIP.

## Qt, PySide6 and other dependencies

Qt for Python/PySide6 and Shiboken are projects of the Qt Project/The Qt Company
and their contributors. The port directly uses `QtCore`, `QtGui` and `QtWidgets`,
installed separately, and envisages the LGPLv3 option for components offering it.
PyFracPaQ's MIT licence does not change the licences of those libraries.

The full [LGPLv3](qt/LGPL-3.0-only.txt), [GPLv3](qt/GPL-3.0-only.txt),
[GPLv2](qt/GPL-2.0-only.txt) and [Qt exception](qt/Qt-GPL-exception-1.0.txt) texts
were obtained from the official `pyside/pyside-setup` repository, tag `v6.12.0`.
LGPLv3 incorporates provisions of GPLv3; including alternative texts neither
relicenses the port nor asserts that every Qt module is available under LGPL.

Versions and missing notices in inspected wheels remain accurately recorded in
`tests/reference/dependency_licenses.json`. The new texts are upstream supplements,
not files claimed to have been found in those wheels. [manifest.json](manifest.json)
records URLs, versions and hashes for the supplements. Other notices available
in the wheels are in [dependencies/](dependencies/).

Users may replace the libraries installed in their Python environment. No
restrictions are imposed on modification or reverse engineering needed to debug
those modifications. Official sources: [PySide/Shiboken 6.12.0](https://github.com/pyside/pyside-setup/tree/v6.12.0)
and [Qt](https://code.qt.io/cgit/qt/). These links identify the origin; they do not
constitute an offer of corresponding source for binaries redistributed by the
maintainer.

If wheels, a wheelhouse or an executable containing Qt are delivered in future,
review each module and its third parties, supply the applicable notices, ensure
replacement/relinking as permitted by LGPL, and fulfil an appropriate method of
providing corresponding source, including for unmodified libraries. This source
candidate does not certify those formats. See
[Qt for Python licences](https://doc.qt.io/qtforpython-6/licenses.html) and
[obligations published by Qt](https://www.qt.io/development/open-source-lgpl-obligations).

## Preparation and verification

From the clone's root, with development dependencies installed:

```bash
PYTHONPATH=.:scripts .venv/bin/python scripts/prepare_source_archive.py --evidence dist/0.9.0rc1/public/source-evidence.json
PYTHONPATH=.:scripts .venv/bin/python scripts/check_distribution_licenses.py --archive dist/0.9.0rc1/public/pyfracpaq-0.9.0rc1-code.zip
```

The generator checks notices, inventoried resource hashes and exclusions before
making the candidate available. The checker can also be run independently on
the exact ZIP to be delivered. It does not detect authorship automatically or
replace licence review when new resources, dependencies or formats are added.
The inventory includes the PyFracPaQ manual images and PDFs and notices copied
from wheels, alongside the official supplements obtained during this review.

Publish only the files listed in `publication-manifest.json` in the `public/`
directory. Older `*-source.zip` files, wheels and wheelhouses in `dist/` are
internal material; some contain the complete MATLAB reference distribution.
They are not the product to deliver. No file is published automatically.
