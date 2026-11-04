# Roadmap

This roadmap is intentionally scoped around privacy boundaries. An item is not implemented until it has code, tests, and documented limitations.

## Initial release

- [x] Offline BIP-39 English word membership and checksum validation for 12, 15, 18, 21, and 24 words.
- [x] Invalid-word position reporting.
- [x] Non-enumerating missing-position search-space estimates and checksum expectations.
- [x] Loopback-only dashboard and hidden-input terminal validation.
- [x] Synthetic-vector test suite, CI, and threat-model documentation.

## Later research

- [x] Add an offline fixture-only recovery testing framework with one-based missing positions, bounded candidate checksum validation, exact fixture-match counts, progress, and cancellation.
- [x] Add repeatable performance benchmarks with aggregate-only results and no timing-based test failures.
- [x] Pin published entropy/mnemonic pairs and cover deterministic disposable fixtures at all five supported lengths, missing-word locations, limits, cancellation, and privacy boundaries.
- [x] Add source security scanning and dependency auditing to development checks and CI.
- [ ] Improve missing-position visualization and explain derivation-path/passphrase compatibility without deriving or testing private keys.
- [ ] Add additional independent published-vector sources and language support only with clear offline provenance.
- [ ] Consider a separately packaged, read-only public-chain research module with no access to phrase input. Never transmit a recovery phrase, private key, or derived secret.
- [ ] Document EVM/Bitcoin wallet compatibility and the limits of labels, ownership events, and transaction history.

## Explicit non-goals

- No unrestricted brute force or automated candidate generation for arbitrary phrases. The only candidate-testing exception is bounded experiments on built-in public/disposable fixtures.
- No unauthorized wallet access, credential harvesting, seed storage, key derivation, signing, or transaction submission.
- No cloud recovery, telemetry, analytics, or secret logging.
