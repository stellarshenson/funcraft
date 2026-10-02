"""Checks the month files of the Cult Mechanicus calendar, calendar/MM-<month>.md.

    python3 src/liturgy.py            # all twelve months; with 0 faults it writes the whole year to out/14-calendar.md
    python3 src/liturgy.py 09 10      # reports on these months only

An entry is three blocks, each followed by a blank line:

    ## January 7 - Rite of Device Selection

    **Purpose** - Naming of the engine before the framework is roused.

    **Context** - The enginseer speaks the number of the chosen engine ...

Rules and voice: references/calendar-brief.md
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).parent.parent / "calendar"
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
          "november", "december"]
DAYS = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
PURPOSE, CONTEXT = (20, 95), (150, 310)                 # characters
ONLY = sys.argv[1:]
# the short list of cult words; an entry needs at least one
CULT = re.compile(
    r"tech-priest|priest|magos|enginseer|adept|acolyte|servitor|servo-skull|cogitator|machine spirit|omnissiah"
    r"|machine god|\bforges?\b|litan|\brites?\b|ritual|incense|purity seal|sacred|holy|bless|heres|scrap-code"
    r"|binary chant|chant|\bsaint|\bcult\b|\bsins?\b|motive force|sixteen laws", re.I)
# words the reader would have to translate
HARD = re.compile(
    r"\b(lest|upon|kin|thereof|whereof|hath|ere|thee|thy|lexmechanics?|logis|transmechanics?|datasmiths?|genetors?"
    r"|noosphere|auspex\w*|binharic|binaric|canticles?|catechism|unguents?|reliquar\w+|relics?|data-slates?"
    r"|data-vaults?|vaults?|vox|inton\w+|anoint\w*|consecrat\w+|venerat\w+|augur\w*|omens?|penance|aton\w+"
    r"|congregation|petition\w*|appeas\w+|ledger|hallow\w*|sanctif\w+|exorcis\w+|incantations?|manufactor\w+"
    r"|pilgrim\w*|profan\w+|wrath|dogma|creed|doctrine|engines?|scrolls?)\b", re.I)

faults, titles, done = [], {}, 0
for m, (name, days) in enumerate(zip(MONTHS, DAYS), 1):
    key = f"{m:02d}"
    path = ROOT / f"{key}-{name}.md"
    report = not ONLY or key in ONLY
    if not path.exists():
        if report:
            faults.append(f"{path.name}: file is missing")
        continue
    text = path.read_text()
    head, *blocks = re.split(r"^## ", text, flags=re.M)
    found = []
    if head.strip() != f"# Cult Mechanicus Liturgical Calendar - {name.capitalize()}":
        found.append("first line is not the month heading")
    if not text.isascii() or "--" in text or "!!" in text or '"' in text:
        bad = sorted({c for c in text if not c.isascii()})
        found.append(f"character outside the allowed set {bad or ''}")
    for n, block in enumerate(blocks, 1):
        lines = [x for x in block.split("\n") if x.strip()]
        at = f"{key}-{n:02d}"
        hit = re.fullmatch(rf"{name.capitalize()} (\d+) - (.+)", lines[0])
        if not hit or int(hit[1]) != n:
            found.append(f"{at}: heading '{lines[0][:40]}' is not '{name.capitalize()} {n} - <title>'")
            continue
        title = hit[2]
        if not 2 <= len(title.split()) <= 7:
            found.append(f"{at}: title of {len(title.split())} words")
        if title.lower() in titles:
            found.append(f"{at}: title repeats {titles[title.lower()]}")
        titles[title.lower()] = at
        if len(lines) != 3 or not lines[1].startswith("**Purpose** - ") or not lines[2].startswith("**Context** - "):
            found.append(f"{at}: not one Purpose line and one Context line")
            continue
        purpose, context = lines[1][14:], lines[2][14:]
        for label, body, (low, high) in (("Purpose", purpose, PURPOSE), ("Context", context, CONTEXT)):
            if not low <= len(body) <= high:
                found.append(f"{at}: {label} of {len(body)} characters, allowed {low} to {high}")
            if not body.endswith("."):
                found.append(f"{at}: {label} does not end with a full stop")
        if not CULT.search(purpose + " " + context):
            found.append(f"{at}: no cult word of the short list")
        hard = sorted({x.lower() for x in HARD.findall(purpose + " " + context)})
        if hard:
            found.append(f"{at}: hard words {hard}")
        longest = max(len(x.split()) for x in re.split(r"(?<=[.:;]) ", context))
        if longest > 25:
            found.append(f"{at}: a sentence of {longest} words, at most 25")
    if len(blocks) != days:
        found.append(f"{len(blocks)} entries, the month has {days} days")
    if report:
        done += min(len(blocks), days)
        print(f"{path.name}: {len(blocks)} of {days} days, {len(found)} faults")
        faults += [f"{path.name}: {x}" if not x[:2].isdigit() else x for x in found]

for x in faults:
    print("FAULT", x)
wanted = sum(d for m, d in enumerate(DAYS, 1) if not ONLY or f"{m:02d}" in ONLY)
print(f"{done} of {wanted} days, {len(faults)} faults")
if faults or ONLY:
    sys.exit(bool(faults))
year = ["# Cult Mechanicus Liturgical Calendar\n"]
for m, name in enumerate(MONTHS, 1):
    text = (ROOT / f"{m:02d}-{name}.md").read_text()
    text = text.replace("\n## ", "\n### ").replace("# Cult Mechanicus Liturgical Calendar - ", "## ", 1)
    year.append(text.strip() + "\n")
out = ROOT.parent / "out" / "14-calendar.md"
out.write_text("\n".join(year))
print("wrote", out)
