"""Word error rate between a reference text and a transcript."""
import re


def words(text: str) -> list[str]:
    """Lower-case words without punctuation."""
    return re.findall(r"[a-z0-9']+", text.lower().replace("’", "'"))


def word_error_rate(reference: str, heard: str) -> float:
    """Word edit distance between the two texts divided by the number of reference words."""
    ref, hyp = words(reference), words(heard)
    row = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, 1):
        previous, row[0] = row[0], i
        for j, h in enumerate(hyp, 1):
            previous, row[j] = row[j], min(row[j] + 1, row[j - 1] + 1, previous + (r != h))
    return row[-1] / max(len(ref), 1)
