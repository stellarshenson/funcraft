# Controlled-voice TTS models

This note compares open-weights text-to-speech models that clone a voice and accept sound tags. The figures come from the owner's comparison of 2026-11-06; "not checked" marks a value the comparison did not state.

| Model | Cloning leaderboard Elo, open-weights rank | Size | Sound tags | Cloning input | Licence |
|---|---|---|---|---|---|
| Fish Audio Drama 3 (2026-10) | 1075, 1st | 36B MoE, about 3B active | `[sigh]` `[laugh]` `[breath]` `[pause]`, word-level `<whisper>` and emphasis, emotions in plain language, up to 16 speakers in one text | clip plus its transcript; Fish asks for 10 s or more | Fish Audio Community License |
| Ming-3.0-TTS 0.5B (2026-10) | 1067, 2nd | 0.5B | 14 tags: `[Sigh]` `[Laughter]` `[Breathing]` `[Cough]` `[Uhm]` and others, in English and Chinese text only | reference WAV plus its transcript | MIT |
| Breeze TTS 2 | 1020, 4th | not checked | not checked | not checked | not checked |
| Lure 0.6B, Tesslate (2026-10) | not on the leaderboard | 0.6B | 36 tags, the largest set; laughs and sighs work most reliably | 3-12 s clip plus its transcript | Apache 2.0 |

`leftenant_voice` uses Ming-3.0-TTS 0.5B; its tasks, tags and control values are in [ming-3.0-tts-controls.md](ming-3.0-tts-controls.md).

Fish Audio Drama 3 was tried beside Ming; its control sequences are in [fish-audio-drama-3-controls.md](fish-audio-drama-3-controls.md), its facts and the comparison with Ming in [fish-audio-drama-3.md](fish-audio-drama-3.md).
