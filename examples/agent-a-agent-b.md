# Example: agent-a to agent-b reliable handoff

```bash
export AGENT_HANDOFF_HOME="$PWD/.agent-handoff-bus"

# Terminal 1: receiver-side auto receipt bridge
agent-handoff-auto-reply --sessions agent-b --fallback-source agent-a --include-existing

# Terminal 2: reliable sender
agent-handoff-reliable \
  --from agent-a \
  --to agent-b \
  --title "Review request" \
  --body "Please review the attached local plan and reply with REPLY or BLOCKED." \
  --timeout 15
```

The sender sees `PASS` only after the bridge creates an `AUTO-RECEIVED` handoff back to `agent-a`.
