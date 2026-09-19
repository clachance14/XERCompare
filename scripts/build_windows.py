"""Build the standalone desktop with local packages; console builds are optional."""

from __future__ import annotations

import importlib.metadata as metadata
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "build" / "bundle_assets"


def prepare_assets():
    from PIL import Image, ImageDraw
    import reportlab

    gui_assets = ASSETS / "xercompare" / "gui" / "assets"
    gui_assets.mkdir(parents=True, exist_ok=True)
    notice_sections = [
        ("XERCompare — MIT", (ROOT / "LICENSE").read_text(encoding="utf-8"))
    ]
    for name in [
        "openpyxl",
        "et-xmlfile",
        "reportlab",
        "pillow",
        "charset-normalizer",
        "pyinstaller",
    ]:
        dist = metadata.distribution(name)
        licenses = [
            f
            for f in dist.files or []
            if ".dist-info/" in str(f).replace("\\", "/")
            and any(
                term in str(f).lower() for term in ["license", "licence", "copying"]
            )
            and Path(f).name.lower() not in {"metadata", "record"}
        ]
        if not licenses:
            raise RuntimeError(
                f"No local license text found for {name}; packaging stopped."
            )
        for relative in licenses:
            path = Path(dist.locate_file(relative))
            if path.is_file():
                notice_sections.append(
                    (
                        f"{name} {dist.version} — {path.name}",
                        path.read_text(encoding="utf-8", errors="replace"),
                    )
                )
    base = Path(sys.base_prefix)
    for title, path in [
        ("Python", base / "LICENSE.txt"),
        ("Tcl/Tk", base / "tcl" / "tk8.6" / "license.terms"),
    ]:
        notice_sections.append(
            (title, path.read_text(encoding="utf-8", errors="replace"))
        )
    fonts = Path(reportlab.__file__).parent / "fonts"
    target_fonts = ASSETS / "reportlab" / "fonts"
    target_fonts.mkdir(parents=True, exist_ok=True)
    # Only permissively licensed Vera fonts are needed. Do not bundle DarkGarden.
    for font in fonts.glob("Vera*.ttf"):
        shutil.copy2(font, target_fonts / font.name)
    vera_license = fonts / "bitstream-vera-license.txt"
    shutil.copy2(vera_license, target_fonts / vera_license.name)
    notice_sections.append(
        ("Bitstream Vera fonts", vera_license.read_text(encoding="utf-8"))
    )
    notice = "\n\n".join(
        f'{title}\n{"=" * 72}\n{text}' for title, text in notice_sections
    )
    (gui_assets / "THIRD_PARTY_NOTICES.txt").write_text(notice, encoding="utf-8")
    # Rasterize the repo-native geometric SVG into the Windows icon format.
    svg = ET.parse(ROOT / "src/xercompare/gui/assets/icon.svg").getroot()
    image = Image.new("RGBA", (256, 256))
    draw = ImageDraw.Draw(image)
    scale = 4
    for rect in svg:
        a = rect.attrib
        x, y = int(a.get("x", 0)) * scale, int(a.get("y", 0)) * scale
        box = (x, y, x + int(a["width"]) * scale - 1, y + int(a["height"]) * scale - 1)
        draw.rounded_rectangle(box, radius=int(a.get("rx", 0)) * scale, fill=a["fill"])
    image.save(
        gui_assets / "xercompare.ico",
        sizes=[
            (16, 16),
            (24, 24),
            (32, 32),
            (48, 48),
            (64, 64),
            (128, 128),
            (256, 256),
        ],
    )
    return gui_assets


def version_resource(name):
    sys.path.insert(0, str(ROOT / "src"))
    from xercompare import __version__

    numbers = tuple(int(part) for part in __version__.split(".")) + (0,)
    text = f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={numbers!r}, prodvers={numbers!r}, mask=0x3f,
    flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[StringFileInfo([StringTable('040904B0', [
    StringStruct('CompanyName', 'XERCompare contributors'),
    StringStruct('FileDescription', 'Offline P6 schedule comparison'),
    StringStruct('FileVersion', '{__version__}'),
    StringStruct('ProductName', 'XERCompare'),
    StringStruct('ProductVersion', '{__version__}'),
    StringStruct('OriginalFilename', '{name}.exe'),
    StringStruct('LegalCopyright', 'MIT — XERCompare contributors')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])])
"""
    path = ROOT / "build" / f"{name}-version.txt"
    path.write_text(text, encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--with-cli",
        action="store_true",
        help="Also build the developer console executable",
    )
    args = parser.parse_args()
    if os.name != "nt":
        raise SystemExit(
            "Build Windows executables with Windows Python, not WSL Python."
        )
    assets = prepare_assets()
    targets = [("XERCompare", "src/xercompare/gui/launcher.py", "--windowed")]
    if args.with_cli:
        targets.append(("XERCompare-CLI", "src/xercompare/cli.py", "--console"))
    for name, script, mode in targets:
        command = [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onefile",
            mode,
            "--noupx",
            "--name",
            name,
            "--paths",
            "src",
            "--specpath",
            "build/specs",
            "--distpath",
            "dist",
            "--workpath",
            f"build/pyinstaller/{name}",
            "--icon",
            str(assets / "xercompare.ico"),
            "--version-file",
            str(version_resource(name)),
            "--add-data",
            f"{assets}:xercompare/gui/assets",
            "--add-data",
            f"{ASSETS / 'reportlab' / 'fonts'}:reportlab/fonts",
        ]
        excluded = [
            "pytest",
            "numpy",
            "pandas",
            "scipy",
            "matplotlib",
            "IPython",
            "jupyter",
            "PyQt5",
            "PyQt6",
            "PySide2",
            "PySide6",
            "wx",
            "torch",
            "tensorflow",
            "lxml",
            "requests",
            "httpx",
            "reportlab.graphics.renderPM",
        ]
        if mode == "--console":
            excluded.append("tkinter")
        for module in excluded:
            command.extend(["--exclude-module", module])
        command.append(script)
        subprocess.run(command, cwd=ROOT, check=True)
    shutil.copy2(ROOT / "LICENSE", ROOT / "dist" / "LICENSE.txt")
    shutil.copy2(
        assets / "THIRD_PARTY_NOTICES.txt", ROOT / "dist" / "THIRD_PARTY_NOTICES.txt"
    )
    print(
        "Built "
        + ", ".join(f"dist/{name}.exe" for name, _, _ in targets)
        + ". No dependency downloads performed."
    )


if __name__ == "__main__":
    main()
