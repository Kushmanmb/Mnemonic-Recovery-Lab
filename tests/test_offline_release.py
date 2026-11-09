"""Release-candidate packaging must be reproducible, minimal and verifiable."""

from __future__ import annotations

import hashlib
import importlib.util
import os
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "build_offline_release", ROOT / "scripts" / "build_offline_release.py"
)
assert _spec and _spec.loader
release = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(release)


def _copy_app(dst: Path, mtime: int) -> Path:
    app = dst / "offline-app"
    shutil.copytree(ROOT / "offline-app", app)
    for path in app.iterdir():
        os.utime(path, (mtime, mtime))
    return app


def test_builds_are_byte_identical_regardless_of_file_mtimes(tmp_path: Path) -> None:
    a = release.build(tmp_path / "a", _copy_app(tmp_path / "src_a", 1_000_000_000))
    b = release.build(tmp_path / "b", _copy_app(tmp_path / "src_b", 1_800_000_000))
    assert a.read_bytes() == b.read_bytes()
    sums_a = (tmp_path / "a" / "SHA256SUMS").read_text()
    assert sums_a == (tmp_path / "b" / "SHA256SUMS").read_text()


def test_archive_contains_only_allowlisted_files(tmp_path: Path) -> None:
    archive = release.build(tmp_path / "out")
    with zipfile.ZipFile(archive) as zf:
        names = zf.namelist()
        assert names == [f"offline-app/{n}" for n in release.FILES]
        for info in zf.infolist():
            assert info.date_time == release.ZIP_EPOCH
            assert (info.external_attr >> 16) & 0o777 == 0o644


def test_sha256sums_match_archive_and_files(tmp_path: Path) -> None:
    out = tmp_path / "out"
    archive = release.build(out)
    entries = dict(
        reversed(line.split("  ", 1))
        for line in (out / "SHA256SUMS").read_text().splitlines()
    )
    expected_archive = hashlib.sha256(archive.read_bytes()).hexdigest()
    assert entries[release.ARCHIVE_NAME] == expected_archive
    with zipfile.ZipFile(archive) as zf:
        for name in release.FILES:
            data = zf.read(f"offline-app/{name}")
            assert entries[f"offline-app/{name}"] == hashlib.sha256(data).hexdigest()
            assert data == (ROOT / "offline-app" / name).read_bytes()


def test_rejects_non_canonical_wordlist(tmp_path: Path) -> None:
    app = _copy_app(tmp_path / "src", 1_000_000_000)
    (app / "english.txt").write_text("abandon\n", encoding="utf-8")
    try:
        release.build(tmp_path / "out", app)
    except SystemExit as exc:
        assert "canonical BIP-39" in str(exc)
    else:
        raise AssertionError("non-canonical word list was packaged")
