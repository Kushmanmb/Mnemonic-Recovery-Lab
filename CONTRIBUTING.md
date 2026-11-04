# Contributing

Contributions should preserve the offline-first and privacy-first design.

## Development setup

```bash
python -m pip install -e '.[dev]'
ruff check .
ruff format --check .
mypy src
pytest
bandit -r src -q
pip-audit .
```

## Security rules

- Use published BIP-39 vectors or deterministic synthetic phrases in tests.
- Never submit real recovery phrases, private keys, wallet exports, or personal wallet addresses in code, tests, issues, pull requests, or CI.
- Do not add telemetry, remote phrase processing, arbitrary-phrase candidate enumeration, key derivation, or transaction signing. Bounded candidate testing is allowed only for the built-in public/disposable fixtures in the offline experiment module; do not extend it to user-supplied phrases or entropy.
- Experiment callbacks, CLI output, and benchmark records must contain only aggregate metrics and public fixture identifiers, never candidate phrases. Preserve cancellation and per-run limits.
- Security auditing may contact advisory/package services using package metadata, never phrase inputs. Runtime validation and experiments must work without network access.
- Keep any future public-chain research separate from secret phrase processing.
- Explain the privacy impact of any proposed feature and include focused tests.

Report vulnerabilities privately as described in [SECURITY.md](SECURITY.md).
