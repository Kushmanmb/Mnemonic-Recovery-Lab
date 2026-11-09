# Offline Mnemonic Recovery Lab

This folder contains a **standalone, local-file BIP-39 checksum validator**. It has no package installation, accounts, cloud APIs, or network dependencies at runtime. The UI only activates when opened from a local `file://` URL.

## Run on Windows

1. Download the repository ZIP from GitHub and extract it to your own computer.
2. Disconnect from the internet.
3. Open `offline-app/index.html` in Microsoft Edge or Chrome.
4. Enter only a recovery phrase that belongs to you. Use the missing markers and locks to organize your manual checks.

The 2048-word English list is bundled in `wordlist.js`. No recovery words are saved. Use a trusted offline computer; browser extensions, malware, and screen capture can still compromise secrets.

## iPhone

This release is **not yet a verified native iOS offline app**. Do not enter a real recovery phrase in Codespaces, a forwarded port, or a hosted website. A locally downloaded HTML file may not behave consistently across iOS Files/Safari. Test local-file compatibility and secure installation on a physical iPhone before claiming iOS support.

## Scope

- Real English BIP-39 wordlist and checksum checking for 12/15/18/21/24 words.
- Manual candidate entry, missing markers, explicit word locks, masking, clearing, and theoretical search-space estimates.
- No brute-force recovery, no key derivation, no address matching, no signing, no server.
- A valid checksum does not establish that a phrase belongs to a particular wallet.
- Client-side JavaScript cannot guarantee secure memory erasure.

## Verify a release candidate

Release candidates are built by `scripts/build_offline_release.py`. The archive is byte-for-byte reproducible: entries use a fixed order, timestamp (1980-01-01) and permissions, so the checksum depends only on file contents. Anyone can rebuild it from the same commit and compare.

```bash
# Rebuild from a clean checkout of the release commit
python scripts/build_offline_release.py --out dist
cat dist/SHA256SUMS        # first line: the archive; then each packaged file

# Verify a downloaded archive against the published SHA256SUMS
sha256sum -c SHA256SUMS --ignore-missing     # Linux/macOS
# Windows PowerShell: Get-FileHash .\mnemonic-recovery-offline-app.zip -Algorithm SHA256
```

The archive contains only `index.html`, `styles.css`, `app.js`, `wordlist.js`, `english.txt` and this README. The build refuses to package an `english.txt` that differs from the canonical BIP-39 list (SHA-256 `2f5eed53a4727b4bf8880d8f3f199efc90e58503646d9ff8eff3a2ed3b24dbda`). Do the checksum check before disconnecting and opening `index.html`.

## Release gates

- [ ] GitHub CI green, including offline-app tests.
- [ ] Manually test local file in Edge/Chrome with internet disconnected.
- [ ] Validate CSP and zero network requests.
- [ ] Reproducible build: an independent rebuild of the release commit matches the published `SHA256SUMS` (CI checks this on every release-candidate run).
- [ ] Publish `SHA256SUMS` with the release and link it from 0xcon.org next to the download.
- [ ] Independent security review before processing high-value wallet credentials.
- [ ] Package and verify a dedicated iPhone offline application separately.

Do **not** deploy this sensitive-input interface on a public website. The public site may link to a signed/downloadable offline package after release verification.
