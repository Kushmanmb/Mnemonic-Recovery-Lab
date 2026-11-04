# 0xcon / GEN0X integration contract

Status: **design only**. This repository currently runs a Python loopback HTTP server. It is **not** safe to embed its mnemonic entry form into the hosted 0xcon.org site or to proxy mnemonic requests through Cloudflare, Render, GitHub, or other infrastructure.

## Supported first phase (public information only)

- Link from the authenticated 0xcon GEN0X tools navigation to a **documentation and launch instructions** page for the locally installed Mnemonic Recovery Lab.
- Present word-count and missing-position search-space estimates on 0xcon without collecting actual mnemonic words. These inputs are not secrets.
- Keep public Ethereum contract inspection and ownership-event research in a distinct read-only module. Never combine its request payloads with sensitive phrase inputs.
- Display an explicit warning: no real recovery phrase should ever be typed into the hosted 0xcon.org website.

## Required security gate before any hosted UI

A production-hosted integration must **not** send mnemonic words to a Python loopback server, hosted backend, Cloudflare Worker, RPC endpoint, analytics, error reporting, service worker, or third-party script. The current local dashboard sends phrases from the browser to the Python process over loopback, which is acceptable only for a trusted local-only installation, not as a hosted website design.

If a future hosted interface is proposed, implement and independently review a self-contained, audited, browser-only validation module with no network request paths for secrets. Use strict CSP, isolate secret-entry pages from third-party assets, disable telemetry, avoid storage and clipboard handling, and document the unavoidable risks of compromised browsers and extensions. Prefer a downloadable offline application for real phrases.

## Acceptance criteria

1. Existing 0xcon and GEN0X navigation and authentication continue working.
2. Hosted pages never accept or transmit actual recovery phrases.
3. Public-only inputs and contract lookups are clearly separated from offline secret handling.
4. Tests use published BIP-39 vectors and synthetic phrases only.
5. Security review verifies network requests, logging, CSP, and privacy boundaries.
6. Do not deploy or merge automatically.

## Recovery expectations

A checksum-valid phrase does not establish wallet ownership or identify a target address. Four unknown English BIP-39 words imply 2048^4 possible combinations before checksum filtering. This project does not claim that a recovery phrase can unlock a historical multisignature smart contract directly.
