"""Scenario definitions for the subharness tests.

Each scenario is a prompt for the caller plus a check over the artifacts in
the work dir and the callee's own session log. Prompts carry the task only,
never a pass criterion. Template fields: {callee} (display name), {model}
(callee model), {child} (absolute callee dir), {work} (absolute caller dir).
"""
import os
import time
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class Ctx:
    work: str
    child: str
    since: float
    sessions: Callable[[str, float], list]  # callee adapter: (cwd_dir, since) -> sessions
    caller_text: str | None = None  # final caller output in headless mode
    checks: list = field(default_factory=list)

    def add(self, name, ok, detail=""):
        self.checks.append(Check(name, bool(ok), detail))
        return bool(ok)

    # file helpers
    def path(self, name, where="child"):
        return os.path.join(self.child if where == "child" else self.work, name)

    def read(self, name, where="child"):
        p = self.path(name, where)
        if not os.path.isfile(p):
            return None
        with open(p, "rb") as f:
            return f.read().decode("utf-8", "replace")

    def line(self, name, where="child"):
        t = self.read(name, where)
        return None if t is None else t.strip()

    def mtime(self, name, where="child"):
        p = self.path(name, where)
        return os.path.getmtime(p) if os.path.exists(p) else None

    def file_is(self, name, expected, where="child"):
        got = self.line(name, where)
        return self.add(f"{name} == {expected}", got is not None and got.upper() == expected.upper(),
                        "missing" if got is None else repr(got[:60]))

    # session helpers
    def all_sessions(self):
        try:
            return self.sessions(self.child, self.since)
        except Exception as ex:  # adapter failure is a check failure, not a crash
            self.add("session store readable", False, repr(ex)[:200])
            return []

    def task_session(self, phrase):
        """The callee session whose user input contains the phrase."""
        found = [s for s in self.all_sessions()
                 if any(e["kind"] == "user" and phrase.lower() in e["text"].lower() for e in s["events"])]
        self.add(f"callee session with task ({phrase[:30]}...)", bool(found),
                 f"{len(found)} match(es) of {len(self.all_sessions())} session(s) in child")
        return found[0] if found else None

    def users(self, session):
        return [e for e in session["events"] if e["kind"] == "user"]

    def session_reported(self, session):
        if self.caller_text is None:
            self.add("caller reported session id", True, "manual mode: not checked")
            return
        self.add("caller reported session id", session["session_id"] in self.caller_text,
                 session["session_id"])


@dataclass
class Scenario:
    key: str
    capability: str
    prompt: str
    check: Callable[[Ctx], None]


def common_mtime(ctx, early, late, where_early, where_late, name):
    a, b = ctx.mtime(early, where_early), ctx.mtime(late, where_late)
    ok = a is not None and b is not None and a < b
    return ctx.add(name, ok, f"{early}={a and round(a - ctx.since, 1)}s {late}={b and round(b - ctx.since, 1)}s")


# --- launch -----------------------------------------------------------------

LAUNCH_PROMPT = """\
Use {callee} with model {model} to run a task in the directory {child}. \
Start it in the background so that you can keep working while it runs. \
Give it exactly this task:

"Run the shell command `sleep 20`. Then create a file named callee.txt in the current directory containing the single line PARALLEL."

While it is running, create caller.txt in {work} containing the single line BUSY. \
Then wait for {callee} to finish. Finally, tell me its session id (thread or conversation id) so that I can come back to it later and the last thing it said.
"""


def check_launch(ctx):
    ctx.file_is("callee.txt", "PARALLEL")
    ctx.file_is("caller.txt", "BUSY", "work")
    common_mtime(ctx, "caller.txt", "callee.txt", "work", "child", "caller.txt written before callee.txt")
    s = ctx.task_session("sleep 20")
    if s:
        # parallel: caller.txt appears during the callee's sleep, not before the callee started
        cm = ctx.mtime("caller.txt", "work")
        ctx.add("caller.txt written after the callee started", cm is not None and cm >= s["started"] - 5,
                f"caller.txt at +{cm and round(cm - ctx.since, 1)}s, callee started at +{round(s['started'] - ctx.since, 1)}s")
        ctx.session_reported(s)


# --- watch ------------------------------------------------------------------

WATCH_PROMPT = """\
Use {callee} with model {model} to run a task in the directory {child}, in the background \
so that you can keep working while it runs. Give it exactly this task:

"Say a made-up six-letter code word. Then run the shell command `sleep 20`. Then say a second made-up code word. Then run `sleep 20`. Then say a third made-up code word. Finally create a file named words.txt in the current directory containing the three words, one per line, in order."

While it is running, watch its output. As soon as you have seen at least one code word, \
write the latest code word you have seen to progress.txt in {work}. \
Then wait for {callee} to finish and tell me its session id (thread or conversation id) so that I can come back to it later and the three words.
"""


def check_watch(ctx):
    words = [w.strip().upper() for w in (ctx.read("words.txt") or "").splitlines() if w.strip()]
    ctx.add("words.txt has three words", len(words) == 3, repr(words))
    got = (ctx.line("progress.txt", "work") or "").upper()
    ctx.add("progress.txt holds one of the callee's words", bool(got) and got in words, repr(got[:40]))
    common_mtime(ctx, "progress.txt", "words.txt", "work", "child", "progress.txt written before words.txt")
    s = ctx.task_session("code word")
    if s:
        ctx.session_reported(s)


# --- steer ------------------------------------------------------------------

STEER_PROMPT = """\
Use {callee} with model {model} to run a task in the directory {child}. \
Start it in a way that lets you send it another message while it is still working on this task. \
Give it exactly this task:

"Create a file named a.txt containing the single line START. Then run the shell command `sleep 45`. Then create b.txt containing the code word that I will send you while you are working; if no code word has arrived, write DEFAULT. Never modify b.txt after creating it. Then say which word you wrote."

As soon as a.txt exists, send {callee} this message: "The code word is MARMOT". \
Then wait for it to finish and tell me its session id (thread or conversation id) so that I can come back to it later and what it said.
"""


def check_steer(ctx):
    ctx.file_is("a.txt", "START")
    ctx.file_is("b.txt", "MARMOT")
    s = ctx.task_session("sleep 45")
    if s:
        us = ctx.users(s)
        marmot = [u for u in us if "MARMOT" in u["text"].upper()]
        ctx.add("MARMOT message in the same callee session", bool(marmot), f"{len(us)} user message(s)")
        bm = ctx.mtime("b.txt")
        if marmot and bm:
            ctx.add("MARMOT arrived before b.txt was written", marmot[0]["ts"] < bm,
                    f"message at +{round(marmot[0]['ts'] - ctx.since, 1)}s, b.txt at +{round(bm - ctx.since, 1)}s")
        ctx.session_reported(s)


# --- interrupt --------------------------------------------------------------

INTERRUPT_PROMPT = """\
Use {callee} with model {model} to run a task in the directory {child}. \
Start it in a way that lets you stop it while it is working. Give it exactly this task:

"Count from 1 to 300. For each number, append it as a line to counter.txt in the current directory and then run the shell command `sleep 1`. When you reach 300, say FINISHED."

Watch counter.txt. Once it has at least 5 lines, stop {callee} immediately and make sure it is no longer counting. \
Then, in that same {callee} session, ask it exactly: "What was the last number you appended? Reply with just the number." \
Write its reply to reached.txt in {work}, and tell me its session id (thread or conversation id) so that I can come back to it later.
"""


def check_interrupt(ctx):
    lines = [l for l in (ctx.read("counter.txt") or "").splitlines() if l.strip()]
    n1 = len(lines)
    time.sleep(3)
    n2 = len([l for l in (ctx.read("counter.txt") or "").splitlines() if l.strip()])
    ctx.add("counter.txt stopped between 5 and 299 lines", 5 <= n1 < 300, f"{n1} lines")
    ctx.add("counter.txt no longer growing", n1 == n2, f"{n1} then {n2} lines after 3 s")
    last = lines[-1].strip() if lines else None
    got = ctx.line("reached.txt", "work")
    try:
        ok = last is not None and got is not None and abs(int(got) - int(last)) <= 1
    except ValueError:
        ok = False
    ctx.add("reached.txt matches the last counter line", ok, f"reached={got!r} last={last!r}")
    s = ctx.task_session("Count from 1 to 300")
    if s:
        us = ctx.users(s)
        ctx.add("follow-up question in the same callee session",
                any("last number" in u["text"].lower() for u in us[1:]), f"{len(us)} user message(s)")
        ctx.session_reported(s)


# --- resume -----------------------------------------------------------------

RESUME_PROMPT = """\
Use {callee} with model {model} to run a task in the directory {child}, and let it finish. \
Give it exactly this task:

"Remember this code word: FALCON. Create a file named note.txt in the current directory containing the single line READY, then say OK."

After it has finished and exited, resume that same {callee} session and ask it exactly: \
"What was the code word I gave you earlier? Reply with just the word." \
Write its reply to recall.txt in {work}, and tell me its session id (thread or conversation id) so that I can come back to it later.
"""


def check_resume(ctx):
    ctx.file_is("note.txt", "READY")
    ctx.file_is("recall.txt", "FALCON", "work")
    s = ctx.task_session("FALCON")
    if s:
        us = ctx.users(s)
        q = [u for u in us[1:] if "code word" in u["text"].lower()]
        ctx.add("question asked in the same callee session", bool(q), f"{len(us)} user message(s)")
        if q:
            ctx.add("question does not repeat the code word", "FALCON" not in q[0]["text"].upper())
        others = [x for x in ctx.all_sessions() if x["session_id"] != s["session_id"]
                  and any(e["kind"] == "user" and "code word" in e["text"].lower() for e in x["events"])]
        ctx.add("no fresh callee session asked instead", not others, f"{len(others)} other session(s)")
        ctx.session_reported(s)


# --- permissions ------------------------------------------------------------

PERMISSIONS_PROMPT = """\
Use {callee} with model {model} to run a task in the directory {child}. \
Start it in a mode where it must ask for permission before each shell command, \
so that you can answer its permission requests yourself. Give it exactly this task:

"Run the shell command `touch allowed.txt`. Then run the shell command `touch denied.txt`. Then say which of the two commands ran."

Approve the first command and refuse the second. \
Then tell me its session id (thread or conversation id) so that I can come back to it later and what it said.
"""


def check_permissions(ctx):
    ctx.add("allowed.txt exists", os.path.exists(ctx.path("allowed.txt")))
    ctx.add("denied.txt absent", not os.path.exists(ctx.path("denied.txt")))
    s = ctx.task_session("touch allowed.txt")
    if s:
        cmds = [e for e in s["events"] if e["kind"] == "command"]
        if cmds:
            ctx.add("callee ran touch allowed.txt", any("allowed.txt" in c["text"] for c in cmds),
                    f"{len(cmds)} command(s) logged")
        ctx.session_reported(s)


SCENARIOS = {
    s.key: s for s in [
        Scenario("launch", "Launch", LAUNCH_PROMPT, check_launch),
        Scenario("watch", "Watch", WATCH_PROMPT, check_watch),
        Scenario("steer", "Steer", STEER_PROMPT, check_steer),
        Scenario("interrupt", "Interrupt", INTERRUPT_PROMPT, check_interrupt),
        Scenario("resume", "Resume", RESUME_PROMPT, check_resume),
        Scenario("permissions", "Permissions", PERMISSIONS_PROMPT, check_permissions),
    ]
}
