# Call Claude Code

## Launch and choose options

Run in the desired working directory; Claude inherits cwd.

```sh
claude -p --output-format stream-json --verbose --include-partial-messages 'TASK' < /dev/null
```

This emits JSONL on stdout, with diagnostics on stderr. Plain `-p` returns text;
`--output-format json` returns a completion envelope. A pipe can supply a prompt:
`claude -p < prompt.txt`. `-p` skips the workspace trust dialog; interactive and
`--bg` sessions require the directory to be trusted already.

| Need | Options |
| --- | --- |
| Model / reasoning | `--model ALIAS_OR_ID`, `--effort LEVEL`; `haiku` is the small-model alias |
| Agent / instructions | `--agent NAME`, `--agents JSON_OR_FILE`, `--append-system-prompt TEXT`, `--system-prompt TEXT` (replaces default) |
| Tool access | `--tools LIST` selects tools; `--allowedTools LIST` grants permission; `--disallowedTools LIST` denies |
| Permissions | `--permission-mode MODE`; `--permission-prompts host\|none` (see below) |
| Broad permissions | `--dangerously-skip-permissions` bypasses permission checks |
| Scope / config | `--add-dir DIR`, `--settings FILE_OR_JSON`, `--setting-sources user,project,local`, `--mcp-config FILE`, `--strict-mcp-config` |
| Isolated checkout | `--worktree NAME` |
| Final output / budget | `--json-schema JSON`, `--max-budget-usd AMOUNT` |
| Persistence | `--session-id UUID`, `--resume ID`, `--continue`, `--fork-session`; `--no-session-persistence` prevents later resume |

`dontAsk` denies unapproved tools; `acceptEdits` accepts edits; `plan` restricts
execution. Pick permissions for the intended task. `--tools` availability and
tool approval are separate controls.

List options (`--tools`, `--allowedTools`, `--disallowedTools`, `--add-dir`,
`--mcp-config`) are variadic and swallow a following prompt (`-p` errors, `--bg`
starts idle). Put the prompt before them.

`--bare` changes context AND authentication: local help says it skips normal
customizations and OAuth/keychain reads. It is not a neutral speed flag.
`--safe-mode` disables customizations while retaining normal authentication;
useful when isolating a configuration failure.

## Watch while it runs

- `system` with `subtype: init` contains `session_id` and tool/model metadata.
- `stream_event` wraps partial model events. Display only
  `event.delta.type == "text_delta"`, using `event.delta.text`, for streamed text.
- Assistant `tool_use` blocks identify activity. Summarize names rather than
  dumping arguments/results. Do not forward thinking blocks.
- `result` ends a turn. Inspect `subtype`, `is_error`, `terminal_reason`,
  `permission_denials`, and `result`; save `session_id`. A turn ending need not
  mean background work has exited.

For text alone, filter the stream with this expression (if `jq` is available):

```sh
jq --unbuffered -rj 'select(.type == "stream_event" and .event.delta.type? == "text_delta") | .event.delta.text'
```

Keep lifecycle/errors separately if using this text-only view. Forwarding the
entire stream, or enabling `--forward-subagent-text`, can import reasoning and
nested transcripts into the parent context.

## Keep a process open, interrupt, and follow up

The CLI speaks the Agent SDK's JSONL protocol without requiring an SDK install:

```sh
claude -p --input-format stream-json --output-format stream-json --verbose --include-partial-messages
```

Keep stdin open and flush each line. Initialize, wait for the matching
`control_response`, then send a user message:

```jsonl
{"type":"control_request","request_id":"init-1","request":{"subtype":"initialize","hooks":null}}
{"type":"user","message":{"role":"user","content":"TASK"},"parent_tool_use_id":null,"session_id":"default"}
```

The initialize response is large; read only needed fields. `system`/`init`
arrives after each user message, not after initialize. `session_id: "default"`
is the SDK's input label; save the real emitted session ID for later CLI
resume. Subsequent user lines submit further turns. Do not assume they cancel
an active tool/model call. For an immediate change of course, interrupt the
active turn, then send the correction in the same process:

```jsonl
{"type":"control_request","request_id":"stop-1","request":{"subtype":"interrupt"}}
```

Match the response by `response.request_id` (payload `{"still_queued":[]}`).
The interrupted turn ends with `result` `subtype: error_during_execution`,
`is_error: true`, `terminal_reason: aborted_streaming`; wait for it before the
next turn. The process stays usable. Close stdin to end it (exit 0).

## Permission prompts

The default `--permission-prompts host` sends prompts to the host only when
`--permission-prompt-tool stdio` is also passed (the SDK does this). Without
it, a prompt-requiring call is denied with a `system` `permission_denied`
event. `--permission-prompts none` denies the same way even with `stdio`.
With `stdio`, the CLI emits and waits for a reply:

```jsonl
{"type":"control_request","request_id":"REQ","request":{"subtype":"can_use_tool","tool_name":"Bash","input":{...},"tool_use_id":"...","permission_suggestions":[...]}}
{"type":"control_response","response":{"subtype":"success","request_id":"REQ","response":{"behavior":"allow","updatedInput":{...}}}}
{"type":"control_response","response":{"subtype":"success","request_id":"REQ","response":{"behavior":"deny","message":"Reason"}}}
```

For allow, echo `input` as `updatedInput` to run it unchanged. A deny
`message` becomes the model's tool error; the turn still ends `success`.

## Existing sessions and terminal control

```sh
claude -p --resume SESSION_ID 'Follow-up'
claude --bg 'TASK' --model haiku
claude agents --json
claude logs|attach|stop|rm BACKGROUND_ID
```

`--bg` prints a short ID and returns; it cannot be combined with `-p` and
fails in an untrusted directory. `agents --json` (`--all` adds exited) lists
`id`, `sessionId`, `kind`, `state` (`working`, `blocked`, `done`, `stopped`).
`logs` prints raw terminal output with ANSI escapes. `attach` needs a PTY and
accepts typed prompts. `stop` keeps the conversation; `-p --resume` takes the
`sessionId`, not the short ID. `rm` deletes. `--bg --exec 'CMD'` runs a
PTY-backed shell job under the same commands.

In the TUI, messages can be queued while Claude works; `Ctrl+Enter` sends queued
input immediately. `Esc`/`Ctrl+C` interrupt active work. These are terminal
gestures, not bytes to send to a JSON pipe. Prefer explicit session IDs over
`--continue` when several sessions share a directory.

## Pitfalls and deeper reference

- Startup hooks/MCP servers and background tasks can delay output or exit.
  `SessionStart` hook events appear in stream-json regardless;
  `--include-hook-events` adds the rest (for example `Stop`).
- Any permission denial yields a `success` result and exit 0 that explains the
  inability to act. Check `result.permission_denials`.
- Launching `claude` from inside Claude Code with `CLAUDECODE` set worked for
  both `-p` and the TUI. If a nesting guard appears, unset that marker only in
  the child (`env -u CLAUDECODE claude -p ...`), retaining actual sandbox and
  permission settings.

Discovery: `claude --help`, `claude agents --help`, `claude auth status --text`.

- [CLI reference](https://code.claude.com/docs/en/cli-reference)
- [Headless execution](https://code.claude.com/docs/en/headless)
- [Terminal controls](https://code.claude.com/docs/en/interactive-mode)
- [Models](https://code.claude.com/docs/en/model-config)
- [SDK client: user messages](https://github.com/anthropics/claude-agent-sdk-python/blob/main/src/claude_agent_sdk/client.py)
- [SDK control protocol](https://github.com/anthropics/claude-agent-sdk-python/blob/main/src/claude_agent_sdk/_internal/query.py)
- [Agent-readable documentation index](https://code.claude.com/docs/llms.txt)
