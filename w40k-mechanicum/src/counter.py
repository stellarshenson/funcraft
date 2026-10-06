"""Prints a report of the prayers that the prayer counter of the sermon page has counted, as Markdown: the totals, the
prayers of every reader, and the prayers of every day with its sermon.

    python3 src/counter.py

It reads GET /api/report of the counter (SERMON.md, section 2.5) and sends nothing that counts a prayer. The counter
has a self-signed certificate, so the certificate is not checked. The command /prayer-counter runs this script.
"""
import json
import ssl
import urllib.request

REPORT = "https://prayer-counter.lab.stellars-tech.eu/api/report"


def table(head, rows):
    """A Markdown table. A column whose cells are all numbers, plain or bold, is set to the right."""
    number = lambda cell: isinstance(cell, int) or str(cell).startswith("**")
    rule = ["---:" if all(number(row[column]) for row in rows) else "---" for column in range(len(head))]
    return "\n".join("| " + " | ".join(map(str, line)) + " |" for line in [head, rule, *rows])


def moment(stamp):
    """2026-10-03T20:29:43+00:00 as 2026-10-03 20:29 UTC."""
    return f"{stamp[:10]} {stamp[11:16]} UTC"


request = urllib.request.Request(REPORT, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(request, context=ssl._create_unverified_context(), timeout=20) as answer:
    report = json.loads(answer.read())

if not report["count"]:
    print("The prayer counter holds no prayers.")
else:
    prayers = [row["prayer"] for row in report["prayers"]]                 # the columns: the most said prayer first
    print(f"The prayer counter holds {report['count']} prayers by {len(report['users'])} readers",
          f"on {len(report['dates'])} days. First: {moment(report['first'])}. Last: {moment(report['last'])}.\n")

    rows = [[row["user"], row["count"], *(row["prayers"].get(prayer, 0) for prayer in prayers)]
            for row in report["users"]]
    rows.append(["**Total**", f"**{report['count']}**", *(f"**{row['count']}**" for row in report["prayers"])])
    print(table(["Reader", "Total", *prayers], rows) + "\n")

    rows = [[row["date"], ", ".join(row["sermons"]), row["count"],
             *(row["prayers"].get(prayer, 0) for prayer in prayers),
             ", ".join(f"{user} {count}" for user, count in row["users"].items())]
            for row in sorted(report["dates"], key=lambda row: row["date"])]
    print(table(["Date", "Sermon", "Total", *prayers, "Readers"], rows))
