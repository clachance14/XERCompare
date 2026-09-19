# Contributing to XERCompare

Start with the [feedback forms](https://github.com/clachance14/XERCompare/issues/new/choose)
or [Discussions](https://github.com/clachance14/XERCompare/discussions).
Small, reproducible examples and clear expected results are especially helpful.

## Protect project data

Issues, discussions, commits, and pull requests in this repository are public.
Do not submit real or confidential schedules, reports, screenshots, credentials,
or local logs containing identifying paths. Use synthetic examples made with
`tests/fixtures/make_xer.py`. Private integration exports belong only in the
ignored `tests/fixtures/real/` folder and must never be committed.

## Local development

Use Python 3.11 or newer. Windows is required for EXE builds and native Windows
verification. Prepare approved dependency wheels locally before installing in
an offline environment:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install --no-index --find-links C:\wheels -e ".[dev,build]"
.venv\Scripts\python.exe -m pytest -q
```

The app uses `openpyxl`, `reportlab`, and Python's native Tk/ttk. It has its own
XER parser. Do not add PyP6Xer, GPL/LGPL dependencies, or runtime network calls.

Run the desktop or source CLI:

```powershell
.venv\Scripts\xercompare-desktop.exe
.venv\Scripts\xercompare.exe demo\phase3\base.xer demo\phase3\revised.xer -o out
```

The CLI writes `compare.xlsx` and `compare.pdf` in the selected output directory.
No CLI EXE is included in the public Windows ZIP.

## Change and test

Read `AGENTS.md`, `docs/SPEC.md`, and `docs/REPORTS.md` before changing behavior.
Extend a synthetic fixture test, implement the change, run pytest, then update
the relevant phase checkbox and documentation. Preserve visible Activity ID
matching and explicit N/A reasons for analyses needing baseline or CPM data.

The guarded real-file test skips unless exactly two XER files are present in
`tests/fixtures/real/`. Those exports remain local. Test fixtures and examples
committed to this repository must be synthetic.

## Build the Windows package

With the required build packages already installed locally:

```powershell
.venv\Scripts\python.exe scripts\build_windows.py
.venv\Scripts\python.exe scripts\verify_windows.py
.venv\Scripts\python.exe scripts\package_windows.py
```

The output is `dist/XERCompare-Windows.zip`. Packaging checks the EXE against
the successful verification record and includes only the app, PDF guide, PDF
licenses, and two synthetic examples. Build evidence, generated reports, and
real files are excluded from both source control and the release ZIP.

Build scripts do not download dependencies. A separate clean-machine smoke
test remains part of the release checklist; see [verification](docs/VERIFICATION.md).
