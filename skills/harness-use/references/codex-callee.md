# Call Codex CLI

## Launch and options

```sh
codex exec --json -C /work/project 'TASK'
codex exec --json -C /work/project - < prompt.txt
```

Plain `exec` writes progress to stderr and the final answer to stdout. `--json`
makes stdout a JSONL event stream. Stdin is the initial prompt/context, not a
live instruction channel; reading a prompt from it requires EOF.

| Need | Options |
| --- | --- |
| Model / reasoning | `-m MODEL`, `-c 'model_reasoning_effort="low"'` (or another supported effort) |
| Workspace | `-C DIR`, `--add-dir DIR`, `--worktree` |
| Sandbox | `-s read-only\|workspace-write\|danger-full-access` |
| Approvals | Global `-a on-request\|never` before `exec`; `--approve-for-me` enables automatic approval review |
| Broad permissions | `--dangerously-bypass-approvals-and-sandbox` disables both controls |
| Config | `-p PROFILE`, repeatable `-c KEY=TOML_VALUE`, `--ignore-user-config`, `--ignore-rules` |
| Input | Prompt argument, stdin `-`, `-i IMAGE`; piped stdin plus a prompt adds context |
| Output | `--json`, `-o FILE` / `--output-last-message FILE`, `--output-schema FILE`, `--color never` |
| Persistence | `--ephemeral` disables saved sessions; omit for later resume |
| Outside a Git repo | `--skip-git-repo-check` |

For example, `codex -a never exec -s workspace-write 'TASK'` allows workspace
writes while returning failures instead of requesting approval. Permission
choices are independent of which role you give Codex. Config, project
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
documented text deltas and explicit live control. `-o FILE` gives a separate
final-answer artifact. Collect terminal turn state and process exit status.

## Continue or attach

```sh
codex exec resume SESSION_ID --json 'Follow-up'
codex resume SESSION_ID
codex queue --thread SESSION_ID --message 'Follow-up'
```

`exec resume` starts another noninteractive turn. `resume` opens the TUI and
needs a terminal. Explicit IDs avoid `--last` selecting a concurrent session.
`exec fork`/`fork` branch saved history; use their help for arguments.

`queue` addresses an existing session through Codex's shared server. It queues
input; it is not an acknowledgement that an active turn was steered. `codex
agents` browses shared-server sessions. A standalone `exec` process is not a
general-purpose listener for further stdin messages.

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
{"id":2,"method":"thread/start","params":{"cwd":"/work/project"}}
{"id":3,"method":"turn/start","params":{"threadId":"THREAD_ID","input":[{"type":"text","text":"TASK"}]}}
```

Wait for initialization success before `initialized`. Save `result.thread.id`
from `thread/start`, then substitute it into `turn/start`; save `result.turn.id`.
`thread/start` accepts `model`, `approvalPolicy`, and `sandbox` choices. Its
`sandbox` values are `read-only`, `workspace-write`, and `danger-full-access`.
Turn-level `sandboxPolicy.type` instead uses camelCase, such as `readOnly`.
`model/list` lists available models without starting a turn.

Watch `item/started`, `item/completed`, `item/agentMessage/delta`, and
`turn/completed`. Text deltas are in `params.delta`. Turn completion includes
`params.turn.status`: `completed`, `failed`, or `interrupted`. Subscribe by
starting/resuming the thread; a separate unassociated server does not see every
other process's live work.

Send additional input into the active turn:

```jsonl
{"id":4,"method":"turn/steer","params":{"threadId":"THREAD_ID","expectedTurnId":"TURN_ID","input":[{"type":"text","text":"CORRECTION"}]}}
```

The response confirms admission to that turn, not completion of the correction.
If the turn has already ended, start a new turn instead. To interrupt:

```jsonl
{"id":5,"method":"turn/interrupt","params":{"threadId":"THREAD_ID","turnId":"TURN_ID"}}
```

Wait for the interrupted completion event. The process remains usable for a new
`turn/start`. After restarting the server, initialize again and call
`thread/resume` with `{"threadId":"THREAD_ID"}`, then start another turn.
`thread/read` can inspect saved metadata without dumping the full history;
request history only when needed.

Server-initiated approval/input requests have IDs and require responses, just
like your own requests. Ignoring `item/commandExecution/requestApproval`, file
approval, or user-input requests can stall progress. Follow the App Server
response schemas, or select a nonprompting policy for a task that can run under
it. A blanket approval is not a hang diagnostic.

## Pitfalls and deeper reference

- A parent sandbox can prevent a nested sandbox from starting. Read stderr;
  sandbox failure is different from authentication failure or model inactivity.
- Hooks and required MCP startup can delay or fail a run before model output.
- TUI `--no-alt-screen` preserves scrollback, but screen updates are still not a
  structured event protocol. Ctrl-C in a PTY differs from a control byte in a pipe.
- `--full-auto` is obsolete. Use the explicit sandbox/approval options above.

Discovery: `codex --help`, `codex exec --help`, `codex exec resume --help`,
`codex app-server --help`. For an omitted RPC shape, the server's
`generate-json-schema`/`generate-ts` subcommands provide local protocol schemas.

- [Noninteractive execution](https://learn.chatgpt.com/docs/non-interactive-mode.md)
- [CLI flags](https://learn.chatgpt.com/docs/developer-commands?surface=cli)
- [App Server protocol](https://learn.chatgpt.com/docs/app-server.md)
- [Agent-readable documentation index](https://learn.chatgpt.com/llms.txt)
