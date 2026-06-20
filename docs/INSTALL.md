# Installation guide

This guide is the repeatable customer/operator path for installing
`agent-handoff-bus` without local one-off tuning.

If the customer has a local terminal-capable AI assistant, the fastest path is
the [AI-assisted 5-minute install](AI_ASSISTED_5_MIN_INSTALL.md).

For paid pilots and customer onboarding scope, see [Pricing and offer](PRICING_AND_OFFER.md), [Support](../SUPPORT.md), [Terms](../TERMS.md), and [Privacy](../PRIVACY.md).

## What gets installed

The package provides:

- `handoff-bus`: short operator CLI.
- `agent-handoff`: canonical CLI for the same command surface.
- `agent-handoff-auto-reply`: local auto-receipt bridge.
- `agent-handoff-reliable`: send-and-wait-for-receipt helper.

State is local file + SQLite storage under `AGENT_HANDOFF_HOME` or
`~/.agent-handoff-bus`. No hosted service, OAuth flow, paid API, or cloud model
is required.

## Requirements

- Python 3.10 or newer.
- A POSIX-like shell for the examples below.
- Optional: `git` for source installs.
- Optional: `pipx` if you want a globally available isolated CLI.

## Install path A: source checkout

Use this path until a versioned package has been published to an index.

```bash
git clone https://github.com/Voicle99/agent-handoff-bus.git
cd agent-handoff-bus
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
handoff-bus doctor
```

Expected result:

```json
{
  "status": "PASS"
}
```

`doctor` may include additional check details, but the top-level status must be
`PASS`.

## Install path B: pipx from Git

Use this when you want `handoff-bus` on your shell PATH without manually
activating a project virtual environment.

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install git+https://github.com/Voicle99/agent-handoff-bus.git
handoff-bus doctor
```

Upgrade:

```bash
pipx upgrade agent-handoff-bus
```

Uninstall:

```bash
pipx uninstall agent-handoff-bus
```

## Install path C: package index release

Do not use a package-index command until a release is actually visible on the
target index.

Check first:

```bash
python3 -m pip index versions agent-handoff-bus
```

Then install a pinned version:

```bash
python3 -m pip install "agent-handoff-bus==<version>"
```

If the index reports no matching distribution, use source checkout or pipx from
Git instead.

## First smoke test

Use an isolated bus home so the test cannot collide with real operator state:

```bash
export AGENT_HANDOFF_HOME="$(mktemp -d)"
handoff-bus doctor
handoff-bus send \
  --source-session agent-a \
  --to agent-b \
  --title "install smoke" \
  --body "hello from agent-a"
handoff-bus catchup agent-b
handoff-bus inbox --for agent-b --plain
```

Expected:

- `doctor` returns `PASS`.
- `send` returns `SENT`.
- `catchup` returns `pending_count: 1`.
- `inbox --plain` prints the handoff body.

Clean up the temporary state when done:

```bash
rm -rf "$AGENT_HANDOFF_HOME"
unset AGENT_HANDOFF_HOME
```

## Reliable receipt smoke test

Terminal 1:

```bash
export AGENT_HANDOFF_HOME="$(mktemp -d)"
agent-handoff-auto-reply \
  --sessions agent-b \
  --fallback-source agent-a \
  --include-existing
```

Terminal 2, using the same `AGENT_HANDOFF_HOME` value:

```bash
agent-handoff-reliable \
  --from agent-a \
  --to agent-b \
  --title "receipt smoke" \
  --body "confirm local receipt" \
  --timeout 15
```

Expected:

```json
{
  "status": "PASS"
}
```

If the receiver bridge is not running, the reliable sender must fail closed with
`BLOCKED_NO_AUTO_RECEIPT`.

## Persistent local auto-receipt service

Persistent services are optional. They are local-only and only send delivery
receipts. They do not approve tasks, post publicly, publish releases, upload
packages, call paid APIs, use OAuth, read credentials, or mark the original
handoff complete.

Templates:

- macOS launchd: [`../examples/launchd-auto-reply.plist.template`](../examples/launchd-auto-reply.plist.template)
- Linux systemd user service: [`../examples/systemd-auto-reply.service.template`](../examples/systemd-auto-reply.service.template)

Render placeholders locally:

- `${PYTHON_BIN}`: path to the Python interpreter that can import the package.
- `${AGENT_HANDOFF_HOME}` or equivalent environment value: local state directory.
- source and target sessions: the two local agents you want to coordinate.

Do not commit rendered service files. Keep machine paths in the operator's local
service directory only.

## Common commands

```bash
handoff-bus doctor
handoff-bus status
handoff-bus send --source-session agent-a --to agent-b --title "review" --body "Review this."
handoff-bus catchup agent-b
handoff-bus inbox --for agent-b --plain
handoff-bus show <handoff-id> --full
handoff-bus ack <handoff-id> --note DONE
```

## Troubleshooting

### `handoff-bus: command not found`

The CLI is not on the current shell PATH.

- If you used a virtual environment, activate it again:
  `. .venv/bin/activate`
- If you used `pipx`, run `python3 -m pipx ensurepath` and open a new shell.
- Verify the executable:
  `python3 -m pip show agent-handoff-bus`

### `doctor` returns `HOLD` for `cli_available`

This means neither `agent-handoff` nor `handoff-bus` is visible on PATH from the
current process. Re-check your virtual environment or `pipx` PATH. The top-level
status must be `PASS` before treating the install as ready.

### `BLOCKED_NO_AUTO_RECEIPT`

The receiver-side `agent-handoff-auto-reply` bridge is not running, is watching
the wrong session, or is using a different `AGENT_HANDOFF_HOME`.

Run:

```bash
handoff-bus doctor
echo "$AGENT_HANDOFF_HOME"
agent-handoff-auto-reply --sessions <receiver-session> --fallback-source <sender-session> --include-existing
```

### Secret-like body is rejected

The scanner blocks common API keys, bearer tokens, private-key blocks, and
similar material by default. Do not put credentials into handoff bodies. Use a
redacted summary and store sensitive values in the appropriate local secret
manager.

### Public or paid action confusion

A handoff is coordination, not approval. It does not authorize public comments,
posts, uploads, package publishing, releases, OAuth/login changes, paid APIs, or
credential access.

## Production/customer checklist

Before calling an install ready:

- `handoff-bus doctor` returns top-level `PASS`.
- A send/catchup/inbox smoke test passes under an isolated `AGENT_HANDOFF_HOME`.
- If receipts are required, `agent-handoff-reliable` returns `PASS`.
- The operator knows the exact state directory in use.
- No rendered service file or local path has been committed to the repository.
- Public/paid/OAuth/credential actions remain separately approved outside the
  handoff bus.
