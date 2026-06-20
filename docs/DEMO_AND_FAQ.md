# Demo and FAQ

## Two-minute demo script

Audience: AI operator, agency owner, founder, or engineering lead already using
multiple local AI agents.

### 0:00 — Problem

“Right now your AI agents are chat boxes. When TOM needs Jelly, or one local
agent needs another, you either paste manually or lose context. That is slow and
not auditable.”

### 0:20 — Install proof

Run:

```bash
handoff-bus doctor
```

Show top-level `PASS`.

### 0:40 — Send handoff

Run:

```bash
handoff-bus send \
  --source-session agent-a \
  --to agent-b \
  --title "Demo handoff" \
  --body "Please review this local task and reply with PASS or BLOCKED."
```

Show `status: SENT` and the handoff ID.

### 1:05 — Receiver catch-up

Run:

```bash
handoff-bus catchup agent-b
handoff-bus inbox --for agent-b --plain
```

Show the body is visible without UI paste or focus stealing.

### 1:30 — ACK semantics

Run:

```bash
handoff-bus ack <handoff-id> --note DONE
```

Explain: receipt is delivery; ACK is after the receiver has handled it.

### 1:50 — Safety boundary

Say:

“Notice this did not post, upload, deploy, use OAuth, charge money, or read
credentials. It is local coordination infrastructure.”

## Demo checklist

Before recording a demo:

- Use dummy handoff content only.
- Use a temporary `AGENT_HANDOFF_HOME`.
- Do not show private paths if recording publicly.
- Do not include customer data, tokens, browser sessions, or private logs.
- End with the AI-assisted install guide link.

## FAQ

### Is this SaaS?

No. The core package is local-first software. It can be wrapped by a guided setup
or managed support offer.

### Does it require OpenAI, Anthropic, or paid APIs?

No. The core package has no runtime dependencies and does not require cloud AI.

### Does it replace my AI agent?

No. It coordinates handoffs between agents or sessions. It is plumbing, not the
worker itself.

### Is it safe for secrets?

Do not put secrets in handoff bodies. The package includes a basic scanner for
common secret-like material, but it is not a full DLP system.

### Can it run on Windows?

The package is pure Python and may work where Python and SQLite work, but current
CI supports Linux and local smoke has been run on macOS. Treat Windows as not yet
formally supported until a Windows CI matrix is added.

### Is it production-ready?

It is ready for guided pilots and technical operators. For broad enterprise
rollout, add organization-specific support, policy, and compliance review.
