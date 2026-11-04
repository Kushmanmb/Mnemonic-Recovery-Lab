# Mnemonic Recovery Lab

An offline-first toolkit for legitimate owners to validate BIP-39 English recovery phrases and understand missing-word search-space size. Sensitive phrases are processed on your machine and are never saved, logged, or sent to a remote service.

> **Safety:** Only enter a phrase on a device you control and trust. A checksum-valid phrase never confirms an individual missing word, the correct phrase, or wallet ownership. Automated candidate search is restricted to built-in public/disposable fixtures; complete candidates can be checked manually. This project does not derive keys or addresses, query blockchains, or sign transactions. Never fund a fixture wallet.

## Features

- Validates the BIP-39 English wordlist, supported phrase lengths (12, 15, 18, 21, and 24), and mnemonic checksum.
- Identifies unknown words and their positions without persisting the phrase.
- Estimates the theoretical phrase combinations and expected checksum filter for user-specified missing positions. It does not search them.
- Provides a browser dashboard served only on loopback; the browser and Python service use local resources only.
- Provides responsive 12-, 15-, 18-, 21-, and 24-word layouts with numbered slots, user-controlled locks, missing markers, manual candidate checks, progress, and cancellation.
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

## Recovery dashboard

Open the printed **HTTP `127.0.0.1` URL** on a trusted local device. Hosted/forwarded origins disable recovery input and do not request reference data. In Codespaces, remote desktops, port-forwarded sessions, or other hosted development environments, use public fixtures only; a transparent loopback tunnel cannot be detected by the app. No CDN, external fonts, telemetry, browser storage, or cloud API is used. Node.js is not needed to run the packaged dashboard.

- Select a supported phrase length. Slots are numbered and masked by default; **Show words** is explicit and session-only. Reducing the layout asks for confirmation if it would discard entered words or locks.
- Word membership is checked against the installed 2,048-word English list in the browser. Membership is not a checksum result or proof of correctness. Invalid words cannot be locked.
- Mark missing positions independently of the entered candidate. **Lock word** is an explicit user assertion about a known word, not independent verification. Locked words are read-only and survive bulk imports and retained positions during length changes. Unlocking is also explicit.
- **Phrase input** fills only unlocked slots when the word count matches; its textarea is immediately cleared. Numbered slots remain in active-page memory for iterative checks. **Clear session**, reload, or leaving the page clears them on a best-effort basis; memory wiping cannot be guaranteed.
- **Check candidate** validates only the complete candidate you supplied through the same-origin loopback Python API. There is no automatic enumeration of user phrases. A checksum pass never changes missing markers, locks, or slot confirmation state.
- **Cancel** aborts the pending request; editing slots also cancels it. Late responses cannot overwrite current input/result state. A local validation may already have finished when cancelled; cancellation does not erase process memory.
- **Fixture experiment** runs the existing bounded engine on the selected built-in public fixture, using only the missing-position markers and budget. Entered words are never sent to this endpoint or used by its search. **Load fixture** explicitly replaces the workspace and asks before discarding entered words or locks.
- Fixture progress shows checked candidates, checksum-valid counts, exact public-fixture matches, and rate. The bar measures the run budget, not the entire theoretical space; budget-limited runs are labeled partial. **Cancel run** disconnects the stream; the server cooperatively stops on the next failed progress write (reported every 32 candidates). These results never confirm entered words.

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
- Generated candidates are never printed, persisted, or sent to the dashboard. The dashboard receives only aggregate progress and separate public fixture reference data. No external network access is needed after dependency installation. Existing CLI and Python APIs remain available alongside the dashboard.

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
npm ci
npm run check
npm run build
npx playwright install --with-deps chromium
npm test
npm audit --audit-level=low
```

Frontend development requires Node.js 22 or later. `dashboard.js` is the editable source; `npm run build` bundles the pinned Lucide icons into the shipped `app.js`, with no runtime package downloads. Commit the rebuilt asset and npm lockfile. CI verifies that rebuilding leaves the bundle unchanged. `npm run format` formats frontend source. Chromium installation requires OS browser libraries; arrange administrator installation separately when necessary.

Playwright checks desktop and mobile-emulated Chromium, all five layouts, 320px overflow, user locks, missing-word non-confirmation, manual checks, cancellation/late-response behavior, fixture isolation, non-loopback blocking, and storage/network privacy. Traces and automatic video/screenshots are disabled; the explicit visual-review test captures public fixture material only. This is not a claim of testing native iOS Safari.

Tests use published BIP-39 test vectors and synthetic phrases only. Never add a real recovery phrase, private key, or wallet export to source, tests, issues, or CI artifacts. See [CONTRIBUTING.md](CONTRIBUTING.md).

Dependency/browser installation, `pip-audit`, and `npm audit` access package/advisory services using package metadata only. They are development-time operations, separate from offline validation and experiments; never supply recovery material to them.

## License

The source code is provided without a declared license at this initial stage. See the project owner for licensing terms before reuse.
