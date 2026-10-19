# Call from OpenCode

The built-in `bash` tool can run an external harness directly. Its current
implementation is a bounded command with captured stdout/stderr and ignored
stdin, not a persistent interactive process handle. Its default timeout is two
minutes, with a ten-minute maximum. It returns output after completion/timeout;
an external CLI streaming to stdout does not itself give the model live updates.

For long runs, ordinary process control remains available: launch a process with
output redirected to a file, retain its PID or process-group ID, then use later
`bash` calls to read new output or send a signal. Manage the lifetime explicitly;
a shell `&` is not an OpenCode-managed job with a completion notification. A
temporary pipe-owning helper or available `tmux` can supply an input channel
when needed. No maintained helper or plugin is required by this skill.

For structured interaction, the callee's own server/session API can be simpler
than terminal control: start it once, then make bounded requests with `bash`.
OpenCode's integrated terminal and server PTY API are separate features; do not
assume either is exposed as a native agent tool.

The native `task` tool launches OpenCode subagents. It can isolate harness
research or debugging when available, but a task ID is not a child shell PID.
Do not assume that a task continuation injects stdin into an active external
agent. Experimental background-subagent features are unnecessary for the basic
shell path; use only capabilities already exposed in the current session.

TUI notification sounds and plugin events do not create a portable child-to-parent
messaging channel. For selected updates, use a watcher with native messaging if
available, or a small status file read between calls.

- [V2 tools](https://dev.opencode.ai/v2/docs/tools/)
- [Current bash implementation](https://github.com/anomalyco/opencode/blob/dev/packages/core/src/tool/bash.ts)
- [V2 agents](https://dev.opencode.ai/v2/docs/agents/)
- [V2 commands](https://dev.opencode.ai/v2/docs/cli/commands/)
