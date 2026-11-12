# leftenant_voice

Speaks a given text in a voice cloned from a recording. The text-to-speech model is Ming-3.0-tts-0.5B (Ant Group, team inclusionAI, MIT licence). It runs on the RTX PRO 4000 Blackwell (nvidia-smi index 0) and clones a voice zero-shot from a reference clip and its transcript.

The folder is self-contained. Nothing outside it is referenced except `uv`, a Python 3.11 that `uv` finds, and the GPU.

## Inputs

- The recordings of the four voices, as received, in `resources/assets/`: Dijkstra and Vesemir (The Witcher 3), Setrakian (The Strain), Grimaldus (Helsreach) and the Doctor (Doctor Who, The Zygon Inversion)
- No system package is needed beyond `uv`: the audio decoder is the ffmpeg binary of the `imageio-ffmpeg` package
- Demucs `htdemucs` (PyPI `demucs`, installed by `make install-tools`) separates the voice from music in the two short recordings
- FlashAttention 2.8.3, a prebuilt wheel installed by `make install` (torch 2.7, CUDA 12, Python 3.11); it runs on the RTX PRO 4000 (sm_120)
- The model code, cloned by `make install` to `resources/models/Ming-3.0-tts` at commit `a39b806`
- The model weights, downloaded by `make install` to `~/.cache/huggingface/hub` at revision `7247f4c` (2.96 GB); a copy is kept on the NAS in `/mnt/nas-shared/models/inclusionAI--Ming-3.0-tts-0.5B/`

## Commands

| Command | What it does |
|---|---|
| `make install` | creates `.venv-ming` (Python 3.11, torch 2.7.1 for CUDA 12.8), installs the model's requirements, clones its code and downloads its weights |
| `make smoke` | speaks one English sentence in the built-in voice to `wip/smoke.wav` and logs device, load time, real-time factor and peak VRAM to `wip/logs/smoke.log` |
| `make install-tools` | creates `.venv-tools` (torch 2.7.1 for CUDA 12.8, transformers from source for Nemotron, speechbrain, librosa, demucs) and downloads Nemotron and the speaker model |
| `make voices` | builds the clean segments and reference clips of the five voices from the recordings in `resources/assets/`; the table of voices and recordings is at the top of the `Makefile` (see Voices) |
| `make mp3` | converts every WAV left under `out/` (`MP3DIR=<folder>` narrows it) to MP3 with `ffmpeg -q:a 2`, checks that the lengths agree within 0.2 s and moves the WAV to the trash; the `speak` targets run it at their end |
| `make speak VOICE=<name> TEXT="<text>" OUT=<path>` | speaks the text in the voice (`dijkstra`, `vesemir`, `setrakian`, `grimaldus` or `doctor`) and writes one MP3 at 44.1 kHz (a `.wav` name under `out/` is written as the `.mp3` of the same name); `FILE=<path>` replaces `TEXT=` to read the text from a file; relative paths are taken from the folder `make` runs in; `EMOTION=`, `SPEED=`, `PITCH=`, `VOLUME=` add whole-text controls (see Controls) |

## Speaking

`src/speak.py` splits the text at sentence ends, speaks each sentence with the voice's chosen reference clip (`resources/voices/<voice>/chosen.txt`, the clip with the highest speaker similarity among those with a word error rate of at most 10 % on the test sentence), joins the sentences with a pause of 0.4 s and scales the result down if a sample exceeds 0.98. `--ref <n>` picks another clip. The model runs with FlashAttention 2 on its Qwen2 backbone. The speech in `texts/inspiring-speech.txt` is rendered to `out/inspiring-speech-<voice>.mp3`, and the same speech marked for delivery in `texts/inspiring-speech-controlled.txt` to `out/inspiring-speech-<voice>-controlled.mp3`. Every render in `out/` is an MP3 and no WAV stays there; work files under `wip/` stay WAV.

The second number in `chosen.txt`, if present, is the reference clip for EMOTION and BASIC paragraphs; they clone the voice from the audio alone, and another clip can match the voice better (`dijkstra` is `3 2`).

## Controls

Ming takes one task per call, so `src/speak_text.py` splits the text at blank lines and gives each paragraph its own task. A paragraph is spoken in one of three ways:

| Form in the text | Task | Example |
|---|---|---|
| Inline tags anywhere in the paragraph | `TTS` with the clip and its transcript | `[Breathing] Hold the line. [Sigh] It is a long night.` |
| `{emotion: <e>}` at the start | `EMOTION` | `{emotion: angry} Do not listen.` |
| `{speed: <s>, pitch: <p>, volume: <v>}` at the start | `BASIC` | `{speed: slow, pitch: low, volume: medium} Listen to me.` |

- Tags (case-sensitive, with brackets): `[Breathing]` `[Cough]` `[Sigh]` `[Laughter]` `[Uhm]` `[Surprise-ah]` `[Surprise-oh]` `[Dissatisfaction-hnn]` `[Confirmation-en]` `[Question-ei]` `[Question-ah]` `[Question-en]` `[Question-oh]` `[Question-huh]`
- Emotions: `happy` `sad` `angry` `fearful` `disgusted` `surprised` `neutral`
- Speed `slow` `medium` `fast`; pitch and volume `low` `medium` `high`; a missing one of the three is `medium`
- A paragraph with a directive and tags is an error that names the line; so are an unknown tag, name or value
- Whole-text options give the same controls to every paragraph without a directive or tags: `--emotion angry`, or `--speed slow --pitch low --volume medium`; with make: `make speak VOICE=vesemir FILE=texts/inspiring-speech.txt OUT=out/slow.mp3 SPEED=slow PITCH=low`
- Full reference of the model's controls: `references/ming-3.0-tts-controls.md`

EMOTION and BASIC take the voice from the audio alone, and the speaker similarity of such paragraphs to the voice is lower than that of TTS paragraphs (0.4 to 0.6 against 0.7 to 0.8, measured). The delivered controlled speeches keep every directive: no paragraph is moved back to TTS because of a low similarity. `[Confirmation-en]` is spoken as the word "Confirmation" in the Setrakian and Grimaldus voices. `[Surprise-oh]` is transcribed "Oh" in all four voices and `[Uhm]` "Um" in three (not Setrakian); `[Breathing]` is not a word and no transcript shows it.

Measurement scripts, run in `.venv-tools`: `score_words.py` transcribes WAV files with Nemotron on GPU 2, `score_speaker.py` gives their cosine similarity to each voice centroid on GPU 0, and `measure_audio.py` combines both with the word error rate, the peak and the longest silence. For controlled renders: `measure_paragraphs.py` (task, similarity, word error rate, rate and level per paragraph), `measure_tags.py` (sound before speech at each tag, against the same sentence without the tag) and `measure_basic.py` (rate and level of BASIC paragraphs against the plain render).

## Voices

`make voices` builds five voices, `dijkstra`, `vesemir`, `setrakian`, `grimaldus` and `doctor`, from the recordings in `resources/assets/`. The steps, one script each in `src/`:

1. `decode_audio.py` writes a mono WAV at 16 kHz (speech recognition) and at 44.1 kHz (the Ming sample rate) to `wip/voices/<voice>/`
1b. `separate_voice.py` (Setrakian, Grimaldus and Doctor only, listed in `DEMUCS_VOICES`) replaces the audio by the vocals stem of Demucs `htdemucs` on GPU 0 and keeps the mixed audio as `mixed-44k.wav` and `mixed-16k.wav`; without it the music under the voice leaves no segment that passes the pause filter
2. `transcribe.py` transcribes windows of about 120 s, cut at quiet points, with NVIDIA Nemotron 3.5 Transcribe (full bf16 checkpoint, revision `c176676`) on GPU 2, the RTX PRO 5000 72GB. It saves the text and the alignment tensors of each window; the model needs 62.4 GiB, so nothing else may use GPU 2
3. `align.py` gives each word a start and end time, cuts the words into sentence pieces and measures how well the text fits the sound (CTC loss per token, `nll`)
4. `embed.py` embeds each piece of 1 s or more with the SpeechBrain ECAPA model on GPU 0
5. `build_voice.py` clusters the embeddings, takes the group with the most speech as the target speaker, joins neighbouring pieces into segments of 2 to 20 s and keeps those that pass the filters below
6. `verify_segments.py` transcribes every kept segment and reference clip again on its own and records the word error rate against the stored text in `wip/voices/<voice>/verify.csv`
7. `prune_segments.py` removes the segments with a word error rate above 0.2 from `metadata.csv` and deletes their files

Segment filters: `nll` at most 0.6, the quietest 50 ms frame within 0.3 s around the segment at most -60 dBFS (no music or noise bed under the voice), no sample at or above 0.99 of full scale.

Each voice has `wip/voices/<voice>/segments/*.wav` with `metadata.csv` (`file|text|seconds`), `centroid.npy` (mean speaker embedding of all pieces of the target group) and `speaker-model.txt`. The three reference clips for cloning are `resources/voices/<voice>/ref-1.wav` to `ref-3.wav`, each with its transcript in `ref-N.txt`: complete sentences of 4 to 8 s with `nll` at most 0.1, closest to the centroid, at least 30 s apart in the recording. A short recording that gives fewer than three such clips gets the relaxed rule of `build_voice.py` (3 to 8 s, `nll` at most 0.15, any start, 10 s apart), and a recording under one minute (Setrakian) the last rule (2.5 to 8 s, `nll` at most 0.6, no overlap); it may still end with fewer than three clips.

## Speaking with Fish Audio S2 Pro

The winning voice of the TTS trial is Fish Audio S2 Pro cloning `grimaldus`: `make -f s2pro.mk speak VOICE=grimaldus FILE=<text file> OUT=out/<name>.mp3 FGPU=2` (needs `make -f fish.mk install` and `make -f s2pro.mk install`). It speaks one request per sentence, levels the sentences and joins them with 0.4 s pauses. Method, measures, limits and licence (non-commercial): `references/fish-audio-s2-pro.md`. The HTTP service and its Docker image, text in and MP3 out, are described in `service/README.md`.

## Layout

```
src/          scripts
texts/        texts to speak
in/           files as received (not in git)
resources/    assets/ the recordings, models/ the model code, voices/ the reference clips (not in git)
wip/          intermediate files and logs (not in git)
out/          finished audio (not in git)
```

The recordings are game audio of real voice actors. They, every clip cut from them and every cloned output stay on this workstation. Audio files are ignored by git in every folder.
