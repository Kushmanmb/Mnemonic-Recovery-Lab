# Mnemonic Recovery Lab

An offline-first toolkit for legitimate owners to validate BIP-39 English recovery phrases and understand missing-word search-space size. Sensitive phrases are processed on your machine and are never saved, logged, or sent to a remote service.

> **Safety:** Only enter a phrase on a device you control and trust. A checksum-valid phrase is not proof that it is yours or that it controls a particular wallet. Candidate testing is restricted to built-in public/disposable fixtures, never arbitrary recovery phrases. This project does not derive keys or addresses, query blockchains, or sign transactions. Never fund a fixture wallet.

## Features

- Validates the BIP-39 English wordlist, supported phrase lengths (12, 15, 18, 21, and 24), and mnemonic checksum.
- Identifies unknown words and their positions without retaining the phrase.
- Estimates the theoretical phrase combinations and expected checksum filter for user-specified missing positions. It does not search them.
- Provides a browser dashboard served only on loopback; the browser and Python service use local resources only.
- Includes a hidden-input CLI mode for validation.
- Runs bounded offline missing-position recovery experiments and repeatable benchmarks on built-in fixtures, with aggregate progress and cancellation.

The app is a deliberately small, safe foundation. Wallet-specific derivation paths, public blockchain forensics, and address matching are not implemented. See the [roadmap](ROADMAP.md) for boundaries and future work.

### Wallet compatibility notes

BIP-39 phrases can be used by multiple wallets, but wallet support also depends on derivation paths, account conventions, and any optional BIP-39 passphrase. A passphrase changes the derived seed and is not validated by the mnemonic checksum; the same words with different passphrases produce different wallet material. This release does not derive or match wallet addresses and makes no compatibility claim for MetaMask, Trust Wallet, Coinbase Wallet, Ledger, Trezor, Ethereum, EVM, or Bitcoin wallets.

## Install and run

Python 3.12 or later is required; CI verifies Python 3.13.

```bash
python -m pip install .
python -m mnemonic_recovery
```

Open the loopback URL printed in the terminal (default `http://127.0.0.1:8765`). The server binds to `127.0.0.1` only. Press `Ctrl+C` to stop it. To select a port, use `python -m mnemonic_recovery serve --port 8766`.

For terminal-only validation, use `python -m mnemonic_recovery validate`. The phrase is entered with terminal echo disabled. Do not pass a phrase as a command-line argument.

The `mnemonic` dependency includes the English BIP-39 list and is installed once; validation itself works offline. For stronger isolation, install and run the project on a dedicated offline device. Review [SECURITY.md](SECURITY.md) before handling sensitive material.

## Offline recovery experiments

These commands accept only fixture identifiers and one-based missing positions, not phrases, private keys, addresses, or passphrases. Known words come from the selected fixture. Every replacement combination is checked using the installed `mnemonic` BIP-39 implementation. An exact fixture match is counted separately from a checksum-valid candidate; it is not wallet/address validation.

```bash
python -m mnemonic_recovery experiment --fixture bip39-zero-128 --missing 12
python -m mnemonic_recovery experiment --fixture disposable-160 --missing 1 15 --max-candidates 10000
python -m mnemonic_recovery benchmark --fixture bip39-zero-128 --missing 12 --repeats 3
```

- `--missing` accepts unique positions within the fixture's word count. Input order is normalized.
- Candidates are visited deterministically in English wordlist order. The default budget is 2,048 checks; `--max-candidates` accepts 1 through 100,000 per run. Multiple missing words usually produce a partial search, not a recovery guarantee.
- Progress goes to stderr every 256 checks, configurable using `--progress-every` (1 through 100,000). Final JSON on stdout contains only fixture IDs, positions, counts, timing, and status: `completed`, `limit_reached`, or `cancelled`.
- Press `Ctrl+C` to cancel between candidate checks. Final counts are emitted and the CLI exits with status 130. The Python API accepts a `threading.Event` and an aggregate-only progress callback.
- Benchmarks perform 1-10 identical runs (`--repeats`, default 3), reporting each run and the median candidates/second. Timing includes validation and progress-callback overhead, excludes fixture setup, and depends on hardware/load. Cancelled or budget-limited runs are explicitly marked. There are no fragile timing thresholds in tests.
- No candidates are printed, persisted, or sent to the dashboard. No network access is needed after dependency installation. Recovery experiments are CLI/Python-only; the existing dashboard remains a validator and search-space estimator.

### Fixture provenance

The `bip39-zero-128`, `bip39-zero-192`, and `bip39-zero-256` fixtures use the all-zero entropy entries from the [published Trezor/python-mnemonic BIP-39 vectors](https://github.com/trezor/python-mnemonic/blob/master/vectors.json), referenced by [BIP-39](https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki). Tests pin their exact expected mnemonic strings, plus additional published nonzero entropy vectors, without downloading anything at runtime.

The `disposable-160` and `disposable-224` fixtures use deterministic entropy bytes `00..13` and `00..1b`, respectively. Together the fixtures cover 12, 15, 18, 21, and 24 words. They are publicly reproducible test material, not securely generated wallets. No keys or addresses are derived, and no wallet software, funds, blockchain access, or seed/passphrase derivation is involved.

## Development

```bash
python -m pip install -e '.[dev]'
ruff check .
ruff format --check .
mypy src
pytest
bandit -r src -q
pip-audit .
```

Tests use published BIP-39 test vectors and synthetic phrases only. Never add a real recovery phrase, private key, or wallet export to source, tests, issues, or CI artifacts. See [CONTRIBUTING.md](CONTRIBUTING.md).

Dependency installation and `pip-audit` access package/advisory services using package metadata only. They are development-time operations, separate from offline validation and experiments; never supply recovery material to them.

## License

The source code is provided without a declared license at this initial stage. See the project owner for licensing terms before reuse.
