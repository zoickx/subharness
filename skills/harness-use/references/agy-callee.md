# Call Antigravity CLI (`agy`)

This is Google's Antigravity CLI, not the IDE launcher or Gemini CLI. Run it in
the desired cwd. `agy models` and `agy agents` list available choices without
starting an agent turn.

## Launch and options

```sh
agy -p 'TASK' --output-format stream-json
```

| Need | Options |
| --- | --- |
| Model / agent | `--model SLUG`, `--agent NAME`; omit for configured defaults |
| Reasoning | `--effort low\|medium\|high\|xhigh\|max` (model-dependent) |
| Output | `--output-format text\|json\|stream-json`, `--json-schema JSON_OR_PATH` |
| Time limit | `--print-timeout DURATION`; `0` waits for completion |
| Execution mode | `--mode accept-edits\|auto\|plan` |
| Scope | `--add-dir DIR` (repeatable), `--project ID_OR_NAME`, `--new-project` |
| Permissions | `--sandbox` enables terminal restrictions; `--dangerously-skip-permissions` auto-approves tool requests |
| Conversation | `--conversation ID`, `--continue` / `-c` |
| Interactive launch | `--prompt-interactive 'TASK'` / `-i 'TASK'`, `--remote-control` |

Use a model slug returned by `agy models`; model and effort choices vary by
account. The cached CLI login is reused. An unauthenticated headless run fails
instead of completing interactive sign-in.

## Watch progress

Stdout is NDJSON; stderr contains diagnostics and permission notices:

| Event | Useful fields |
| --- | --- |
| `init` | `conversation_id`, `cwd`, `model`, `tools`, `permission_mode` |
| `step_update` | Nested `step_update`: `step_index`, `state`, `step_type`, `text_delta`, tool details |
| `result` | Nested `result`: `status`, `response`, `conversation_id`, usage, duration |

For a small text view (with `jq` available):

```sh
jq --unbuffered -rj 'select(.event == "step_update" and .step_update.step_type == "agent_response") | .step_update.text_delta // empty'
```

Separately retain tool activity, stderr, and final status. Tool updates can be
summarized by name and state; avoid importing tool payloads and reasoning.
`--output-format json` waits for completion instead of exposing live events.

## Multiple turns in one process

```sh
agy --input-format stream-json --output-format stream-json
```

Write and flush one line per prompt:

```jsonl
{"event":"user","message":{"content":"TASK"}}
```

Keep stdin open for further turns. There is one `init` per process and one
`result` per turn. Wait for the current result when the next prompt depends on
it; several lines supplied in advance queue sequential turns. EOF exits after
processing the submitted turns. Conversation counters are cumulative.

This input is a turn queue, not an in-flight steering protocol.
`control_request`/`control_response` messages are explicitly unsupported and
terminate the session with an error. CLI slash commands such as `/model` also
cannot be sent through this stream.

## Interrupt, steer, and resume

For active terminal intervention, launch a TUI with `agy` or `agy -i 'TASK'`
through a PTY. `Ctrl+C`/`Esc` stop active generation so a correction can be
submitted. `Ctrl+D` or `/exit` exits. These controls are not JSON stdin messages.

```sh
agy -p 'Follow-up' --conversation CONVERSATION_ID --output-format stream-json
```

The emitted conversation ID identifies saved history. `--continue` picks the
latest conversation, which can be ambiguous with concurrent work. Do not assume
terminating an OS process guarantees its interrupted work was saved; retain the
last known conversation ID and inspect the resumed state.

For a human control surface, `agy --remote-control` or `/remote-control` in the
TUI supplies a browser link with live prompts, progress, and approvals. The
tunnel follows that TUI's lifetime. `agy remote-control start/status/stop`
manages a separate machine daemon. Neither is documented as attaching an input
channel to an arbitrary already-running headless child.

## Pitfalls and deeper reference

- Headless tools needing approval are denied rather than interactively approved.
  A live test returned `SUCCESS` and exit 0 after denying a command, with an empty
  response and the explanation on stderr. Inspect all three; an outer success
  does not prove that a tool ran. Scoped existing permission rules or a terminal
  approval path can support the intended action.
- Some headless documentation still says the timeout defaults to five minutes;
  current help and the changelog say unlimited. Set `--print-timeout` if a ceiling
  matters, rather than inferring a hang from that old default.
- Leaving warm-session stdin open intentionally keeps the process alive after
  a result. Closing it is a lifecycle action, not a progress poll.

Discovery: `agy --help`, `agy models`, `agy agents`, `agy help remote-control`.

- [Headless protocol and examples](https://antigravity.google/docs/cli/headless/)
- [CLI reference](https://antigravity.google/docs/cli/reference)
- [Interactive controls](https://antigravity.google/docs/cli/using)
- [Remote Control](https://antigravity.google/docs/remote-control/)
- [CLI changelog](https://antigravity.google/docs/changelog?tab=cli)
- [Official CLI identity/download](https://antigravity.google/download#antigravity-cli)
