# Security policy and threat model

Mnemonic Recovery Lab is an early-stage research utility, not a wallet and not a substitute for a hardware wallet or professional incident response.

## Current safeguards

- The dashboard binds only to `127.0.0.1`; its API accepts same-origin requests for a fixed route.
- The UI and Python service have no remote API calls, analytics, telemetry, browser storage, or file writes.
- HTTP request logging is disabled. Responses omit the submitted phrase.
- The phrase field is cleared before a validation request is sent. Terminal validation uses hidden input and does not accept a phrase as a command-line argument.
- The application has no candidate phrase generator, key/address derivation, blockchain lookup, signing, or transaction features.
- CI uses only public BIP-39 test vectors and deterministic synthetic phrases.

## Threat model and limitations

This application can reduce accidental disclosure to remote services, but cannot protect a phrase from a compromised operating system, malicious browser extension, screen capture, clipboard manager, keylogger, memory inspection, swap, or physical access. Python and browser processes temporarily handle the phrase in memory; clearing a field is not a guaranteed memory wipe. The local HTTP service is not intended for shared machines or untrusted browser sessions.

Install dependencies before disconnecting from the internet, then run on a trusted offline device if your threat model requires it. Do not copy sensitive phrases into shell commands, terminal transcripts, screenshots, issue trackers, CI, or configuration files. A valid checksum only detects some input errors; it does not prove wallet ownership, phrase correctness, or that an address is derived from the phrase.

The project does not currently implement wallet derivation, address matching, or public-chain analysis. Never infer control from a label or transaction history. Future public blockchain research must remain read-only and architecturally separate from sensitive recovery input.

## Reporting

Do not include secrets or live wallet details in reports. Open a private security advisory through GitHub's repository Security tab when available; otherwise contact the maintainers privately.
