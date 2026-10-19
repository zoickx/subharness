# subharness

Agent skills for using another AI harness directly through its CLI. Instead of
relying on plugins or complex external tooling, this skill takes the zero-setup
approach of trusting an agent to use what's already availble.

This skill bundles no executables, and is intentially minimally prescriptive
and mostly instructive. It aims to tell agents *how* they can interact with
each other in different configurations, using basic standard tooling, leaving
actual operation to judgement in context. It is effectively a focused exerpt
from their documentation.

## Installation

Using the [skills](https://github.com/vercel-labs/skills) CLI:

```sh
npx skills add zoickx/subharness --skill subharness
```

If installing manually, make sure to keep `references/` beside `SKILL.md`.
Invoke `subharness`, or let the caller discover it normally.

## Example

Claude Code calling Codex:

> Have Codex review this branch with GPT 6 Astra at high effort. Meanwhile,
> fix the failing parser test. Tell me what Codex finds when it is done.

Claude Code reads the Codex callee reference, then starts Codex through its
`Bash` tool with `run_in_background`:

```sh
codex exec --json -C . -m gpt-6-astra -c 'model_reasoning_effort="high"' \
  'Review the diff against main' < /dev/null
```

The call returns a task ID at once, so Claude fixes the test while Codex
reviews in parallel. A task notification arrives when Codex exits. Claude
reads the completed `agent_message` items from the output file, reports the
review, and keeps the thread ID so a follow-up is one `codex exec resume`.

## Capabilities

Rows are the calling harness, columns the called one. Each contains five
capabilities in a fixed order:
1. Watch live progress
2. Steer mid-turn
3. Interrupt
4. Resume a saved session 
5. Answer the child's permission prompts

- ✅ direct with the caller's own tools, verified live.
- ⚠️ works with a caveat.
- ❌ not available.

Hover an emoji for the specific reason; the caveats are also listed below.

Launch flags, an output file, and session resume cover most workflows with no
extra tooling. Mid-turn steering, interruption, and permission replies are the
advanced capabilities: they rely on protocol details that change between
releases, so expect to re-verify them.

<!-- matrix:start -->
| Caller \ Callee | Claude Code | Codex CLI | OpenCode | agy |
| --- | --- | --- | --- | --- |
| Claude Code | <abbr title="Watch (direct): stream-json with text deltas">✅</abbr><abbr title="Steer (caveat): interrupt, then send the correction in the same stdin process. Caller: Bash has no writable stdin; run the child behind a FIFO held open, recipe in the callee reference">⚠️</abbr><abbr title="Interrupt (caveat): control_request interrupt over stdin. Caller: Bash has no writable stdin; run the child behind a FIFO held open, recipe in the callee reference">⚠️</abbr><abbr title="Resume (direct): --resume SESSION_ID">✅</abbr><abbr title="Permissions (caveat): can_use_tool round-trip over stdin with --permission-prompt-tool stdio. Caller: Bash has no writable stdin; run the child behind a FIFO held open, recipe in the callee reference">⚠️</abbr> | <abbr title="Watch (direct): exec --json items, or app-server text deltas">✅</abbr><abbr title="Steer (caveat): app-server turn/steer. Caller: Bash has no writable stdin; run the child behind a FIFO held open, recipe in the callee reference">⚠️</abbr><abbr title="Interrupt (caveat): app-server turn/interrupt; the command keeps running until the server exits. Caller: Bash has no writable stdin; run the child behind a FIFO held open, recipe in the callee reference">⚠️</abbr><abbr title="Resume (direct): exec resume or thread/resume">✅</abbr><abbr title="Permissions (caveat): app-server requestApproval, accept or decline. Caller: Bash has no writable stdin; run the child behind a FIFO held open, recipe in the callee reference">⚠️</abbr> | <abbr title="Watch (direct): run --format json, or the server event stream">✅</abbr><abbr title="Steer (direct): POST prompt with delivery steer; lands after the running tool call">✅</abbr><abbr title="Interrupt (direct): POST interrupt">✅</abbr><abbr title="Resume (direct): run --session SESSION_ID">✅</abbr><abbr title="Permissions (direct): HTTP permission reply; only for sessions driven over HTTP, run auto-rejects">✅</abbr> | <abbr title="Watch (direct): stream-json text deltas">✅</abbr><abbr title="Steer (not available): headless stdin only queues the next turn">❌</abbr><abbr title="Interrupt (caveat): kill or --print-timeout only; the result still says SUCCESS, exit 0">⚠️</abbr><abbr title="Resume (direct): --conversation ID; an unknown ID silently starts a new one">✅</abbr><abbr title="Permissions (not available): headless auto-denies; TUI or remote control only">❌</abbr> |
| Codex CLI | <abbr title="Watch (caveat): stream-json with text deltas. Caller: the sandbox has no network; grant it or run the child outside the sandbox">⚠️</abbr><abbr title="Steer (caveat): interrupt, then send the correction in the same stdin process. Caller: the sandbox has no network; grant it or run the child outside the sandbox; write_stdin can send text per its schema, untested live">⚠️</abbr><abbr title="Interrupt (caveat): control_request interrupt over stdin. Caller: the sandbox has no network; grant it or run the child outside the sandbox; write_stdin can send text per its schema, untested live">⚠️</abbr><abbr title="Resume (caveat): --resume SESSION_ID. Caller: the sandbox has no network; grant it or run the child outside the sandbox">⚠️</abbr><abbr title="Permissions (caveat): can_use_tool round-trip over stdin with --permission-prompt-tool stdio. Caller: the sandbox has no network; grant it or run the child outside the sandbox; write_stdin can send text per its schema, untested live">⚠️</abbr> | <abbr title="Watch (caveat): exec --json items, or app-server text deltas. Caller: the sandbox has no network; grant it or run the child outside the sandbox">⚠️</abbr><abbr title="Steer (caveat): app-server turn/steer. Caller: the sandbox has no network; grant it or run the child outside the sandbox; write_stdin can send text per its schema, untested live">⚠️</abbr><abbr title="Interrupt (caveat): app-server turn/interrupt; the command keeps running until the server exits. Caller: the sandbox has no network; grant it or run the child outside the sandbox; write_stdin can send text per its schema, untested live">⚠️</abbr><abbr title="Resume (caveat): exec resume or thread/resume. Caller: the sandbox has no network; grant it or run the child outside the sandbox">⚠️</abbr><abbr title="Permissions (caveat): app-server requestApproval, accept or decline. Caller: the sandbox has no network; grant it or run the child outside the sandbox; write_stdin can send text per its schema, untested live">⚠️</abbr> | <abbr title="Watch (caveat): run --format json, or the server event stream. Caller: the sandbox has no network; grant it or run the child outside the sandbox">⚠️</abbr><abbr title="Steer (caveat): POST prompt with delivery steer; lands after the running tool call. Caller: the sandbox has no network; grant it or run the child outside the sandbox">⚠️</abbr><abbr title="Interrupt (caveat): POST interrupt. Caller: the sandbox has no network; grant it or run the child outside the sandbox">⚠️</abbr><abbr title="Resume (caveat): run --session SESSION_ID. Caller: the sandbox has no network; grant it or run the child outside the sandbox">⚠️</abbr><abbr title="Permissions (caveat): HTTP permission reply; only for sessions driven over HTTP, run auto-rejects. Caller: the sandbox has no network; grant it or run the child outside the sandbox">⚠️</abbr> | <abbr title="Watch (caveat): stream-json text deltas. Caller: the sandbox has no network; grant it or run the child outside the sandbox">⚠️</abbr><abbr title="Steer (not available): headless stdin only queues the next turn">❌</abbr><abbr title="Interrupt (caveat): kill or --print-timeout only; the result still says SUCCESS, exit 0. Caller: the sandbox has no network; grant it or run the child outside the sandbox">⚠️</abbr><abbr title="Resume (caveat): --conversation ID; an unknown ID silently starts a new one. Caller: the sandbox has no network; grant it or run the child outside the sandbox">⚠️</abbr><abbr title="Permissions (not available): headless auto-denies; TUI or remote control only">❌</abbr> |
| OpenCode | <abbr title="Watch (direct): stream-json with text deltas">✅</abbr><abbr title="Steer (caveat): interrupt, then send the correction in the same stdin process. Caller: shell has no stdin channel; a FIFO held open should work, untested from shell">⚠️</abbr><abbr title="Interrupt (caveat): control_request interrupt over stdin. Caller: shell has no stdin channel; a FIFO held open should work, untested from shell">⚠️</abbr><abbr title="Resume (direct): --resume SESSION_ID">✅</abbr><abbr title="Permissions (caveat): can_use_tool round-trip over stdin with --permission-prompt-tool stdio. Caller: shell has no stdin channel; a FIFO held open should work, untested from shell">⚠️</abbr> | <abbr title="Watch (direct): exec --json items, or app-server text deltas">✅</abbr><abbr title="Steer (caveat): app-server turn/steer. Caller: shell has no stdin channel; a FIFO held open should work, untested from shell">⚠️</abbr><abbr title="Interrupt (caveat): app-server turn/interrupt; the command keeps running until the server exits. Caller: shell has no stdin channel; a FIFO held open should work, untested from shell">⚠️</abbr><abbr title="Resume (direct): exec resume or thread/resume">✅</abbr><abbr title="Permissions (caveat): app-server requestApproval, accept or decline. Caller: shell has no stdin channel; a FIFO held open should work, untested from shell">⚠️</abbr> | <abbr title="Watch (direct): run --format json, or the server event stream">✅</abbr><abbr title="Steer (direct): POST prompt with delivery steer; lands after the running tool call">✅</abbr><abbr title="Interrupt (direct): POST interrupt">✅</abbr><abbr title="Resume (direct): run --session SESSION_ID">✅</abbr><abbr title="Permissions (direct): HTTP permission reply; only for sessions driven over HTTP, run auto-rejects">✅</abbr> | <abbr title="Watch (direct): stream-json text deltas">✅</abbr><abbr title="Steer (not available): headless stdin only queues the next turn">❌</abbr><abbr title="Interrupt (caveat): kill or --print-timeout only; the result still says SUCCESS, exit 0">⚠️</abbr><abbr title="Resume (direct): --conversation ID; an unknown ID silently starts a new one">✅</abbr><abbr title="Permissions (not available): headless auto-denies; TUI or remote control only">❌</abbr> |
| agy | <abbr title="Watch (direct): stream-json with text deltas">✅</abbr><abbr title="Steer (caveat): interrupt, then send the correction in the same stdin process. Caller: manage_task send_input writes lines; driving a JSON protocol this way is untested">⚠️</abbr><abbr title="Interrupt (caveat): control_request interrupt over stdin. Caller: manage_task send_input writes lines; driving a JSON protocol this way is untested">⚠️</abbr><abbr title="Resume (direct): --resume SESSION_ID">✅</abbr><abbr title="Permissions (caveat): can_use_tool round-trip over stdin with --permission-prompt-tool stdio. Caller: manage_task send_input writes lines; driving a JSON protocol this way is untested">⚠️</abbr> | <abbr title="Watch (direct): exec --json items, or app-server text deltas">✅</abbr><abbr title="Steer (caveat): app-server turn/steer. Caller: manage_task send_input writes lines; driving a JSON protocol this way is untested">⚠️</abbr><abbr title="Interrupt (caveat): app-server turn/interrupt; the command keeps running until the server exits. Caller: manage_task send_input writes lines; driving a JSON protocol this way is untested">⚠️</abbr><abbr title="Resume (direct): exec resume or thread/resume">✅</abbr><abbr title="Permissions (caveat): app-server requestApproval, accept or decline. Caller: manage_task send_input writes lines; driving a JSON protocol this way is untested">⚠️</abbr> | <abbr title="Watch (direct): run --format json, or the server event stream">✅</abbr><abbr title="Steer (direct): POST prompt with delivery steer; lands after the running tool call">✅</abbr><abbr title="Interrupt (direct): POST interrupt">✅</abbr><abbr title="Resume (direct): run --session SESSION_ID">✅</abbr><abbr title="Permissions (direct): HTTP permission reply; only for sessions driven over HTTP, run auto-rejects">✅</abbr> | <abbr title="Watch (direct): stream-json text deltas">✅</abbr><abbr title="Steer (not available): headless stdin only queues the next turn">❌</abbr><abbr title="Interrupt (caveat): kill or --print-timeout only; the result still says SUCCESS, exit 0">⚠️</abbr><abbr title="Resume (direct): --conversation ID; an unknown ID silently starts a new one">✅</abbr><abbr title="Permissions (not available): headless auto-denies; TUI or remote control only">❌</abbr> |
<!-- matrix:end -->

Caveats:

- Claude Code and Codex are controlled over a stdin JSON protocol. A caller's
  shell tool has no writable stdin, so run the child behind a FIFO held open;
  the callee references give the one-line recipe. Verified from Claude Code,
  untested from OpenCode's shell. The agy caller can write lines, but driving
  a JSON protocol that way is untested.
- Codex's sandbox has no network, so any child harness fails until network is
  granted or the child runs outside the sandbox.
- agy has no mid-turn steering or permission replies in headless mode;
  interrupt means killing the process or a timeout, and the result still says
  `SUCCESS`.
- Targeted messages back from the child are a prompt convention in every cell:
  ask for a marker line or a status file and let a watcher forward matches.

## Develop

The repo-local
[refresh skill](.agents/skills/refresh-subharness/SKILL.md) describes
manual research and smoke tests. It is a development tool, not part of the
installable skill. Ask an agent working in this repo to "refresh subharness for
Claude Code", or to refresh all four.

We target current stable releases. Version/date evidence belongs in
[verification notes](docs/verification.md), not runtime version gates. Tests
use small tasks and inexpensive available models. Documentation and actual
observations are distinguished; untested interaction paths are labeled.
