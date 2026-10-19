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

Advanced path. It relies on protocol details observed on one release and
can break with an update; prefer launch flags and resume when they suffice.

```sh
OPENCODE_PASSWORD=SECRET opencode serve --hostname 127.0.0.1 --port 4096
```

A manually started server adopts `OPENCODE_PASSWORD` (legacy
`OPENCODE_SERVER_PASSWORD`); otherwise it generates one and prints it on
stdout. `/api/...` and the route spec `/openapi.json` require HTTP Basic auth
with user `opencode` and that password; `/doc` and other paths serve the web UI.
Clients launched with `--server` read the same variable. The background service
keeps its own password (`opencode service status`, `opencode service set password`).
JSON responses wrap the payload as `{"data":...}`; errors carry `_tag` and `message`.

`GET /api/event` (`Accept: text/event-stream`) streams every event on the server
as `data:` lines (no SSE `id:`/`event:`) and `: heartbeat` comments. Each payload
is `{"id":"evt_...","type":"...","data":{...}}`; filter on `data.sessionID` and
`type`. Observed: `session.execution.started|succeeded|interrupted`,
`session.step.started|ended|failed`, `session.tool.called|progress|success|failed`,
`session.text.started|delta|ended`, `session.inbox.enqueued|delivered`,
`session.synthetic`, `session.retry.scheduled`, `session.usage.updated`, and
`permission.asked|replied`. `shell.created|exited` lack `data.sessionID`; match
`metadata.shellID` from `session.tool.progress`. Skip `session.reasoning.*` and
`session.tool.input.*`. The stream is volatile: a slow consumer is disconnected
and misses events. `GET /api/session/SESSION_ID/message` returns stored messages
newest first; `GET /api/session/active` lists executions this server owns. The
documented replay log `/api/experimental/session/SESSION_ID/log?after=SEQ&follow=true`
returned only `{"type":"log.synced","seq":N}` here, with no replayed or live events.

Steer a running session by posting more input:

```http
POST /api/session/SESSION_ID/prompt
Content-Type: application/json

{"text":"CORRECTION","delivery":"steer"}
```

The response is the stored user message; `GET /api/session/SESSION_ID/inbox`
shows it until `session.inbox.delivered`. `steer` (the default) is delivered at
the next step boundary, after the running tool call returns. `queue` is held
until the turn would otherwise end, then runs as another turn in the same
execution; an attached `run` prints it too. `resume:false` records input without
waking execution. `PATCH`/`DELETE` on `/inbox/INBOX_ID` change or cancel an item.

```http
POST /api/session/SESSION_ID/interrupt
```

Returns bare `{"interrupted":true}` when execution was active, `false` when idle.
Events: `session.tool.failed`, `session.step.failed`, then
`session.execution.interrupted` (`data.reason` `user`); an attached `run` exits 1
with an `error` line whose `error.type` is `aborted`. `?resume=true` also lets
pending steering input run (untested). `opencode run --session SESSION_ID`
continued an interrupted session. Only the server owning an execution can stop it.

## Permissions

Project rules go in `opencode.jsonc`; the last matching rule wins:
`"permissions":[{"action":"shell","resource":"*","effect":"ask"}]`.

`run` cannot answer a prompt. On `ask` it rejects at once (stderr
`permission requested: shell (CMD); auto-rejecting`), the model sees a
`permission.rejected` tool error, and the run usually exits 0 with an
explanation. `--auto` makes the client answer `once`; `deny` rules still apply.
To answer prompts yourself, drive the session over HTTP with no `run` client:
`POST /api/session` with `{"location":{"directory":"/abs/cwd"},"model":
{"providerID":"opencode","id":"MODEL"}}`, then `POST .../prompt` with `{"text":"TASK"}`.

`permission.asked` carries `data.id` (`per_...`), `action`, `resources`, and
`save` (what `always` would store). `GET /api/session/SESSION_ID/permission`
lists pending requests. `POST /api/session/SESSION_ID/permission/REQUEST_ID/reply`
returns 204:

- `{"decision":"once"}` or `always`: the tool runs.
- `{"decision":"reject"}`: the tool fails as `aborted`; the execution ends
  `interrupted` with reason `shutdown`.
- `{"decision":"reject","message":"TEXT"}`: the model gets TEXT and continues.

An unanswered request stays pending with no further events; `interrupt` clears
it. Questions use `/api/session/SESSION_ID/form/FORM_ID/reply` (untested).
`opencode api --server URL GET /api/session` (or an operation ID such as
`session.active`) calls the same routes; it exits 1 on a missing or rejected
password and on an HTTP error status.

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
  `/session/:id/prompt_async`, `permission` config, and tools `bash`/`task`.
  V2 uses `--server`, `/api/...`, `permissions`, and `shell`/`subagent`.
- Unauthenticated `/api` requests get 401 `UnauthorizedError`; a `run` or `api`
  client without the variable exits 1 with `requires a password; set
  OPENCODE_PASSWORD`. Localhost is not open by default.
- `run` exits when the session first goes idle. A later wake-up, such as a
  background shell completion (`session.synthetic`), runs on the server without
  the client. With `--standalone`, background shells die with the client.
- Text in `--format json` arrives per completed part; a quiet stream during a
  long tool call is normal. An `error` line may be followed by a provider retry
  and a normal reply. The session and log routes are experimental; check the
  running server's `/openapi.json` when a route is missing.

Discovery: `opencode --help`, `opencode run --help`, `opencode serve --help`,
`opencode api --help`, `opencode models`, `opencode service status`.

- [CLI commands](https://dev.opencode.ai/v2/docs/cli/commands/)
- [Server, service, and passwords](https://dev.opencode.ai/v2/docs/cli/web/)
- [HTTP API](https://dev.opencode.ai/v2/docs/api/)
- [Permissions](https://dev.opencode.ai/v2/docs/permissions/)
- [Session contract: inbox, steer, interrupt](https://github.com/anomalyco/opencode/blob/dev/specs/v2/session.md)
- [V1 to V2 changes](https://dev.opencode.ai/v2/docs/migrate-v1/)
- [Agent-readable documentation index](https://dev.opencode.ai/v2/llms.txt)
