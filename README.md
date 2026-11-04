# Mnemonic Recovery Lab

An offline-first toolkit for legitimate owners to validate BIP-39 English recovery phrases and understand missing-word search-space size. Sensitive phrases are processed on your machine and are never saved, logged, or sent to a remote service.

> **Safety:** Only enter a phrase on a device you control and trust. A checksum-valid phrase is not proof that it is yours or that it controls a particular wallet. This project does not generate candidate phrases, derive keys or addresses, query blockchains, or sign transactions.

## Features

- Validates the BIP-39 English wordlist, supported phrase lengths (12, 15, 18, 21, and 24), and mnemonic checksum.
- Identifies unknown words and their positions without retaining the phrase.
- Estimates the theoretical phrase combinations and expected checksum filter for user-specified missing positions. It does not search them.
- Provides a browser dashboard served only on loopback; the browser and Python service use local resources only.
- Includes a hidden-input CLI mode for validation.

The app is a deliberately small, safe foundation. Wallet-specific derivation paths, public blockchain forensics, and address matching are not implemented. See the [roadmap](ROADMAP.md) for boundaries and future work.

## Install and run

Python 3.12 or later is required; CI verifies Python 3.13.

```bash
python -m pip install .
python -m mnemonic_recovery
```

Open the loopback URL printed in the terminal (default `http://127.0.0.1:8765`). The server binds to `127.0.0.1` only. Press `Ctrl+C` to stop it. To select a port, use `python -m mnemonic_recovery --port 8766`.

For terminal-only validation, use `python -m mnemonic_recovery validate`. The phrase is entered with terminal echo disabled. Do not pass a phrase as a command-line argument.

The `mnemonic` dependency includes the English BIP-39 list and is installed once; validation itself works offline. For stronger isolation, install and run the project on a dedicated offline device. Review [SECURITY.md](SECURITY.md) before handling sensitive material.

## Development

```bash
python -m pip install -e '.[dev]'
ruff check .
ruff format --check .
mypy src
pytest
```

Tests use published BIP-39 test vectors and synthetic phrases only. Never add a real recovery phrase, private key, or wallet export to source, tests, issues, or CI artifacts. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

The source code is provided without a declared license at this initial stage. See the project owner for licensing terms before reuse.
