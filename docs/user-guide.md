# PyFracPaQ local user guide

The illustrated manual covers the SD11A workflow, all 30 analytical features, figures, theory and formulae. It is available in **Brazilian Portuguese** ([PDF](manual/pyfracpaq-user-manual.pdf), [LaTeX](manual/pyfracpaq-user-manual.tex)) and **English** ([PDF](manual/pyfracpaq-user-manual-en.pdf), [LaTeX](manual/pyfracpaq-user-manual-en.tex)). [Compilation instructions](manual/README.md) accompany both versions. This Markdown document provides a quick reference in English.

The port follows the FracPaQ 2.8 interface and works offline after its libraries are installed. Version **0.9.0rc1**, November 2026, contact luismauricio@me.com. Run from the project root in a terminal or VS Code using Python 3.13 or a Miniforge environment; installing the project package is unnecessary. See [environment preparation](install.md), [release notes and accepted differences](release-notes.md), [credits](../THIRD_PARTY_NOTICES.md) and the [licence](../LICENSE). MATLAB and tests are not required to use the application. Windows/Linux remain for the maintainer's later testing.

## Install and start

At the project root, create a .venv with Python 3.13, or use a Miniforge Python 3.13 environment, and install the dependencies in requirements.txt. You do not need to install the PyFracPaQ package. The complete procedure, development dependencies and PowerShell commands are in the [README](../README.md). Start with `.venv/bin/python run_gui.py` or `.venv/bin/python -m pyfracpaq`. In VS Code, select the .venv interpreter. MATLAB is not required during operation.

Choose an input file, click Preview, check the statistics, select outputs across the six tabs and click Run. The Run1 tag produces the _Run1 suffix. PNGs are 20×20 cm at 600 dpi; files are written to the current working directory. Reusing a tag replaces the same files. Do not use the original reference directory for outputs.

## Prepare inputs

TXT input requires one trace per line, TAB-separated X/Y pairs and at least two distinct nodes. Do not use headers, commas or comments in GUI TXT input. The complementary generic text reader is a separate API. A blank scale retains pixels; a positive pixels/metre value divides coordinates and derives areas/units. Changing the input, scale or Hough parameters requires a new preview.

SVG input accepts line, polyline and M/L path commands within the documented subset, without transformations, curves or external CSS. Prepare layers in an external editor and use hexadecimal stroke colours through compatible attributes, styles or groups. Curves are not automatically converted to straight lines. Converted TXT files are written alongside the SVG; loading one colour's TXT allows individual analysis. The application does not edit or digitise traces.

GUI images must be eight-bit grayscale JPG/JPEG/TIF/TIFF files. RGB/alpha inputs are not silently converted. The complementary preprocess tool prepares RGB photographs; check its output before importing. Preview displays the four Hough panels; adjust peaks, threshold, FillGap and MinLength before running analyses. See the [valid examples](../examples/README.md).

## Select analyses

Maps produces traces/nodes, length/angle maps, P21/P20 and stability/Mohr figures. Circular maps use at least two circles along the shorter side; any estimate writes both centre/value TXT files. Finite geometric counting follows the approved Q-20 correction. Slip tendency also writes segmentdata with coordinates/raw angles.

Lengths offers histograms, log-log distributions, MLE, cross-plot, censoring, blocks and a variogram. MLE depends on Log-log; Lower/Upper cuts remove the smaller/larger tails. Censoring uses a consistent mask per trace. Q-14 blocks use enclosed white components, original resolution and area conversion, with a visible BMP of fixed name; they do not measure vector polygon area. The variogram uses segment centres/lengths and 30 bins, without fitting a theoretical model. The family writes its three TXT files even when only blocks or the variogram are selected.

Angles produces a histogram and an equal-area rose, with weighting/colour/mean options. Fluid flow provides I/Y/X, crack tensors 0/2/4/8 and permeability with fixed/scaled aperture and λ. Connectivity and statistical fits use approved corrections Q-11/Q-15; stability uses Q-17. Three-dimensional flow rate or pressure is not modelled.

Graphs: Select end points captures two clicks in the preview. Escape or right-click cancels the attempt. ALONG measures each intersection with the finite line, repeating traces when multiple segments intersect; FROM uses signed perpendicular distance to the infinite line. North does not alter these raw angles. Selecting P21 or P20 generates a map and both profiles; P20=m/(2πr²), following the approved Q-20 extension. Changing the input/scale clears the line; flips preserve the selection.

## Wavelets

Select Run wavelet analysis and choose Morlet or Mexican Hat. Enter positive integer a/L lists, such as `8 16` and `2 4`; the calculation uses the reciprocals of the L factors. The angular increment must be an integer divisor of 180, such as 10, 20, 30, 45, 60 or 90. MATLAB expressions such as `2:2:8` are not executed; enter `2 4 6 8` instead.

The input raster is always 1944×1944, 27 inches at 72 dpi, with the reference margins and long traces (≥45% of the longest) drawn at 4 points, others at 1 point. Physical scale/north are not added to raster coordinates. Approved Q-12 documents raster/antialiasing differences and the numerical tie-break for isotropic orientations. An optimum orientation at L=1 may be physically indeterminate; the tie-break is declared in the evidence.

Each a produces a 2×2 panel with the image, normalised WC, rose and log10 frequency histogram, plus FracPaQ2Dwavelet_theta_a{a}_{tag}.txt. The threshold is fixed: WC strictly greater than 50% of the maximum; there is no slider. FracPaQ2D_wavelet_traces.png is a visible untagged intermediate. Vertical colour bars follow plot height during resizing/export and retain the shared physical clearance.

Wavelets can take time. Reducing the number of scales, L factors and orientations reduces the work. A prior estimate and a specific 2 GiB memory budget are provided; inputs exceeding the limit are rejected with a message before the larger allocation. Coefficients are processed per orientation/L, without a global tensor of every combination. The main tab has no Cancel button; the auxiliary dialogue has its own Cancel.

## Complementary tools

Run from the root after preparing the environment; quote paths containing spaces:

```bash
.venv/bin/python -m pyfracpaq.tools preprocess photo.jpg prepared.tif --panel stages.png
.venv/bin/python -m pyfracpaq.tools move examples/move_objects.dat nodes.txt --x-column 1 --y-column 3 --skip-header 1
.venv/bin/python -m pyfracpaq.tools wavelet-dialog FracPaQ2D_wavelet_traces.png --output-directory . --tag Run1
```

Preprocess requires distinct input and output paths: a grayscale 0/255 TIFF and the six-stage panel. It reproduces grayscale conversion, 20×20 median filtering, saturated subtraction, Sobel, closing and thinning/inversion. The panel helps assess whether preprocessing preserves the intended fractures; no AI segmentation is used.

Move uses one-based columns, defaulting to 1/3, blank-line-separated objects and an explicitly counted header. The default is zero header lines; the last fracture is preserved even without a final blank line. Invalid conversion does not replace an existing output. TXT uses four decimal places and TAB, as in the script.

The separate wavelet dialogue reuses an eight-bit L/RGB raster, with the same controls/defaults as the auxiliary FIG. Run freezes parameters and processes them in a QThread; Cancel closes only that dialogue or requests interruption of its own job, waiting for a safe stage. Its TXT files retain the auxiliary name **without a tag**, while PNGs use the tag supplied to the tool. It neither replaces the main tab nor changes the trace preview.

## APIs and legacy routines

Complementary APIs: readtext in `pyfracpaq.io.text`; tensor16 and probe_plane in `pyfracpaq.analysis.auxiliary`; linear/historical roses in `pyfracpaq.analysis.roses`; the advanced variogram in `pyfracpaq.analysis.variogram`; colour maps in `pyfracpaq.analysis.palettes`; drawing in `pyfracpaq.plots.auxiliary`. These are not GUI 2.8 selectors. Technical contracts and the complete disposition are in docs/parity/legacy.md in the full repository; they are unnecessary for ordinary use.

Older scripts may have EPS/JPEG/TIFF formats, fixed paths and incompatible signatures. They are preserved as references and are not executed automatically. The GUI does not save sessions or produce a consolidated report; these would be future extensions. index.html/assets/params.json belong to the historical website, rather than a web frontend or application configuration.

## Audit and close-out — 0.1.0rc1

The GUI uses the reference Helvetica font, with explicit Arial/DejaVu Sans fallback when unavailable. Plots use Arial/fallback. Run keeps the interface busy until PNG presentation also finishes, processing events between files. Exit interrupts the sequence after the current figure; files already saved remain. Each figure supports the standard Close shortcut (Cmd+W on Mac/Ctrl+W elsewhere); closing a figure does not close the main window. Hough endpoint ordering was corrected in S16, so older S6 results are historical.

Q05 censoring was explicitly approved: exclude an entire trace when its first/last endpoint touches any actual boundary, and apply the same mask to IDs, lengths and angles. Corrected data can differ from defective MATLAB behaviour. Angular convention Q10 was retained: north is subtracted and rounded; EZROSE is corrected/duplicated, whereas length pairs and segmentdata retain raw angles.

For file checks, consult the S16 catalogue/manifests. An available capture does not establish parity: differences in layout/ticks/text and families without complete regional acceptance remain. Do not treat this candidate as a declaration of general scientific/visual identity.
