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

Current repeatable install path:

```bash
git clone https://github.com/Voicle99/agent-handoff-bus.git
cd agent-handoff-bus
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
handoff-bus doctor
```

The package is not useful to operators until `doctor` returns top-level
`PASS`. For pipx, future package-index installs, persistent service templates,
smoke tests, troubleshooting, and customer readiness checks, see the
[installation guide](docs/INSTALL.md).

For the fastest customer onboarding path, use the
[AI-assisted 5-minute install](docs/AI_ASSISTED_5_MIN_INSTALL.md).

For local development after cloning:

```bash
python3 -m pip install -e .
```

The package installs both command names:

- `agent-handoff`: canonical package command.
- `handoff-bus`: short operator command for the same CLI, so teams can use one
  memorable command without machine-specific shell wrappers.

## Quick start

Use an isolated bus home while trying it:

```bash
export AGENT_HANDOFF_HOME="$PWD/.agent-handoff-bus"
handoff-bus doctor
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

Or use the operator-friendly catch-up alias:

```bash
handoff-bus catchup agent-b
handoff-bus inbox --for agent-b --plain
```

Ack only after the receiver has actually read or handled it:

```bash
handoff-bus ack <handoff-id> --note DONE
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

## Local service templates

Use the templates in [`examples/`](examples/) when you want the local auto-reply
bridge to start from your workstation service manager. They intentionally contain
placeholders; render user-specific paths locally and do not commit rendered
service files.

- macOS launchd: [`examples/launchd-auto-reply.plist.template`](examples/launchd-auto-reply.plist.template)
- Linux systemd user service: [`examples/systemd-auto-reply.service.template`](examples/systemd-auto-reply.service.template)

These templates only run the local auto-receipt bridge. They do not approve,
post, publish, release, upload packages, call paid APIs, access credentials, or
mark the original task complete.

Before committing service-template changes, run:

```bash
PYTHONPATH=src python3 tools/service_template_guard.py
```

The guard blocks rendered service files and user-specific paths under `examples/`.


## Project maintenance

- [Roadmap](ROADMAP.md)
- [Installation guide](docs/INSTALL.md)
- [AI-assisted 5-minute install](docs/AI_ASSISTED_5_MIN_INSTALL.md)
- [Pricing and offer](docs/PRICING_AND_OFFER.md)
- [Demo and FAQ](docs/DEMO_AND_FAQ.md)
- [Terms](TERMS.md)
- [Privacy](PRIVACY.md)
- [Support](SUPPORT.md)
- [Changelog](CHANGELOG.md)
- [Maintenance log](docs/MAINTENANCE_LOG.md)
- [Maintainer workflow recipes](docs/MAINTAINER_RECIPES.md)
- [GitHub issue and PR dry-run workflow](docs/GITHUB_WORKFLOW_DRY_RUN.md)
- [Optional local adapter boundary](docs/ADAPTERS.md)
- [Security policy](SECURITY.md)
- [Contributing guide](CONTRIBUTING.md)

## Development checks

```bash
python3 -m py_compile src/agent_handoff_bus/*.py tests/*.py tools/*.py
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 tools/docs_link_check.py
```

Check that the local checkout itself is usable:

```bash
PYTHONPATH=src python3 tools/worktree_health_check.py
```

For a single local maintainer routine that bundles the recurring safe gates:

```bash
PYTHONPATH=src python3 tools/maintainer_check.py
```

Save a durable local JSON receipt for scheduled or repeated maintainer runs:

```bash
PYTHONPATH=src python3 tools/maintainer_check.py --output /tmp/agent-handoff-bus-maintainer-check.json
```

The bundle performs no public action. It only reports whether the selected local checks passed.

Draft release notes locally from recent commit summaries:

```bash
PYTHONPATH=src python3 tools/release_notes_dry_run.py --limit 10
```

The dry run does not create a release, tag, package upload, or public post.

Run the local receipt benchmark when changing reliable-send or auto-reply behavior:

```bash
PYTHONPATH=src python3 tools/receipt_benchmark.py
```

For repeatable local automation or CI-like dry runs, use the workflow in
[`docs/MAINTAINER_RECIPES.md#ci-like-local-operation`](docs/MAINTAINER_RECIPES.md#ci-like-local-operation).

Run the local handoff policy checker before executing high-risk handoff requests:

```bash
PYTHONPATH=src python3 tools/handoff_policy_check.py \
  --body "Review this local patch. Do not post, release, or access credentials."
```

High-risk handoffs fail closed until an exact approval is supplied. The checker never performs public, paid, OAuth, or credential actions.

Run the dummy local adapter example when exploring adapter boundaries:

```bash
PYTHONPATH=src python3 tools/local_adapter_dry_run.py --body "Dummy local-only request."
```

Guard local issue or PR drafts before any public maintainer action:

```bash
PYTHONPATH=src python3 tools/public_action_draft_guard.py --draft path/to/local-draft.md
```

Check local Markdown links before committing docs changes:

```bash
PYTHONPATH=src python3 tools/docs_link_check.py
```

## Privacy

Do not put API keys, private tokens, customer data, or private chat transcripts into handoff bodies. The scanner catches common secret patterns but is not a full DLP product.
