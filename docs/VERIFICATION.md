# Verification — v0.3.0 public beta

## Windows application

The native Windows Python 3.13 suite passed **84 tests**, with no skips, on
2026-09-18. Coverage includes synthetic parser/comparison fixtures, decimal
formatting, advanced reports, quality profiles, history, cancellation, native
GUI interactions, packaging, and a guarded local real-XER integration test.

The final PyInstaller x64 windowed EXE is 20,902,581 bytes. SHA256:
`000bd3e5fdd608fe20b1069b128e4165add92199c6c12dc9bcded25ab83c92a8`.

The public beta uses that same executable. Publication changes are limited to
repository documentation, feedback forms, and feedback links in the PDF guide.

The publication rerun on 2026-09-19 passed **84 tests**, with no skips, in
134.59 seconds. The revised guide remains four pages; its GitHub links were
checked as PDF link annotations and its help page was rendered and inspected.
The source and release allowlists, issue-form YAML, relative documentation
links, binary hash, and synthetic example contents were also checked.

## Packaged runtime

The packaged app passed verification with a Windows-only PATH, bundled module
origins checked, and socket connections blocked. The journey used the actual
Compare control, produced a 39-sheet workbook and PDF, previewed combined
changes, drilled into quality findings, saved/reloaded a profile, and generated
two full synthetic history comparison sets.

The app bundles Python, Tcl/Tk, openpyxl, reportlab, required fonts, and license
notices. The verification checks those module origins inside the extracted
bundle. No installed Python is needed on PATH for this journey.

Local real exports were parsed and compared successfully. Their resulting
workbook and owner PDF were inspected; the source inputs were not changed.
Real files, project details, generated reports, paths, and screenshots remain
private and are not part of this repository or the downloadable ZIP.

## Remaining limits

- A separate machine or VM with Python uninstalled was not available. The
  isolated-path check is not a substitute for that separate-machine test.
- The longer packaged real-data history journey ended before its completion
  record was produced and is not claimed as a pass. History passed synthetic
  core tests, native UI tests, and the isolated packaged journey above.
- Checks use stored export fields, not a P6 scheduling engine. See
  [report definitions](REPORTS.md) for approximation and N/A explanations.

## Package contents and evidence

The release ZIP is constructed from an explicit five-file allowlist:
`XERCompare.exe`, `START HERE.pdf`, `Documents/Licenses.pdf`, and the two synthetic
examples. Packaging refuses an EXE whose hash differs from the successful
verification record. No CLI EXE, source code, real data, or logs enter the ZIP.

The PDF guide covers the comparison workflow, quality findings, profiles,
history, examples, and voluntary GitHub feedback. The license PDF preserves the
full locally supplied license notices.

Detailed test logs, binary records, screenshots, and private validation outputs
are retained locally in the ignored `build/verification/` directory. They are
not uploaded with the source or release.
