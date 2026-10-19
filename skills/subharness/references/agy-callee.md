# Call Antigravity CLI (`agy`)

This is Google's Antigravity CLI, not the IDE launcher or Gemini CLI. Run it in
the desired cwd. `agy models` and `agy agents` list available choices without
starting an agent turn.

## Launch and options

```sh
agy -p 'TASK' --output-format stream-json --model SLUG --print-timeout 10m < /dev/null
```

| Need | Options |
| --- | --- |
| Model / agent | `--model SLUG`, `--agent NAME`; omit for configured defaults |
| Reasoning | `--effort low\|medium\|high\|xhigh\|max` (model-dependent) |
| Output | `--output-format text\|json\|stream-json`, `--json-schema JSON_OR_PATH` |
| Time limit | `--print-timeout DURATION`; `0` (help default) waits for completion |
| Execution mode | `--mode accept-edits\|auto\|plan` |
| Scope | `--add-dir DIR` (repeatable), `--project ID_OR_NAME`, `--new-project` |
| Permissions | `--sandbox` enables terminal restrictions; `--dangerously-skip-permissions` auto-approves tool requests |
| Conversation | `--conversation ID`, `--continue` / `-c` |
| Interactive launch | `--prompt-interactive 'TASK'` / `-i 'TASK'`, `--remote-control` |
| Misc | `--log-file PATH` (default under `~/.gemini/antigravity-cli/log/`), `--disable-slash-commands` |

Use a model slug returned by `agy models`; model, effort, and mode choices vary
by account. An unavailable `--mode` (seen with `auto`) prints a stderr warning and
continues in the default mode. The cached CLI login is reused. An unauthenticated
headless run fails instead of completing interactive sign-in.

## Watch progress

Stdout is NDJSON; stderr contains diagnostics and permission notices:

| Event | Useful fields |
| --- | --- |
| `init` | Top-level `conversation_id`; nested `init`: `cwd`, `model`, `tools`, `permission_mode` |
| `step_update` | Nested `step_update`: `step_index`, `state` (`ACTIVE`/`DONE`), `step_type` (`user_input`, `agent_response`, `tool`, `system_message`), `text_delta`, `tool_name`, `tool_info`, `duration_seconds` |
| `result` | Nested `result`: `status`, `response`, `error`, `conversation_id`, `num_turns`, usage, duration |

`permission_mode` is `request-review` by default and `always-proceed` with
`--dangerously-skip-permissions`. `tool_info.parameters` is a partial summary
(for example, it omitted the input text of a stdin send). For a small text view:

```sh
jq --unbuffered -rj 'select(.event == "step_update" and .step_update.step_type == "agent_response") | .step_update.text_delta // empty'
```

Separately retain tool names/states, stderr, and final status; avoid importing
tool payloads and reasoning. `--output-format json` waits for completion.

## Multiple turns in one process

Advanced path. It relies on protocol details observed on one release and
can break with an update; prefer launch flags and resume when they suffice.

```sh
agy --input-format stream-json --output-format stream-json --model SLUG
```

Write and flush one line per prompt; `-p` text is ignored in this mode:

```jsonl
{"event":"user","message":{"content":"TASK"}}
```

Keep stdin open for further turns. There is one `init` per process and one
`result` per turn. Wait for the current result when the next prompt depends on
it; lines supplied in advance queue sequential turns. EOF exits 0 after the
submitted turns. `num_turns` and usage are cumulative for the conversation.

This input is a turn queue, not an in-flight steering protocol.
Per docs, `control_request`/`control_response` lines end the session with exit 2
and invalid JSON lines exit 1. CLI slash commands such as `/model` cannot be sent.

## Interrupt, steer, and resume

For active terminal intervention, launch a TUI with `agy` or `agy -i 'TASK'`
through a PTY. Docs bind `Ctrl+C`/`Esc` to stopping the stream and `Ctrl+D` to
exit; these are keystrokes, not JSON stdin messages (untested). In an untrusted
cwd the TUI first shows a workspace-trust menu, even with
`--dangerously-skip-permissions`; trusted paths are kept in `trustedWorkspaces`
in `~/.gemini/antigravity-cli/settings.json`. Headless `-p` skips that menu.

```sh
agy -p 'Follow-up' --conversation CONVERSATION_ID --output-format stream-json < /dev/null
```

An unknown `--conversation` ID only warns on stderr, then starts a new
conversation and exits 0. Compare the `init` `conversation_id` with the requested
one. `--continue` picks the latest conversation, which can be ambiguous with
concurrent work. Retain the last known ID and inspect the resumed state.

For a human control surface, `agy --remote-control` or `/remote-control` in the
TUI supplies a browser link with live prompts, progress, and approvals. The
tunnel follows that TUI's lifetime. `agy remote-control start/status/stop`
manages a separate machine daemon. Neither is documented as attaching an input
channel to an arbitrary already-running headless child. Untested.

## Pitfalls and deeper reference

- Headless tools needing approval are soft-denied. The tool step still goes
  `ACTIVE` then `DONE` with no denial field; the result is `SUCCESS`, exit 0,
  often with an empty response, and the explanation is on stderr. Inspect all
  three. `permissions.allow` rules in settings or a terminal approval path can
  support the intended action.
- `--mode plan` headless tried `write_to_file` for its plan, was denied, and
  returned an empty `SUCCESS`.
- `--print-timeout` expiry also returns `SUCCESS`, exit 0, and a partial
  response. Only stderr says `print timeout after ...; returning partial output`.
  Background commands started by the child are terminated on exit.
- Help says the timeout default is `0` (no limit); the headless page still says
  five minutes. Set it explicitly when a ceiling matters.
- Leaving warm-session stdin open intentionally keeps the process alive after
  a result. Closing it is a lifecycle action, not a progress poll.

Discovery: `agy --help`, `agy models`, `agy agents`, `agy help remote-control`.

- [Headless protocol and examples](https://antigravity.google/docs/cli/headless/)
- [CLI reference](https://antigravity.google/docs/cli/reference)
- [Interactive controls](https://antigravity.google/docs/cli/using)
- [Remote Control](https://antigravity.google/docs/remote-control/)
- [CLI changelog](https://antigravity.google/docs/changelog?tab=cli)
- [Official CLI identity/download](https://antigravity.google/download#antigravity-cli)
