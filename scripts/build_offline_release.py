"""Build a byte-for-byte reproducible offline-app release candidate.

Usage: python scripts/build_offline_release.py [--out dist]

Writes:
  <out>/mnemonic-recovery-offline-app.zip
  <out>/SHA256SUMS   (the zip plus each packaged file, `sha256sum -c` format)

Reproducibility: entries are written in a fixed order with a fixed timestamp
(1980-01-01, the ZIP epoch), fixed permissions (0644) and fixed compression
settings, so the archive depends only on file contents, not on checkout time.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "offline-app"
# Explicit allowlist: only these files are ever packaged.
FILES = (
    "index.html",
    "styles.css",
    "app.js",
    "wordlist.js",
    "english.txt",
    "README.md",
)
ARCHIVE_NAME = "mnemonic-recovery-offline-app.zip"
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)
# Canonical BIP-39 English word list (github.com/bitcoin/bips, bip-0039/english.txt).
BIP39_ENGLISH_SHA256 = (
    "2f5eed53a4727b4bf8880d8f3f199efc90e58503646d9ff8eff3a2ed3b24dbda"
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build(out_dir: Path, app_dir: Path = APP_DIR) -> Path:
    contents = {name: (app_dir / name).read_bytes() for name in FILES}
    if sha256(contents["english.txt"]) != BIP39_ENGLISH_SHA256:
        raise SystemExit("english.txt does not match the canonical BIP-39 word list")

    out_dir.mkdir(parents=True, exist_ok=True)
    archive = out_dir / ARCHIVE_NAME
    with zipfile.ZipFile(archive, "w") as zf:
        for name in FILES:
            info = zipfile.ZipInfo(f"offline-app/{name}", date_time=ZIP_EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3  # Unix, so external_attr is interpreted consistently
            info.external_attr = (0o100644 & 0xFFFF) << 16
            zf.writestr(info, contents[name], compresslevel=9)

    lines = [f"{sha256(archive.read_bytes())}  {ARCHIVE_NAME}"]
    lines += [f"{sha256(contents[name])}  offline-app/{name}" for name in FILES]
    (out_dir / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return archive


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=ROOT / "dist")
    args = parser.parse_args(argv)
    archive = build(args.out)
    print((args.out / "SHA256SUMS").read_text(encoding="utf-8"), end="")
    print(f"built {archive}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
