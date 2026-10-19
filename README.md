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

Rows are the calling harness, columns the called one. Each cell lists five
capabilities in a fixed order:

`W` watch live progress, `S` steer mid-turn, `I` interrupt, `R` resume a saved
session, `P` answer the child's permission prompts.

Uppercase: direct with the caller's own tools, verified live. Lowercase: works
with a caveat, listed below. `-`: not available.

| Caller \ Callee | Claude Code | Codex CLI | OpenCode | agy |
| --- | --- | --- | --- | --- |
| Claude Code | `W s i R p` | `W s i R p` | `W S I R P` | `W - i R -` |
| Codex CLI | `w S I R P` | `w S I R P` | `w s i R p` | `w - i R -` |
| OpenCode | `W s i R p` | `W s i R p` | `W S I R P` | `W - i R -` |
| agy | `W s i R p` | `W s i R p` | `W S I R P` | `W - i R -` |

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
