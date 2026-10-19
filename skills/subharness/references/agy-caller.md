# Call from Antigravity CLI

The headless `init` catalog lists `run_command`, `command_status`, and
`send_command_input`, but that catalog is broader than the model's callable set.
In a live run the agent could not call `command_status`; process follow-up went
through `manage_task`. Trust the tool schema the agent actually has. Do not copy
tool arguments from Antigravity IDE examples without checking them.

Observed shape (parameter names as reported by the agent; `step_update`
`tool_info.parameters` shows only a subset):

- `run_command`: `CommandLine`, `Cwd`, `WaitMsBeforeAsync`, optional `IsDaemon`,
  `RunPersistent`, `RequestedTerminalID`. A command still running after the
  wait is moved to the background and gets a task ID.
- `manage_task`: `Action` (`list`, `status`, `send_input`, `kill`), `TaskId`,
  `Input` for `send_input`. `status` returns progress/output and completion;
  `send_input` delivered a line to a waiting `read`. `kill` is untested.

For an external harness:

- Start it with `run_command`, and retain its task ID.
- Use `manage_task` `status` for a small progress update and completion state.
- Use `send_input` for line input to the child's stdin; feeding a stream-json
  turn this way is untested. A terminal Ctrl-C and a protocol interrupt are
  different operations; sending control characters is untested.
- Keep the task ID distinct from the external harness's conversation ID. The
  former addresses a process; the latter resumes AI context.

Tool availability does not grant permission to execute commands. Headless runs
soft-deny `run_command` under the default `request-review` mode; the step looks
completed and the denial is only on the child's stderr. `--mode auto` was not
available on the tested account and fell back to the same denial.
`--dangerously-skip-permissions` permits it; stderr suggests a scoped
`permissions.allow` rule instead (untested).
When a headless `agy` exits, including on `--print-timeout`, it terminates its
background tasks, so a long-lived child needs a session that stays open.

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
