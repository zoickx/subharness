# Verification notes

Maintenance evidence for `skills/harness-use`. Dates, versions, and models are
what was on this Linux machine at the time; references target current stable
behavior and do not gate on these numbers.

## 2026-10-18 and 2026-10-19

Research used first-party docs, local `--help`, and SDK/source files. Live
checks used temporary directories, existing logins, and the cheapest available
model. No installs, config edits, or persistent processes were left behind.

| Harness | Version | Model | Passed | Not exercised |
| --- | --- | --- | --- | --- |
| Claude Code | 2.1.302 (2.1.303 installed on 10-19, not retested) | `haiku` alias | `stream-json` live text deltas; `control_request` initialize and interrupt acknowledged; follow-up turn in the same process recalled a marker; `--resume` in a new process recalled it | `--bg`/`logs`/`attach`; `--permission-prompts host` control requests; nested `CLAUDECODE` guard |
| Codex CLI | codex-cli 0.163.0 | `gpt-6-luna` | `exec --json` events and `exec resume`; App Server `thread/start`, `turn/start`, text deltas; `turn/steer` admitted during an in-progress shell item and the turn completed; `turn/interrupt` ended the turn as `interrupted`; `thread/resume` after restart | Approval requests (`approvalPolicy: never`); `codex queue`; `exec fork` |
| Antigravity CLI | agy 1.4.2 | `gemini-3.8-flash-low` | One-shot `stream-json` with `init`/`step_update`/`result`; warm stdin multi-turn in one process; `--conversation` resume | TUI interrupt; remote control; caller-side `run_command` succeeded only as far as a headless denial |
| OpenCode | opencode v2.0.32 | `opencode/nemotron-3.5-super-vl-free`, `opencode-go/gpt-6-luna` | `serve` with `OPENCODE_PASSWORD` and Basic auth; `run --format json`; `--session` resume; `/api/event` SSE; `prompt` with `delivery: steer` during a shell call was delivered after the call and honored; `interrupt` during a shell call returned `interrupted: true` and the run exited 1; `run --session` continued the interrupted session | Permission/form reply routes; `queue` delivery; durable log replay; `--standalone`; background service; `opencode api` auth |

Findings that changed the references:

- Antigravity headless denial: `result.status` was `SUCCESS` with exit 0 and an
  empty response; the denial was only on stderr.
- Codex `thread/start` takes `sandbox: "read-only"`; turn-level
  `sandboxPolicy.type` is camelCase.
- OpenCode `run` with an inherited open stdin pipe produced no output for four
  minutes; `< /dev/null` completed in under four seconds.
- OpenCode servers require Basic auth (`opencode:<password>`) on `/api`;
  `/doc` and `/v2/openapi.json` are open. The server prints a generated
  password when the environment does not supply one.
- OpenCode V2 renamed the caller-side tools: `bash` is `shell`, `task` is
  `subagent`. Both accept `background: true` with completion notification.
  The caller reference is from docs and source, not a live tool call.

The OpenCode checks were run twice on 2026-10-19: once while the OpenCode Go
login had silently expired, and again after it was renewed, on both the public
free model and a Go-provider model. Results were identical, including the stdin
hang and the password error, so none of the recorded OpenCode behavior depends
on login state. Expired login was not visible in any client or server output.

Caller-side process tools were exercised only for Claude Code, through the
`Bash` tool's background mode, output file, and completion notification while
running the OpenCode checks. Other caller references rest on documentation and
tool schemas captured from `init`/help output.

Remaining gaps across harnesses: permission prompt round-trips through each
machine protocol, and behavior under a parent sandbox.
