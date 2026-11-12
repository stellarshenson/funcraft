"""The S2 Pro text splitter: paragraphs at blank lines, then sentences at sentence ends."""
import pytest

from speak_s2pro import paragraphs_of, sentences_of
from speak_text import split_sentences


def test_split_sentences_breaks_at_sentence_ends():
    assert split_sentences("One. Two! Three?") == ["One.", "Two!", "Three?"]


def test_split_sentences_keeps_a_text_without_ends_whole():
    assert split_sentences("A wall without end") == ["A wall without end"]


def test_sentences_of_splits_paragraphs_then_sentences():
    text = "First paragraph. It has two sentences.\n\nSecond paragraph."
    assert sentences_of(text) == ["First paragraph.", "It has two sentences.", "Second paragraph."]


def test_paragraphs_of_keeps_the_paragraph_groups():
    text = "First paragraph. It has two sentences.\n\nSecond paragraph."
    assert paragraphs_of(text) == [["First paragraph.", "It has two sentences."], ["Second paragraph."]]


def test_sentences_of_collapses_whitespace_inside_a_paragraph():
    assert sentences_of("One line\nwrapped here. Next.") == ["One line wrapped here.", "Next."]


def test_sentences_of_rejects_text_without_words():
    with pytest.raises(ValueError):
        sentences_of(" \n\n ")


def test_sentences_of_cuts_a_long_sentence_into_pieces_of_at_most_400_characters():
    text = "word " * 300  # 1500 characters, no sentence end
    pieces = sentences_of(text)
    assert all(len(piece) <= 400 for piece in pieces)
    assert " ".join(pieces) == " ".join(text.split())
    edge = "a" * 400 + "," + "b" * 10  # a delimiter one position past the cap is not taken
    assert all(len(piece) <= 400 for piece in sentences_of(edge))
    assert "".join(sentences_of(edge)) == edge
