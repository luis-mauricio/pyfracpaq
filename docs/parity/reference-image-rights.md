# Reference image provenance and reuse review

Review date: 16 November 2026. Scope: image files in the full repository,
including development references. This review does not remove files or rewrite
repository history; no Git commands were executed.

## Findings

The reviewed repository snapshot contained **1,620 image files**, representing **1,476 distinct
file contents**. The local bytes of every image match the corresponding published
GitHub blob in repository tree `7f4160bcc5d1be263da33cbdb07ce5f44da03257`.
The remote tree response was complete, not truncated. The
[inventory](../../tests/reference/image_rights_inventory.json) records each path,
SHA-256, remote blob ID, category, provenance references and review limitations.

| Group | Files | Provenance and treatment |
| --- | ---: | --- |
| Project test figures, captures, diagnostics and graphics probes | 1,445 | Generated in project validation/capture contexts. Preserve input-data and upstream asset credits; a generated-output classification is not an independent software-vendor permission grant. |
| Copies extracted or rendered from the legacy FracPaQ manual | 110 | Retain the supplied FracPaQ attribution and MIT notice. One specific third-party screenshot reuse issue is identified below. |
| Current PyFracPaQ manual illustrations | 52 | Project figures/interface captures and maintainer-supplied artwork, recorded in docs/manual/figure-provenance.json. |
| Synthetic inputs and public examples | 9 | Project analytical inputs, including a misleadingly named synthetic JPEG described below. |
| Application artwork | 3 | Two supplied FracPaQ assets with retained attribution and the maintainer-supplied PyFracPaQ logo. |
| Adapted FracPaQ vector example | 1 | map1_prepared.svg derives from map1_edit.svg, with explicit removals and FracPaQ MIT attribution already recorded. |

These groups record origin and intended use. They are not a declaration that
every embedded element or underlying dataset has been independently cleared.

## One specific case requiring a decision

**File:** [tests/reference/manual/page-09-image-00.png](../../tests/reference/manual/page-09-image-00.png).

This is Figure 6 on page 9 of the original FracPaQ User Guide 2.8: a screenshot
of Adobe Illustrator containing a rock photograph, visible annotations and
cropped interface content. It was present in the reviewed published snapshot.
The supplied FracPaQ MIT notice remains relevant to the manual, but does not
establish Adobe's or a separate photograph owner's permission.

[Adobe's published screenshot conditions](https://www.adobe.com/legal/permissions/images-user-guides.html)
permit specified uses subject to conditions including reproducing the entire
screenshot, limiting alterations to resizing, providing attribution and excluding
third-party content. This review could not establish that the existing image
qualifies, or independently establish permission for the underlying photograph.
Adding a credit alone would not establish compliance with those conditions.

**Prepared treatment:** preserve an unchanged local documentary copy and exclude
this copy from the public repository unless the relevant permissions can be
established. It is not used by the application or the current PyFracPaQ manuals.
The [distribution policy](../../tests/reference/image_distribution_policy.json)
identifies the exact file and hash. The extraction manifest retains its historical
entry; integrity tests allow only this registered image to be absent from a public
checkout and still verify it if a local copy is present.

The root .gitignore includes this exact path. An ignore rule does not remove an
already tracked file: the maintainer must remove it from the Git index, commit
the change and push. No Git commands or history rewrite were performed here,
and the local image was neither removed nor replaced. Older commits may still
contain the image; this change concerns the current public tree.

## What the legacy manual archive contains

The 110 files in tests/reference/manual are **103 extracted image occurrences**
and **seven rendered pages**. There are 64 unique extracted image contents;
39 occurrences repeat the manual's header logo. All 64 unique extracts and the
seven rendered pages were inspected in contact sheets, and the identified Adobe
image was inspected at full resolution. The remaining manual material consists
of FracPaQ figures, diagrams, interface screenshots and a node-file illustration;
no second specific third-party reuse issue was identified in this visual review.

Its source PDF SHA-256 is
`5b0d4fdf1d7eaced795ae5d4e116a86da0781eb52d31b6d98a2aedce768d703c`.
The original author credits and the [supplied MIT text](../licenses/fracpaq/LICENSE)
must remain attached to copies and derivatives. The original manual is not a
current PyFracPaQ user manual, and the archive is not required at runtime.

## A filename that is not a copied photograph

`tests/reference/sprint15/native/MacduffColourCropped.jpg` is a **synthetic test
input**, not the original Macduff field photograph. In
[capture_native_s1415.m](../../scripts/capture_native_s1415.m), a 43×39 meshgrid
and three modular arithmetic expressions generate RGB channels; imwrite saves
them with that filename so the original preprocessing script can read its expected
input name. This removes the earlier ambiguity caused by the name without
renaming the fixture or changing test data.

## Integrity, attribution and limits

- All 1,620 image files remain unchanged, including approved scientific figures
  and reference captures. The Git index and repository history were not modified.
- Existing JSON metadata mentions checksums for 1,256 images. The remaining 364
  receive a current baseline in the new inventory; lack of a previous checksum
  is not itself a copyright or permission finding.
- The visual review targeted the legacy extracts and rendered pages, not every
  one of the 1,620 files individually. Other groups rely on their project generation
  context and available provenance records. Checksums prove integrity, not ownership.
- The separate `cmmib10.ttf` research font is accompanied by BAKOMA_LICENSE.txt,
  which grants distribution under its stated notice conditions. It is not an
  Arial/Helvetica or MathWorks font file. No font or licence text was changed.
- FracPaQ's [upstream MIT licence](https://github.com/DaveHealy-github/FracPaQ/blob/master/LICENSE)
  is the recorded basis for supplied FracPaQ material. This review does not
  turn third-party interface content into MIT material or treat a community
  discussion about generated plots as a permission grant.

The known unresolved case is deliberately specific. This is not a recommendation
to delete the entire reference archive, nor a legal certification of every
image in the repository.
