# Fish Audio S2 Pro - the voice engine of leftenant_voice

Fish Audio S2 Pro (`fishaudio/s2-pro`) clones a voice zero-shot from a recording and its transcript. Its render of the grimaldus status text, `out/trial/status-grimaldus-s2pro-fixed.mp3`, is the winner of the TTS trial. Written 2026-11-07.

## Why it won

The Star Colonel chose `out/trial/status-grimaldus-s2pro-fixed.mp3` by ear on 2026-11-07 ("winner"). The bars do not rank the models: the similarity to the voice ranks S2 Pro low and the choice was by ear. The trial measured 18 renders of the same text (about 92 s of speech, 5 paragraphs, 19 sentences):

| Render | WER % | Own similarity (ECAPA) | Real-time factor | Peak GPU GiB | Commercial use |
|---|---|---|---|---|---|
| S2 Pro, fixed (the winner) | 0.0 to 0.4 | 0.782 | 2.55 | 18.4 | needs a Fish Audio licence |
| S2 Pro, trial render (one request per paragraph) | 0.0 | 0.650 | 3.14 | 19.3 | as above |
| F5-TTS | 0.4 | 0.847 | 0.79 | 1.6 | no (CC BY-NC) |
| AuK-Flash | 0.0 | 0.833 | 0.09 | 17.8 | no (Qwen Research encoder) |
| Higgs TTS 3 | 0.4 | 0.748 | 0.26 | 64.4 | no |
| Audio8-Air | 0.0 | 0.685 | 3.01 | 3.2 | yes (Apache 2.0) |
| Fish Audio Drama 3 | 0.9 | 0.605 | 0.45 | 42.7 | Community License |
| Ming plain | 0.0 | 0.780 | - | 3 | yes (MIT) |

Source: `tmp/workflows/tts-trial/comparison.md`, `tmp/workflows/s2pro-fade/s2pro-fade.md` and the reproduction below. Every render of the trial met the bars (WER at most 10 %, own centroid highest, peak below 0.999).

## Method

`src/fish/speak_s2pro.py` (module `S2ProSpeaker`, one class, model loaded once):

1. Split the text at blank lines into paragraphs and each paragraph at sentence ends (`PARAGRAPH` and `split_sentences` of `src/speak_text.py`)
2. One request per sentence to `generate_long` of the fish-speech code, with the voice recording as the prompt (tokens encoded once per voice), bfloat16, no compile, the code's sampling defaults (temperature 0.7, top-p 0.7, top-k 30) and seed 42 set before every request
3. A gain per sentence to the median voiced level of the text (frames above -50 dBFS), a positive gain capped at +3 dB so the sentence's background hiss rises no more (`MAX_BOOST_DB` in `src/fish/speak_s2pro.py`); attenuation is not capped. The loud sentences of a paragraph are then trimmed (attenuation only) so the paragraph spread stops at `MAX_PARA_SPREAD_DB` (1.2 dB), because a capped quiet sentence would otherwise leave it uneven
4. Join with 0.4 s of digital silence; scale down if the peak exceeds 0.98
5. Write through `src/audio_out.py`: an MP3 at `-q:a 2`, 44.1 kHz

Why one request per sentence: the fish-speech code splits a text only at `<|speaker:N|>` tags, so a paragraph is one request whatever `chunk_length` says. A request of 18 to 24 s drifts down 3 to 8 dB in level; requests of one sentence hold -21 to -24 dB. Details: `tmp/workflows/s2pro-fade/s2pro-fade.md`.

## Settings

| Setting | Value |
|---|---|
| Model | `fishaudio/s2-pro`, revision `1de9996b6be38b745688de084d87a5633f714e4e` (2026-03-11), 11 GB, gated; `make -f s2pro.mk install` downloads it |
| Code | `src/fish/fish-speech`, commit `0f8a12e8a651062fdee9c33a894bdccd3a8513f1`, run in `.venv-fish` (`make -f fish.mk install`) |
| Voice | `wip/fish/refs/grimaldus.wav` (15.7 s) and `grimaldus.txt` |
| Seed, sampling | 42 per request, code defaults |
| Pause, peak | 0.4 s, 0.98 |

## Measures

The winner and the reproduction by `speak_s2pro.py` (text `tmp/workflows/ming-status/status-plain.txt`; measured on the MP3 files with Nemotron 3.5 Transcribe and ECAPA). The capped reproduction is a fresh render through `tmp/workflows/gpu-queue.sh` on GPU 0, with the same text, voice, seed and settings:

| Measure | Winner | Reproduction | Reproduction, gain capped |
|---|---|---|---|
| Duration | 95.6 s | 95.6 s | 95.8 s |
| Worst paragraph level range | 0.4 dB | 0.4 dB | 1.3 dB (paragraph 2) |
| File level range | 0.6 dB | 0.6 dB | 1.8 dB |
| Word error rate | 0.0 | 0.0 | 0.004 (Grimaldus heard as Grimaldi) |
| ECAPA to grimaldus (next: dijkstra) | 0.782 (0.355) | 0.782 (0.356) | 0.778 (0.375) |
| Peak | 0.754 | 0.748 | 0.837 |
| Longest pause inside a paragraph | 1.29 s | 1.29 s | 0.54 s |
| Load, synthesis, real-time factor | - | 43 s, 244 s, 2.55 | 46 s, 229 s, 2.39 |
| Peak GPU memory (torch allocated) | - | 18.4 GiB | 18.4 GiB |

The MP3 files differ in bytes. The peak differs by 0.006 and one sentence level by 0.1 dB. The winner's per-sentence pieces were written as 16-bit WAV files before the gain; the new module keeps float samples. GPU sampling is not bit-exact between runs either; which of the two caused the difference was not separated.

Hiss of the capped render, at its quietest sentence (`Both of his speeches are finished, though they are quiet.`, paragraph 2): the gain wanted +4.63 dB and was held at +3.00 dB, and the 10th-percentile frame level inside the sentence rose 3.00 dB, from -61.13 to -58.13 dBFS (the 5th percentile also 3.00 dB, -67.63 to -64.63). The earlier worst measured gain was +6.9 dB (variant a3, piece a3-p4s4: 10th percentile -44.1 to -37.2 dBFS). Four loud sentences of that paragraph were then trimmed by 0.43 to 0.44 dB, which brings the paragraph range to 1.3 dB (1.32 dB by the MP3 word-window measure) against the accepted 1.5 dB; the quiet sentence keeps its full +3 dB.

## Limits

- Speed: a real-time factor of about 2.5 to 3 (95 s of speech takes about 4 min after a 45 s load), without the compiled path or the SGLang engine the model card recommends
- GPU memory: about 19 GiB allocated, so it fits a 24 GB card and not a 16 GB card
- The gain raises the noise inside a quiet sentence by the same amount; the worst measured was +6.9 dB (variant a3). The fade fix now lifts the hiss by at most 3 dB, and a quiet sentence sits up to 3.9 dB below the median; the loud sentences of its paragraph are trimmed so the paragraph spread stops at 1.2 dB (1.3 dB measured)
- No Scottish accent: the plain render and ten tag and sampling variants (`[Scottish accent]` and nine others) were rendered and scored with an accent classifier; none was classed Scotland, and the recording's accent dominates (`tmp/workflows/s2pro-fade/s2pro-fade.md`)
- One sentence is one request: a very long sentence is one long request and can drift

## Licence

Fish Audio Research License (2026-03-07): free for research and non-commercial use. Commercial use, including a paid or hosted service, needs a written licence from Fish Audio (business@fish.audio). Outputs may not be used to train a foundation model. Redistribution needs the licence copy, a notice file and "Built with Fish Audio". The Acceptable Use Policy, incorporated by reference, was not read; imitating a real person's voice falls under it. The recordings of `leftenant_voice` are game audio of real voice actors.

## Run

```
make -f fish.mk install        # once: .venv-fish
make -f s2pro.mk install       # once: the weights
make -f s2pro.mk speak VOICE=grimaldus FILE=texts/x.txt OUT=out/x.mp3 FGPU=2
```

`FGPU=2` waits in `tmp/workflows/gpu2-queue.sh`; another index runs on that card directly. An `.mp3` output needs `ffmpeg` on PATH (`src/audio_out.py` encodes it; the Docker image carries it). A voice is a pair `<voice>.wav` + `<voice>.txt` in `wip/fish/refs/`. The HTTP service and Docker image are in `service/README.md`.
