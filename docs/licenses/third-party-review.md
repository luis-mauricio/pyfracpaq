# Review of the three questioned utilities

Review dated 16 November 2026. Scope: David Legland's
`distancePoints`/`distancePointEdge`, Peder Axensten's `readtext` and John L.
Galenski III/MathWorks' `centax2`/CENTAXES. This stage concerns the licences
and provenance of these routines.

## Decision

Retain the current Python implementations and complete their provenance notices.
The evidence below resolves the identified questions without introducing another
library or changing calculations, file reading or axis presentation. Python
dependencies retain their own licences; historical notices are neither removed
nor replaced by the project's MIT licence.

| Case | Evidence obtained | Treatment |
| --- | --- | --- |
| David Legland: distancePoints/distancePointEdge | At the official matGeom commit adding the two-clause BSD licence, both routines have the same statement lines as the supplied references after removing comments, whitespace and trailing semicolons. Header differences are not presented as byte identity. | Preserve the [full BSD text](fracpaq/matGeom-BSD-2-Clause.txt), the upstream 2019 copyright and historical INRA copyrights from 2009/2016. Retain the existing Python norm/projection calculations. |
| Peder Axensten: readtext | The `readtext.m` file in the official File Exchange archive is byte-identical to the supplied reference. The same archive includes a two-clause BSD `license.txt`. The difference between the source's 2006–2007 copyright and the licence's 2009 copyright appears within the published archive itself. | Preserve both copyright records. Use the [exact archive notice](fracpaq/readtext-BSD-2-Clause.txt), replacing the earlier copy that differed only in whitespace/line wrapping. Retain the current Python parser. |
| Galenski/MathWorks: centax2/CENTAXES | The supplied header expressly permits editing and distributing the file. The current Python function positions spines and ticks through the Matplotlib API; it does not reproduce the MATLAB implementation that disables the axes and reconstructs them with line/text objects, nor its handle dispatch and argument swapping. | Preserve authorship, copyright and the [specific permission](fracpaq/centax2-permission.txt). Do not call this permission MIT. Retain the existing Matplotlib implementation. |

## Sources and comparison limits

The [third-party-review.json](third-party-review.json) record contains URLs,
checksums, the comparison method and hashes of the reviewed Python modules.

- [matGeom: licence at commit 97c6001](https://github.com/mattools/matGeom/blob/97c600192b36c31eaf5b5401fda925c1ea21c0b9/LICENSE.txt).
- [matGeom: distancePoints at the same commit](https://github.com/mattools/matGeom/blob/97c600192b36c31eaf5b5401fda925c1ea21c0b9/matGeom/geom2d/distancePoints.m).
- [matGeom: distancePointEdge at the same commit](https://github.com/mattools/matGeom/blob/97c600192b36c31eaf5b5401fda925c1ea21c0b9/matGeom/geom2d/distancePointEdge.m).
- [readtext: official page](https://www.mathworks.com/matlabcentral/fileexchange/10946-readtext) and [version 1 archive](https://www.mathworks.com/matlabcentral/mlc-downloads/downloads/submissions/10946/versions/1/download/zip).
- centax2: the header of the supplied `fracpaq-matlab/centax2.m` file, with its hash recorded; no licence obtained from another program was attributed to it.
- [Matplotlib API used to position spines](https://matplotlib.org/stable/api/spines_api.html#matplotlib.spines.Spine.set_position).

The MATLAB statement comparison is restricted to the two identified files;
it is not a general semantic equivalence analyser. Byte-identity confirmation
specifically concerns `readtext.m`. The port is not claimed to have been produced
through a clean-room process: the original sources were consulted, and their
provenance remains recorded. These conclusions neither replace the licences
of other components nor constitute legal certification of the entire project.
