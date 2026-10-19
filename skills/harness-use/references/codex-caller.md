# Call from Codex

Use the shell/process tool exposed in your current Codex session. Tool names
and persistence differ across CLI and hosted surfaces; the loaded schema is the
contract.

Where `exec_command` and `write_stdin` are available:

- Launch with a short `yield_time_ms` to receive a `session_id` while the process
  continues. Yielding is not an execution timeout.
- Poll that same ID with empty `chars`, using a bounded output budget. Send text
  with `chars` only when the tool supports writable stdin for that session.
- `tty: true` requests terminal behavior for a TUI. Some hosts require it to keep
  stdin writable. PTY echo and control sequences can contaminate a JSON stream;
  use a pipe-owning temporary process when clean bidirectional JSON is needed.
- A Ctrl-C byte has terminal semantics only with an appropriate PTY. In a plain
  pipe it is just input. Prefer the child's documented interrupt protocol, or a
  signal to the specific process you launched.

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
