# Call Claude Code

## Launch and choose options

Run in the desired working directory; Claude inherits cwd.

```sh
claude -p --output-format stream-json --verbose --include-partial-messages 'TASK'
```

This emits JSONL on stdout, with diagnostics on stderr. Plain `-p` returns text;
`--output-format json` returns a completion envelope. A pipe can supply a prompt:
`claude -p < prompt.txt`.

| Need | Options |
| --- | --- |
| Model / reasoning | `--model ALIAS_OR_ID`, `--effort LEVEL`; `haiku` is the small-model alias |
| Agent / instructions | `--agent NAME`, `--agents JSON_OR_FILE`, `--append-system-prompt TEXT`, `--system-prompt TEXT` (replaces default) |
| Tool access | `--tools LIST` selects tools; `--allowedTools LIST` grants permission; `--disallowedTools LIST` denies |
| Permissions | `--permission-mode MODE`; `--permission-prompts none` denies requests that would otherwise prompt in print mode |
| Broad permissions | `--dangerously-skip-permissions` bypasses permission checks |
| Scope / config | `--add-dir DIR`, `--settings FILE_OR_JSON`, `--setting-sources user,project,local`, `--mcp-config FILE`, `--strict-mcp-config` |
| Isolated checkout | `--worktree NAME` |
| Final output / budget | `--json-schema JSON`, `--max-budget-usd AMOUNT` |
| Persistence | `--session-id UUID`, `--resume ID`, `--continue`, `--fork-session`; `--no-session-persistence` prevents later resume |

`dontAsk` denies unapproved tools; `acceptEdits` accepts edits; `plan` restricts
execution. Pick permissions for the intended task. `--tools` availability and
tool approval are separate controls.

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
- `result` ends a turn. Inspect `subtype`, `is_error`, and `result`; save
  `session_id`. A turn ending need not mean background work has exited.

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

`session_id: "default"` is the SDK's input label; save the real emitted session
ID for later CLI resume. Subsequent user lines submit further input. Do not
assume they cancel an active tool/model call. For an immediate change of course,
interrupt the active turn, then send the correction in the same process:

```jsonl
{"type":"control_request","request_id":"stop-1","request":{"subtype":"interrupt"}}
```

Match the response by `response.request_id`, and observe the interrupted turn's
`result` before sending the next turn. Responses and events can interleave.
With `--permission-prompts host`, the host must also handle permission control
requests; ignoring them can stall work. `--permission-prompts none` provides a
noninteractive denial path. Close stdin when finished and collect the exit code.

These wire examples come from Anthropic's SDK source and were exercised locally.
For advanced control or permission replies, consult that source rather than
guessing envelopes.

## Existing sessions and terminal control

```sh
claude -p --resume SESSION_ID 'Follow-up'
claude --bg 'TASK'
claude logs BACKGROUND_ID
claude attach BACKGROUND_ID
claude stop BACKGROUND_ID
```

`--bg` returns a managed session ID; `claude agents --json` lists them. It cannot
be combined with `-p`. `logs` reads recent terminal output; `attach` needs a
terminal. `stop` keeps conversation history. Use the background ID returned by
that interface, rather than assuming every identifier has the same meaning.

In the TUI, messages can be queued while Claude works; `Ctrl+Enter` sends queued
input immediately. `Esc`/`Ctrl+C` interrupt active work. These are terminal
gestures, not bytes to send to a JSON pipe. Prefer explicit session IDs over
`--continue` when several sessions share a directory.

## Pitfalls and deeper reference

- Startup hooks/MCP servers and background tasks can delay output or exit.
  `--include-hook-events` helps identify hook activity. A print-mode process may
  remain alive after a result while background work continues.
- Headless permission denial may produce an answer that explains inability to
  act. Inspect the result rather than assuming exit 0 means the requested action
  happened.
- A nested Claude launch may encounter the `CLAUDECODE` nesting guard. Prefer
  native Claude subagents when that fits; for an intentional independent CLI
  session, unset that marker only in the child's environment, retaining actual
  sandbox and permission settings.

Discovery: `claude --help`, `claude agents --help`, `claude auth status --text`.

- [CLI reference](https://code.claude.com/docs/en/cli-reference)
- [Headless execution](https://code.claude.com/docs/en/headless)
- [Terminal controls](https://code.claude.com/docs/en/interactive-mode)
- [Models](https://code.claude.com/docs/en/model-config)
- [SDK client: user messages](https://github.com/anthropics/claude-agent-sdk-python/blob/main/src/claude_agent_sdk/client.py)
- [SDK control protocol](https://github.com/anthropics/claude-agent-sdk-python/blob/main/src/claude_agent_sdk/_internal/query.py)
- [Agent-readable documentation index](https://code.claude.com/docs/llms.txt)
