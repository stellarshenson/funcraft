"""Applies the accepted rewrites of the calendar clarity review to calendar/*.md.

    python3 src/calendar-review/apply.py            # report only; writes wip/calendar-review/changes.md
    python3 src/calendar-review/apply.py --write    # also changes the month files

A rewrite is applied when the reviewer marked the entry unclear, the checker accepted it and it passes the
rules of src/liturgy.py that concern one entry. Run `python3 src/liturgy.py` afterwards.
"""
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent.parent
DATA = ROOT / "wip" / "calendar-review"
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
          "november", "december"]
liturgy = (ROOT / "src/liturgy.py").read_text()
# the two word lists of src/liturgy.py, read from its source: the script itself runs its check when imported
CULT = re.compile(eval("(" + re.search(r"CULT = re\.compile\(\n(.+?), re\.I\)", liturgy, re.S)[1] + ")"), re.I)
HARD = re.compile(eval("(" + re.search(r"HARD = re\.compile\(\n(.+?), re\.I\)", liturgy, re.S)[1] + ")"), re.I)


def faults(purpose, context):
    """The faults src/liturgy.py would report for one entry."""
    found = []
    for label, body, (low, high) in (("Purpose", purpose, (20, 95)), ("Context", context, (150, 310))):
        if not low <= len(body) <= high:
            found.append(f"{label} of {len(body)} characters")
        if not body.endswith("."):
            found.append(f"{label} without a full stop")
    both = purpose + " " + context
    if not both.isascii() or "--" in both or "!!" in both or '"' in both:
        found.append("character outside the allowed set")
    if not CULT.search(both):
        found.append("no cult word")
    if HARD.findall(both):
        found.append(f"hard words {sorted({x.lower() for x in HARD.findall(both)})}")
    longest = max(len(x.split()) for x in re.split(r"(?<=[.:;]) ", context))
    if longest > 25:
        found.append(f"a sentence of {longest} words")
    return found


missing, applied, rejected, invalid, clear, lines = [], [], [], [], 0, []
texts = {m: (ROOT / f"calendar/{m:02d}-{name}.md").read_text() for m, name in enumerate(MONTHS, 1)}
for n in range(1, 38):
    batch = json.loads((DATA / f"batch-{n:02d}.json").read_text())["entries"]
    try:
        result = {e["id"]: e for e in json.loads((DATA / f"result-{n:02d}.json").read_text())["entries"]}
        verdict = {e["id"]: e for e in json.loads((DATA / f"verdict-{n:02d}.json").read_text())["entries"]}
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as error:
        missing.append(f"batch {n:02d}: {type(error).__name__}")
        continue
    for old in batch:
        new = result.get(old["id"])
        if new is None:
            missing.append(f"{old['id']}: not in the result")
            continue
        same = (new["purpose"], new["context"]) == (old["purpose"], old["context"])
        if new["verdict"] == "clear" or same:
            clear += 1
            continue
        check = verdict.get(old["id"])
        if check is None:
            missing.append(f"{old['id']}: no verdict of the checker")
            continue
        if not check["accept"]:
            rejected.append(f"{old['id']}: {check['reason']}")
            continue
        found = faults(new["purpose"], new["context"])
        if found:
            invalid.append(f"{old['id']}: {found}")
            continue
        month = int(old["id"][:2])
        for label, key in (("**Purpose** - ", "purpose"), ("**Context** - ", "context")):
            if new[key] != old[key]:
                assert texts[month].count(label + old[key] + "\n") == 1, (old["id"], key)
                texts[month] = texts[month].replace(label + old[key] + "\n", label + new[key] + "\n")
        applied.append(old["id"])
        lines += [f"## {old['id']} - {old['heading']}", "", f"Problem: {new['problem']}", ""]
        for key in ("purpose", "context"):
            if new[key] != old[key]:
                lines += [f"- {key} before: {old[key]}", f"- {key} after: {new[key]}"]
        lines.append("")

(DATA / "changes.md").write_text("\n".join(["# Calendar clarity review - applied rewrites", ""] + lines))
print(f"clear {clear} | rewrites applied {len(applied)} | rejected by the checker {len(rejected)} | "
      f"invalid {len(invalid)} | missing {len(missing)}")
for title, items in (("REJECTED", rejected), ("INVALID", invalid), ("MISSING", missing)):
    for item in items:
        print(title, item)
# the variety rule of the brief: within a month no two entries open with the same three words
for month, text in texts.items():
    opens = {}
    for day, context in enumerate(re.findall(r"^\*\*Context\*\* - (.+)$", text, re.M), 1):
        opens.setdefault(" ".join(context.split()[:3]).lower(), []).append(day)
    for words, days in opens.items():
        if len(days) > 1:
            print(f"VARIETY month {month:02d}: days {days} open with '{words}'")
if "--write" in sys.argv:
    for m, name in enumerate(MONTHS, 1):
        (ROOT / f"calendar/{m:02d}-{name}.md").write_text(texts[m])
    print("wrote the month files")
