# Scenario tests

Two scenarios, one per path of the skill, run against any caller and callee
pair. A scenario is a numbered prompt for the caller plus checks. The prompt
names the callee, its model, and the tasks; it never states a pass criterion.
The checks read files in the work dir and the callee's own session log, so
neither agent's self-report counts. Each check is tagged with the capability
it judges, and the grid names the failed capabilities per cell.

| Scenario | Capabilities | The caller must |
| --- | --- | --- |
| `basic` | launch, watch, resume | start the callee in the background, work while it runs, read its output, then resume the finished session |
| `live` | permissions, steer, interrupt, followup | keep one channel open: approve one command and refuse another, deliver a message mid-turn, stop a running command, then continue the session |

Callee tasks are one or two shell commands with exact file names and
contents. The password and the code word are random per run.

## Isolation

`prepare` makes `/tmp/subharness-tests/RUN_ID` with the skill copied into the
caller's project skill dir, plus an empty `child` dir for the callee. Nothing
else is in it. Scenario texts and checks stay in this repo, which the caller
never sees. Run state and the caller's headless output go to `tests/.runs/`.

## Manual mode

```sh
uv run --no-project python -I tests/run.py prepare --caller claude --callee codex --scenario steer
```

It prints the work dir and the prompt. Open the caller interactively in the
work dir, accept its trust prompt if it shows one, paste the prompt, wait,
then run the printed `check` command. `clean RUN_ID` kills leftover
processes in the work dir and deletes it.

## Headless mode

```sh
uv run --no-project python -I tests/run.py run --caller claude --callee codex --scenario steer
uv run --no-project python -I tests/run.py matrix --scenario launch resume
uv run --no-project python -I tests/run.py grid
```

`run` chains prepare, launch, check, clean. `matrix` does that for every
selected cell and prints a grid; `grid` reprints the latest result per cell.
The headless caller runs with permissions off and a cheap model
(`--caller-model` and `--callee-model` override). That differs from an
interactive caller, so when headless and manual disagree, manual is the
reference. A failing cell is one run of a nondeterministic agent: rerun it
once before treating it as a defect in that pair's reference.

Known constraints: Codex as caller runs outside its sandbox so the child can
reach the network; agy as callee is headless unless the test is manual and the
work dir is trusted.
