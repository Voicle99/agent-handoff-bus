# agent-handoff-bus

Local-first handoff bus for coordinating AI agents without UI paste, focus stealing, or hidden public actions.

`agent-handoff-bus` gives multiple local agent sessions a small shared mailbox:

- SQLite metadata + file-backed message bodies
- CLI and optional localhost-only HTTP API
- `send`, `latest`, `show`, `ack`, `watch`, `doctor`, `serve`
- exact-once auto-receipt bridge for reliable delivery checks
- fail-closed reliable sender: no receipt means `BLOCKED_NO_AUTO_RECEIPT`
- secret-like material blocked by default
- no dependencies outside the Python standard library

## Safety model

A handoff is **not** approval for public, paid, credential, OAuth, or account actions.

This project is designed to be safe by default:

- no UI paste, click automation, or focus stealing
- API server refuses non-loopback hosts
- secret-like content is blocked unless explicitly bypassed
- auto-receipts never quote the original body
- delivery receipt is not task completion and does not ACK the original handoff
- all state is local under `AGENT_HANDOFF_HOME` or `~/.agent-handoff-bus`

See [`docs/SAFETY.md`](docs/SAFETY.md).

## Install

```bash
python3 -m pip install agent-handoff-bus
```

For local development:

```bash
git clone https://github.com/Voicle99/agent-handoff-bus.git
cd agent-handoff-bus
python3 -m pip install -e .
```

## Quick start

Use an isolated bus home while trying it:

```bash
export AGENT_HANDOFF_HOME="$PWD/.agent-handoff-bus"
agent-handoff doctor
```

Send a handoff from one local agent/session to another:

```bash
agent-handoff send \
  --from agent-a \
  --to agent-b \
  --title "Please review this plan" \
  --body "Check the assumptions, then reply with REPLY or BLOCKED."
```

Read it:

```bash
agent-handoff latest --for agent-b --pending-only --plain
```

Ack only after the receiver has actually read or handled it:

```bash
agent-handoff ack <handoff-id> --note DONE
```

## Reliable receipt bridge

Start an auto-receipt bridge in one terminal:

```bash
export AGENT_HANDOFF_HOME="$PWD/.agent-handoff-bus"
agent-handoff-auto-reply --sessions agent-b --fallback-source agent-a --include-existing
```

Then send and wait for a receipt:

```bash
agent-handoff-reliable \
  --from agent-a \
  --to agent-b \
  --title "critical handoff" \
  --body "Return a concise decision." \
  --timeout 15
```

Success returns `PASS` only after a receipt handoff is observed. If the bridge is not running, the command fails closed with `BLOCKED_NO_AUTO_RECEIPT`.

## Localhost API

```bash
agent-handoff serve --host 127.0.0.1 --port 8791
curl http://127.0.0.1:8791/health
```

The server refuses public binds such as `0.0.0.0`.

## Configuration

- `AGENT_HANDOFF_HOME`: state directory. Default: `~/.agent-handoff-bus`.
- `AGENT_HANDOFF_SESSION`: optional default source session for reliable sends.

## macOS launchd

Use the templates in [`examples/`](examples/). They intentionally contain placeholders; generate user-specific paths locally and do not commit rendered plist files.


## Project maintenance

- [Roadmap](ROADMAP.md)
- [Maintenance log](docs/MAINTENANCE_LOG.md)
- [Maintainer workflow recipes](docs/MAINTAINER_RECIPES.md)
- [Optional local adapter boundary](docs/ADAPTERS.md)
- [Security policy](SECURITY.md)
- [Contributing guide](CONTRIBUTING.md)

## Development checks

```bash
python3 -m py_compile src/agent_handoff_bus/*.py tests/*.py
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Run the local receipt benchmark when changing reliable-send or auto-reply behavior:

```bash
PYTHONPATH=src python3 tools/receipt_benchmark.py
```

For repeatable local automation or CI-like dry runs, use the workflow in
[`docs/MAINTAINER_RECIPES.md#ci-like-local-operation`](docs/MAINTAINER_RECIPES.md#ci-like-local-operation).

Run the dummy local adapter example when exploring adapter boundaries:

```bash
PYTHONPATH=src python3 tools/local_adapter_dry_run.py --body "Dummy local-only request."
```

## Privacy

Do not put API keys, private tokens, customer data, or private chat transcripts into handoff bodies. The scanner catches common secret patterns but is not a full DLP product.
