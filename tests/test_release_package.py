import hashlib
import json
from zipfile import ZipFile

import pytest

from scripts.package_windows import package_release
from tests.fixtures.make_xer import make_xer


@pytest.fixture
def release_tree(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "XERCompare.exe").write_bytes(b"verified desktop binary")
    (dist / "XERCompare-CLI.exe").write_bytes(b"old console binary")
    (dist / "THIRD_PARTY_NOTICES.txt").write_text(
        "XERCompare - MIT\n" + "=" * 72 + "\nLicense text retained in PDF.\n",
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "0.2.1"\n')
    evidence = tmp_path / "build/verification"
    evidence.mkdir(parents=True)
    (evidence / "release-verification.json").write_text(
        json.dumps(
            {
                "ok": True,
                "binaries": [
                    {
                        "file": "XERCompare.exe",
                        "sha256": hashlib.sha256(
                            (dist / "XERCompare.exe").read_bytes()
                        ).hexdigest(),
                    }
                ],
            }
        )
    )
    demo = tmp_path / "demo/phase3"
    demo.mkdir(parents=True)
    for name in ("base.xer", "revised.xer"):
        (demo / name).write_text(
            make_xer(activities=[{"task_code": "A1"}]), encoding="cp1252"
        )
    return tmp_path


def test_share_package_has_one_app_pdf_documents_and_optional_examples(release_tree):
    package = package_release(release_tree)
    with ZipFile(package) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == {
            "XERCompare.exe",
            "START HERE.pdf",
            "Documents/Licenses.pdf",
            "Example files/base.xer",
            "Example files/revised.xer",
        }
        assert archive.read("XERCompare.exe") == b"verified desktop binary"
        for name in ("START HERE.pdf", "Documents/Licenses.pdf"):
            assert archive.read(name).startswith(b"%PDF-")


def test_share_package_rejects_changed_app_before_publishing(release_tree):
    (release_tree / "dist/XERCompare.exe").write_bytes(b"unverified change")
    with pytest.raises(SystemExit, match="Reverify"):
        package_release(release_tree)
    assert not (release_tree / "dist/XERCompare-Windows.zip").exists()
