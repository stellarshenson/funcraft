"""The transcription rules the endpoint and the Nemotron worker share: prompt, languages, windows, decoding.

The prompt guide and the language support matrix are the Nemotron 3.5 Transcribe model card's; the window
cut is `src/transcribe.py`'s. `decode_audio` turns any upload ffmpeg decodes - mp3, m4a, wav, flac, ogg -
into the model's 16 kHz mono float32 input, refusing a recording the model cannot take before decoding it.
"""
import subprocess
import tempfile
from pathlib import Path

import numpy as np

MODEL_ID = "nvidia/NVIDIA-Nemotron-3.5-Transcribe-30B-A4B"
REVISION = "c17667641642c4265ff2b7037dd101b7d4567634"
SAMPLE_RATE = 16000
MAX_UPLOAD_BYTES = 250 * 1024 * 1024
MAX_SECONDS = 3600
WINDOW_SECONDS = 120
SEARCH_SECONDS = 15
AUTO_LANGUAGE = "as spoken"

# The model card's language support matrix, in its order: the 40 languages with ASR support. Norwegian is
# in the matrix for translation only, so it is not here. "as spoken" is the automatic default, not a language.
LANGUAGES = (
    "Czech", "Dutch", "English", "French", "German", "Hindi", "Italian", "Korean", "Polish",
    "Portuguese", "Russian", "Slovak", "Spanish", "Bulgarian", "Croatian", "Danish", "Estonian",
    "Finnish", "Hungarian", "Japanese", "Latvian", "Lithuanian", "Romanian", "Slovenian", "Swedish",
    "Thai", "Turkish", "Ukrainian", "Arabic", "Bengali", "Chinese Mandarin", "Greek", "Hebrew",
    "Indonesian", "Maltese", "Marathi", "Tagalog", "Tamil", "Telugu", "Vietnamese",
)

WORDING = {
    "verbatim": "Wording: verbatim, including fillers and repetitions.",
    "readable": ("Wording: omit fillers and accidental repetitions; keep the remaining spoken wording "
                 "unchanged."),
}


def build_prompt(language: str, wording: str, context: str = "") -> str:
    """The model card's transcription prompt for a language, a wording style and optional context terms.

    Args:
        language: "as spoken" for automatic detection, or one of `LANGUAGES`.
        wording: "verbatim" keeps fillers and repetitions; "readable" removes fillers and accidental ones.
        context: names and terms the recording uses; an empty context adds nothing.

    Returns:
        The instruction the processor sends with the audio.

    Raises:
        ValueError: `language` is neither "as spoken" nor in `LANGUAGES`, or `wording` is unknown.
    """
    if language != AUTO_LANGUAGE and language not in LANGUAGES:
        raise ValueError(f"unknown language {language!r}; "
                         f"use 'as spoken' or one of the {len(LANGUAGES)} supported languages")
    if wording not in WORDING:
        raise ValueError(f"unknown wording {wording!r}; use 'verbatim' or 'readable'")
    prompt = (f"Audio transcription. Language: {language}. {WORDING[wording]} "
              f"Formatting: punctuation and capitalization. Output: transcript only.")
    terms = context.strip()
    if terms:
        prompt += f" Context terms: {terms}."
    return prompt


def window_bounds(audio: np.ndarray) -> list[tuple[int, int]]:
    """Sample ranges of about `WINDOW_SECONDS`, each cut at the quietest 0.5 s near its end.

    Args:
        audio: mono float32 samples at `SAMPLE_RATE`.

    Returns:
        (start, end) sample pairs that cover every sample once, in order.
    """
    step, bounds, start = SAMPLE_RATE // 2, [], 0
    while len(audio) - start > (WINDOW_SECONDS + SEARCH_SECONDS) * SAMPLE_RATE:
        lo = start + (WINDOW_SECONDS - SEARCH_SECONDS) * SAMPLE_RATE
        hi = start + (WINDOW_SECONDS + SEARCH_SECONDS) * SAMPLE_RATE
        frames = np.abs(audio[lo:hi][: (hi - lo) // step * step]).reshape(-1, step).mean(1)
        cut = lo + int(frames.argmin()) * step + step // 2
        bounds.append((start, cut))
        start = cut
    bounds.append((start, len(audio)))
    return bounds


def decode_audio(data: bytes) -> tuple[np.ndarray, int]:
    """Decode an upload to the model's input: mono float32 samples at `SAMPLE_RATE`.

    ffprobe reads the duration first, so a recording over `MAX_SECONDS` is refused before ffmpeg decodes it.

    Args:
        data: the uploaded file's bytes.

    Returns:
        The samples and `SAMPLE_RATE`.

    Raises:
        ValueError: the upload is over `MAX_UPLOAD_BYTES`, is longer than `MAX_SECONDS`, holds no audio,
            or is not a format ffprobe and ffmpeg can read.
    """
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError(f"the recording is over {MAX_UPLOAD_BYTES} bytes")
    with tempfile.TemporaryDirectory(prefix="asr-") as folder:
        source = Path(folder) / "upload"
        source.write_bytes(data)
        try:
            probed = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(source)],
                capture_output=True, text=True, check=True)
        except FileNotFoundError:
            raise ValueError("ffprobe is not installed") from None
        except subprocess.CalledProcessError as error:
            raise ValueError(f"the recording is not readable audio: {error.stderr.strip()}") from error
        try:
            seconds = float(probed.stdout.strip())
        except ValueError:
            raise ValueError("the recording has no readable duration") from None
        if seconds > MAX_SECONDS:
            raise ValueError(f"the recording is {seconds:.0f} s; the limit is {MAX_SECONDS} s")
        try:
            converted = subprocess.run(
                ["ffmpeg", "-v", "error", "-i", str(source), "-f", "f32le", "-ac", "1",
                 "-ar", str(SAMPLE_RATE), "pipe:1"],
                capture_output=True, check=True)
        except FileNotFoundError:
            raise ValueError("ffmpeg is not installed") from None
        except subprocess.CalledProcessError as error:
            raise ValueError("the recording could not be decoded: "
                             f"{error.stderr.decode(errors='replace').strip()}") from error
    samples = np.frombuffer(converted.stdout, dtype="<f4").astype(np.float32)
    if not samples.size:
        raise ValueError("the recording holds no audio")
    return samples, SAMPLE_RATE
