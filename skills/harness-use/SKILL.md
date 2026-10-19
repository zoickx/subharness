---
name: harness-use
description: >-
  Launch and interact with another installed AI harness on Linux: Claude Code,
  Codex CLI, OpenCode, or Antigravity CLI (agy). Covers CLI options, live progress,
  steering, background processes, and session resume for external agents.
---

# Harness use

A **subharness** is another AI agent running through its own harness. Use it for
whatever role the task needs. These references describe access and capabilities;
they do not prescribe delegation, review, or ownership of its work.

## Load the relevant pair

Read the callee reference for the harness you want to use. Read the caller
reference only if you need guidance on your own process tools. There is no need
to load the other combinations.

| Harness | Call this harness | Call from this harness |
| --- | --- | --- |
| Claude Code | [Callee](references/claude-callee.md) | [Caller](references/claude-caller.md) |
| Codex CLI | [Callee](references/codex-callee.md) | [Caller](references/codex-caller.md) |
| OpenCode | [Callee](references/opencode-callee.md) | [Caller](references/opencode-caller.md) |
| Antigravity CLI (`agy`) | [Callee](references/agy-callee.md) | [Caller](references/agy-caller.md) |

Other callers can use the callee references with their own shell/process tools.
Assume the requested CLI is installed and authenticated. These notes target
current stable releases. Consult the linked docs or command help when something
is missing or fails; routine version matching is unnecessary.

## Process and context choices

- A direct foreground call is enough for a short task. A retained process handle
  or native background session permits other work while it runs. A watcher
  subagent is useful when interpreting events would otherwise consume the main
  agent's attention; it is not required for every launch.
- Live output, queued follow-up, active-turn steering, and interruption are
  distinct capabilities. Select the interface that provides what you need.
  Streaming output alone does not imply writable stdin or live steering.
- Machine streams work best through pipes. A TUI needs a PTY. Keep stdin open
  for a multi-turn protocol; closing it may end the session. A tool yielding
  control is different from its execution timeout killing the command.
- To watch cheaply, keep raw output in a file and consume new events or a bounded
  tail: state, tool name, a short message, errors, final result. Avoid importing
  reasoning, repeated snapshots, and entire tool outputs into the parent context.
  For a process you may revisit, retain its handle/session ID, cwd, and log path.
- For targeted messages, ask the subharness to emit an agreed short text marker
  or write to a shared status file. A watcher can forward matching updates through
  its own messaging tool. This is a prompt convention, not a cross-harness native
  messaging channel; OS notifications alone do not deliver model input.
- If harness troubleshooting becomes a task of its own, delegate it to a native
  subagent when available. Give it the command, failure, and log location; ask for
  a diagnosis and working invocation. Without subagents, keep the investigation
  bounded and return the concrete blocker instead of burying the main task.

The child loads its own credentials, configuration, plugins, and directory
instructions. Permission flags change its behavior, not the caller's authority.
Pending approvals, questions, retries, and unclosed stdin can look like hangs.
Use the target's status/result events and stderr to distinguish them; an exit
code alone does not establish task success.
