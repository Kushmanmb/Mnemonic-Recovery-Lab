# Contributing

Contributions should preserve the offline-first and privacy-first design.

## Development setup

```bash
python -m pip install -e '.[dev]'
ruff check .
ruff format --check .
mypy src
pytest
```

## Security rules

- Use published BIP-39 vectors or deterministic synthetic phrases in tests.
- Never submit real recovery phrases, private keys, wallet exports, or personal wallet addresses in code, tests, issues, pull requests, or CI.
- Do not add telemetry, remote phrase processing, candidate enumeration, key derivation, or transaction signing.
- Keep any future public-chain research separate from secret phrase processing.
- Explain the privacy impact of any proposed feature and include focused tests.

Report vulnerabilities privately as described in [SECURITY.md](SECURITY.md).
