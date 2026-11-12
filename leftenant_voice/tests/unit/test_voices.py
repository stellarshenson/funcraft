"""The voice loader: a voice is a `.wav` with a `.txt` transcript of the same name beside it."""
from engine import voice_names


def test_voice_names_requires_both_files(tmp_path):
    (tmp_path / "a.wav").write_bytes(b"")
    (tmp_path / "a.txt").write_text("hello")
    (tmp_path / "b.wav").write_bytes(b"")
    (tmp_path / "c.txt").write_text("transcript without audio")
    assert voice_names(tmp_path) == ["a"]


def test_voice_names_are_sorted(tmp_path):
    for name in ("vesemir", "dijkstra"):
        (tmp_path / f"{name}.wav").write_bytes(b"")
        (tmp_path / f"{name}.txt").write_text("text")
    assert voice_names(tmp_path) == ["dijkstra", "vesemir"]


def test_voice_names_of_an_empty_folder_is_empty(tmp_path):
    assert voice_names(tmp_path) == []
