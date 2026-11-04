"""Command-line entry point."""

from __future__ import annotations

import argparse
from getpass import getpass

from mnemonic_recovery.core import validate_mnemonic
from mnemonic_recovery.server import serve_dashboard


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline BIP-39 phrase analysis")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser(
        "validate", help="validate a phrase with hidden terminal input"
    )
    serve_parser = subparsers.add_parser("serve", help="run the local dashboard")
    serve_parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    if args.command == "validate":
        print("Sensitive input: only continue on a device you trust.")
        result = validate_mnemonic(getpass("Recovery phrase (input hidden): "))
        if result.invalid_words:
            for item in result.invalid_words:
                print(f"Unknown English word at position {item.position}: {item.word}")
        print(f"Word count: {result.word_count}")
        print(f"Checksum valid: {result.checksum_valid}")
        print(f"Phrase valid: {result.valid}")
    else:
        serve_dashboard(getattr(args, "port", 8765))


if __name__ == "__main__":
    main()
