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

### Scanner limits

Known false-positive cases:

- dummy tokens that intentionally match a real provider shape
- documentation snippets that show token-like examples
- redacted incident reports that preserve a token prefix for explanation

Known false-negative cases:

- provider formats not listed above
- credentials split across several words, lines, or files
- encoded, compressed, image, binary, or attachment-based secrets
- natural-language descriptions that reveal sensitive account context without a token pattern

When an auto-receipt sees a secret-like hint in the stored body, it reports `BLOCKED_SECRET_HINT: body not quoted`. Receipts must stay summary-only and must not copy the original handoff body.

## Local-only transport

- Default state lives under `~/.agent-handoff-bus`.
- HTTP API may only bind to `127.0.0.1`, `localhost`, or `::1`.
- Handoff bodies are normal local markdown files. Protect your filesystem accordingly.

## High-risk handoff policy check

Use the local policy checker before acting on handoffs that may request public,
paid, OAuth, account, credential, release, package, or deployment actions:

```bash
PYTHONPATH=src python3 tools/handoff_policy_check.py \
  --body-file /path/to/local-handoff-draft.md
```

Expected fail-closed statuses:

- `BLOCKED_PRIVATE_OR_SECRET_DATA`: remove real secrets, private logs, personal paths, account data, or private transcripts.
- `BLOCKED_HIGH_RISK_HANDOFF_REQUIRES_APPROVAL`: the handoff asks for a high-risk action without exact approval.

Exact approval must start with `APPROVED_HIGH_RISK_HANDOFF:` and name the concrete
action and target. A passing policy check still performs no public, paid, OAuth,
credential, release, or package action; it only says the local text is ready for
a separately approved execution step.

## Receipt semantics

`AUTO-RECEIVED` means only that a local receiver-side bridge saw the handoff. It is not task completion. It is not permission. It is not an ACK of the original handoff.
