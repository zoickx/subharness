# Call from Claude Code

Use `Bash` for a short external CLI command. For longer jobs,
`run_in_background: true` returns a task ID and an output file path; a
`task-notification` with status and exit code arrives on completion, and the
file ends with `[exited with code N]`. That code is the last pipeline stage's,
so a child failure piped through `jq` reports 0; use `pipefail` or check events.
`TaskOutput` may not be exposed; read a bounded slice of the file instead.
`TaskStop` takes the task ID and kills the process. A command exceeding a
foreground `timeout` is moved to the background with a new task ID, not killed.
Foreground `sleep` is blocked by the tool; poll with a bounded `until` loop.

`Monitor`, when exposed, runs a command (or WebSocket) whose stdout lines each
become a notification. It has a deadline (default 5 minutes, capped at 30) and
no stdin channel to the watched process; `TaskStop` cancels it early. Emit only
meaningful status changes, including failure signatures.

Do not assume a Bash task handle is a writable PTY. `claude --bg --exec
'COMMAND'` runs a PTY-backed shell job managed by `claude logs`, `attach`, and
`stop`; `attach` itself needs a terminal. For a stdin protocol, start the child
as a background task reading a FIFO held open (recipe in the callee reference)
and write lines to the FIFO from later `Bash` calls; verified with Claude Code
as the child for permission replies, interrupt, and a follow-up. For terminal
interaction, a TUI or a handover to a human, a `tmux` session on a private
socket (`tmux -L NAME`) supplies the PTY: `send-keys -l` writes, `pipe-pane`
logs, `kill-session` ends it; `logs` alone does not provide input.

A native subagent can own a noisy harness investigation and return only the
result. If it owns a long-running command, keep its lifecycle in mind:
foreground-subagent background commands may end with the subagent (untested).
A watcher must remain alive for as long as its observations are needed.

When session/agent messaging tools are exposed, they can forward a watcher's
selected updates. An external CLI does not automatically become a Claude
teammate or acquire `SendMessage`. Terminal/desktop notifications are human
alerts, not a generic injection channel into Claude's context.

Available tools depend on the session's configuration; some (`Monitor`,
`TaskStop`) may need loading through tool search first. Use the actual tool
schemas; CLI terminal shortcuts and agent-facing tools are separate surfaces.

- [Tools: Bash, Monitor, task control and messaging](https://code.claude.com/docs/en/tools-reference)
- [CLI background commands](https://code.claude.com/docs/en/cli-reference)
- [Subagent lifecycle](https://code.claude.com/docs/en/sub-agents)
- [Interactive controls](https://code.claude.com/docs/en/interactive-mode)
