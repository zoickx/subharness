# Call from Antigravity CLI

Use the terminal tools exposed in the CLI session. A live headless `init` catalog
advertised `run_command`, `command_status`, and `send_command_input`. Their names
alone do not establish input fields or PTY behavior; use their actual schemas.
Do not copy tool arguments from Antigravity IDE examples without checking them.

When those tools expose a persistent command handle:

- Start the external harness with `run_command`, retaining its returned handle.
- Use `command_status` for a small progress update and completion state.
- Use `send_command_input` only for the input/termination operations its schema
  supports. A terminal Ctrl-C and a protocol interrupt are different operations.
- Keep the handle distinct from the external harness's conversation ID. The
  former addresses a process; the latter resumes AI context.

Tool availability does not grant permission to execute commands. Headless runs
may deny commands that would need approval. Public CLI docs do not specify the
full persistent-input contract; use the exposed schema. If only a bounded shell
call is available, use the callee's one-shot mode, or an ordinary process/log
arrangement for later observation.

The TUI's `/tasks` panel shows background shell logs. `/agents` shows
Antigravity's own subagents, including their state and tool output; it is not a
registry of all external CLI processes. A native subagent can isolate harness
debugging or summarize watched output if that capability is exposed.

Task-completion desktop/bell notifications alert the operator. They are not
automatically delivered as messages to the parent agent. A watcher needs its own
messaging channel, or the parent can read a small shared status file.

- [CLI reference and task panels](https://antigravity.google/docs/cli/reference)
- [Subagent management](https://antigravity.google/docs/cli/commands/agents)
- [CLI terminal behavior](https://antigravity.google/docs/cli/using)
- [Headless tool inventory and permissions](https://antigravity.google/docs/cli/headless/)
