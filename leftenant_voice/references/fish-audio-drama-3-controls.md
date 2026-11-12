# Fish Audio Drama 3 control sequences

This note lists how Fish Audio Drama 3 is told how to speak: the speaker token, the point tags, the scoped tags, the style prefix and the notes. It mirrors [ming-3.0-tts-controls.md](ming-3.0-tts-controls.md), and the last table maps every Ming control to its Fish form. Facts about the model, its licence and its measurements are in [fish-audio-drama-3.md](fish-audio-drama-3.md).

Sources, used below by number:

- [1] Technical report, Appendix C "Control Syntax Reference", Table 10 and Appendix B: https://arxiv.org/abs/2610.18010
- [2] Model card: https://huggingface.co/fishaudio/drama-3
- [3] vLLM recipe, section "Event and emotion tags" and "Known limitations": https://recipes.vllm.ai/fishaudio/drama-3
- [4] SGLang-Omni cookbook: https://sgl-project.github.io/sglang-omni/cookbook/fishaudio_drama3.html
- [5] Inference guide of the code repository: https://github.com/fishaudio/fish-speech/blob/main/docs/en/inference.md

## Rule

Only the speaker token (`<|speaker:N|>`), the line separator and the hints are special tokens. Every other control is ordinary text in square or angle brackets, so any short wording is accepted; the examples in the report are examples, not a closed list [1][3]. Controls hold a few words, no nested brackets and no line breaks; text in round parentheses is spoken [1]. Unlike Ming, one call can mix every control: tags, an emotion and a scoped tag share one text.

## Point tags

Form: `[words]` written where the event should land. The tag acts at its position [1].

| Tag | Sound | Example | Source |
|---|---|---|---|
| `[sighs]` | a sigh | `Well [sighs] fine, you win.` | [1][2][3] |
| `[laughs]`, `[laughing]` | laughter | `[laughs] Well, maybe that's fair.` | [1][2][3] |
| `[pause]` | a pause | `Hold the line. [pause] Now begin.` | [1][3] |
| `[gasps]` | a gasp | `[gasps] You came back.` | [1] |
| `[clears throat]` | throat clearing | `[clears throat] Listen to me.` | [1] |
| `[hesitates]` | a hesitation | `I think [hesitates] we should go.` | [1] |
| `[breath]`, `[hmm]` | a breath; a spoken "hmm" | `Our enemy is not a person. [breath] Our enemy is the deadline.` | [1] convention; free wording, see below |

- Table 10 does not list `[breath]` or `[hmm]`. Appendix C says every point tag is free natural language and Table 10 only gives examples; the report's benchmark section names a breath as a paralinguistic event added at a marked position [1]. The model card and recipe do not list them. Their effect is measured in [fish-audio-drama-3.md](fish-audio-drama-3.md): `[breath]` filled the gap in 8 of 8 places, `[hmm]` was spoken as "hmm"
- A tag or filler at the very start of a line more often renders the first word or event and then only silence until `max_new_tokens`; a mid-sentence tag is more reliable, and `max_new_tokens` should be capped near the expected length [3]

## Scoped tags

Form: `<tag>words</tag>`. The tag sets the delivery of the enclosed words only [1].

| Tag | Effect | Example | Source |
|---|---|---|---|
| `<whisper>...</whisper>` | the words are whispered | `Promise me <whisper>you won't tell her</whisper>.` | [1] |
| `<emphasis>...</emphasis>` | the words are stressed | `This is <emphasis>not</emphasis> a drill.` | [1] |
| `<slow>...</slow>` | the words are spoken slowly | `<slow>Listen to me.</slow>` | [1] |

## Emotion and style, in plain language

- Style prefix: `[description] line` sets the delivery of the whole line; the description is free natural language [1]. Examples: `[with bright eager excitement] We won!`, `[icy calm, as if you already accepted it] Fine.` [1]
- Single-word emotion tags work the same way as point tags at the start of a line: `[angry]`, `[excited]`, `[whisper]` [3]
- Director's note: a line pair `Direction: <note>` and `Line: <text>`; the note can ask for intent, pacing or emphasis: `Direction: icy calm, as if you already accepted it. Put the rise on "goodbye".` `Line: So this is goodbye.` [1]
- Relative note, second turn onward: `[softer and warmer versus previous] line` or `Direction: more amused than before; drop the hurt.`; the earlier takes stay in context as audio [1][2]
- Speed and loudness have no number: pace comes from `<slow>`, a style description or a note; loudness comes from a style description such as `[loud, at full voice]` [1]
- The reference clip also shapes delivery, but it is not a targeted control [3]

## Speakers in one text

- `<|speaker:N|>` with N from 0 to 15 marks a turn: `<|speaker:0|> Ready? <|speaker:1|> Always.` [1][2]
- Text without a leading speaker token is speaker 0 [3]
- Each reference carries its speaker token; several clips of one voice share it [1]. The command line takes them as `--prompt-audio` and `--prompt-text`, the API as `references` with `audio` and `text` [5]
- The line separator `<|audio_separator|>` joins lines for line-separated synthesis [1]

## Hints and edits

| Control | Form | Example | Source |
|---|---|---|---|
| Language hint | `line [language: xx]` | `Welcome back to the show. [language: en]` | [1] |
| Duration hint | `line [audio tokens: N]`, N in frames (21.5 per second) | `Welcome back to the show. [audio tokens: 65]` | [1][4] |
| Look-ahead chunk | `<|endofturn|>` between streamed chunks | `It was late<|endofturn|>and the hall was empty.` | [1] |
| Edit as continuation | `previous_takes` with the earlier texts of the same line | change `Wednesday` to `Thursday` | [2][4] |

Hints are never spoken. `previous_takes` and long-text chunking are not exposed through the vLLM speech API [3]; the repository's own command line chunks a long text at about 300 UTF-8 bytes, and `--single-chunk` generates a whole text in one pass [5].

## Ming control to Fish form

| Ming control | Fish form | Note |
|---|---|---|
| `[Breathing]` | `[breath]` | free wording [1]; not in Table 10; measured |
| `[Cough]` | `[clears throat]` or `[coughs]` | free wording |
| `[Sigh]` | `[sighs]` | documented |
| `[Laughter]` | `[laughs]` or `[laughing]` | documented |
| `[Uhm]` | `[hesitates]` or the spoken word "Uhm" | free wording |
| `[Surprise-ah]`, `[Surprise-oh]` | `[gasps]` or `[surprised]` | free wording |
| `[Dissatisfaction-hnn]` | `[annoyed grunt]` | free wording |
| `[Confirmation-en]` | `[hmm]` or `[affirmative hum]` | free wording |
| `[Question-ei]`, `[Question-ah]`, `[Question-en]`, `[Question-oh]`, `[Question-huh]` | a spoken "Huh?" or `[questioning]` | free wording |
| `emotion` happy, sad, angry, fearful, disgusted, surprised, neutral | style prefix `[happy]`, `[sad]`, `[angry]`, `[fearful]`, `[disgusted]`, `[surprised]`, none for neutral; or a longer description | free language |
| `speed` slow / medium / fast | `<slow>...</slow>`, a style description, none for medium | no fast tag in Table 10 |
| `pitch` low / medium / high | a style description such as `[low voice]` | no pitch control |
| `volume` low / medium / high | `<whisper>` for low; `[loud, at full voice]` for high | no volume control |
| `dialect` | none | language hint only |
| `FREEFORM` instruction | style prefix or director's note | same idea |
| `VOICE_DESIGN`, `IP` | none; a voice comes from a reference clip | no built-in voices in the documents |
| one task per call | none; every control mixes in one text | |
| `use_spk_emb`, `prompt_text` | reference audio plus its exact transcript, 10 s or more | transcript is required |
| paragraph gap | `[pause]` | |
