# Call from OpenCode

The built-in `shell` tool runs an external harness directly. A foreground call
returns captured output after completion or timeout. The default timeout is two
minutes; set `timeout` in milliseconds (`0` disables it) and `workdir` instead
of `cd`. Large output is cut to a bounded tail, with the complete output kept in
a managed file whose path is returned. A streaming CLI does not give the model
live updates while the foreground call is still running.

`background: true` returns immediately with a shell ID and an output file path,
has no timeout by default, and OpenCode notifies the session when the command
finishes. Do not poll for completion; read a bounded slice of that output file
in a later call if progress matters before the end. The tool has no documented
stdin channel to a running command, so the handle is for observation and
lifetime, not for typing into a TUI.

For a shell `&` process, retain the PID or process-group ID yourself and use
later `shell` calls to read new output or send a signal. A temporary pipe-owning
helper or an available `tmux` can supply an input channel. For structured
interaction, the callee's own server/session API is usually simpler than
terminal control: start it once, then make bounded requests from `shell`.
OpenCode's PTY API serves its own clients and is not a model-facing tool.

The native `subagent` tool starts a child session with a configured subagent
and returns a `sessionID`; pass it back to continue that child. Foreground calls
wait for the result. `background: true` returns immediately and the parent is
notified when the child finishes, which is a workable channel for a watcher that
reports selected events. A child session is not a shell process handle, and
continuing it does not inject stdin into an external agent. Nesting depth
defaults to one.

TUI notification sounds and plugin events do not create a portable
child-to-parent messaging channel. For targeted updates, use a background
subagent, or a small status file read between calls.

- [V2 tools: shell and subagent](https://dev.opencode.ai/v2/docs/tools/)
- [Shell tool source](https://github.com/anomalyco/opencode/blob/dev/packages/core/src/tool/plugin/shell.ts)
- [Subagent tool source](https://github.com/anomalyco/opencode/blob/dev/packages/core/src/tool/plugin/subagent.ts)
- [V2 agents](https://dev.opencode.ai/v2/docs/agents/)
- [V2 commands](https://dev.opencode.ai/v2/docs/cli/commands/)
