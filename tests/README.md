# Scenario tests

Six scenarios, one per capability, run against any caller and callee pair.
A scenario is a prompt for the caller plus a check. The prompt names the
callee, its model, and the task; it never states a pass criterion. The check
reads files in the work dir and the callee's own session log, so neither
agent's self-report counts.

| Scenario | The caller must |
| --- | --- |
| `launch` | start the callee in the background and work while it runs |
| `watch` | read the callee's output while it runs |
| `steer` | deliver a message into the callee's running turn |
| `interrupt` | stop the callee mid-task, then continue the same session |
| `resume` | resume a finished callee session |
| `permissions` | approve one callee command and refuse another |

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
