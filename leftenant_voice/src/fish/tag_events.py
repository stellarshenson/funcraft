"""Find the inline controls of a Fish or Ming text paragraph and the spoken words around them.

A point tag is `[name]` inside or at the end of a paragraph; a style prefix is a bracket group that opens the
paragraph with more than one word; a scoped tag is `<name>words</name>`; a Ming directive is `{...}` at the start.
"""
import re
from dataclasses import dataclass

from wer import words

TOKEN = re.compile(r"\[[^\]]*\]|</?\w+>|\{[^}]*\}")
POINT_NAMES = {"breath", "sighs", "hmm", "pause", "Breathing", "Sigh", "Confirmation-en"}


@dataclass(frozen=True)
class Event:
    """A control: its kind (point, scoped, style), label, and the spoken-word range it touches.

    A point tag sits before word index `first`; a scoped tag covers words `first` up to `last` (exclusive).
    """

    kind: str
    label: str
    first: int
    last: int


def parse_paragraph(text: str) -> tuple[list[str], list[Event]]:
    """Return the spoken words of a paragraph and its controls."""
    spoken, events, open_scoped, position = [], [], {}, 0
    for piece in re.split(f"({TOKEN.pattern})", text):
        if not piece.strip():
            continue
        if not TOKEN.fullmatch(piece):
            spoken += words(piece)
            continue
        label = piece.strip("[]{}<>/")
        if piece.startswith("</"):
            events.append(Event("scoped", label, open_scoped.pop(label), len(spoken)))
        elif piece.startswith("<"):
            open_scoped[label] = len(spoken)
        elif piece.startswith("{") or (label not in POINT_NAMES and not spoken):
            events.append(Event("style", label, 0, 0))
        else:
            events.append(Event("point", label, len(spoken), len(spoken)))
    return spoken, events
