# Security policy and threat model

Mnemonic Recovery Lab is an early-stage research utility, not a wallet and not a substitute for a hardware wallet or professional incident response.

## Current safeguards

- The dashboard binds only to `127.0.0.1`; validation and fixture-stream POST endpoints require an exact loopback Host, same-origin Origin, and JSON content type. The browser disables recovery input and reference fetching on non-HTTP/non-127.0.0.1 origins. Never use real phrases through cloud-hosted or tunneled development sessions: a transparent loopback tunnel is not detectable.
- The UI and Python service have no remote API calls, analytics, telemetry, browser storage, or file writes.
- HTTP request logging is disabled. Responses omit the submitted phrase.
- The bulk phrase textarea is cleared on import. Numbered slots are masked by default and remain in active-page memory for manual candidate checks; clear-session/navigation handlers discard them on a best-effort basis. They are not placed in URLs, cookies, browser storage, or files. Terminal validation still uses hidden input, does not echo invalid words, and does not accept phrases as command-line arguments.
- Dictionary membership and checksum results never automatically lock words or confirm missing positions. A lock reflects only the user's explicit assertion. A checksum-valid manual candidate is not a confirmed recovery.
- Candidate testing accepts only built-in public/disposable fixture identifiers, never arbitrary phrases or user-supplied entropy. Per-run candidate checks are capped at 100,000, benchmark repetitions at 10. Progress and final records contain aggregate metrics only. Cancellation is checked between candidates.
- The public reference endpoint returns only the installed English word list and built-in fixture words. The fixture stream accepts only fixture ID, positions, and budget, never entered words. Disconnecting cancels on the next failed progress write (every 32 candidates); partial counts do not imply recovery. The browser suppresses late responses after cancellation or input edits.
- The application has no general-purpose recovery search, key/address derivation, blockchain lookup, signing, or transaction features. Fixture wallets are public test material and must never receive funds.
- CI uses only public BIP-39 test vectors and deterministic synthetic phrases.
- CI runs source security scanning, Python/npm dependency auditing, a reproducible frontend build check, and browser privacy/regression tests. Auditors contact package/advisory services with package metadata only; they are not part of offline runtime processing. Browser traces and automatic video/screenshots are disabled; explicit visual-test screenshots use public fixture words only.

## Threat model and limitations

This application can reduce accidental disclosure to remote services, but cannot protect a phrase from a compromised operating system, malicious browser extension, screen capture, clipboard manager, keylogger, memory inspection, swap, or physical access. Python and browser processes temporarily handle the phrase in memory; clearing a field is not a guaranteed memory wipe. The local HTTP service is not intended for shared machines or untrusted browser sessions.

The experiment module also temporarily constructs public fixture candidates in memory. It does not retain or emit them. A progress callback runs synchronously and should return promptly; cancellation cannot interrupt a blocked callback. Benchmark timings include callback overhead and are not an estimate of unrestricted recovery throughput. The candidate cap bounds work, not the theoretical search space; partial searches may never encounter the known fixture.

Install dependencies before disconnecting from the internet, then run on a trusted offline device if your threat model requires it. Do not copy sensitive phrases into shell commands, terminal transcripts, screenshots, issue trackers, CI, or configuration files. A valid checksum only detects some input errors; it does not prove wallet ownership, phrase correctness, or that an address is derived from the phrase.

The project does not currently implement wallet derivation, address matching, or public-chain analysis. Never infer control from a label or transaction history. Future public blockchain research must remain read-only and architecturally separate from sensitive recovery input.

## Reporting

Do not include secrets or live wallet details in reports. Open a private security advisory through GitHub's repository Security tab when available; otherwise contact the maintainers privately.
