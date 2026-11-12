# Fish Audio Drama 3 trial beside Ming

Fish Audio Drama 3 was run on the two voices of `leftenant_voice` (`dijkstra`, `vesemir`) with the speech of `texts/inspiring-speech-controlled.txt` translated into Fish syntax, and measured against Ming-3.0-TTS 0.5B on the same speech. Written 2026-11-06. The control syntax is in [fish-audio-drama-3-controls.md](fish-audio-drama-3-controls.md); the model families are compared in [tts-controlled-voice-models.md](tts-controlled-voice-models.md).

## Result

- Fish and Ming match in speaker similarity and word error rate; Fish is 0.5-0.6 of real time against Ming's 1.8-3.2, and takes 42 GiB of GPU memory against Ming's 3 GiB
- Fish carries more of the controls: breaths, sighs and the spoken "hmm" were audible in 12 of 12 placements by energy, against 7 of 12 for Ming (Fish's `[pause]` was audible in 1 of 2, and Ming has none); whisper, emphasis and the loud close change level measurably, where Ming's volume control changed nothing
- Fish speaks 35 to 37 % slower than Ming from the same reference (103.5 s and 110.0 s against 75.5 s and 81.5 s), and the `<slow>` tag shows no further slowing
- Licence trap for these two voices: the Fish Audio Community License forbids speech that imitates an identifiable natural person without consent (section IV(b)); Dijkstra and Vesemir are game characters with voice actors, so the cloned voices fall under that clause even for private use. Ming's MIT licence has no such clause
- The measurements are energy and timing only; no listening was done, so the comparison by ear is open

## Facts

| Fact | Value | Source |
|---|---|---|
| Hugging Face id and revision | `fishaudio/drama-3` at `78e5ab79e49aa9a25abe8799eff2c4d73a1c3216`; weights ungated, no token | https://huggingface.co/fishaudio/drama-3 |
| Code | `fishaudio/fish-speech` 3.0.0 at `0f8a12e8a651062fdee9c33a894bdccd3a8513f1` (2026-10-30) | https://github.com/fishaudio/fish-speech |
| Size | 35B parameters, about 3B active per token; mixture-of-experts text backbone with hybrid full and linear attention, codebook decoder with 10 codebooks, 44.1 kHz mono output | model card; https://sgl-project.github.io/sglang-omni/cookbook/fishaudio_drama3.html |
| Weights on disk | 41.5 GB (39 GiB): 15 safetensors shards, `codec.pth` 1.87 GB; experts in FP8, the rest bf16 | file listing of the model card |
| Smaller checkpoint | `fishaudio/drama-3-int4`, GPTQ 4-bit, engine weights 20.8 GB instead of 37.0 GB, WER the same on Seed-TTS English | SGLang cookbook, "Int4 Checkpoint" |
| GPU memory | at least 48 GB for FP8; NVIDIA only, no CPU, MPS or ROCm, no `--compile` | https://github.com/fishaudio/fish-speech/blob/main/docs/en/install.md |
| Engines | SGLang-Omni (recommended by Fish), vLLM-Omni (`vllm serve fishaudio/drama-3 --omni`), the repository's command line and API server | model card; https://recipes.vllm.ai/fishaudio/drama-3 |
| Engine used here | the repository's own `generate_long` (one process, one GPU, one pass per paragraph, `--single-chunk` behaviour) in `src/fish/speak_fish.py` | `fish_speech/models/text2semantic/inference.py` |
| Sampling | repository and API defaults temperature 0.7, top-p 0.7, top-k 30 (used here, seed 42); SGLang serving uses 1.0 and 0.9; Fish's reference sampling recommends 1.0, top-p 1.0, no top-k, epsilon cutoff 1e-3 | https://github.com/fishaudio/fish-speech/blob/main/docs/en/inference.md; SGLang cookbook, "Defaults Parameters" |
| Reference clip | clip plus its exact transcript; each reference at most 60 s; the model card example uses 3.9 s; Fish's S2-Pro page names 10-30 s for a timbre (used here: 17.6-18.2 s) | SGLang cookbook, "Reference Audio Length"; https://github.com/fishaudio/fish-speech/blob/main/README.md |
| Long text | split into chunks of about 300 UTF-8 bytes with at most three speakers unless `--single-chunk`; one chunk is at most 1024 frames (47 s) by default | inference.md "Model differences" |
| Published speed | H200: real-time factor 0.131 at concurrency 1 streaming; one H100: first audio 126 ms, real-time factor 0.28 | model card "Production Serving"; vLLM recipe |
| Known fault | a tag or filler at the very start of a line more often renders the first word and then silence until `max_new_tokens`; mid-sentence tags are more reliable | vLLM recipe, "Known limitations" |
| Release and report | 2026-10-13; technical report arXiv 2610.18010 | https://arxiv.org/abs/2610.18010 |

## Licence

Fish Audio Community License Version 1.0, last updated 2026-10-13, text in the model repository (`LICENSE`): https://huggingface.co/fishaudio/drama-3/blob/main/LICENSE

- Research and non-commercial use are free, and "Non-Commercial Purpose" names personal (hobbyist) use and evaluation and testing: private use of this trial is inside the licence (section II)
- Commercial use is free below USD 500,000 annual revenue of the user and its affiliates, with a notice to business@fish.audio within 30 days of reaching it (section III)
- A hosted service (an API or website where third parties supply text or voice samples) needs a separate licence (section III(c))
- Forbidden for every use, including output: speech that imitates the voice of an identifiable natural person without that person's prior consent or another legal right; impersonation to deceive; sexual content with a minor's voice; removing a watermark or provenance signal; training or distilling another speech model from the model or its output (section IV(b))
- Distribution of the weights needs a copy of the licence, the notice "These Fish Audio Materials are licensed under the Fish Audio Community License, Version 1.0. Copyright (c) 39 AI, INC. All Rights Reserved.", and "Built with Fish Audio" on the related page (section IV(a)); the NAS copy keeps the `LICENSE` file
- The user owns the outputs as far as the law permits (section IV(c)(iii))
- Open question for the owner: whether the voices of the two game characters count as "identifiable natural person" voices under section IV(b); the licence does not say

## Setup and files

- `fish.mk`: `make -f fish.mk install` creates `.venv-fish` (Python 3.12, torch 2.8.0 for CUDA 12.8, the repository pins), clones the code to `src/fish/fish-speech`, and downloads the weights; `make -f fish.mk speak VOICE=<name> FILE=<text> OUT=<wav>` renders on GPU 1 (`FGPU=`); `make -f fish.mk nas` archives the weights on the NAS
- System packages added with apt: `portaudio19-dev`, `ffmpeg`, `rsync`
- `src/fish/speak_fish.py` renders; `src/fish/build_refs.py` builds the references; `src/fish/asr_words.py`, `tag_events.py` and `measure_fish.py` measure
- References: `wip/fish/refs/<voice>.wav` and `.txt`, 18.2 s for `dijkstra` (chosen clip 3, then two clean segments) and 17.6 s for `vesemir` (chosen clip 1, then three clean segments)
- Speech: `texts/fish/inspiring-speech-fish.txt`; renders `out/fish/inspiring-speech-<voice>-fish.wav` with a timing file `.json`; paragraph WAVs in `wip/fish/paragraphs/<voice>/`
- Measurements: `wip/fish/measure/result.json`, transcripts in `wip/fish/measure/words-*.json`
- NAS archive: see the status line at the end of this note

## Comparison with Ming's controlled speech

The same speech text; Ming's renders are `out/inspiring-speech-<voice>-controlled.wav` as they stood at 19:23, copied to `wip/fish/ming/` before measuring; every Ming number in this note is of that copy (sha256 `4470dcba...` dijkstra, `a40bc83e...` vesemir). The other workflow rewrote the live files at 19:29-19:30 (now 74.5 s and 80.3 s, 1.0 s and 1.2 s shorter) and may rewrite them again, so the live files are not the compared ones. Fish ran on the RTX PRO 6000 (GPU 1) alone; Ming ran on the RTX PRO 4000 (GPU 0).

| Measure | dijkstra Fish | dijkstra Ming | vesemir Fish | vesemir Ming |
|---|---:|---:|---:|---:|
| Audio duration | 103.5 s | 75.5 s | 110.0 s | 81.5 s |
| Synthesis time | 62.5 s | 238.1 s | 54.0 s | 248.7 s |
| Real-time factor | 0.60 | 3.15 | 0.49 | 3.05 |
| Peak GPU memory | 42.1 GiB | 3.0 GiB | 42.0 GiB | 3.0 GiB |
| Word error rate | 0.014 | 0.019 | 0.014 | 0.009 |
| ECAPA similarity to own centroid | 0.782 | 0.773 | 0.754 | 0.757 |
| ECAPA similarity to the other voice | 0.301 | 0.377 | 0.291 | 0.321 |

- Fish synthesis time is the sum of the seven paragraph calls after a warm-up call; loading took 42-71 s with a warm file cache (211 s the first time), and the CUDA graphs are captured in the warm-up
- Ming's rate of 3.05-3.15 is from the render logged next to those WAVs, which ran while other renders shared the machine; the earlier uncontended Ming renders of the same text ran at 1.81-1.97 (`wip/logs/render-ctl*-<voice>.log`), so Fish is about 3 to 4 times faster than the uncontended Ming renders and 5 to 6 times faster than the logged run
- Ming's peak is `max_memory_allocated` of the smoke test (`wip/logs/smoke-flash.log`), not of this render
- Word error rate: Nemotron 3.5 Transcribe against the text without tags, the transcripts of the seven paragraph WAVs joined; Fish's rate is mostly its spoken "Hmm" for `[hmm]` (one inserted word); Ming read `[Confirmation-en]` aloud as "Confirmation in" for `dijkstra` and skipped it for `vesemir`
- ECAPA: `speechbrain/spkrec-ecapa-voxceleb` on the CPU against `wip/voices/<voice>/centroid.npy`; the loud closing paragraph scores lowest in both models (Fish 0.557 and 0.429, Ming 0.533 and 0.565)

## Are the controls audible

Method: Nemotron word times locate each tag between the words around it. A point tag counts as audible if the gap at its place is at least 0.2 s longer than an ordinary untagged sentence-end gap of the same render, or its loudest 25 ms is at least 6 dB above that gap's and above -50 dBFS. This shows that something fills the gap, not that it sounds like a breath.

| Tag | Fish (placements audible) | Ming (placements audible) |
|---|---|---|
| breath: Fish `[breath]`, Ming `[Breathing]` | 8 of 8 (peaks -43 to -28 dBFS) | 4 of 8 (`dijkstra` 0 of 4, `vesemir` 4 of 4) |
| sigh: `[sighs]`, `[Sigh]` | 2 of 2 | 2 of 2 |
| "hmm": `[hmm]`, `[Confirmation-en]` | 2 of 2 (spoken "hmm", peak -18 dBFS) | 1 of 2 |
| `[pause]` | 1 of 2 (gap 0.77 s and 0.58 s against baseline 0.53 s and 0.55 s) | no equivalent |

| Whole-paragraph and word-level controls | Fish `dijkstra` | Fish `vesemir` | Ming |
|---|---|---|---|
| `<whisper>` on one word: level against the rest of the paragraph | -7.8 dB | -4.7 dB | no equivalent |
| `<emphasis>` on "Do not listen.": level, rate | +3.9 dB, 1.7 against 2.7 words/s | +2.0 dB, 1.4 against 2.3 | no equivalent |
| `<emphasis>` on "Victory": level | +2.1 dB | +0.9 dB | no equivalent |
| Loud close: level against paragraphs 1-6 | +7.2 dB | +7.4 dB | +0.8 dB `dijkstra`, +0.5 dB `vesemir` (`volume: high`) |
| Slow opening: rate of paragraph 1 against the others | 2.16 against 2.31 words/s | 1.99 against 2.12 | 2.70 against 3.15; 2.59 against 2.98 |
| `<slow>` on "Listen to me, team." | 2.78 against 2.18 words/s (no slowing) | 2.72 against 1.99 | no equivalent |
| Angry paragraph: level against the others | -1.6 dB | -3.8 dB | -1.2 dB; -0.3 dB |

- The slow opening is 6 % slower than the other paragraphs in Fish and 13-14 % slower in Ming; the `<slow>` tag on three words did not slow them
- The angry style prefix did not raise the level in either model; whether it changes the delivery needs a listening check
- Pitch was not measured: the pitch tracker returned octave errors on the loud close

## Status of the NAS archive

See `wip/fish/nas.verified` (present only after every file was compared byte for byte) and `logs/fish-nas.log`; the sidecar `/mnt/nas-shared/models/fishaudio--drama-3.md` and the row in `INDEX.md` are written only after that check.
