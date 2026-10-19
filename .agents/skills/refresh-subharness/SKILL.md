---
name: refresh-subharness
description: >-
  Maintain this repository's subharness skill. Manually refresh selected
  harness references from current first-party documentation, local CLI help,
  and small live tests. Repository development only; not a user-facing runtime
  skill.
---

# Refresh subharness

Work on the requested harnesses in `skills/subharness/`. This is a manual
maintenance procedure. There is no watcher, release monitor, or CI requirement.

## Research only what changed

1. Read the callee and caller references for each selected harness, plus
   `docs/verification.md`. Follow their first-party documentation links. Use the
   documentation index, release notes, command help, or official source if a page
   moved or omits a wire format. Prefer agent-readable Markdown when available.
2. Capture `--version` and relevant subcommand help as maintenance evidence.
   Target current stable behavior. Do not add backward-compatibility matrices,
   runtime version checks, or install/update steps to user-facing references.
   Record a local testing mismatch without turning it into a compatibility task.
3. Check both directions: CLI launch/control as callee, and actual shell/process
   tools as caller. Distinguish agent tools from TUI controls, SDK/client APIs,
   IDE features, and experimental source. Never infer writable stdin or live
   steering merely from streaming output.

## Small live checks

Use an isolated temporary directory and the user's existing authentication.
Choose a cheap available model explicitly. Use short prompts and a finite process
deadline. Do not change global configuration or install dependencies. If a test
needs a package, use an isolated project/environment; Python work uses `uv`.

Exercise the changed capabilities, not every model or every caller/callee pair:

| Check | Observable result |
| --- | --- |
| Launch and progress | A short marker reply; events arrive before the final result |
| Activity | A harmless command or temporary-file operation exposes tool/status events |
| Warm follow-up | First turn remembers a marker; next turn recalls it in the same process |
| Active steering | Observe work in progress, submit a correction through the documented control surface, verify its receipt/effect |
| Interrupt | Explicit interrupt acknowledged; terminal state distinguishable from success |
| Resume | Stop the owned process, start another with the saved session ID, recall the marker |
| Denial/failure | An unavailable approval or rejected action produces observable diagnostic/result state |
| Caller process tools | Harmless child produces progress and accepts input if that tool claims to support it |

Keep stdout events and stderr separate. Read selected event fields rather than
reasoning/full transcripts. Track and clean up only test-owned processes and
servers. Preserve existing user sessions and configuration. A permission/auth
failure is a test outcome, not a reason to remove restrictions silently.

If a failure becomes an investigation, give a subagent the command, logs, and
expected behavior where delegation is available. Return a short diagnosis. An
untested or blocked feature should be labeled, not promoted to a guarantee.

## Update and check

- Edit the relevant reference and any affected routing/examples. Keep useful
  options, observation, input, interruption/resume, pitfalls, and primary links.
  Describe capabilities without assigning roles or requiring oversight/review.
- Record date, tested version/model, checks, and remaining gaps in
  `docs/verification.md`. Do not commit raw transcripts, auth data, session IDs,
  temporary helper scripts, or copied manuals.
- If a capability or caveat changed, update the data blocks in `docs/matrix.py`
  and run `uv run --no-project python -I docs/matrix.py` to regenerate the
  README matrix.
- Check relative links, frontmatter, example syntax/flags, and source links.
  Use an available skill validator if useful; do not add dependencies just for
  Markdown checks. For a substantial protocol change, a fresh agent trying the
  written example can expose missing steps.
- Make an atomic conventional commit with terse bullet points in the body.
  Summarize behavior changes and what was tested. Stop after the relevant checks
  pass; no broad testing campaign is needed.
