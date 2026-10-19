# Harness use

Markdown skills for using another AI harness like a subagent, consultant, peer,
or interactive assistant. We call that external agent a **subharness**.

Supports Claude Code, Codex CLI, OpenCode, and Antigravity CLI (`agy`) on Linux.
Focus: launch options, cheap live progress, steering, interruption, and resume.
No runtime wrapper, dependencies, prescribed delegation roles, or mandatory
oversight workflow.

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
