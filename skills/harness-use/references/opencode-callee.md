# Call OpenCode

## Launch and options

Run in the desired working directory. One-shot use needs no server setup:

```sh
opencode run --standalone --format json 'TASK'
opencode run --server http://127.0.0.1:4096 --format json 'TASK'
```

`run` sends one message and prints the reply. `--format json` makes stdout
NDJSON for that run; the default is text. Without `--server` or `--standalone`,
commands go through OpenCode's shared background service (`opencode service
status`). `--standalone` gives the command a private server; `--server URL`
targets one you started with `opencode serve` (see below).

| Need | Options |
| --- | --- |
| Model | `--model provider/model#variant`; `opencode models` lists choices without a turn |
| Agent | `--agent NAME` |
| Session | `--session ID` continues, or creates that ID; `--continue`/`-c` is this project's last session; `--fork` branches before continuing |
| Input | Message argument, `--file PATH` (repeatable), `--title TEXT` |
| Output | `--format default\|json`; `--thinking` adds reasoning blocks |
| Permissions | `--auto` approves permissions that are not explicitly denied |
| Diagnostics | `--print-logs`, `--log-level LEVEL` (server logs need `--standalone`) |

Leave `--thinking` off for compact progress. Project config, agents, skills, and
plugins load from the cwd as usual.

Redirect stdin from `/dev/null` when launching `run` from a process tool. A local
run with an inherited open pipe on stdin produced no output until killed; the
same command with closed stdin finished in seconds.

## Watch progress

Each NDJSON line has `type`, `timestamp`, `sessionID`, and `part`. Save
`sessionID` from the first line. Observed types: `step_start`, `tool_use`
(`part.tool` is the tool name, `part.state.status` is `completed` or `error`),
`step_finish`, `text` (`part.text` is a completed text part, not a token delta),
and `error`. For a small view (with `jq` available):

```sh
jq --unbuffered -r 'if .type == "text" then .part.text elif .type == "tool_use" then "[\(.part.tool) \(.part.state.status)]" else empty end'
```

Keep stderr and the exit code separately. For token-level deltas or events from
a session you did not launch, use the server's event stream below.

## Server: live events, steering, interruption

```sh
OPENCODE_PASSWORD=SECRET opencode serve --hostname 127.0.0.1 --port 4096
```

A manually started server adopts `OPENCODE_PASSWORD` (legacy
`OPENCODE_SERVER_PASSWORD`); otherwise it generates one and prints it on
stdout. Everything under `/api` requires HTTP Basic auth with user `opencode`
and that password; `/doc` and `/v2/openapi.json` are open. Clients launched with
`--server` read the same variable. The background service keeps its own
password (`opencode service status`, `opencode service set password`).

`GET /api/event` (`Accept: text/event-stream`) streams every event on the server.
Each `data:` line is `{"id":"evt_...","type":"...","data":{...}}`; filter on
`data.sessionID` and `type`. Observed vocabulary for one run:
`session.execution.started|succeeded|interrupted`,
`session.step.started|ended|failed`,
`session.tool.called|progress|success|failed` (`shell.created` for shell calls),
`session.text.started|delta|ended`, `session.inbox.enqueued|delivered`, and
`session.usage.updated`. Skip `session.reasoning.*` and `session.tool.input.*`.
The stream is volatile: a slow consumer is disconnected and misses events.
`GET /api/session/SESSION_ID/message` returns the authoritative messages;
`GET /api/experimental/session/SESSION_ID/log?after=SEQ&follow=true` is the
durable replay-then-follow log. `GET /api/session/active` lists executions this
server owns.

Steer a running session by posting more input:

```http
POST /api/session/SESSION_ID/prompt
Content-Type: application/json

{"text":"CORRECTION","delivery":"steer"}
```

The response is the stored user message; `GET /api/session/SESSION_ID/inbox`
shows it until `session.inbox.delivered`. `steer` (the default) is delivered at
the next step boundary, after the running tool call returns; `queue` waits for
idle. `resume:false` records input without waking execution. `PATCH` and
`DELETE` on `/inbox/INBOX_ID` change delivery or cancel an undelivered item. A
steer sent during a 25-second shell call was delivered when that call ended, and
the final reply followed it.

```http
POST /api/session/SESSION_ID/interrupt
```

Returns `{"interrupted":true}` when execution was active, `false` when idle.
Events: `session.tool.failed`, `session.step.failed`, then
`session.execution.interrupted`; an attached `run` client exits 1 with an `error`
line. `?resume=true` also lets pending steering input run. The session stays
usable: `opencode run --session SESSION_ID` continued one after interruption.
Interruption is process-local; only the server owning the execution can stop it.

A pending permission or question looks like silence on the stream.
`GET /api/session/SESSION_ID/permission` lists requests; reply with
`POST /api/session/SESSION_ID/permission/REQUEST_ID/reply` and
`{"decision":"once"}`, `always`, or `reject`. Forms are under `/form`.
`opencode api --server URL GET /api/session` wraps the same routes.

## Existing sessions and terminal control

```sh
opencode run --session SESSION_ID 'Follow-up'
opencode session list --format json
opencode session export SESSION_ID --sanitize
opencode --session SESSION_ID
```

The last form opens the TUI and needs a PTY; `Esc`/`Ctrl+C` there are
keystrokes, not API calls. Prefer explicit IDs over `--continue` when several
sessions share a project. `export --sanitize` redacts transcript and file data.

## Pitfalls and deeper reference

- V1 recipes still rank highly: `run --attach`, `/event` without `/api`,
  `/session/:id/prompt_async`, and the tools `bash`/`task`. V2 uses `--server`,
  `/api/...` routes, and `shell`/`subagent`.
- Unauthenticated `/api` requests get 401 `UnauthorizedError`, and a `run`
  client without the variable exits at once with `requires a password; set
  OPENCODE_PASSWORD`. Localhost is not open by default.
- Text in `--format json` arrives per completed part; a quiet stream during a
  long tool call is normal. An interrupted run exits nonzero; a run that was
  denied a permission may still exit 0 with an explanatory reply.
- The session, model, and log routes are labeled experimental; confirm a route
  on the running server's `/doc` when something is missing.

Discovery: `opencode --help`, `opencode run --help`, `opencode serve --help`,
`opencode api --help`, `opencode models`, `opencode service status`.

- [CLI commands](https://dev.opencode.ai/v2/docs/cli/commands/)
- [Server, service, and passwords](https://dev.opencode.ai/v2/docs/cli/web/)
- [HTTP API](https://dev.opencode.ai/v2/docs/api/)
- [Session contract: inbox, steer, interrupt](https://github.com/anomalyco/opencode/blob/dev/specs/v2/session.md)
- [V1 to V2 changes](https://dev.opencode.ai/v2/docs/migrate-v1/)
- [Agent-readable documentation index](https://dev.opencode.ai/v2/llms.txt)
