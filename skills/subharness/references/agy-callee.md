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

A headless run denies every tool that needs approval, shell commands and
file writes included, and still ends `SUCCESS` with the denial only on stderr
and in `result.denied_actions`; pass `--dangerously-skip-permissions` for a
task that writes (details under Pitfalls).

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

For active terminal intervention, run the TUI (`agy` or `agy -i 'TASK'`) in
a PTY such as a `tmux` pane. Keys are keystrokes, not JSON stdin messages. In
an untrusted cwd it first shows a workspace-trust menu, even with
`--dangerously-skip-permissions`; trusted paths are kept in `trustedWorkspaces`
in `~/.gemini/antigravity-cli/settings.json`. Headless `-p` skips that menu.

Advanced path. Observed through `tmux send-keys` on one release:

- The `>` input line appears in about 5 s. A first-start notice overlay ends
  in `esc to dismiss`; `Escape` dismisses it. The footer starts with
  `? for shortcuts` when idle and `esc to cancel` during a turn.
- Submit with `send-keys -l -- 'TEXT'`, then `Enter` as a separate key.
- `Escape` or `C-c` during a turn stopped the stream within a second and
  printed `Interrupted`. Partial output stays; the next prompt worked.
- Docs say `C-c`/`Esc` also clear the prompt; not observed. At an idle
  prompt, even with a draft, `C-c` shows `press ctrl+c again to exit` and a
  second `C-c` exits. `C-u` clears a draft. `Up` on an empty prompt recalls
  the previous input.
- `Enter` during a turn queues the message (`alt+m to send immediately`); it
  runs as the next turn. `M-m` injects a queued message at the next step
  boundary: after a tool step it redirected the turn; during a single text
  stream it waited for the stream to end.
- A long shell command can move to a background task (footer `1 task(s)`).
  The turn then ends, queued input runs, and task completion starts another
  turn.

Shell commands in the default mode show `Run this command?` with options
`1. Yes, run command`, `2.` allow in this conversation, `3.` allow and
persist to `settings.json`, `4. No, cancel`. A digit selects at once;
`Up`/`Down` then `Enter` also work; `Enter` alone takes option 1. Denial
(`4` or `Escape`) ends the turn as `Interrupted`. After `Escape` the tool line
reads `Ran (...)` without `failed`. File-viewing tools did not prompt.

The TUI does not use the alternate screen. `capture-pane -p -S -N` returns a
clean transcript: each line once, no spinners, within tmux `history-limit`.
Tool output is collapsed. The visible screen adds a spinner line, a `Tip:`
line, rules around the input, and the footer. The `Interrupted` note is
dropped after the next turn. `pipe-pane` output is a stream of redraw frames
that repeat content, not a readable log.

Quit with `/quit` (completes to `/exit`) and `Enter`, or `C-d` twice on an
empty prompt; both exit 0. On exit the TUI prints `agy --conversation=UUID`;
it showed the ID nowhere else, so keep the pane (`remain-on-exit on`) to read
it. `agy --conversation=UUID` reopened the TUI with the transcript and the
prior context. Headless follow-up:

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
  `ACTIVE` then `DONE`; the result is `SUCCESS`, exit 0, often with an empty
  response, and lists the denials in `result.denied_actions`; the explanation
  is on stderr. Inspect all three. `permissions.allow` rules in settings or a terminal approval path can
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
