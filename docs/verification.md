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

## 2026-10-19 second pass: fresh-agent walkthroughs and gap fills

One Opus subagent per harness followed the callee reference as written, then
exercised the items listed as untested above and the caller-side tools live.
Each edited only its two reference files; findings were integrated here.

| Harness | Newly verified | Corrections to the references | Still untested |
| --- | --- | --- | --- |
| Claude Code 2.1.303, `haiku` | `--bg`, `agents --json`, `logs`, `attach` via a Python pty, `stop`, `rm`, `--bg --exec`; host permission round-trip with allow and deny replies; `--permission-prompts none`; nesting check; all table flags; caller `Bash` background task, foreground-timeout backgrounding, `Monitor`, `TaskStop` | Host prompts need `--permission-prompt-tool stdio` in addition to `--permission-prompts host`; `system/init` arrives after each user message, not after `initialize`; variadic list flags swallow a trailing prompt; interrupt reply and interrupted-result fields; every denial still ends `success` with exit 0; `CLAUDECODE` nesting guard did not trigger; `SessionStart` hook events appear without `--include-hook-events`; `--bg` needs a trusted directory; `-p --resume` takes the long session ID; pipeline exit code is the last stage's | `--bg` from an untrusted directory (ran in the repo instead); `updatedPermissions`, `control_cancel_request`; a user line during an active turn; subagent-owned background command lifecycle; TUI gestures |
| Codex CLI 0.163.0, `gpt-6-luna` | `queue` semantics (shared server required, delivered after the next turn); `exec fork`; `-o` on failure; `thread/resume` in a fresh server; steer/interrupt error strings on an idle thread; all table flags; `approvalPolicy` values and the `experimentalApi` capability | `exec` reads non-TTY stdin to EOF even with a prompt; `exec` ignores `-a` and runs with approval `never`; `exec resume`/`fork` reject `-C` and `-s`; `--worktree` conflicts with `--ephemeral`; `-o` not written on failure; failure notification fields; caller tools sit behind a code-mode `exec` cell with a `wait` tool | First pass was blocked by an exhausted weekly usage limit; see the rerun section below |
| Antigravity CLI 1.4.2, `gemini-3.8-flash-low` | Caller tools live: `run_command` returns a task ID and `manage_task` (`status`, `send_input`) drives it; `--mode auto` unavailable on this account; `--print-timeout` expiry; unknown `--conversation`; all table flags | `command_status`/`send_command_input` appear in the `init` catalog but are not callable; `manage_task` is the interface; timeout expiry and permission denial both return `SUCCESS` with exit 0 and a stderr note; `init` `conversation_id` is top-level; headless exit kills background tasks; `--log-file`, `--disable-slash-commands` added | TUI `Esc`/`Ctrl+C` interrupt (blocked by a workspace-trust menu that would edit global settings); `manage_task` `kill`; control characters via `send_input`; `permissions.allow` rules; `--sandbox`; remote control (deliberately excluded) |
| OpenCode v2.0.32, `opencode/nemotron-3.5-super-vl-free` | Permission replies over HTTP (`once`, `reject`, `reject` with message, no reply then `interrupt`); `run` auto-rejects `ask` and `--auto` answers `once`; `queue` delivery after the first turn's final text; `--standalone`; `opencode api` with and without password; caller `shell` background mode returns shell ID and output path and later posts a synthetic completion turn; tool names are `shell`/`subagent` | `/doc` and `/v2/openapi.json` serve the web UI; the spec is the authenticated `/openapi.json`; responses wrap payloads in `data`; `shell.*` events lack `data.sessionID`; the experimental log returned only `log.synced`, no replay; `run` exits at first idle so a background shell's completion turn is never printed, and `--standalone` kills it | Durable log replay (bug or misuse unclear); forms; `always`; `interrupt?resume=true`; inbox `PATCH`/`DELETE`; `resume:false`; live `subagent` call; background service paths (by design) |

Constraints met in this pass: no installs, no global config or auth changes,
temp directories only (except one `--bg` check in the repo, session removed
afterwards), owned processes killed. Workspace-trust prompts in both Claude Code
and Antigravity block some interactive checks in a temp directory; accepting
them would edit `~/.claude.json` or `~/.gemini/antigravity-cli/settings.json`,
so those checks were not forced.
