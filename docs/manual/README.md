# User manuals

Both manuals cover PyFracPaQ **0.9.0rc1**, with the same SD11A worked examples, figures, methods and formulae.

| Language | Read | Edit | Chapters |
| --- | --- | --- | --- |
| English (British terminology) | [PDF](pyfracpaq-user-manual-en.pdf) | [LaTeX](pyfracpaq-user-manual-en.tex) | `chapters-en/` |
| Português brasileiro | [PDF](pyfracpaq-user-manual.pdf) | [LaTeX](pyfracpaq-user-manual.tex) | `chapters/` |

The Portuguese files retain their original filenames. Both versions preserve the English control labels used in the application. The English prose follows the application's British terminology, including **colour**, **centre** and **normalisation**.

The manuals describe all 30 analytical features across the six tabs, inputs and units, auxiliary tools, outputs and limits of interpretation. Most analytical figures use [SD11A.txt](../../examples/SD11A.txt); SVG, Hough and image preprocessing are identified as separate examples. The SD11A file is an unchanged copy from the supplied FracPaQ distribution, with attribution and provenance in [examples/provenance.json](../../examples/provenance.json).

## Compile in TeXStudio

Open either main `.tex` file above, select **XeLaTeX** as the compiler, and compile until the contents and cross-references settle (usually two or three passes). The `% !TeX program = xelatex` comment already specifies the compiler. The documents use fontspec/unicode-math and require XeLaTeX rather than pdfLaTeX.

Keep the entire folder: the main `.tex` file needs its chapter folder, `manual-style.tex` and `assets/`. The TeX Gyre/Latin Modern fonts and packages are supplied by current full TeX Live/MacTeX installations. LaTeX is needed only to rebuild the manuals; it is not required to run PyFracPaQ.

With latexmk, run from this folder:

```bash
latexmk -xelatex -interaction=nonstopmode -halt-on-error pyfracpaq-user-manual-en.tex
latexmk -xelatex -interaction=nonstopmode -halt-on-error pyfracpaq-user-manual.tex
```

The compiled PDFs are included. Both languages share the same figures in `assets/`; [figure-provenance.json](figure-provenance.json) records their sources and checksums. Original scientific figures and audit evidence remain in the full repository. They are not required to compile these manuals, as the figures used here are included in `assets/`.
