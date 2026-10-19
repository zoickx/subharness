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
| Codex CLI 0.163.0, `gpt-6-luna` | After the weekly limit reset: `exec --json` with real output and `-o` on success; approval round-trip on a model-issued command with `accept` and `decline`; steer honored and interrupt on a model-issued `sleep`; `queue` during an active `exec` turn; caller tools live (code-mode `exec` cell calling `tools.exec_command` and `tools.write_stdin`). Without a model: `queue` on an idle thread, `exec fork`, `-o` on failure, `thread/resume` in a fresh server, steer/interrupt error strings, all table flags, `approvalPolicy` values and the `experimentalApi` capability | `exec` reads non-TTY stdin to EOF even with a prompt; `exec` ignores `-a` and runs with approval `never`; `exec resume`/`fork` reject `-C` and `-s`; `--worktree` conflicts with `--ephemeral`; `-o` not written on failure; a command item has no progress events; interrupt leaves a model-issued command running as a thread background terminal until the server exits, while a `thread/shellCommand` child is reparented to init; `decline` works although unlisted in `availableDecisions`; under `on-request` with a read-only sandbox the model often claims denial without trying; the sandbox has no network, so a child harness fails with `EAI_AGAIN`; caller tools sit behind a code-mode `exec` cell with a `wait` tool | `acceptForSession` and `cancel` decisions; file-change approvals; a network override for child harnesses; the `wait`/`cell_id` path (every cell finished within its yield) |
| Antigravity CLI 1.4.2, `gemini-3.8-flash-low` | Caller tools live: `run_command` returns a task ID and `manage_task` (`status`, `send_input`) drives it; `--mode auto` unavailable on this account; `--print-timeout` expiry; unknown `--conversation`; all table flags | `command_status`/`send_command_input` appear in the `init` catalog but are not callable; `manage_task` is the interface; timeout expiry and permission denial both return `SUCCESS` with exit 0 and a stderr note; `init` `conversation_id` is top-level; headless exit kills background tasks; `--log-file`, `--disable-slash-commands` added | TUI `Esc`/`Ctrl+C` interrupt (blocked by a workspace-trust menu that would edit global settings); `manage_task` `kill`; control characters via `send_input`; `permissions.allow` rules; `--sandbox`; remote control (deliberately excluded) |
| OpenCode v2.0.32, `opencode/nemotron-3.5-super-vl-free` | Permission replies over HTTP (`once`, `reject`, `reject` with message, no reply then `interrupt`); `run` auto-rejects `ask` and `--auto` answers `once`; `queue` delivery after the first turn's final text; `--standalone`; `opencode api` with and without password; caller `shell` background mode returns shell ID and output path and later posts a synthetic completion turn; tool names are `shell`/`subagent` | `/doc` and `/v2/openapi.json` serve the web UI; the spec is the authenticated `/openapi.json`; responses wrap payloads in `data`; `shell.*` events lack `data.sessionID`; the experimental log returned only `log.synced`, no replay; `run` exits at first idle so a background shell's completion turn is never printed, and `--standalone` kills it | Durable log replay (bug or misuse unclear); forms; `always`; `interrupt?resume=true`; inbox `PATCH`/`DELETE`; `resume:false`; live `subagent` call; background service paths (by design) |

The Codex first pass ran while the account's weekly usage limit was exhausted
(`account/rateLimits/read` showed `usedPercent: 100`); every model turn failed
with `usageLimitExceeded`. The model-dependent items were rerun the same day
after the limit was reset.

Constraints met in this pass: no installs, no global config or auth changes,
temp directories only (except one `--bg` check in the repo, session removed
afterwards), owned processes killed. Workspace-trust prompts in both Claude Code
and Antigravity block some interactive checks in a temp directory; accepting
them would edit `~/.claude.json` or `~/.gemini/antigravity-cli/settings.json`,
so those checks were not forced.

## Third pass: stdin channels without a helper (2026-10-19)

Checked which standard tools can hold a stdin JSON protocol open from a
caller's shell tool, so the references could drop the "small helper" wording.

- Claude Code 2.1.303 (`haiku`) behind a FIFO started as Claude Code's own
  `Bash` background task (`exec 3<>in; claude ... <&3`): permission allow and
  deny, interrupt, and a follow-up turn, each written from a later `Bash`
  call. Without the `3<>` holder the process exited 0 after the first turn.
- Claude Code in a `tmux` 3.7c pane: `-p --input-format stream-json` with a
  terminal stdin exits with `Input must be provided either through stdin or as
  a prompt argument when using --print`; with a prompt argument it ran one
  turn and exited without reading stdin. With `cat | claude ...` and `stty raw
  -echo icrnl`, permission allow and deny, interrupt, a correction after the
  interrupt, and a 6000-byte message all worked with a clean `pipe-pane` log.
- Codex 0.163.0 `app-server --listen stdio://`: accepted a terminal stdin
  directly in a raw-mode `tmux` pane (initialize, `thread/start`, command
  approval round-trip on `gpt-6-luna`); behind a FIFO, initialize and
  `thread/start` responded without a model turn.
- Terminal line discipline, measured with `cat` in a pane: canonical mode
  truncated a 6000-byte line to 4095 bytes and echoed input; raw mode passed
  it intact with no CR.
- The interrupted Claude Code `result` varied: `error_during_execution` with
  `aborted_streaming`, `success` with `aborted_streaming`, and `success` with
  `stop_hook_prevented`. The reference no longer promises specific fields.

Untested: the FIFO from OpenCode's `shell` and agy's `run_command`; large
payloads through `tmux load-buffer`/`paste-buffer`; TUI control through `tmux`
(agy's trust menu still blocks temp directories).
