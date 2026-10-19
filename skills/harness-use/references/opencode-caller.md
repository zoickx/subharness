# Call from OpenCode

The built-in `shell` tool runs an external harness directly. A foreground call
returns captured output after completion or timeout. The default timeout is two
minutes; set `timeout` in milliseconds (`0` disables it) and `workdir` instead
of `cd`. Large output is returned as a truncated preview, with the complete
output kept in a managed file whose path is returned. A streaming CLI does not
give the model live updates while the foreground call is still running.

`background: true` returns at once with `Command moved to the background (shell
ID: sh_...)` and `Output is streaming to: PATH`, plus an instruction not to poll.
It has no timeout by default. When the command ends, OpenCode posts a synthetic
message `<shell id="sh_..." state="completed" command="...">OUTPUT</shell>`,
which starts a new turn. Read a bounded slice of the output file in a later call
if progress matters before the end. The tool has no stdin channel to a running
command, so the handle is for observation and lifetime, not for typing into a TUI.

That notification needs a live server. Under `opencode run`, the client exits
when the first turn ends: on a shared server the notified turn still runs but is
not printed, and with `--standalone` the background command is killed at exit.
In a headless run, use a foreground call or keep the server and watch its
events. A model may also claim a notification before one arrives; only the
later synthetic turn carries the result.

For a shell `&` process, retain the PID or process-group ID yourself and use
later `shell` calls to read new output or send a signal. A FIFO held open by
the background command supplies an input channel (recipe in the Claude Code
and Codex callee references; untested from `shell`), and `tmux` supplies a PTY
when a terminal is needed. For structured interaction, the callee's own
server/session API is usually simpler than terminal control: start it once,
then make bounded requests from `shell`. OpenCode's PTY API serves its own
clients and is not a model-facing tool.

The native `subagent` tool starts a child session with a configured subagent
and returns a `sessionID`; pass it back to continue that child. Foreground calls
wait for the result. `background: true` returns immediately and the parent is
notified when the child finishes (from docs and source; not exercised live).
A child session is not a shell process handle, and continuing it does not
inject stdin into an external agent. Nesting depth defaults to one.

TUI notification sounds and plugin events do not create a portable
child-to-parent messaging channel. For targeted updates, use a background
subagent, or a small status file read between calls.

- [V2 tools: shell and subagent](https://dev.opencode.ai/v2/docs/tools/)
- [Shell tool source](https://github.com/anomalyco/opencode/blob/dev/packages/core/src/tool/plugin/shell.ts)
- [Subagent tool source](https://github.com/anomalyco/opencode/blob/dev/packages/core/src/tool/plugin/subagent.ts)
- [V2 agents](https://dev.opencode.ai/v2/docs/agents/)
- [V2 commands](https://dev.opencode.ai/v2/docs/cli/commands/)
