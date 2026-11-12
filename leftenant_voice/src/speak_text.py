"""Split a text into paragraphs, each with the Ming task and controls that speak it.

A paragraph may open with one directive in braces, in English: `{emotion: angry}` or
`{speed: slow, pitch: low, volume: medium}`. A paragraph without a directive that holds inline tags
(`[Breathing]`, `[Sigh]`, ...) is spoken with task `TTS`. Any other paragraph uses the whole-text controls
if given, else task `TTS`. Ming accepts one task per call, so a directive and tags in one paragraph is an error.
"""
import re
from dataclasses import dataclass

TAGS = frozenset(
    f"[{name}]" for name in (
        "Breathing", "Cough", "Sigh", "Laughter", "Uhm", "Surprise-ah", "Surprise-oh", "Dissatisfaction-hnn",
        "Confirmation-en", "Question-ei", "Question-ah", "Question-en", "Question-oh", "Question-huh",
    )
)
EMOTIONS = {
    "happy": "高兴", "sad": "悲伤", "angry": "愤怒", "fearful": "恐惧",
    "disgusted": "厌恶", "surprised": "惊讶", "neutral": "中性",
}
SPEEDS = {"slow": "慢速", "medium": "中速", "fast": "快速"}
LEVELS = {"low": "低", "medium": "中", "high": "高"}
BASIC_VALUES = {"speed": SPEEDS, "pitch": LEVELS, "volume": LEVELS}
DIRECTIVE = re.compile(r"^\{([^}]*)\}\s*")
BRACKETS = re.compile(r"\[[^\]]*\]")
PARAGRAPH = re.compile(r"\S[\s\S]*?(?=\n\s*\n|\Z)")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


class TextError(ValueError):
    """The text or a control option cannot be spoken."""


@dataclass(frozen=True)
class Paragraph:
    """One paragraph of the text: its first line, spoken text, Ming task and Ming controls."""

    line: int
    text: str
    task: str
    controls: dict[str, str]


def controls_from(pairs: dict[str, str], where: str) -> tuple[str, dict[str, str]]:
    """Map English control names and values to the task `EMOTION` or `BASIC` and Ming's exact values.

    Args:
        pairs: English names to English values, for example `{"speed": "slow"}`.
        where: place named in error messages.

    Raises:
        TextError: unknown name or value, or emotion mixed with speed, pitch or volume.
    """
    if "emotion" in pairs:
        if len(pairs) > 1:
            raise TextError(f"{where}: emotion cannot be combined with speed, pitch or volume")
        if pairs["emotion"] not in EMOTIONS:
            raise TextError(f"{where}: emotion must be one of {sorted(EMOTIONS)}, not {pairs['emotion']!r}")
        return "EMOTION", {"emotion": EMOTIONS[pairs["emotion"]]}
    unknown = set(pairs) - set(BASIC_VALUES)
    if unknown:
        raise TextError(f"{where}: unknown control {sorted(unknown)}")
    controls = {}
    for name, values in BASIC_VALUES.items():
        value = pairs.get(name, "medium")
        if value not in values:
            raise TextError(f"{where}: {name} must be one of {sorted(values)}, not {value!r}")
        controls[name] = values[value]
    return "BASIC", controls


def parse_directive(body: str, where: str) -> dict[str, str]:
    """Read `name: value, name: value` into a dict."""
    pairs = {}
    for item in body.split(","):
        name, separator, value = item.partition(":")
        if not separator:
            raise TextError(f"{where}: directive item {item.strip()!r} is not `name: value`")
        pairs[name.strip()] = value.strip()
    return pairs


def parse_paragraphs(text: str, whole_text: dict[str, str]) -> list[Paragraph]:
    """Split a text at blank lines and resolve the task of each paragraph.

    Args:
        text: the text to speak, with optional directives and tags.
        whole_text: English controls for every paragraph without a directive or tags (may be empty).

    Raises:
        TextError: a directive and tags in one paragraph, an unknown tag or control, or no words.
    """
    whole = controls_from(whole_text, "whole-text option") if whole_text else ("TTS", {})
    paragraphs = []
    for found in PARAGRAPH.finditer(text):
        line = text.count("\n", 0, found.start()) + 1
        where, block = f"line {line}", found.group()
        directive = DIRECTIVE.match(block.strip())
        body = block.strip()[directive.end():] if directive else block.strip()
        unknown = [t for t in BRACKETS.findall(body) if t not in TAGS]
        if unknown:
            raise TextError(f"{where}: unknown tag {unknown[0]}; the tags are {sorted(TAGS)}")
        tagged = bool(BRACKETS.search(body))
        if directive and tagged:
            raise TextError(f"{where}: a directive and inline tags in one paragraph; Ming takes one task per call")
        if directive:
            task, controls = controls_from(parse_directive(directive.group(1), where), where)
        else:
            task, controls = ("TTS", {}) if tagged else whole
        if body:
            paragraphs.append(Paragraph(line, " ".join(body.split()), task, controls))
    if not paragraphs:
        raise TextError("the text has no words to speak")
    return paragraphs


def split_sentences(text: str) -> list[str]:
    """Split a paragraph at sentence ends."""
    return [piece for piece in SENTENCE_END.split(text) if piece]
