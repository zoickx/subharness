# Call from Codex

Use the shell/process tool exposed in your current Codex session. Tool names
and persistence differ across CLI and hosted surfaces; the loaded schema is the
contract.

In `codex exec` and IDE sessions with code mode, the top-level tool is `exec`:
it runs a JavaScript cell that calls nested tools such as `tools.exec_command`
and `tools.write_stdin`; self-reports often name only the nested tools. A
cell that outlives its yield returns `Script running with cell ID N`; poll it
with the top-level `wait` tool (`cell_id`, `yield_time_ms`, `max_tokens`).
Short cells that yield a process `session_id` avoid this.

Where `exec_command` and `write_stdin` are available, directly or inside a cell:

- `exec_command` takes `cmd`, plus optional `workdir`, `yield_time_ms`, and
  `max_output_tokens`. A short `yield_time_ms` returns a `session_id` while the
  process continues. Yielding is not an execution timeout. The `session_id`
  stays valid in later cells.
- Poll that same ID with `write_stdin` and empty `chars`, using a bounded
  `max_output_tokens`. An empty poll waited about 5 s even with a 1000 ms
  yield. Send text with `chars` only when the tool supports writable stdin for
  that session. The caller's `--json` stream shows the whole process as one
  `command_execution` item, not each poll.
- `tty: true` requests terminal behavior for a TUI. Some hosts require it to keep
  stdin writable. PTY echo and control sequences can contaminate a JSON stream;
  use a pipe-owning temporary process when clean bidirectional JSON is needed.
- A Ctrl-C byte has terminal semantics only with an appropriate PTY. In a plain
  pipe it is just input. Prefer the child's documented interrupt protocol, or a
  signal to the specific process you launched. Killing only a shell wrapper can
  leave its children running; signal the process group.

Under `-s workspace-write` or `read-only`, network is off by default. A child
harness then cannot reach its API: a `claude -p` child retried for about two
minutes and exited 1 with `EAI_AGAIN`. Give such children network access
deliberately or run them outside the sandbox.

If the host exposes only a blocking shell command, output files and separately
addressable processes provide observation between calls. A bare shell `&` does
not establish lifetime, cancellation, or automatic completion notification.

If native subagents are available, a watcher can retain the process handle and
send concise updates. Use a separate subagent for harness debugging that would
distract the parent. Codex `/subagents` and `codex agents` list Codex sessions;
they do not discover arbitrary external CLI processes.

For a client already driving Codex App Server, `command/exec` offers streamed
output and process control under its sandbox. The separate experimental
`process/*` API offers explicit handles and PTYs outside that sandbox. These
are client APIs, not guaranteed model-facing tools, and are unnecessary when
the existing shell tool suffices. Neither implies survival across host restarts.

- [App Server process APIs](https://learn.chatgpt.com/docs/app-server.md)
- [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents.md)
- [CLI command reference](https://learn.chatgpt.com/docs/developer-commands?surface=cli)
- [Agent-readable documentation index](https://learn.chatgpt.com/llms.txt)
