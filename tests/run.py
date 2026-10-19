#!/usr/bin/env python3
"""Scenario runner for the subharness skill. See tests/README.md.

prepare  make a work dir with the skill installed and print the prompt
launch   run the caller headless on a prepared run
check    verify artifacts and the callee's session log
run      prepare + launch + check
matrix   run every selected cell, then print the grid
grid     print the latest result per cell from past runs
clean    kill leftover processes and delete the work dir
"""
import argparse
import json
import os
import random
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from harnesses import HARNESSES  # noqa: E402
from scenarios import SCENARIOS, Ctx  # noqa: E402

RUNS = HERE / ".runs"
WORK_ROOT = Path(os.environ.get("SUBHARNESS_TEST_ROOT", "/tmp/subharness-tests"))
SELF = f"uv run --no-project python -I {HERE.relative_to(Path.cwd()) if HERE.is_relative_to(Path.cwd()) else HERE}/run.py"


def state_path(run_id):
    return RUNS / run_id / "state.json"


def load(run_id):
    return json.loads(state_path(run_id).read_text())


def save(st):
    state_path(st["id"]).parent.mkdir(parents=True, exist_ok=True)
    state_path(st["id"]).write_text(json.dumps(st, indent=1))


def word():
    """A pronounceable six-letter word, new for every run."""
    return "".join(random.choice("BDFGKLMNPRSTVZ" if i % 2 == 0 else "AEIOU") for i in range(6))


def procs_in(root):
    """PIDs whose cwd is under root (the caller's and callee's leftovers)."""
    out = []
    for p in os.listdir("/proc"):
        if p.isdigit() and int(p) != os.getpid():
            try:
                if os.readlink(f"/proc/{p}/cwd").startswith(root):
                    out.append(int(p))
            except OSError:
                pass
    return out


def prepare(caller, callee, scenario, callee_model=None, quiet=False):
    run_id = f"{scenario}-{caller}-{callee}-{time.strftime('%m%d-%H%M%S')}"
    work = WORK_ROOT / run_id
    child = work / "child"
    child.mkdir(parents=True)
    shutil.copytree(HERE.parent / "skills" / "subharness", work / HARNESSES[caller].skill_dir / "subharness")
    c = HARNESSES[callee]
    words = {"password": word(), "code": word()}
    prompt = SCENARIOS[scenario].prompt.format(callee=c.name, model=callee_model or c.model, child=child, work=work,
                                               **words)
    st = dict(id=run_id, caller=caller, callee=callee, scenario=scenario, work=str(work), child=str(child),
              since=time.time(), words=words, prompt=prompt)
    save(st)
    if not quiet:
        print(f"run id:   {run_id}\nwork dir: {work}\n\nStart {HARNESSES[caller].name} interactively in the "
              f"work dir and paste this prompt:\n\n{prompt}\nThen: {SELF} check {run_id}\n")
    return st


def launch(st, caller_model=None, timeout=1200):
    h = HARNESSES[st["caller"]]
    out = state_path(st["id"]).parent
    with open(out / "caller.out", "wb") as o, open(out / "caller.err", "wb") as e:
        p = subprocess.Popen(h.caller_cmd(st["prompt"], caller_model or h.model), cwd=st["work"],
                             stdin=subprocess.DEVNULL, stdout=o, stderr=e, start_new_session=True)
        try:
            rc = p.wait(timeout)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            rc = "timeout"
    st["caller_rc"] = rc
    st["caller_text"] = h.final_text((out / "caller.out").read_text(errors="replace"))
    st["headless"] = True
    save(st)
    print(f"caller exited: {rc}")


def check(st):
    ctx = Ctx(work=st["work"], child=st["child"], since=st["since"], words=st["words"],
              sessions=HARNESSES[st["callee"]].sessions, caller_text=st.get("caller_text"))
    SCENARIOS[st["scenario"]].check(ctx)
    if st.get("headless"):
        left = procs_in(st["work"])
        ctx.cap = "cleanup"
        ctx.add("no leftover processes in the work dir", not left, " ".join(map(str, left[:8])))
    st["checks"] = [c.__dict__ for c in ctx.checks]
    st["passed"] = all(c.ok for c in ctx.checks)
    save(st)
    for c in ctx.checks:
        print(("PASS " if c.ok else "FAIL ") + c.name + (f"  | {c.detail}" if c.detail else ""))
    print("RESULT", "PASS" if st["passed"] else "FAIL", st["id"])
    return st["passed"]


def clean(st):
    for pid in procs_in(st["work"]):
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
    shutil.rmtree(st["work"], ignore_errors=True)


def grid(scenarios=None):
    """Latest result per cell: 'pass', or the capabilities with a failed check."""
    latest = {}
    for p in sorted(RUNS.glob("*/state.json")):
        st = json.loads(p.read_text())
        if "checks" in st:
            failed = sorted({c["name"].split(":")[0] for c in st["checks"] if not c["ok"]})
            latest[(st["scenario"], st["caller"], st["callee"])] = " ".join("-" + f for f in failed) or "pass"
    keys = list(HARNESSES)
    for s in scenarios or SCENARIOS:
        print(f"\n{s:10}" + "".join(f"{k:>18}" for k in keys) + "   (rows: caller, columns: callee)")
        for a in keys:
            print(f"{a:10}" + "".join(f"{latest.get((s, a, b), '.'):>18}" for b in keys))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("prepare", "run", "matrix"):
        q = sub.add_parser(name)
        q.add_argument("--caller", nargs="+", default=list(HARNESSES) if name == "matrix" else None,
                       choices=list(HARNESSES), required=name != "matrix")
        q.add_argument("--callee", nargs="+", default=list(HARNESSES) if name == "matrix" else None,
                       choices=list(HARNESSES), required=name != "matrix")
        q.add_argument("--scenario", nargs="+", default=list(SCENARIOS) if name == "matrix" else None,
                       choices=list(SCENARIOS), required=name != "matrix")
        q.add_argument("--callee-model")
        if name != "prepare":
            q.add_argument("--caller-model")
            q.add_argument("--timeout", type=int, default=1200)
            q.add_argument("--keep", action="store_true", help="keep work dirs after the check")
    for name in ("launch", "check", "clean"):
        q = sub.add_parser(name)
        q.add_argument("run_id")
        if name == "launch":
            q.add_argument("--caller-model")
            q.add_argument("--timeout", type=int, default=1200)
    sub.add_parser("grid").add_argument("--scenario", nargs="+", choices=list(SCENARIOS))
    a = ap.parse_args()

    if a.cmd == "prepare":
        prepare(a.caller[0], a.callee[0], a.scenario[0], a.callee_model)
    elif a.cmd == "launch":
        launch(load(a.run_id), a.caller_model, a.timeout)
    elif a.cmd == "check":
        sys.exit(0 if check(load(a.run_id)) else 1)
    elif a.cmd == "clean":
        clean(load(a.run_id))
    elif a.cmd == "grid":
        grid(a.scenario)
    else:
        for s in a.scenario:
            for caller in a.caller:
                for callee in a.callee:
                    st = prepare(caller, callee, s, a.callee_model, quiet=True)
                    print(f"\n=== {st['id']}")
                    launch(st, a.caller_model, a.timeout)
                    check(st)
                    if not a.keep:
                        clean(st)
        if a.cmd == "matrix":
            grid(a.scenario)


if __name__ == "__main__":
    main()
