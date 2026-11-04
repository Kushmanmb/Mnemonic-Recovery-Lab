# Roadmap

This roadmap is intentionally scoped around privacy boundaries. An item is not implemented until it has code, tests, and documented limitations.

## Initial release

- [x] Offline BIP-39 English word membership and checksum validation for 12, 15, 18, 21, and 24 words.
- [x] Invalid-word position reporting.
- [x] Non-enumerating missing-position search-space estimates and checksum expectations.
- [x] Loopback-only dashboard and hidden-input terminal validation.
- [x] Synthetic-vector test suite, CI, and threat-model documentation.

## Later research

- [ ] Improve missing-position visualization and explain derivation-path/passphrase compatibility without deriving or testing private keys.
- [ ] Add independent published-vector coverage and language support only with clear offline provenance.
- [ ] Consider a separately packaged, read-only public-chain research module with no access to phrase input. Never transmit a recovery phrase, private key, or derived secret.
- [ ] Document EVM/Bitcoin wallet compatibility and the limits of labels, ownership events, and transaction history.

## Explicit non-goals

- No unrestricted brute force or automated candidate generation.
- No unauthorized wallet access, credential harvesting, seed storage, key derivation, signing, or transaction submission.
- No cloud recovery, telemetry, analytics, or secret logging.
