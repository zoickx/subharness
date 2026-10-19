# Call Codex CLI

## Launch and options

```sh
codex exec --json -C /work/project 'TASK' < /dev/null
codex exec --json -C /work/project - < prompt.txt
```

Plain `exec` writes progress to stderr and the final answer to stdout. `--json`
makes stdout a JSONL event stream. Stdin is the initial prompt/context, not a
live instruction channel. Even with a prompt argument, non-TTY stdin is read to
EOF and appended; an inherited open pipe blocks before any event. Redirect
`< /dev/null` when stdin carries nothing.

| Need | Options |
| --- | --- |
| Model / reasoning | `-m MODEL`, `-c 'model_reasoning_effort="low"'` (or another supported effort) |
| Workspace | `-C DIR`, `--add-dir DIR`, `--worktree` (not with `--ephemeral`) |
| Sandbox | `-s read-only\|workspace-write\|danger-full-access` |
| Approvals | `exec` runs with approval `never`; `--approve-for-me` routes requests to automatic review |
| Broad permissions | `--dangerously-bypass-approvals-and-sandbox` disables both controls |
| Config | `-p PROFILE`, repeatable `-c KEY=TOML_VALUE`, `--ignore-user-config`, `--ignore-rules` |
| Input | Prompt argument, stdin `-`, `-i IMAGE`; piped stdin plus a prompt adds context |
| Output | `--json`, `-o FILE` / `--output-last-message FILE`, `--output-schema FILE`, `--color never` |
| Persistence | `--ephemeral` disables saved sessions; omit for later resume |
| Outside a Git repo | `--skip-git-repo-check` |

Global `-a on-request|never` must precede `exec` (it is rejected after it),
but `exec` still reports and uses approval `never`: a command needing approval
fails back to the model. For interactive approval round-trips use App Server.
`exec resume` and `exec fork` reject `-C`, `-s`, `--add-dir`, and `--color`;
use `-c sandbox_mode="read-only"` and similar keys there. Config, project
instructions, hooks, and MCP servers can affect the run.

## Watch progress cheaply

JSONL events include `thread.started` (save `thread_id`), `turn.started`,
`item.started`, `item.updated`, `item.completed`, `turn.completed`, `turn.failed`,
and `error`. Items include `agent_message`, `command_execution`, file changes,
MCP calls, searches, plans, and reasoning.

Summarize item type/name/status as it changes. For text, take
`item.completed` where `item.type == "agent_message"` and read `item.text`.
Skip reasoning and full command output unless needed for diagnosis.
`exec --json` is useful for activity and completed messages; use App Server for
documented text deltas and explicit live control. Failure is an `error` event
plus `turn.failed` with `error.message`, and exit 1. A usage limit fails this
way within seconds. `-o FILE` is written only on success; after a failed turn
an existing file keeps its old content, so check exit status and turn state.

## Continue or attach

```sh
codex exec resume SESSION_ID --json 'Follow-up' < /dev/null
codex exec fork SESSION_ID --json 'Branch prompt' < /dev/null
codex resume SESSION_ID
codex queue --thread SESSION_ID --message 'Follow-up'
```

`exec resume` starts another noninteractive turn. `resume` opens the TUI and
needs a terminal. Explicit IDs avoid `--last` selecting a concurrent session.
`exec fork` makes a new thread from saved history (new `thread_id`). Without a
prompt it only creates the fork and exits 0; `-o` then errors and requires a
prompt. The fork takes model and settings from current config and flags, not
from the source thread; pass `-m` explicitly.

`queue` needs Codex's shared server (`--no-daemon` is rejected) and returns at
once with `Queued message ID for thread ID.` The message is stored in the
thread's queue. It is not delivered to an idle thread: it starts as a new turn
after the next turn on that thread completes in a server that has the thread
loaded. App Server `thread/queue/list|start|delete` (experimental) inspect,
start, or remove it. Queue during an active `exec` turn is untested. `codex
agents` browses shared-server sessions. A standalone `exec` process is not a
listener for further stdin messages.

## Live steering through App Server

The bundled server is a child process with a newline-delimited JSON-RPC interface;
no SDK or external service is needed:

```sh
codex app-server --listen stdio://
```

Keep stdin open; parse stdout as JSON and stderr as diagnostics. Send each
request on its own line, match responses by `id`, and handle interleaved events.
Do not include a JSON-RPC `jsonrpc` version field.

```jsonl
{"id":1,"method":"initialize","params":{"clientInfo":{"name":"harness_use","title":"Harness use","version":"1"}}}
{"method":"initialized","params":{}}
{"id":2,"method":"thread/start","params":{"cwd":"/work/project","model":"MODEL","approvalPolicy":"on-request","sandbox":"read-only"}}
{"id":3,"method":"turn/start","params":{"threadId":"THREAD_ID","input":[{"type":"text","text":"TASK"}]}}
```

Wait for initialization success before `initialized`. Save `result.thread.id`
from `thread/start`, then substitute it into `turn/start`; save `result.turn.id`.
`approvalPolicy` is `untrusted`, `on-request`, or `never`. `sandbox` is
`read-only`, `workspace-write`, or `danger-full-access`; turn-level
`sandboxPolicy.type` uses camelCase, such as `readOnly`. Experimental methods and
fields need `"capabilities":{"experimentalApi":true}` in `initialize`.
`model/list` lists models and `account/rateLimits/read` shows remaining quota
without starting a turn.

Watch `item/started`, `item/completed`, `item/agentMessage/delta`, and
`turn/completed`. Text deltas are in `params.delta`. Turn completion includes
`params.turn.status`: `completed`, `failed`, or `interrupted`. A failure also
sends an `error` notification with `params.error.codexErrorInfo` (for example
`usageLimitExceeded`) and `willRetry`. A separate unassociated server does not
see every other process's live work.

Send additional input into the active turn:

```jsonl
{"id":4,"method":"turn/steer","params":{"threadId":"THREAD_ID","expectedTurnId":"TURN_ID","input":[{"type":"text","text":"CORRECTION"}]}}
```

The result `{"turnId":...}` confirms admission, not completion of the
correction. With no active turn the error is `-32600` `no active turn to steer`;
start a new turn instead. To interrupt:

```jsonl
{"id":5,"method":"turn/interrupt","params":{"threadId":"THREAD_ID","turnId":"TURN_ID"}}
```

The result is `{}`, then `turn/completed` with `interrupted`. The running
command item may get no `item/completed`. In a test with `thread/shellCommand`,
the command's child process kept running after the interrupt, reparented to
init; check for and kill leftovers you own. The server remains usable for a new
`turn/start`. After restarting the server, initialize again and call
`thread/resume` with `{"threadId":"THREAD_ID"}`, then start another turn.
`thread/read` inspects saved metadata without dumping the full history.

Server-initiated requests have their own `id` and need a reply. Ignoring
`item/commandExecution/requestApproval`, file approval, or user-input requests
stalls the turn. Per docs and schema (not live-tested), answer a command
approval with `{"id":REQUEST_ID,"result":{"decision":"accept"}}`; other
decisions are `acceptForSession`, `decline` (turn continues), and `cancel`
(turn is interrupted). Then `serverRequest/resolved` and `item/completed`
(`declined` when refused) follow. Select a nonprompting policy for a task that
can run under it. A blanket approval is not a hang diagnostic.

## Pitfalls and deeper reference

- A parent sandbox can prevent a nested sandbox from starting. Read stderr;
  sandbox failure is different from authentication failure or model inactivity.
- Hooks and required MCP startup can delay or fail a run before model output.
- `thread/shellCommand` runs a command in the thread without the model, outside
  the sandbox. It is a user action, not an agent tool.
- TUI `--no-alt-screen` preserves scrollback, but screen updates are still not a
  structured event protocol. Ctrl-C in a PTY differs from a control byte in a pipe.
- `--full-auto` is removed. Use the explicit sandbox/approval options above.

Discovery: `codex --help`, `codex exec --help`, `codex exec resume --help`,
`codex app-server --help`. For an omitted RPC shape, the server's
`generate-json-schema --out DIR` (add `--experimental` for experimental methods)
and `generate-ts` provide local protocol schemas.

- [Noninteractive execution](https://learn.chatgpt.com/docs/non-interactive-mode.md)
- [CLI flags](https://learn.chatgpt.com/docs/developer-commands?surface=cli)
- [App Server protocol](https://learn.chatgpt.com/docs/app-server.md)
- [Agent-readable documentation index](https://learn.chatgpt.com/llms.txt)
