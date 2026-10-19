"""Scenario definitions for the subharness tests.

Two bundles, one per path of the skill. Each is a numbered prompt for the
caller plus checks over the work dir and the callee's own session log.
Prompts carry the task only, never a pass criterion. Every check is tagged
with the capability it judges. Template fields: {callee} (display name),
{model} (callee model), {child} (absolute callee dir), {work} (absolute
caller dir), {password} and {code} (random words made per run).
"""
import os
import time
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Check:
    name: str  # "capability: what"
    ok: bool
    detail: str = ""


@dataclass
class Ctx:
    work: str
    child: str
    since: float
    words: dict  # the random words substituted into the prompt
    sessions: Callable[[str, float], list]  # callee adapter: (cwd_dir, since) -> sessions
    caller_text: str | None = None  # final caller output in headless mode
    checks: list = field(default_factory=list)
    cap: str = "run"

    def add(self, name, ok, detail=""):
        self.checks.append(Check(f"{self.cap}: {name}", bool(ok), detail))
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

    def lines(self, name, where="child"):
        return [l.strip() for l in (self.read(name, where) or "").splitlines() if l.strip()]

    def mtime(self, name, where="child"):
        p = self.path(name, where)
        return os.path.getmtime(p) if os.path.exists(p) else None

    def rel(self, t):
        return None if t is None else f"+{t - self.since:.1f}s"

    def file_is(self, name, expected, where="child"):
        got = self.line(name, where)
        return self.add(f"{name} == {expected}", got is not None and got.upper() == expected.upper(),
                        "missing" if got is None else repr(got[:60]))

    def before(self, early, late, where_early="work", where_late="child"):
        a, b = self.mtime(early, where_early), self.mtime(late, where_late)
        return self.add(f"{early} written before {late}", a is not None and b is not None and a < b,
                        f"{early} {self.rel(a)}, {late} {self.rel(b)}")

    # session helpers
    def all_sessions(self):
        try:
            return self.sessions(self.child, self.since)
        except Exception as ex:  # an adapter failure is a check failure, not a crash
            self.add("session store readable", False, repr(ex)[:200])
            return []

    def task_session(self, phrase):
        """The callee session whose user input contains the phrase."""
        self.cap = "session"
        found = [s for s in self.all_sessions()
                 if any(e["kind"] == "user" and phrase.lower() in e["text"].lower() for e in s["events"])]
        self.add(f"callee session with the task ({phrase[:30]})", bool(found),
                 f"{len(found)} match(es) of {len(self.all_sessions())} session(s) in child")
        return found[0] if found else None

    def users(self, session):
        return [e for e in session["events"] if e["kind"] == "user"]

    def asked_in(self, session, phrase):
        """The follow-up with the phrase is in this session and in no other."""
        us = self.users(session)
        q = [u for u in us[1:] if phrase in u["text"].lower()]
        self.add(f"'{phrase}' asked in the same callee session", bool(q), f"{len(us)} user message(s)")
        others = [x for x in self.all_sessions() if x["session_id"] != session["session_id"]
                  and any(e["kind"] == "user" and phrase in e["text"].lower() for e in x["events"])]
        self.add("not asked in a fresh callee session instead", not others, f"{len(others)} other session(s)")
        return q[0] if q else None

    def session_reported(self, session):
        self.cap = "report"
        if self.caller_text is None:
            self.add("caller reported the session id", True, "manual mode: not checked")
        else:
            self.add("caller reported the session id", session["session_id"] in self.caller_text,
                     session["session_id"])


@dataclass
class Scenario:
    key: str
    capabilities: str
    prompt: str
    check: Callable[[Ctx], None]


# --- basic: launch, watch, resume (no input channel needed) ------------------

BASIC_PROMPT = """\
Use {callee} with model {model} to run a task in the directory {child}. Do these steps in order.

1. Start it in the background so that you can keep working while it runs, and give it exactly this task:
   "Remember this password: {password}. Say a made-up six-letter word. Then run the shell command `sleep 20`. Then say a second made-up six-letter word. Then create a file named words.txt in the current directory containing the two words, one per line."
2. While it is running, create caller.txt in {work} containing the single line BUSY.
3. While it is still running, read its output. As soon as it has said a word, write that word to progress.txt in {work}.
4. Wait for it to finish and exit.
5. Resume that same {callee} session and ask it exactly: "What was the password I gave you earlier? Reply with just the word." Write its reply to recall.txt in {work}.
6. Tell me its session id (thread or conversation id) so that I can come back to it later.
"""


def check_basic(ctx):
    s = ctx.task_session("Remember this password")
    ctx.cap = "launch"
    ctx.file_is("caller.txt", "BUSY", "work")
    ctx.before("caller.txt", "words.txt")
    if s:
        cm = ctx.mtime("caller.txt", "work")
        ctx.add("caller.txt written after the callee started", cm is not None and cm >= s["started"] - 5,
                f"caller.txt {ctx.rel(cm)}, callee started {ctx.rel(s['started'])}")
    ctx.cap = "watch"
    words = [w.upper() for w in ctx.lines("words.txt")]
    ctx.add("words.txt has two words", len(words) == 2, repr(words))
    got = (ctx.line("progress.txt", "work") or "").upper()
    ctx.add("progress.txt holds one of the callee's words", bool(got) and got in words, repr(got[:40]))
    ctx.before("progress.txt", "words.txt")
    ctx.cap = "resume"
    ctx.file_is("recall.txt", ctx.words["password"], "work")
    if s:
        q = ctx.asked_in(s, "password")
        if q:
            ctx.add("question does not repeat the password", ctx.words["password"] not in q["text"].upper())
        ctx.session_reported(s)


# --- live: permissions, steer, interrupt, follow-up (one open channel) ------

LIVE_PROMPT = """\
Use {callee} with model {model} to run tasks in the directory {child}. Start it in a mode where it must ask you for permission before each shell command, and in a way that lets you send it messages and stop it while it is working. Keep one session for all steps. Do these steps in order.

1. Give it exactly this task: "Run the shell command `touch allowed.txt`. Then run the shell command `touch denied.txt`. Then say which of the two commands ran." Approve the first command and refuse the second. From here on, approve every command it asks about.
2. When it has answered, give it exactly this task: "Run the shell command `sleep 30`. Then create a file named b.txt in the current directory containing the code word that I will send you while you wait; if no code word has arrived, write DEFAULT. Never modify b.txt after creating it. Then say which word you wrote." While the sleep is running, send it this message: "The code word is {code}".
3. When it has answered, give it exactly this task: "Run this shell command: `for i in $(seq 1 20); do echo $i >> counter.txt; sleep 2; done`. Then say FINISHED." Once counter.txt has at least 3 lines, stop it immediately and make sure it is no longer counting.
4. In that same session, ask it exactly: "What was the last number you appended? Reply with just the number." Write its reply to reached.txt in {work}.
5. Tell me its session id (thread or conversation id) so that I can come back to it later.
"""


def check_live(ctx):
    s = ctx.task_session("touch allowed.txt")
    ctx.cap = "permissions"
    ctx.add("allowed.txt exists", os.path.exists(ctx.path("allowed.txt")))
    ctx.add("denied.txt absent", not os.path.exists(ctx.path("denied.txt")))
    if s:
        cmds = [e for e in s["events"] if e["kind"] == "command"]
        if cmds:
            ctx.add("callee ran touch allowed.txt", any("allowed.txt" in c["text"] for c in cmds),
                    f"{len(cmds)} command(s) logged")
    ctx.cap = "steer"
    code = ctx.words["code"]
    ctx.file_is("b.txt", code)
    if s:
        sent = [u for u in ctx.users(s) if code in u["text"].upper()]
        ctx.add("code word message in the same callee session", bool(sent), f"{len(ctx.users(s))} user message(s)")
        bm = ctx.mtime("b.txt")
        if sent and bm:
            ctx.add("code word arrived before b.txt was written", sent[0]["ts"] < bm,
                    f"message {ctx.rel(sent[0]['ts'])}, b.txt {ctx.rel(bm)}")
    ctx.cap = "interrupt"
    lines = ctx.lines("counter.txt")
    time.sleep(3)
    n2 = len(ctx.lines("counter.txt"))
    ctx.add("counter.txt stopped between 3 and 19 lines", 3 <= len(lines) < 20, f"{len(lines)} lines")
    ctx.add("counter.txt no longer growing", len(lines) == n2, f"{len(lines)} then {n2} lines after 3 s")
    ctx.cap = "followup"
    got = ctx.line("reached.txt", "work")
    try:
        ok = bool(lines) and got is not None and abs(int(got) - int(lines[-1])) <= 1
    except ValueError:
        ok = False
    ctx.add("reached.txt matches the last counter line", ok, f"reached={got!r} last={lines[-1] if lines else None!r}")
    if s:
        ctx.asked_in(s, "last number")
        ctx.session_reported(s)


SCENARIOS = {
    "basic": Scenario("basic", "launch, watch, resume", BASIC_PROMPT, check_basic),
    "live": Scenario("live", "permissions, steer, interrupt, followup", LIVE_PROMPT, check_live),
}
