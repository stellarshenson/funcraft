"""Speak a text with Fish Audio S2 Pro in a cloned voice: one request per sentence, levelled, joined with pauses.

Usage (run in .venv-fish from the project folder, normally through `make -f s2pro.mk speak`):
    speak_s2pro.py <text file> <out.mp3> [--voice grimaldus] [--voices-dir wip/fish/refs]
The GPU comes from CUDA_VISIBLE_DEVICES (the model uses cuda:0). A voice is a pair `<voice>.wav` + `<voice>.txt`
(the recording and its transcript) in the voices folder.

Method (the winner of the trial, see references/fish-audio-s2-pro.md): the fish-speech code splits a request only at
speaker tags, so a long request drifts 3 to 8 dB in level. Each sentence is therefore its own request with the
code's sampling defaults and seed 42; every sentence gets a gain to the median voiced level of the text, capped at
+3 dB so a quiet sentence's hiss rises no more, and the loud sentences of its paragraph are trimmed so the
paragraph spread stops at 1.2 dB; sentences are joined with 0.4 s of silence; the peak is held at 0.98 at most.
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import torch
from huggingface_hub import snapshot_download

from fish_speech.models.text2semantic.inference import (
    decode_to_audio, encode_audio, generate_long, init_model, load_codec_model, resolve_codec_path,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from audio_out import write_render  # noqa: E402
from speak_text import PARAGRAPH, split_sentences  # noqa: E402

MODEL, REVISION = "fishaudio/s2-pro", "1de9996b6be38b745688de084d87a5633f714e4e"
DEVICE = "cuda:0"
SEED = 42
PAUSE_SECONDS, PEAK_LIMIT = 0.4, 0.98
FLOOR_DB, FRAME_SECONDS = -50.0, 0.025  # frames below the floor are pauses, not voice
MAX_BOOST_DB = 3.0  # a gain lifts the sentence's background hiss with it, so a positive gain stops at 3 dB
MAX_PARA_SPREAD_DB = 1.2  # inside the accepted 1.5 dB, with 0.3 dB left for the MP3 word-window measure
# 1024 codec frames = 47.55 s at 44.1 kHz, and the probe and the grimaldus reference measure 13.4-14.5 characters
# per second, so 47.55 s covers about 640-690 characters; a request stops at 400.
SPLIT_CHARS = 400
DEFAULT_VOICES = Path(__file__).resolve().parent.parent.parent / "wip/fish/refs"


class VoiceError(ValueError):
    """The voice has no `<voice>.wav` + `<voice>.txt` pair in the voices folder."""


def _split_long(sentence: str) -> list[str]:
    """Cut a sentence longer than `SPLIT_CHARS` at the last comma or space at or before the cap; a run without
    either is cut at the cap, so no character is dropped."""
    pieces = []
    rest = sentence
    while len(rest) > SPLIT_CHARS:
        cut = max(rest.rfind(",", 0, SPLIT_CHARS), rest.rfind(" ", 0, SPLIT_CHARS))
        cut = SPLIT_CHARS if cut < 0 else cut + 1
        pieces.append(rest[:cut].strip())
        rest = rest[cut:].lstrip()
    pieces.append(rest)
    return pieces


def paragraphs_of(text: str) -> list[list[str]]:
    """Split a text at blank lines into paragraphs, then each paragraph at sentence ends; a sentence longer
    than `SPLIT_CHARS` is cut at the last comma or space at or before the cap.

    Raises:
        ValueError: the text has no words.
    """
    found = [[piece for sentence in split_sentences(" ".join(p.split())) for piece in _split_long(sentence)]
             for p in PARAGRAPH.findall(text)]
    found = [paragraph for paragraph in found if paragraph]
    if not found:
        raise ValueError("the text has no words to speak")
    return found


def sentences_of(text: str) -> list[str]:
    """Split a text into its sentences, paragraph after paragraph.

    Raises:
        ValueError: the text has no words.
    """
    return [sentence for paragraph in paragraphs_of(text) for sentence in paragraph]


def voiced_db(audio: np.ndarray, rate: int) -> float:
    """Mean-power level in dBFS of the 25 ms frames above the -50 dB floor."""
    size = int(FRAME_SECONDS * rate)
    power = np.mean(audio[: len(audio) // size * size].reshape(-1, size) ** 2, axis=1)
    return float(10 * np.log10(power[10 * np.log10(power + 1e-12) > FLOOR_DB].mean()))


def sentence_gains(levels: list[float], paragraphs: list[int]) -> list[float]:
    """Gain in dB of each piece: to the median voiced level, a positive gain capped at `MAX_BOOST_DB`; the
    loud pieces of a paragraph are then trimmed (attenuation only) until its spread is `MAX_PARA_SPREAD_DB`
    at most, because a capped quiet sentence would otherwise leave the paragraph uneven.

    Args:
        levels: voiced level in dBFS of each piece.
        paragraphs: the paragraph number of each piece, in order.

    Raises:
        ValueError: the number of paragraph numbers differs from the number of pieces.
    """
    if len(paragraphs) != len(levels):
        raise ValueError("one paragraph number per piece is required")
    goal = float(np.median(levels))
    gains = [min(goal - level, MAX_BOOST_DB) for level in levels]
    groups: dict[int, list[int]] = {}
    for index, number in enumerate(paragraphs):
        groups.setdefault(number, []).append(index)
    for indices in groups.values():
        ceiling = min(levels[i] + gains[i] for i in indices) + MAX_PARA_SPREAD_DB
        for i in indices:
            gains[i] = min(gains[i], ceiling - levels[i])
    return gains


def level_and_join(pieces: list[np.ndarray], rate: int, paragraphs: list[int]) -> np.ndarray:
    """Apply the `sentence_gains` gain to each piece, join with pauses, hold the peak at 0.98 at most.

    Args:
        pieces: the audio of each sentence.
        rate: sample rate in Hz.
        paragraphs: the paragraph number of each piece, in order.
    """
    levels = [voiced_db(p, rate) for p in pieces]
    pause = np.zeros(int(PAUSE_SECONDS * rate), dtype=np.float32)
    parts = []
    for piece, gain in zip(pieces, sentence_gains(levels, paragraphs)):
        parts += [piece * 10 ** (gain / 20), pause]
    joined = np.concatenate(parts[:-1])
    return joined * min(1.0, PEAK_LIMIT / np.abs(joined).max())


class S2ProSpeaker:
    """S2 Pro and its codec, loaded once; speaks any text in any voice of the voices folder."""

    def __init__(self, voices_dir: Path = DEFAULT_VOICES) -> None:
        """Load the pinned model revision from the local Hugging Face cache (no download).

        Args:
            voices_dir: folder of `<voice>.wav` + `<voice>.txt` pairs.
        """
        checkpoint = Path(snapshot_download(MODEL, revision=REVISION, local_files_only=True))
        self.model, self.decode_one_token = init_model(checkpoint, DEVICE, torch.bfloat16)
        self.codec = load_codec_model(resolve_codec_path(checkpoint), DEVICE, torch.bfloat16)
        self.voices_dir = Path(voices_dir)
        self._voices: dict[str, tuple[int, str, torch.Tensor]] = {}

    @property
    def rate(self) -> int:
        """Sample rate of the audio in Hz."""
        return self.codec.sample_rate

    def voices(self) -> list[str]:
        """Names of the voices in the voices folder."""
        return sorted(p.stem for p in self.voices_dir.glob("*.wav") if p.with_suffix(".txt").exists())

    def _voice(self, name: str) -> tuple[str, torch.Tensor]:
        """Transcript and codec tokens of a voice, encoded once per version of its WAV.

        Raises:
            VoiceError: the voice has no `<name>.wav` + `<name>.txt` pair in the voices folder.
        """
        names = self.voices()
        if name not in names:
            raise VoiceError(f"unknown voice {name!r}; available: {names}")
        wav = self.voices_dir / f"{name}.wav"
        stamp = wav.stat().st_mtime_ns
        cached = self._voices.get(name)
        if cached is None or cached[0] != stamp:
            tokens = encode_audio(wav, self.codec, DEVICE).cpu()
            self._voices[name] = (stamp, wav.with_suffix(".txt").read_text().strip(), tokens)
        return self._voices[name][1], self._voices[name][2]

    def _sentence(self, sentence: str, voice: tuple[str, torch.Tensor]) -> np.ndarray:
        """One request: the audio of one sentence."""
        torch.manual_seed(SEED)
        torch.cuda.manual_seed(SEED)
        responses = generate_long(
            model=self.model, device=DEVICE, decode_one_token=self.decode_one_token, text=sentence, num_samples=1,
            compile=False, prompt_text=[voice[0]], prompt_tokens=[voice[1]],
        )
        codes = torch.cat([r.codes for r in responses if r.action == "sample"], dim=1)
        return decode_to_audio(codes.to(DEVICE), self.codec).cpu().float().numpy()

    def speak(self, text: str, voice: str) -> np.ndarray:
        """Speak a text.

        Args:
            text: paragraphs separated by blank lines.
            voice: name of a voice in the voices folder.

        Returns:
            Mono float32 samples at `self.rate`.

        Raises:
            VoiceError: unknown voice.
            ValueError: the text has no words.
        """
        prompt = self._voice(voice)
        paragraphs = paragraphs_of(text)
        pieces = [self._sentence(sentence, prompt) for paragraph in paragraphs for sentence in paragraph]
        numbers = [number for number, paragraph in enumerate(paragraphs) for _ in paragraph]
        return level_and_join(pieces, self.rate, numbers)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("text_file", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--voice", default="grimaldus")
    parser.add_argument("--voices-dir", type=Path, default=DEFAULT_VOICES)
    args = parser.parse_args()
    start = time.time()
    speaker = S2ProSpeaker(args.voices_dir)
    load_seconds = time.time() - start
    torch.cuda.reset_peak_memory_stats()
    start = time.time()
    audio = speaker.speak(args.text_file.read_text(), args.voice)
    synth_seconds = time.time() - start
    write_render(args.out, audio, speaker.rate)
    print(f"audio {len(audio) / speaker.rate:.1f}s load {load_seconds:.0f}s synthesis {synth_seconds:.0f}s "
          f"rtf {synth_seconds / (len(audio) / speaker.rate):.2f} peak GPU {torch.cuda.max_memory_allocated() / 2**30:.1f} GiB", flush=True)
