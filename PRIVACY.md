# Privacy

Last updated: 2026-06-20

`agent-handoff-bus` is designed as local-first software.

## Default data flow

By default, the package stores handoff metadata in SQLite and handoff bodies in
local files under `AGENT_HANDOFF_HOME` or `~/.agent-handoff-bus`.

The core package does not require:

- hosted service accounts;
- cloud AI providers;
- OAuth;
- browser/session access;
- paid APIs;
- telemetry or analytics accounts.

## Telemetry

The core package does not include product telemetry, tracking pixels, analytics
beacons, or background network reporting.

## What may be stored locally

Depending on your usage, local state may include:

- source and target session names;
- handoff titles and bodies;
- body file paths;
- timestamps;
- ACK notes;
- safety metadata such as secret-scan hints.

Do not put passwords, API keys, OAuth tokens, private keys, customer secrets, or
regulated personal data into handoff bodies.

## Local API

The optional HTTP API is intended for loopback use only. The server refuses
non-loopback hosts such as `0.0.0.0`.

## Support data

If you ask for support, only share minimal diagnostic information:

- command used;
- exact error text;
- `handoff-bus doctor` output after redacting paths if needed;
- operating system and Python version.

Do not send real credentials, private customer data, or private handoff bodies in
support requests.

## Data deletion

To delete local bus state, remove the state directory you configured:

```bash
rm -rf "${AGENT_HANDOFF_HOME:-$HOME/.agent-handoff-bus}"
```

Only run this after confirming you no longer need the local handoff history.

## Managed setup

For paid guided setup, the operator should use a customer-approved local
workspace and should not request passwords or long-lived secrets through chat or
email. Any customer-specific support arrangement should define where diagnostic
files may be shared.
