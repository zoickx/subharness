# Harness use

Markdown skills for using another AI harness like a subagent, consultant, peer,
or interactive assistant. We call that external agent a **subharness**.

## Why

Existing interop tooling tends to be heavy and opaque: hidden hangs, wasted
tokens, no live view of what the other agent is doing, no way to steer it. This
repo is the opposite. It is Markdown only, with no wrapper, daemon, or
dependency. Each reference documents the launch flags, event streams, control
protocols, and pitfalls a harness already has, as observed on current stable
releases. The agent decides how to use them, the same way a human operator
would. Linux only.

## Matrix

Rows are the calling harness, columns the called one. Each cell holds five
capabilities in a fixed order: watch live progress, steer mid-turn, interrupt,
resume a saved session, answer the child's permission prompts.

✅ direct with the caller's own tools, verified live. ⚠️ works with a caveat.
❌ not available. Hover an emoji for the specific reason; the caveats are also
listed below.

<!-- matrix:start -->
| Caller \ Callee | Claude Code | Codex CLI | OpenCode | agy |
| --- | --- | --- | --- | --- |
| Claude Code | <abbr title="Watch (direct): stream-json with text deltas">✅</abbr><abbr title="Steer (caveat): interrupt, then send the correction in the same stdin process. Caller: Bash has no writable stdin; hold the pipe with a small helper or tmux">⚠️</abbr><abbr title="Interrupt (caveat): control_request interrupt over stdin. Caller: Bash has no writable stdin; hold the pipe with a small helper or tmux">⚠️</abbr><abbr title="Resume (direct): --resume SESSION_ID">✅</abbr><abbr title="Permissions (caveat): can_use_tool round-trip over stdin with --permission-prompt-tool stdio. Caller: Bash has no writable stdin; hold the pipe with a small helper or tmux">⚠️</abbr> | <abbr title="Watch (direct): exec --json items, or app-server text deltas">✅</abbr><abbr title="Steer (caveat): app-server turn/steer. Caller: Bash has no writable stdin; hold the pipe with a small helper or tmux">⚠️</abbr><abbr title="Interrupt (caveat): app-server turn/interrupt; the command keeps running until the server exits. Caller: Bash has no writable stdin; hold the pipe with a small helper or tmux">⚠️</abbr><abbr title="Resume (direct): exec resume or thread/resume">✅</abbr><abbr title="Permissions (caveat): app-server requestApproval, accept or decline. Caller: Bash has no writable stdin; hold the pipe with a small helper or tmux">⚠️</abbr> | <abbr title="Watch (direct): run --format json, or the server event stream">✅</abbr><abbr title="Steer (direct): POST prompt with delivery steer; lands after the running tool call">✅</abbr><abbr title="Interrupt (direct): POST interrupt">✅</abbr><abbr title="Resume (direct): run --session SESSION_ID">✅</abbr><abbr title="Permissions (direct): HTTP permission reply; only for sessions driven over HTTP, run auto-rejects">✅</abbr> | <abbr title="Watch (direct): stream-json text deltas">✅</abbr><abbr title="Steer (not available): headless stdin only queues the next turn">❌</abbr><abbr title="Interrupt (caveat): kill or --print-timeout only; the result still says SUCCESS, exit 0">⚠️</abbr><abbr title="Resume (direct): --conversation ID; an unknown ID silently starts a new one">✅</abbr><abbr title="Permissions (not available): headless auto-denies; TUI or remote control only">❌</abbr> |
| Codex CLI | <abbr title="Watch (caveat): stream-json with text deltas. Caller: the sandbox has no network; grant it or run the child outside the sandbox">⚠️</abbr><abbr title="Steer (caveat): interrupt, then send the correction in the same stdin process. Caller: the sandbox has no network; grant it or run the child outside the sandbox; write_stdin can send text per its schema, untested live">⚠️</abbr><abbr title="Interrupt (caveat): control_request interrupt over stdin. Caller: the sandbox has no network; grant it or run the child outside the sandbox; write_stdin can send text per its schema, untested live">⚠️</abbr><abbr title="Resume (caveat): --resume SESSION_ID. Caller: the sandbox has no network; grant it or run the child outside the sandbox">⚠️</abbr><abbr title="Permissions (caveat): can_use_tool round-trip over stdin with --permission-prompt-tool stdio. Caller: the sandbox has no network; grant it or run the child outside the sandbox; write_stdin can send text per its schema, untested live">⚠️</abbr> | <abbr title="Watch (caveat): exec --json items, or app-server text deltas. Caller: the sandbox has no network; grant it or run the child outside the sandbox">⚠️</abbr><abbr title="Steer (caveat): app-server turn/steer. Caller: the sandbox has no network; grant it or run the child outside the sandbox; write_stdin can send text per its schema, untested live">⚠️</abbr><abbr title="Interrupt (caveat): app-server turn/interrupt; the command keeps running until the server exits. Caller: the sandbox has no network; grant it or run the child outside the sandbox; write_stdin can send text per its schema, untested live">⚠️</abbr><abbr title="Resume (caveat): exec resume or thread/resume. Caller: the sandbox has no network; grant it or run the child outside the sandbox">⚠️</abbr><abbr title="Permissions (caveat): app-server requestApproval, accept or decline. Caller: the sandbox has no network; grant it or run the child outside the sandbox; write_stdin can send text per its schema, untested live">⚠️</abbr> | <abbr title="Watch (caveat): run --format json, or the server event stream. Caller: the sandbox has no network; grant it or run the child outside the sandbox">⚠️</abbr><abbr title="Steer (caveat): POST prompt with delivery steer; lands after the running tool call. Caller: the sandbox has no network; grant it or run the child outside the sandbox">⚠️</abbr><abbr title="Interrupt (caveat): POST interrupt. Caller: the sandbox has no network; grant it or run the child outside the sandbox">⚠️</abbr><abbr title="Resume (caveat): run --session SESSION_ID. Caller: the sandbox has no network; grant it or run the child outside the sandbox">⚠️</abbr><abbr title="Permissions (caveat): HTTP permission reply; only for sessions driven over HTTP, run auto-rejects. Caller: the sandbox has no network; grant it or run the child outside the sandbox">⚠️</abbr> | <abbr title="Watch (caveat): stream-json text deltas. Caller: the sandbox has no network; grant it or run the child outside the sandbox">⚠️</abbr><abbr title="Steer (not available): headless stdin only queues the next turn">❌</abbr><abbr title="Interrupt (caveat): kill or --print-timeout only; the result still says SUCCESS, exit 0. Caller: the sandbox has no network; grant it or run the child outside the sandbox">⚠️</abbr><abbr title="Resume (caveat): --conversation ID; an unknown ID silently starts a new one. Caller: the sandbox has no network; grant it or run the child outside the sandbox">⚠️</abbr><abbr title="Permissions (not available): headless auto-denies; TUI or remote control only">❌</abbr> |
| OpenCode | <abbr title="Watch (direct): stream-json with text deltas">✅</abbr><abbr title="Steer (caveat): interrupt, then send the correction in the same stdin process. Caller: shell has no stdin channel; hold the pipe with a small helper or tmux">⚠️</abbr><abbr title="Interrupt (caveat): control_request interrupt over stdin. Caller: shell has no stdin channel; hold the pipe with a small helper or tmux">⚠️</abbr><abbr title="Resume (direct): --resume SESSION_ID">✅</abbr><abbr title="Permissions (caveat): can_use_tool round-trip over stdin with --permission-prompt-tool stdio. Caller: shell has no stdin channel; hold the pipe with a small helper or tmux">⚠️</abbr> | <abbr title="Watch (direct): exec --json items, or app-server text deltas">✅</abbr><abbr title="Steer (caveat): app-server turn/steer. Caller: shell has no stdin channel; hold the pipe with a small helper or tmux">⚠️</abbr><abbr title="Interrupt (caveat): app-server turn/interrupt; the command keeps running until the server exits. Caller: shell has no stdin channel; hold the pipe with a small helper or tmux">⚠️</abbr><abbr title="Resume (direct): exec resume or thread/resume">✅</abbr><abbr title="Permissions (caveat): app-server requestApproval, accept or decline. Caller: shell has no stdin channel; hold the pipe with a small helper or tmux">⚠️</abbr> | <abbr title="Watch (direct): run --format json, or the server event stream">✅</abbr><abbr title="Steer (direct): POST prompt with delivery steer; lands after the running tool call">✅</abbr><abbr title="Interrupt (direct): POST interrupt">✅</abbr><abbr title="Resume (direct): run --session SESSION_ID">✅</abbr><abbr title="Permissions (direct): HTTP permission reply; only for sessions driven over HTTP, run auto-rejects">✅</abbr> | <abbr title="Watch (direct): stream-json text deltas">✅</abbr><abbr title="Steer (not available): headless stdin only queues the next turn">❌</abbr><abbr title="Interrupt (caveat): kill or --print-timeout only; the result still says SUCCESS, exit 0">⚠️</abbr><abbr title="Resume (direct): --conversation ID; an unknown ID silently starts a new one">✅</abbr><abbr title="Permissions (not available): headless auto-denies; TUI or remote control only">❌</abbr> |
| agy | <abbr title="Watch (direct): stream-json with text deltas">✅</abbr><abbr title="Steer (caveat): interrupt, then send the correction in the same stdin process. Caller: manage_task send_input writes lines; driving a JSON protocol this way is untested">⚠️</abbr><abbr title="Interrupt (caveat): control_request interrupt over stdin. Caller: manage_task send_input writes lines; driving a JSON protocol this way is untested">⚠️</abbr><abbr title="Resume (direct): --resume SESSION_ID">✅</abbr><abbr title="Permissions (caveat): can_use_tool round-trip over stdin with --permission-prompt-tool stdio. Caller: manage_task send_input writes lines; driving a JSON protocol this way is untested">⚠️</abbr> | <abbr title="Watch (direct): exec --json items, or app-server text deltas">✅</abbr><abbr title="Steer (caveat): app-server turn/steer. Caller: manage_task send_input writes lines; driving a JSON protocol this way is untested">⚠️</abbr><abbr title="Interrupt (caveat): app-server turn/interrupt; the command keeps running until the server exits. Caller: manage_task send_input writes lines; driving a JSON protocol this way is untested">⚠️</abbr><abbr title="Resume (direct): exec resume or thread/resume">✅</abbr><abbr title="Permissions (caveat): app-server requestApproval, accept or decline. Caller: manage_task send_input writes lines; driving a JSON protocol this way is untested">⚠️</abbr> | <abbr title="Watch (direct): run --format json, or the server event stream">✅</abbr><abbr title="Steer (direct): POST prompt with delivery steer; lands after the running tool call">✅</abbr><abbr title="Interrupt (direct): POST interrupt">✅</abbr><abbr title="Resume (direct): run --session SESSION_ID">✅</abbr><abbr title="Permissions (direct): HTTP permission reply; only for sessions driven over HTTP, run auto-rejects">✅</abbr> | <abbr title="Watch (direct): stream-json text deltas">✅</abbr><abbr title="Steer (not available): headless stdin only queues the next turn">❌</abbr><abbr title="Interrupt (caveat): kill or --print-timeout only; the result still says SUCCESS, exit 0">⚠️</abbr><abbr title="Resume (direct): --conversation ID; an unknown ID silently starts a new one">✅</abbr><abbr title="Permissions (not available): headless auto-denies; TUI or remote control only">❌</abbr> |
<!-- matrix:end -->

Caveats:

- Claude Code and Codex are controlled over a stdin JSON protocol. Claude Code
  and OpenCode callers have no writable stdin, so they need a small helper or
  `tmux` to hold the pipe. The agy caller can write lines, but driving a JSON
  protocol that way is untested.
- Codex's sandbox has no network, so any child harness fails until network is
  granted or the child runs outside the sandbox.
- agy has no mid-turn steering or permission replies in headless mode;
  interrupt means killing the process or a timeout, and the result still says
  `SUCCESS`.
- Targeted messages back from the child are a prompt convention in every cell:
  ask for a marker line or a status file and let a watcher forward matches.

## Use

The installable unit is [skills/harness-use](skills/harness-use/SKILL.md).
Copy or symlink that entire directory into a skill directory supported by your
caller. Keep `references/` beside `SKILL.md`. Invoke `harness-use`, or let the
caller discover it normally.

Examples:

- "Use Codex to investigate this. Show me how to watch its progress."
- "Start Claude Code and keep the session available for follow-up."
- "Send this correction to the OpenCode session already running."
- "Ask agy for a second opinion using a small model."

One entry skill links to four callee references and four caller references.
Only the relevant pair needs to enter context. There is no sixteen-pair matrix
to keep synchronized. The CLI must already be installed and authenticated.

## Develop

The repo-local [refresh skill](.agents/skills/refresh-harness-use/SKILL.md) describes
manual research and smoke tests. It is a development tool, not part of the
installable skill. Ask an agent working in this repo to "refresh harness-use for
Claude Code", or to refresh all four.

We target current stable releases. Version/date evidence belongs in
[verification notes](docs/verification.md), not runtime version gates. Tests
use small tasks and inexpensive available models. Documentation and actual
observations are distinguished; untested interaction paths are labeled.
