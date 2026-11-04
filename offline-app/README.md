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

## Release gates

- [ ] GitHub CI green, including offline-app tests.
- [ ] Manually test local file in Edge/Chrome with internet disconnected.
- [ ] Validate CSP and zero network requests.
- [ ] Independent security review before processing high-value wallet credentials.
- [ ] Package and verify a dedicated iPhone offline application separately.

Do **not** deploy this sensitive-input interface on a public website. The public site may link to a signed/downloadable offline package after release verification.
