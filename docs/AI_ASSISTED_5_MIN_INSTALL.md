# AI-assisted 5-minute install

This is the fastest operator path: paste one bounded prompt into a local AI
coding assistant and let it perform the install, smoke test, and summary.

Use this for customer onboarding when the customer has a local AI assistant such
as Codex, Claude Code, or another terminal-capable agent. The AI should run only
local commands and must not request secrets, OAuth, public posting, package
publishing, paid APIs, or browser/session access.

## What the human does

1. Open a local terminal-capable AI assistant.
2. Paste the prompt in [Copy-paste AI installer prompt](#copy-paste-ai-installer-prompt).
3. Wait for the AI to return `INSTALL_READY` or an exact blocker.
4. Run one manual command if you want to inspect the installed CLI:

   ```bash
   handoff-bus status
   ```

Expected elapsed time on a normal developer machine: about 5 minutes after
Python and Git are already available.

## Requirements

The AI should first check these and report blockers instead of guessing:

- Python 3.10 or newer.
- Git.
- Network access to `https://github.com/Voicle99/agent-handoff-bus.git`.
- Permission to create a local directory under `$HOME`.

If any requirement is missing, the AI must stop with `BLOCKED_INSTALL_PREREQ` and
state the exact missing item.

## Copy-paste AI installer prompt

Paste this into the local AI assistant:

````text
Goal: install agent-handoff-bus locally in about 5 minutes and prove it works.

Rules:
- Run local terminal commands only.
- Do not ask for or read secrets, tokens, credentials, browser sessions, OAuth,
  paid APIs, public posting, package publishing, releases, or uploads.
- Do not use PyPI as the primary path unless `python3 -m pip index versions
  agent-handoff-bus` shows a real release. Source install from Git is the
  default.
- Use a clean local install directory under $HOME.
- Use an isolated AGENT_HANDOFF_HOME for the smoke test.
- If a command fails, stop and return BLOCKED_INSTALL with the exact command,
  exit code, and next fix.

Commands:

```bash
set -euo pipefail

python3 --version
git --version
python3 -m pip index versions agent-handoff-bus || true

INSTALL_DIR="${HOME}/agent-handoff-bus-install"
if [ -d "$INSTALL_DIR/.git" ]; then
  git -C "$INSTALL_DIR" pull --ff-only
else
  rm -rf "$INSTALL_DIR"
  git clone https://github.com/Voicle99/agent-handoff-bus.git "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .

export AGENT_HANDOFF_HOME="$(mktemp -d)"
handoff-bus doctor
handoff-bus send \
  --source-session agent-a \
  --to agent-b \
  --title "install smoke" \
  --body "hello from agent-a"
handoff-bus catchup agent-b
handoff-bus inbox --for agent-b --plain

cat <<REPORT
INSTALL_READY
install_dir=$INSTALL_DIR
venv=$INSTALL_DIR/.venv
state_dir=$AGENT_HANDOFF_HOME
commands_available=$(command -v handoff-bus),$(command -v agent-handoff)
next_manual_check=source $INSTALL_DIR/.venv/bin/activate && handoff-bus status
REPORT
```

DONE contract:
- Return `INSTALL_READY` only if `doctor`, `send`, `catchup`, and `inbox --plain`
  all passed.
- Include install_dir, venv, state_dir, command paths, and next_manual_check.
- If not ready, return `BLOCKED_INSTALL` or `BLOCKED_INSTALL_PREREQ` with exact
  command output and the smallest next fix.
````

## Success criteria

The AI output must include:

```text
INSTALL_READY
install_dir=...
venv=...
state_dir=...
commands_available=...
next_manual_check=...
```

The smoke test is valid only when:

- `handoff-bus doctor` returns top-level `PASS`.
- `handoff-bus send` returns `SENT`.
- `handoff-bus catchup agent-b` returns `pending_count: 1`.
- `handoff-bus inbox --for agent-b --plain` prints the smoke body.

## Optional persistent receipt bridge

After the basic install passes, the AI can set up a local auto-receipt bridge for
the customer's chosen sessions. This is optional and should be done only after
the customer confirms the source and target session names.

AI prompt:

```text
Set up only a local auto-receipt bridge for agent-handoff-bus. Do not approve,
post, publish, upload, use OAuth, call paid APIs, access credentials, or mark
original work complete. Use the existing installation and the chosen local
sessions: source=<source-session>, target=<target-session>. Prefer the packaged
service templates and keep rendered service files local only. Return exact
service file path, launch command, log path, and rollback command.
```

Templates:

- macOS launchd: [`../examples/launchd-auto-reply.plist.template`](../examples/launchd-auto-reply.plist.template)
- Linux systemd user service: [`../examples/systemd-auto-reply.service.template`](../examples/systemd-auto-reply.service.template)

## Troubleshooting for the AI

### `python3` missing or too old

Return:

```text
BLOCKED_INSTALL_PREREQ: Python 3.10+ required
```

Do not install a system Python unless the human explicitly asks.

### `git` missing

Return:

```text
BLOCKED_INSTALL_PREREQ: git required for source install
```

### `handoff-bus: command not found`

Usually the virtual environment is not active. Run:

```bash
cd "$HOME/agent-handoff-bus-install"
. .venv/bin/activate
command -v handoff-bus
handoff-bus doctor
```

### `BLOCKED_NO_AUTO_RECEIPT`

The basic 5-minute install does not require the auto-receipt bridge. This blocker
only applies to `agent-handoff-reliable`. Start `agent-handoff-auto-reply` for
the receiver session and retry.

### Secret-like body rejected

Do not bypass the scanner for onboarding. Use a dummy body such as
`hello from agent-a`.

## Customer handoff summary template

After a successful install, the AI should give the customer this summary:

```text
agent-handoff-bus is installed and smoke-tested.

Install directory: <install_dir>
Virtual environment: <venv>
Temporary smoke-test state: <state_dir>
Main command: handoff-bus
Manual status check: <next_manual_check>

Validated:
- doctor PASS
- send SENT
- catchup pending_count=1
- inbox body visible

Not done:
- no public posts
- no package publishing
- no OAuth/login changes
- no paid APIs
- no credential access
```
