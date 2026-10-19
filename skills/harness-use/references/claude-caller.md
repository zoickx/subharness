# Call from Claude Code

Use `Bash` for a short external CLI command. For longer jobs,
`run_in_background: true` yields a task handle and output file. Use `TaskOutput`
when exposed, or read a bounded slice of that file. `TaskStop` and `/tasks`
manage Claude-owned jobs. A foreground timeout may background a command rather
than end it; retain the returned handle.

`Monitor`, when exposed, can run a filtered tail or poller and deliver updates.
It has a deadline and no documented stdin channel to the watched process.
Emit only meaningful status changes to keep those notifications cheap.

Do not assume a Bash task handle is a writable PTY. The CLI also documents
`claude --bg --exec 'COMMAND'` for a PTY-backed shell job, with `claude logs`,
`attach`, and `stop` for managed background sessions. For bidirectional machine
protocols, an ordinary process with pipes or a small temporary bridge is often
simpler. For terminal interaction, a caller-controlled PTY or an available
`tmux` session supplies an input path; `logs` alone does not.

A native subagent can own a noisy harness investigation and return only the
result. If it owns a long-running command, keep its lifecycle in mind:
foreground-subagent background commands may end with the subagent. A watcher
must remain alive for as long as its observations are needed.

When session/agent messaging tools are exposed, they can forward a watcher's
selected updates. An external CLI does not automatically become a Claude
teammate or acquire `SendMessage`. Terminal/desktop notifications are human
alerts, not a generic injection channel into Claude's context.

Available tools depend on the session's configuration. Use the actual tool
schemas; CLI terminal shortcuts and agent-facing tools are separate surfaces.

- [Tools: Bash, Monitor, task control and messaging](https://code.claude.com/docs/en/tools-reference)
- [CLI background commands](https://code.claude.com/docs/en/cli-reference)
- [Subagent lifecycle](https://code.claude.com/docs/en/sub-agents)
- [Interactive controls](https://code.claude.com/docs/en/interactive-mode)
