"""Drop the segments whose fresh transcript disagrees with the stored text.

Usage: prune_segments.py <voice> [<voice> ...]
Reads  wip/voices/<voice>/verify.csv (from verify_segments.py)
Removes the rows with a word error rate above WER_MAX from metadata.csv and deletes their wav files.
"""
import csv
import sys
from pathlib import Path

WER_MAX = 0.2


def main(voice: str) -> None:
    folder = Path("wip/voices") / voice
    with open(folder / "verify.csv") as handle:
        bad = {r["file"] for r in csv.DictReader(handle, delimiter="|") if float(r["wer"]) > WER_MAX}
    with open(folder / "metadata.csv") as handle:
        rows = list(csv.DictReader(handle, delimiter="|"))
    with open(folder / "metadata.csv", "w", newline="") as handle:
        writer = csv.writer(handle, delimiter="|")
        writer.writerow(["file", "text", "seconds"])
        writer.writerows([r["file"], r["text"], r["seconds"]] for r in rows if r["file"] not in bad)
    for name in bad:
        (folder / "segments" / name).unlink(missing_ok=True)
    print(voice, "pruned", sorted(bad))


if __name__ == "__main__":
    for name in sys.argv[1:]:
        main(name)
