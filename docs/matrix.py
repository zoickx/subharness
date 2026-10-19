"""Regenerate the caller x callee capability matrix in README.md.

Run: uv run --no-project python -I docs/matrix.py
Edit the data blocks below when verification changes capabilities.
"""
from pathlib import Path

OK, WARN, NO = "ok", "warn", "no"
RANK = {OK: 2, WARN: 1, NO: 0}
EMOJI = {OK: "✅", WARN: "⚠️", NO: "❌"}
WORD = {OK: "direct", WARN: "caveat", NO: "not available"}
CAPS = ["Watch", "Steer", "Interrupt", "Resume", "Permissions"]
NAMES = ["Claude Code", "Codex CLI", "OpenCode", "agy"]

# What the called harness offers, independent of the caller.
CALLEE = {
    "Claude Code": {
        "channel": "stdin",
        "Watch": (OK, "stream-json with text deltas"),
        "Steer": (OK, "interrupt, then send the correction in the same stdin process"),
        "Interrupt": (OK, "control_request interrupt over stdin"),
        "Resume": (OK, "--resume SESSION_ID"),
        "Permissions": (OK, "can_use_tool round-trip over stdin with --permission-prompt-tool stdio"),
    },
    "Codex CLI": {
        "channel": "stdin",
        "Watch": (OK, "exec --json items, or app-server text deltas"),
        "Steer": (OK, "app-server turn/steer"),
        "Interrupt": (OK, "app-server turn/interrupt; the command keeps running until the server exits"),
        "Resume": (OK, "exec resume or thread/resume"),
        "Permissions": (OK, "app-server requestApproval, accept or decline"),
    },
    "OpenCode": {
        "channel": "http",
        "Watch": (OK, "run --format json, or the server event stream"),
        "Steer": (OK, "POST prompt with delivery steer; lands after the running tool call"),
        "Interrupt": (OK, "POST interrupt"),
        "Resume": (OK, "run --session SESSION_ID"),
        "Permissions": (OK, "HTTP permission reply; only for sessions driven over HTTP, run auto-rejects"),
    },
    "agy": {
        "channel": "none",
        "Watch": (OK, "stream-json text deltas"),
        "Steer": (WARN, "TUI only, through a PTY: alt+m injects at the next step boundary; headless stdin only queues"),
        "Interrupt": (WARN, "headless: kill or --print-timeout, result still SUCCESS; TUI through a PTY: Esc or Ctrl-C"),
        "Resume": (OK, "--conversation ID; an unknown ID silently starts a new one"),
        "Permissions": (WARN, "TUI only, through a PTY: a digit or Enter answers the prompt; headless auto-denies"),
    },
}

# What the calling harness's own tools can reach.
CALLER = {
    "Claude Code": {
        "launch": (OK, ""),
        "stdin": (WARN, "Bash has no writable stdin; run the child behind a FIFO held open, recipe in the callee reference"),
        "http": (OK, ""),
    },
    "Codex CLI": {
        "launch": (WARN, "the sandbox has no network; grant it or run the child outside the sandbox"),
        "stdin": (WARN, "write_stdin can send text per its schema, untested live"),
        "http": (OK, ""),
    },
    "OpenCode": {
        "launch": (OK, ""),
        "stdin": (WARN, "shell has no stdin channel; a FIFO held open should work, untested from shell"),
        "http": (OK, ""),
    },
    "agy": {
        "launch": (OK, ""),
        "stdin": (WARN, "manage_task send_input writes lines; driving a JSON protocol this way is untested"),
        "http": (OK, ""),
    },
}


def cell(caller: str, callee: str) -> str:
    out = []
    for cap in CAPS:
        status, note = CALLEE[callee][cap]
        caller_notes = []
        for key in ("launch",) + (("stdin",) if CALLEE[callee]["channel"] == "stdin" and cap != "Watch" and cap != "Resume" else ()) + (("http",) if CALLEE[callee]["channel"] == "http" and cap not in ("Watch", "Resume") else ()):
            cstatus, cnote = CALLER[caller][key]
            if status != NO and RANK[cstatus] < RANK[status]:
                status = cstatus
            if cstatus != OK and cnote and status != NO:
                caller_notes.append(cnote)
        text = f"{cap} ({WORD[status]}): {note}"
        if caller_notes:
            text += ". Caller: " + "; ".join(caller_notes)
        out.append(f'<abbr title="{text}">{EMOJI[status]}</abbr>')
    return "".join(out)


def table() -> str:
    lines = ["| Caller \\ Callee | " + " | ".join(NAMES) + " |", "| --- | --- | --- | --- | --- |"]
    for caller in NAMES:
        lines.append(f"| {caller} | " + " | ".join(cell(caller, callee) for callee in NAMES) + " |")
    return "\n".join(lines)


def main() -> None:
    readme = Path(__file__).resolve().parent.parent / "README.md"
    text = readme.read_text()
    start, end = "<!-- matrix:start -->", "<!-- matrix:end -->"
    a, b = text.index(start) + len(start), text.index(end)
    readme.write_text(text[:a] + "\n" + table() + "\n" + text[b:])
    print("README matrix regenerated")


if __name__ == "__main__":
    main()
