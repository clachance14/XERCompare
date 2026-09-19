"""Package the verified desktop app with PDF help and optional synthetic demos."""

import hashlib
import json
from pathlib import Path
import shutil
from zipfile import ZIP_DEFLATED, ZipFile

if __package__:
    from .build_user_docs import build_user_docs
else:
    from build_user_docs import build_user_docs

ROOT = Path(__file__).resolve().parents[1]


def package_release(root=ROOT):
    dist = root / "dist"
    evidence = json.loads(
        (root / "build/verification/release-verification.json").read_text(
            encoding="utf-8"
        )
    )
    binary = next(
        (item for item in evidence["binaries"] if item["file"] == "XERCompare.exe"),
        None,
    )
    if not evidence["ok"] or binary is None:
        raise SystemExit("Run scripts/verify_windows.py successfully first.")
    digest = hashlib.sha256((dist / "XERCompare.exe").read_bytes()).hexdigest()
    if digest != binary["sha256"]:
        raise SystemExit("Reverify the changed executable: XERCompare.exe")
    release = dist / "release"
    build_user_docs(root, release)
    shutil.copy2(dist / "XERCompare.exe", release / "XERCompare.exe")
    examples = release / "Example files"
    examples.mkdir(exist_ok=True)
    for name in ("base.xer", "revised.xer"):
        shutil.copy2(root / "demo/phase3" / name, examples / name)
    # Explicit allowlist prevents old CLI binaries or text docs entering a release.
    files = [
        "XERCompare.exe",
        "START HERE.pdf",
        "Documents/Licenses.pdf",
        "Example files/base.xer",
        "Example files/revised.xer",
    ]
    target = dist / "XERCompare-Windows.zip"
    staged = target.with_suffix(".zip.new")
    with ZipFile(staged, "w", compression=ZIP_DEFLATED) as package:
        for name in files:
            package.write(release / name, name)
    with ZipFile(staged) as package:
        assert package.testzip() is None
    staged.replace(target)
    return target


if __name__ == "__main__":
    print(f"Packaged desktop release: {package_release()}")
