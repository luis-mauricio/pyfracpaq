# PyFracPaQ 0.9.0rc1

November 2026 · luismauricio@me.com. Prerelease of the Python port; **FracPaQ 2.8** identifies the MATLAB reference by David Healy and collaborators.

Run directly from source using Python 3.13 and the libraries in requirements.txt. Miniforge can manage that environment. The six analytical tabs, TXT/SVG/image import and complementary tools are available. The window uses the PyFracPaQ logo, opens at the full available width and remains freely resizable. Colour bars follow the plot with fixed clearance from axis labels; markers use standard geometric squares/circles.

## Accepted differences from the reference

The corrections below were approved by the maintainer and may change results relative to legacy behaviour.

| Family | Adopted behaviour |
| --- | --- |
| Censoring — Q-05 | Endpoints on actual boundaries exclude the entire trace, keeping lengths and angles aligned. |
| Connectivity — Q-11 | Proximity between a real tip and a finite segment; an exact T is Y even at zero tolerance. |
| Wavelets — Q-12 | Deterministic rasterisation, rectangular dimensions and orientation tie-breaking according to the approved decision. |
| Blocks — Q-14 | Excludes components touching the border and calibrates areas/centroids; measures rasterised regions rather than vector polygons. |
| MLE — Q-15 | Consistent Lower/Upper cuts and a tail-based lognormal fit, using the same population for the search and fitting. |
| Stability — Q-17 | Normalisation after angular corrections, linear Sf colours and consistent CSF equality in the map and rose. |
| Maps/Graphs — Q-20 | Counting on finite segments and P20 profile normalisation as m/(2πr²). |

Geometry uses the trace centre halfway along its path and the diagonal from the domain extents. Raw/corrected angular conventions serve different purposes. Length maps retain the accepted convention of linear colour indices with a logarithmic colour bar.

Small visual differences were accepted in five titles and two Hough views, without authorisation to change votes/peaks/endpoints. The 16 presented details were approved after replacing the markers. This does not declare general pixel identity or identity with corrected legacy scientific results.

## Usage and limits

Prepare dependencies before running. MATLAB, tests, reports and installation of the PyFracPaQ package are unnecessary. The usage ZIP is reduced; the full clone retains development material. Windows/Linux remain for the maintainer's later testing.

Outputs use the current directory, and reusing a tag replaces the same names. Replacement is atomic per file, without a transaction covering the entire analysis. Some intermediates have fixed names. TXT data and precision retain their documented contracts.

[Preparation](install.md) · [Manual](user-guide.md) · [Examples](../examples/README.md) · [Credits](../THIRD_PARTY_NOTICES.md). The detailed history of decisions and evidence remains in the full repository, in docs/decisions, docs/parity and tests/reference.
