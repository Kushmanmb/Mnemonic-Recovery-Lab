"""Command-line entry point."""

from __future__ import annotations

import argparse
import json
import signal
import sys
from dataclasses import asdict
from getpass import getpass
from threading import Event

from mnemonic_recovery.core import validate_mnemonic
from mnemonic_recovery.experiments import (
    FIXTURES,
    Progress,
    run_benchmark,
    run_experiment,
)
from mnemonic_recovery.server import serve_dashboard


def _experiment_command(args: argparse.Namespace) -> None:
    cancel = Event()
    previous_handler = signal.signal(signal.SIGINT, lambda *_: cancel.set())

    def report(progress: Progress) -> None:
        print(
            f"{progress.status}: {progress.checked}/{progress.total_candidates} "
            f"checked; {progress.checksum_valid} checksum-valid; "
            f"{progress.candidates_per_second:.0f} candidates/s",
            file=sys.stderr,
            flush=True,
        )

    try:
        if args.command == "benchmark":
            benchmark = run_benchmark(
                args.fixture,
                args.missing,
                repeats=args.repeats,
                max_candidates=args.max_candidates,
                progress_every=args.progress_every,
                cancel=cancel,
                on_progress=report,
            )
            output = asdict(benchmark)
            output["median_candidates_per_second"] = (
                benchmark.median_candidates_per_second
            )
        else:
            result = run_experiment(
                args.fixture,
                args.missing,
                max_candidates=args.max_candidates,
                progress_every=args.progress_every,
                cancel=cancel,
                on_progress=report,
            )
            output = asdict(result)
            output["candidates_per_second"] = result.candidates_per_second
        print(json.dumps(output, sort_keys=True))
    finally:
        signal.signal(signal.SIGINT, previous_handler)
    if cancel.is_set():
        raise SystemExit(130)


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline BIP-39 phrase analysis")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser(
        "validate", help="validate a phrase with hidden terminal input"
    )
    serve_parser = subparsers.add_parser("serve", help="run the local dashboard")
    serve_parser.add_argument("--port", type=int, default=8765)
    for command in ("experiment", "benchmark"):
        experiment_parser = subparsers.add_parser(
            command, help="run bounded recovery tests on built-in fixtures only"
        )
        experiment_parser.add_argument("--fixture", choices=FIXTURES, required=True)
        experiment_parser.add_argument(
            "--missing", type=int, nargs="+", required=True, metavar="POSITION"
        )
        experiment_parser.add_argument("--max-candidates", type=int, default=2048)
        experiment_parser.add_argument("--progress-every", type=int, default=256)
        if command == "benchmark":
            experiment_parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()

    if args.command in ("experiment", "benchmark"):
        try:
            _experiment_command(args)
        except ValueError as error:
            parser.error(str(error))
    elif args.command == "validate":
        if not sys.stdin.isatty():
            raise SystemExit(
                "Validation requires an interactive terminal to protect input."
            )
        print("Sensitive input: only continue on a device you trust.")
        result = validate_mnemonic(getpass("Recovery phrase (input hidden): "))
        if result.invalid_words:
            for item in result.invalid_words:
                print(f"Unknown English word at position {item.position}")
        print(f"Word count: {result.word_count}")
        print(f"Checksum valid: {result.checksum_valid}")
        print(f"Phrase valid: {result.valid}")
    else:
        serve_dashboard(getattr(args, "port", 8765))


if __name__ == "__main__":
    main()
