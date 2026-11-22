# pleer-status

Public metadata for the **Плеер** Android app (`org.nikita.player`).

This repository holds only:

- [`latest.json`](./latest.json) — current version name/code and a Telegram deep link to download the APK
- [`status.json`](./status.json) — signed subscription status, keyed by `SHA-256(installId)` (no Telegram user ids, no raw install ids)
- [`ed25519_public.hex`](./ed25519_public.hex) — Ed25519 public key used to verify `status.json`

Raw URLs:

- https://raw.githubusercontent.com/nikitatereshin00-arch/pleer-status/main/latest.json
- https://raw.githubusercontent.com/nikitatereshin00-arch/pleer-status/main/status.json

A scheduled GitHub Action copies the live files here. Do not commit secrets, bot tokens, or private keys.
