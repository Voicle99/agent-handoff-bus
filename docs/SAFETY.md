# Safety and privacy boundary

`agent-handoff-bus` is a local coordination primitive. It does not grant authority.

## Non-goals

A handoff does not authorize:

- public posting, upload, publishing, deployment, or email/DM sending
- paid API calls or purchases
- OAuth/login/account-permission changes
- credential access, token extraction, Keychain/keyring reads, or password handling
- private scraping or bypassing platform permissions

## Secret handling

The default sender blocks common secret-like patterns, including:

- OpenAI-style `sk-...` keys
- GitHub `ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_` tokens
- AWS access key IDs
- private key blocks
- `Bearer ...` tokens
- long `api_key=...`, `password=...`, `secret=...`, `token=...` assignments

The scanner is a guardrail, not a guarantee. Keep secrets out of handoff text.

## Local-only transport

- Default state lives under `~/.agent-handoff-bus`.
- HTTP API may only bind to `127.0.0.1`, `localhost`, or `::1`.
- Handoff bodies are normal local markdown files. Protect your filesystem accordingly.

## Receipt semantics

`AUTO-RECEIVED` means only that a local receiver-side bridge saw the handoff. It is not task completion. It is not permission. It is not an ACK of the original handoff.
