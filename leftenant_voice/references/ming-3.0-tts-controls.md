# Ming-3.0-TTS control sequences

This note lists how Ming-3.0-TTS 0.5B is told how to speak: the tasks, the inline tags and the control values. Source: the model's `README.md` (cookbook and task table) and `cookbooks/instruction_en.md` in `resources/models/Ming-3.0-tts/`, code revision `a39b806`. Other controlled-voice models are compared in [tts-controlled-voice-models.md](tts-controlled-voice-models.md).

## Rule

One call is one task. A call rejects the controls of another task, so inline tags and an emotion cannot share one call. A longer text can mix them only by speaking each part in its own call.

## Tasks of the 0.5B model

Python API: `ming_tts.MingTTS(...).synthesize(task=..., text=..., ...)`. The lower-case task names in the README (`seed`, `paralinguistic`, `podcast`) belong to the Tiny model's API, not to 0.5B.

| Task | Keeps a cloned voice | Inputs besides `text` | Control |
|---|---|---|---|
| `TTS` | yes | `prompt_wav_path`, `prompt_text` (exact transcript), `use_spk_emb=True` | zero-shot cloning; inline tags in `text` |
| `EMOTION` | yes, from the audio alone | `prompt_wav_path`, `use_spk_emb=True`; no transcript | `controls={"emotion": ...}` |
| `BASIC` | yes, from a speaker embedding | `spk_emb_path` (or the reference audio), `use_spk_emb=True`; no transcript | `controls={"speed": ..., "pitch": ..., "volume": ...}`, all three |
| `MULTILINGUAL` | yes | `prompt_wav_path`, `prompt_text`, `language_id` | target language |
| `DIALECT` | yes | reference audio; no `language_id` | `controls={"dialect": ...}` |
| `FREEFORM` | no; the authors advise against a reference | `use_zero_spk_emb=True` | `instruction="<natural-language description of voice and delivery>"` |
| `VOICE_DESIGN` | no | `use_zero_spk_emb=True` | `controls={"style": "<description of the voice>"}` |
| `IP` | no; a built-in voice | `use_zero_spk_emb=True` | `controls={"ip": "UK_George"}`; recommended: `UK_George`, `US_Emma`, `灵小柔`, `灵楷` |

## Inline paralinguistic tags

Written anywhere in the text, in English or Chinese text. Case-sensitive, brackets included. They bypass text normalisation and reach the model unchanged.

| Tag | Sound |
|---|---|
| `[Breathing]` | audible breath |
| `[Cough]` | cough |
| `[Sigh]` | sigh |
| `[Laughter]` | laughter |
| `[Uhm]` | hesitation filler |
| `[Surprise-ah]` | surprised "ah" |
| `[Surprise-oh]` | surprised "oh" |
| `[Dissatisfaction-hnn]` | disgruntled "hnn" |
| `[Confirmation-en]` | affirming "en" |
| `[Question-ei]` | questioning "ei" |
| `[Question-ah]` | questioning "ah" |
| `[Question-en]` | questioning "en" |
| `[Question-oh]` | questioning "oh" |
| `[Question-huh]` | questioning "huh" |

Example: `model.synthesize(task="TTS", text="[Sigh] The rain has not stopped. [Breathing] We hold here.", prompt_wav_path=..., prompt_text=..., use_spk_emb=True)`

## Control values

The model takes the values exactly as written in the first column; the English words are glosses, not aliases.

| Control | Value | Meaning |
|---|---|---|
| `emotion` | `高兴` | happy |
| | `悲伤` | sad |
| | `愤怒` | angry |
| | `恐惧` | fearful |
| | `厌恶` | disgusted |
| | `惊讶` | surprised |
| | `中性` | neutral |
| `speed` | `慢速` / `中速` / `快速` | slow / medium / fast |
| `pitch` | `低` / `中` / `高` | low / medium / high |
| `volume` | `低` / `中` / `高` | low / medium / high |
| `dialect` | `cantonese`, `chuanyu dialect` | Cantonese, Sichuan-Chongqing |

## Control sequences in leftenant_voice texts

`src/speak.py` reads a text file paragraph by paragraph (paragraphs are separated by a blank line) and gives each paragraph its own Ming call. The parser is `src/speak_text.py`; the worked example is `texts/inspiring-speech-controlled.txt`.

| Paragraph form | Ming task | Example |
|---|---|---|
| plain text | `TTS`, cloned from the chosen reference clip and its transcript | `Hold the line.` |
| text with inline tags | `TTS` with the tags | `[Breathing] Our enemy is not a person.` |
| opens with an emotion directive | `EMOTION` | `{emotion: angry} Do not listen.` |
| opens with a speed, pitch and volume directive | `BASIC` | `{speed: slow, pitch: low, volume: medium} Listen to me, team.` |

- Directive names and values are English and are mapped to Ming's Chinese values: emotion `happy`, `sad`, `angry`, `fearful`, `disgusted`, `surprised`, `neutral`; speed `slow`, `medium`, `fast`; pitch and volume `low`, `medium`, `high`
- In a `BASIC` directive a missing speed, pitch or volume is `medium`; an emotion cannot be combined with speed, pitch or volume
- A paragraph with both a directive and an inline tag is an error that names its line, because Ming rejects tags in `EMOTION` and `BASIC`
- `EMOTION` and `BASIC` take the voice from the reference audio alone, without its transcript; measure the voice likeness of such paragraphs
- Whole-text controls: `--emotion`, `--speed`, `--pitch`, `--volume` on `src/speak.py`, or `EMOTION`, `SPEED`, `PITCH`, `VOLUME` on `make speak`

## Languages

`language_id`: `zh` Chinese, `en` English, `ja` Japanese, `ko` Korean, `de` German, `fr` French, `es` Spanish (short codes or full names). Chinese and English work without it; the other five need it. The voice comes from the reference recording, not from the language.
