#!/usr/bin/env python3
"""chatbrief - turn old AI chats into a short context pack to paste into any AI.

usage:
  python chatbrief.py EXPORT [EXPORT ...] --list
  python chatbrief.py EXPORT [EXPORT ...] (--pick 1,3,5 | --match WORD) [--size medium] [--out pack.md]

EXPORT is a data export (.zip or .json) from Claude, ChatGPT, Gemini (Google Takeout,
My Activity as JSON), Grok or DeepSeek, or a chatvault archive. Standard library only.
Works by spotting phrases in YOUR messages, not by using an AI, so check the result.
"""
import argparse
import html
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

def iso(v):
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return datetime.fromtimestamp(v / 1000 if v > 1e11 else v, tz=timezone.utc).isoformat()
    if isinstance(v, dict):
        d = v.get("$date")
        n = d.get("$numberLong") if isinstance(d, dict) else d
        if n is None:
            return None
        try:
            return iso(float(n))
        except (TypeError, ValueError):
            return str(n)
    return str(v)


def strip_html(s):
    s = re.sub(r"(?i)<br\s*/?>|</(p|li|h\d|div|tr|pre)>", "\n", s)
    s = html.unescape(re.sub(r"<[^>]*>", "", s))
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def parse_mapping(data):
    """ChatGPT and DeepSeek both export a 'mapping' tree of messages."""
    deepseek, convs = False, []
    for c in data:
        mp = c.get("mapping") or {}
        chain, node = [], c.get("current_node")
        if node:
            while node and mp.get(node):
                chain.append(mp[node])
                node = mp[node].get("parent")
            chain.reverse()
        else:
            node = "root" if "root" in mp else next((k for k, v in mp.items() if not v.get("parent")), None)
            seen = set()
            while node and mp.get(node) and node not in seen:
                seen.add(node)
                chain.append(mp[node])
                kids = mp[node].get("children") or []
                node = kids[-1] if kids else None
        msgs = []
        for e in chain:
            m = e.get("message")
            if not m:
                continue
            if isinstance(m.get("fragments"), list):
                deepseek = True
                for f in m["fragments"]:
                    role = {"REQUEST": "user", "RESPONSE": "assistant"}.get(f.get("type"))
                    text = str(f.get("content") or "").strip()
                    if role and text:
                        msgs.append((role, text))
                continue
            role = (m.get("author") or {}).get("role")
            if role not in ("user", "assistant"):
                continue
            parts = (m.get("content") or {}).get("parts") or []
            text = "\n".join(p for p in parts if isinstance(p, str)).strip()
            if text:
                msgs.append((role, text))
        date = c.get("create_time") or c.get("inserted_at") or c.get("update_time") or c.get("updated_at")
        convs.append({"title": c.get("title"), "date": iso(date), "messages": msgs})
    return [("DeepSeek" if deepseek else "ChatGPT", convs)]


def parse_claude(data):
    convs = []
    for c in data:
        msgs = []
        for m in c.get("chat_messages", []):
            text = (m.get("text") or "").strip()
            if not text:
                text = "\n".join(b.get("text", "") for b in m.get("content", []) if b.get("type") == "text").strip()
            if text:
                msgs.append(("user" if m.get("sender") == "human" else "assistant", text))
        convs.append({"title": c.get("name"), "date": iso(c.get("created_at")), "messages": msgs})
    return [("Claude", convs)]


def parse_grok(data):
    convs = []
    for c in data["conversations"]:
        info, msgs = c.get("conversation") or {}, []
        for r in c.get("responses") or []:
            m = r.get("response") or r
            text = str(m.get("message") or "").strip()
            if text:
                who = str(m.get("sender") or "").lower()
                msgs.append(("user" if who in ("human", "user") else "assistant", text))
        convs.append({"title": info.get("title"), "date": iso(info.get("create_time") or info.get("created_at")), "messages": msgs})
    return [("Grok", convs)]


def parse_gemini(data):
    """Takeout 'My Activity' has one entry per prompt and no chat ids: group by day."""
    days = {}
    for it in data:
        if not re.search("gemini", it.get("header") or "", re.I) or not it.get("title"):
            continue
        t = str(it.get("time") or "")
        turn = [("user", re.sub(r"^Prompted\s+", "", str(it["title"])).strip())]
        reply = "\n".join(strip_html(h.get("html") or "") for h in it.get("safeHtmlItem") or []).strip()
        if reply:
            turn.append(("assistant", reply))
        days.setdefault(t[:10] or "undated", []).append((t, turn))
    convs = [{"title": "Gemini prompts", "date": None if day == "undated" else day,
              "messages": [m for _, turn in sorted(turns, key=lambda x: x[0]) for m in turn]}
             for day, turns in days.items()]
    return [("Gemini", convs)] if convs else []


def parse_archive(data):
    names, by = {"claude": "Claude", "chatgpt": "ChatGPT"}, {}
    for c in data:
        src = str(c.get("source") or "other")
        by.setdefault(names.get(src, src[:1].upper() + src[1:]), []).append({
            "title": c.get("title"), "date": iso(c.get("created_at") or c.get("updated_at")),
            "messages": [(m["role"], m["text"]) for m in c.get("messages", []) if (m.get("text") or "").strip()]})
    return list(by.items())


def detect(doc):
    """Return [(ai_name, conversations)] for one parsed JSON document, or [] if it isn't a chat export."""
    if isinstance(doc, list) and doc and isinstance(doc[0], dict):
        f = doc[0]
        if "mapping" in f:
            return parse_mapping(doc)
        if "chat_messages" in f:
            return parse_claude(doc)
        if "header" in f and "title" in f and "time" in f:
            return parse_gemini(doc)
        if "messages" in f and "source" in f:
            return parse_archive(doc)
    if isinstance(doc, dict) and isinstance(doc.get("conversations"), list) \
            and any(isinstance(c, dict) and c.get("responses") for c in doc["conversations"]):
        return parse_grok(doc)
    return []


def read_export(path):
    """Return [(file name, parsed JSON)] for the chat files inside an export (.zip or .json)."""
    path = Path(path)
    if zipfile.is_zipfile(path):
        out = []
        with zipfile.ZipFile(path) as z:
            for n in z.namelist():
                m = re.search(r"(^|/)(conversations[^/]*|prod-grok-backend|MyActivity)\.json$", n, re.I)
                if not m or (m.group(2).lower() == "myactivity" and not re.search("gemini", n, re.I)):
                    continue
                out.append((n, json.loads(z.read(n))))
        return out
    return [(path.name, json.loads(path.read_text(encoding="utf-8")))]


def load_chats(paths):
    """Return (chats, problems). A chat is {ai, title, date, messages: [{role, text}]}."""
    chats, problems = [], []
    for p in paths:
        try:
            found = [g for _, doc in read_export(p) for g in detect(doc)]
        except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as e:
            problems.append(f"{p}: could not read ({e})")
            continue
        if not found:
            problems.append(f"{p}: no chats recognised")
            continue
        for ai, convs in found:
            for c in convs:
                if c["messages"]:
                    chats.append({"ai": ai, "title": str(c["title"] or "Untitled"), "date": (c["date"] or "")[:10],
                                  "messages": [{"role": r, "text": t} for r, t in c["messages"]]})
    return chats, problems


SIZES = {"short": 2000, "medium": 4000, "long": 8000, "xlong": 16000}  # characters (about 4 per token)

RULES = {
    "prefs": re.compile(r"\b(i (?:want|prefer|like|need|hate|don'?t (?:want|like))|i'?d (?:like|prefer|rather)|always|never|make sure|please (?:don'?t|do not|use|keep|avoid)|should(?:n'?t| not)? (?:be|use|have|look)|must(?:n'?t| not)?|instead of|from now on|no more|keep it)\b", re.I),
    "decisions": re.compile(r"\b(let'?s (?:go with|use|do|keep|stick)|i(?:'ll| will) (?:go with|use|take|keep)|i(?:'ve| have)? ?(?:chose|chosen|choose|picked|decided)|we(?:'ll| will) (?:use|go with)|go(?:ing)? with|stick with|the name (?:is|will be)|call it)\b", re.I),
    "todos": re.compile(r"\b(todo|to-do|later|next (?:step|time|up)|still (?:need|have to|missing)|need(?:s)? to|have to|haven'?t|not yet|doesn'?t work|not working|broken|remind me|after that|then (?:we|i|you)|can you (?:also|now)|also (?:add|make|fix))\b", re.I),
}


def clip(s, n):
    s = re.sub(r"\s+", " ", str(s)).strip()
    return s[: n - 1].rstrip() + "…" if len(s) > n else s


def sentences(text):
    """Plain sentences only: skips code, very short fragments and walls of text."""
    out = []
    for s in re.split(r"(?<=[.!?])\s+|\n+", str(text)):
        s = re.sub(r"^[\s>*#-]+", "", s).strip()
        if 12 <= len(s) <= 300 and not re.search(r"[{};=<>]{2,}|```|\bfunction\b|=>", s):
            out.append(s)
    return out


def pick(messages, rule, most):
    out, seen = [], set()
    for m in messages:
        for s in sentences(m["text"]):
            k = s.lower()
            if rule.search(s) and k not in seen:
                seen.add(k)
                out.append(clip(s, 200))
    return out[-most:]  # the most recent ones win


def brief_one(chat, most):
    mine = [m for m in chat["messages"] if m["role"] == "user"]
    if not mine:
        return None
    last_ai = next((m for m in reversed(chat["messages"]) if m["role"] == "assistant"), None)
    tail = mine[-max(2, -(-len(mine) // 3)):]
    decisions = pick(mine, RULES["decisions"], most)
    taken = set(decisions)
    wide = most > 2
    return {
        "head": f"{chat['title']} ({chat['ai']}{', ' + chat['date'] if chat['date'] else ''}, {len(chat['messages'])} messages)",
        "about": clip(mine[0]["text"], 400 if wide else 200),
        "prefs": [s for s in pick(mine, RULES["prefs"], most) if s not in taken],
        "decisions": decisions,
        "open": [s for s in pick(tail, RULES["todos"], most) if s not in taken],
        "last_user": clip(mine[-1]["text"], 300 if wide else 150) if len(mine) > 1 else "",
        "last_ai": clip(last_ai["text"], 500 if wide else 200) if last_ai else "",
    }


def render(briefs):
    lines = ["# Context from my earlier chats", "",
             "This is background from earlier conversations I had with an AI. Treat it as what you already know about this work, "
             "keep to the preferences and decisions below, and ask me if something is unclear or looks out of date.", ""]

    def block(title, items):
        if items:
            lines.extend([f"**{title}**", *["- " + s for s in items], ""])

    for b in briefs:
        lines.extend([f"## {b['head']}", "", f"**Started with:** {b['about']}", ""])
        block("My preferences and instructions", b["prefs"])
        block("Decisions I made", b["decisions"])
        block("Possibly still open", b["open"])
        if b["last_user"] or b["last_ai"]:
            lines.append("**Where it left off**")
            if b["last_user"]:
                lines.append("- Me: " + b["last_user"])
            if b["last_ai"]:
                lines.append("- AI: " + b["last_ai"])
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_brief(chats, budget):
    """Lowers the detail per chat until the pack fits the size budget (in characters)."""
    ordered = sorted(chats, key=lambda c: c["date"])
    text = ""
    for most in range(8, 0, -1):
        text = render([b for b in (brief_one(c, most) for c in ordered) if b])
        if len(text) <= budget:
            return text, False
    return text, True


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("exports", nargs="+", help="export files (.zip or .json)")
    ap.add_argument("--list", action="store_true", help="list the chats with numbers and stop")
    ap.add_argument("--pick", help="chat numbers from --list, e.g. 1,3,5")
    ap.add_argument("--match", help="use every chat whose title or your messages contain this text")
    ap.add_argument("--size", default="medium", help="short, medium, long, xlong, or a number of characters (default medium)")
    ap.add_argument("--out", help="write the pack to this file instead of printing it")
    a = ap.parse_args(argv)

    chats, problems = load_chats(a.exports)
    for p in problems:
        print(p, file=sys.stderr)
    if not chats:
        print("No chats found.", file=sys.stderr)
        return 1
    chats.sort(key=lambda c: c["date"], reverse=True)  # newest first; same order on every run

    if a.list or not (a.pick or a.match):
        for i, c in enumerate(chats, 1):
            print(f"{i}. {c['title']} ({c['ai']}{', ' + c['date'] if c['date'] else ''}, {len(c['messages'])} messages)")
        if not a.list:
            print("\nChoose chats with --pick NUMBERS or --match WORD.", file=sys.stderr)
        return 1 if problems else 0

    chosen = []
    if a.pick:
        try:
            nums = [int(x) for x in re.split(r"[,\s]+", a.pick.strip()) if x]
        except ValueError:
            print("--pick wants numbers like 1,3,5", file=sys.stderr)
            return 2
        bad = [n for n in nums if not 1 <= n <= len(chats)]
        if bad:
            print(f"No chat number {', '.join(map(str, bad))} (there are {len(chats)}).", file=sys.stderr)
            return 2
        chosen += [chats[n - 1] for n in nums]
    if a.match:
        q = a.match.lower()
        for c in chats:
            hay = (c["title"] + "\n" + "\n".join(m["text"] for m in c["messages"] if m["role"] == "user")).lower()
            if q in hay and c not in chosen:
                chosen.append(c)
    if not chosen:
        print("No chats matched.", file=sys.stderr)
        return 1

    size = a.size.lower()
    try:
        budget = SIZES[size] if size in SIZES else int(size)
    except ValueError:
        print("--size wants short, medium, long, xlong or a number", file=sys.stderr)
        return 2
    text, over = build_brief(chosen, budget)
    if over:
        print("The pack is bigger than the size you chose even at the lowest detail: pick fewer chats or a larger --size.", file=sys.stderr)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"wrote {a.out}: {len(chosen)} chats, {len(text)} characters (about {len(text) // 4} tokens)")
    else:
        sys.stdout.write(text)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
