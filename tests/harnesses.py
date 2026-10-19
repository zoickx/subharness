"""Per-harness knowledge for the test runner: where a caller finds a project
skill, how to start a caller headless, and how to read a callee's own session
store. Session readers are read-only and stdlib-only.
"""
import glob
import json
import os
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

HOME = os.path.expanduser("~")


def jsonl(text):
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                yield json.loads(line)
            except ValueError:
                pass


@dataclass
class Harness:
    key: str
    name: str
    model: str  # cheap default, for caller and callee
    skill_dir: str  # relative to the work dir; the skill folder goes inside it
    caller_cmd: Callable[[str, str], list]  # (prompt, model) -> argv, run with cwd = work dir
    final_text: Callable[[str], str]  # caller stdout -> assistant text
    sessions: Callable[[str, float], list]  # (cwd_dir, since_epoch) -> callee sessions


def iso(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def claude_sessions(cwd_dir, since):
    """~/.claude/projects/<cwd with non-alphanumerics as '-'>/<session>.jsonl.
    Only user and assistant lines carry the conversation; the first line's
    timestamp is the start; a resumed turn appends to the same file."""
    cwd_dir = os.path.realpath(cwd_dir)
    out = []
    for path in glob.glob(os.path.join(HOME, ".claude", "projects", re.sub(r"[^A-Za-z0-9]", "-", cwd_dir), "*.jsonl")):
        recs = list(jsonl(open(path, encoding="utf-8", errors="replace").read()))
        stamps = [iso(r["timestamp"]) for r in recs if r.get("timestamp")]
        cwds = [r["cwd"] for r in recs if r.get("cwd")]
        if not stamps or not cwds or cwds[0] != cwd_dir or stamps[0] <= since:
            continue
        events = []
        for r in recs:
            if r.get("type") == "attachment" and r.get("attachment", {}).get("type") == "queued_command":
                # a message delivered into a running turn is logged here, not as a user line
                events.append({"ts": iso(r["timestamp"]), "kind": "user", "text": r["attachment"].get("prompt", "")})
                continue
            if r.get("type") not in ("user", "assistant") or r.get("isSidechain") or r.get("isMeta"):
                continue
            content = r["message"]["content"]
            for b in [{"type": "text", "text": content}] if isinstance(content, str) else content:
                if b.get("type") == "text" and b["text"].strip():
                    events.append({"ts": iso(r["timestamp"]), "kind": r["type"], "text": b["text"]})
                elif b.get("type") == "tool_use" and b.get("name") == "Bash":
                    events.append({"ts": iso(r["timestamp"]), "kind": "command", "text": b["input"].get("command", "")})
        events.sort(key=lambda e: e["ts"])
        out.append({"session_id": recs[0].get("sessionId") or os.path.basename(path)[:-6],
                    "cwd": cwds[0], "started": stamps[0], "events": events})
    return sorted(out, key=lambda s: s["started"])


def codex_sessions(cwd_dir, since):
    """$CODEX_HOME/sessions/Y/M/D/rollout-<time>-<thread>.jsonl. Line 1 is
    session_meta (id, cwd, start); event_msg item_completed lines carry the
    clean transcript; a resume appends to the same file."""
    home = os.environ.get("CODEX_HOME") or os.path.join(HOME, ".codex")
    want, out = os.path.realpath(cwd_dir), []
    for f in glob.glob(os.path.join(home, "sessions", "*", "*", "*", "rollout-*.jsonl")):
        if os.path.getmtime(f) < since:
            continue
        lines = list(jsonl(open(f, encoding="utf-8", errors="replace").read()))
        if not lines or lines[0].get("type") != "session_meta":
            continue
        meta = lines[0]["payload"]
        started = iso(meta["timestamp"])
        if os.path.realpath(meta.get("cwd", "")) != want or started <= since:
            continue
        events = []
        for d in lines:
            p = d.get("payload", {})
            if d.get("type") != "event_msg" or p.get("type") != "item_completed":
                continue
            it, t = p["item"], p["item"].get("type")
            if t in ("UserMessage", "AgentMessage"):
                events.append({"ts": iso(d["timestamp"]), "kind": "user" if t == "UserMessage" else "assistant",
                               "text": "".join(c.get("text", "") for c in it.get("content", []))})
            elif t == "CommandExecution":
                cmd = it.get("command", [])
                events.append({"ts": iso(d["timestamp"]), "kind": "command",
                               "text": cmd[-1] if len(cmd) == 3 and cmd[1] in ("-lc", "-c") else " ".join(cmd)})
        out.append({"session_id": meta["id"], "cwd": meta["cwd"], "started": started, "events": events})
    return sorted(out, key=lambda s: s["started"])


def opencode_sessions(cwd_dir, since):
    """~/.local/share/opencode/opencode.db, tables session_v2 (directory,
    time_created in ms) and session_message (data JSON with content parts).
    User text is stored wrapped in double quotes."""
    con = sqlite3.connect(f"file:{HOME}/.local/share/opencode/opencode.db?mode=ro", uri=True)
    try:
        out = []
        for sid, created in con.execute("SELECT id, time_created FROM session_v2 WHERE directory = ? AND time_created > ?"
                                        " ORDER BY time_created", (cwd_dir, int(since * 1000))):
            events = []
            for mtype, mtc, data in con.execute("SELECT type, time_created, data FROM session_message"
                                                " WHERE session_id = ? ORDER BY seq", (sid,)):
                d = json.loads(data)
                if mtype == "user":
                    events.append({"ts": mtc / 1000, "kind": "user", "text": d.get("text", "")})
                elif mtype == "assistant":
                    for part in d.get("content", []):
                        if part.get("type") == "text" and part.get("text"):
                            events.append({"ts": mtc / 1000, "kind": "assistant", "text": part["text"]})
                        elif part.get("type") == "tool" and part.get("name") == "shell":
                            events.append({"ts": part.get("time", {}).get("created", mtc) / 1000, "kind": "command",
                                           "text": part.get("state", {}).get("input", {}).get("command", "")})
            out.append({"session_id": sid, "cwd": cwd_dir, "started": created / 1000, "events": events})
        return out
    finally:
        con.close()


def pb(b):
    """Minimal protobuf wire decoder: {field: [values]}; no schema."""
    out, i = {}, 0

    def varint():
        nonlocal i
        r = shift = 0
        while True:
            x = b[i]
            i += 1
            r |= (x & 0x7F) << shift
            shift += 7
            if x < 0x80:
                return r

    while i < len(b):
        key = varint()
        f, t = key >> 3, key & 7
        if t == 0:
            v = varint()
        elif t == 1:
            v, i = b[i:i + 8], i + 8
        elif t == 5:
            v, i = b[i:i + 4], i + 4
        elif t == 2:
            n = varint()
            v, i = b[i:i + n], i + n
        else:
            raise ValueError(t)
        out.setdefault(f, []).append(v)
    return out


def pb_get(b, *path):
    for f in path:
        try:
            b = pb(b)[f][0]
        except (KeyError, IndexError, ValueError, TypeError):
            return None
    return b


def agy_sessions(cwd_dir, since):
    """~/.gemini/antigravity-cli/conversations/<id>.db, table steps with
    protobuf blobs. Field numbers were reverse-engineered on agy 1.4.2:
    step_type 14 user, 15 assistant, else tool; metadata.1 is a Timestamp,
    metadata.4 the tool call; user text at payload 19.2 and cwd at 19.12.12,
    assistant text at payload 20.1."""
    want, out = "file://" + os.path.realpath(cwd_dir), []
    for db in glob.glob(os.path.join(HOME, ".gemini", "antigravity-cli", "conversations", "*.db")):
        if os.path.getmtime(db) < since:
            continue
        try:
            con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            rows = con.execute("select idx, step_type, status, metadata, step_payload from steps order by idx").fetchall()
            con.close()
        except sqlite3.Error:
            continue
        if not rows or rows[0][1] != 14 or (pb_get(rows[0][4], 19, 12, 12) or b"").decode() != want:
            continue

        def ts(md):
            t = pb(pb_get(md, 1) or b"")
            return t.get(1, [0])[0] + t.get(2, [0])[0] / 1e9

        started = ts(rows[0][3])
        if started <= since:
            continue
        events = []
        for idx, typ, status, md, pl in rows:
            if typ in (14, 15):
                txt = pb_get(pl, 19, 2) if typ == 14 else pb_get(pl, 20, 1)
                if txt:
                    events.append({"ts": ts(md), "kind": "user" if typ == 14 else "assistant", "text": txt.decode()})
            elif pb_get(md, 4, 2) == b"run_command":
                args = json.loads(pb_get(md, 4, 3) or b"{}")
                events.append({"ts": ts(md), "kind": "command", "text": args.get("CommandLine", "")})
        out.append({"session_id": os.path.basename(db)[:-3], "cwd": want[7:], "started": started, "events": events})
    return sorted(out, key=lambda s: s["started"])


HARNESSES = {
    "claude": Harness(
        "claude", "Claude Code", "haiku", ".claude/skills",
        lambda p, m: ["claude", "-p", "--model", m, "--dangerously-skip-permissions",
                      "--output-format", "stream-json", "--verbose", p],
        lambda out: "\n".join(str(e.get("result", "")) for e in jsonl(out) if e.get("type") == "result"),
        claude_sessions),
    "codex": Harness(
        "codex", "Codex CLI", "gpt-6-luna", ".agents/skills",
        lambda p, m: ["codex", "exec", "--json", "--skip-git-repo-check", "-m", m,
                      "-c", 'model_reasoning_effort="medium"',
                      "--dangerously-bypass-approvals-and-sandbox", p],
        lambda out: "\n".join(e["item"].get("text", "") for e in jsonl(out)
                              if e.get("type") == "item.completed" and e.get("item", {}).get("type") == "agent_message"),
        codex_sessions),
    "opencode": Harness(
        "opencode", "OpenCode", "opencode-go/gpt-6-luna", ".opencode/skills",
        lambda p, m: ["opencode", "run", "--standalone", "--auto", "--format", "json", "--model", m, p],
        lambda out: "\n".join(e.get("part", {}).get("text", "") for e in jsonl(out) if e.get("type") == "text"),
        opencode_sessions),
    "agy": Harness(
        "agy", "Antigravity CLI (agy)", "gemini-3.8-flash-low", ".agents/skills",
        lambda p, m: ["agy", "-p", p, "--model", m, "--output-format", "stream-json",
                      "--print-timeout", "20m", "--dangerously-skip-permissions"],
        lambda out: "\n".join(str(e.get("result", {}).get("response", "")) for e in jsonl(out)
                              if e.get("event") == "result"),
        agy_sessions),
}
