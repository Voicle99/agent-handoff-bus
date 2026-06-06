# Optional local adapter boundary

`agent-handoff-bus` is useful without adapters. The core package must remain local-first, dependency-free, and safe without any cloud provider.

Adapters are optional edges around the bus. They may help a maintainer hand work to a local tool, but they must not change the core safety model.

## Adapter principles

1. **Local-first:** default examples use local commands, temporary state, and dummy data.
2. **Provider-optional:** no cloud model, paid API, OAuth flow, or hosted service is required to use the bus.
3. **Human-gated public action:** adapters may draft or summarize; they must not post, comment, publish, release, deploy, email, or buy anything unless an explicit human approval is provided for that exact action.
4. **No credential access:** adapters must not read keyrings, browser storage, `.env` files, private tokens, or account sessions.
5. **Receipt semantics stay intact:** `AUTO-RECEIVED` is delivery proof only, not completion and not permission.
6. **Fail closed:** uncertain adapter state should return `BLOCKED` or `ERROR`, not a quiet success.

## Minimal adapter shape

A future adapter should accept a small local request and return a small local result.

Request fields:

- `task_id`: stable local identifier
- `source_session`: sender name
- `target_session`: adapter or tool name
- `handoff_id`: original handoff id when available
- `title`: short task title
- `body_path`: local path to the handoff body
- `dry_run`: boolean, default `true` for examples
- `public_action_allowed`: boolean, default `false`

Result fields:

- `status`: `PASS`, `BLOCKED`, `ERROR`, or `SKIP`
- `summary`: concise local result
- `artifacts`: local paths only
- `public_action_taken`: boolean, normally `false`
- `next_action`: exact human or local follow-up

## Allowed examples

- Summarize a local handoff body into a local markdown note.
- Run a local lint/test command and return status plus log path.
- Draft a public issue comment as a local file without posting it.
- Produce a release checklist verdict without tagging or publishing.

## Forbidden examples

- Reading credentials, `.env` files, keyrings, browser cookies, or private account state.
- Binding the HTTP API to a public interface.
- Posting GitHub comments, publishing releases, uploading packages, sending email, or using paid APIs without exact human approval.
- Treating `AUTO-RECEIVED` as completion.
- Sending original handoff bodies to external services by default.

## Local dry-run example

Run the bundled dummy adapter with local-only input:

```bash
PYTHONPATH=src python3 tools/local_adapter_dry_run.py \
  --task-id example-adapter-run \
  --title "Adapter boundary smoke" \
  --body "Dummy local-only request. No credentials. No public action."
```

Expected shape:

```json
{
  "status": "PASS",
  "summary": "Local dummy adapter processed the handoff body summary-only.",
  "artifacts": ["/tmp/agent-handoff-bus-example/result.md"],
  "public_action_taken": false,
  "next_action": "Human may inspect the local artifact before any public action."
}
```

The artifact is summary-only. It records metadata such as body hash and byte count, but it does not quote the original handoff body. The example path above is illustrative; do not commit user-specific rendered paths or private logs.

## Review checklist

Before adding adapter code, verify:

- compile and unit tests pass
- receipt benchmark passes when relevant
- secret/private scans pass
- Bumblebee scan passes when available
- adapter docs state the human gate for public/paid/OAuth actions
- examples use dummy data only
