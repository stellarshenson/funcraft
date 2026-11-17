# Acceptance Criteria - leftenant_voice

The S2 Pro text-to-MP3 service: an HTTP API over a plug-in engine registry, its renderer, its MP3 output, its Docker image and its registry. Every read and write goes through `pm-tools`.

## Authors

- `@kj` Konrad Jelen

## Engine `ENGINE`

The plug-in layer and the models it serves: one interface, a registry by name, S2 Pro and AuK-Flash

- log: 2026-11-09T01:26:47Z @kj category created

- [x] `ACC-ENGINE-1-PROTOCOL` **Five-call engine interface** - HIGH; a model that implements load(), unload(), speak(text, voice) -> (float32 samples, rate), voices() and name plugs into the service; the registry finds engines by name
  - evidence: service/engine.py defines the Engine Protocol; S2ProEngine and AukEngine implement load, unload, speak, voices and name; make test 6 passed in 3.51 s (tmp/workflows/goal-trackers/unit.log)
  - test: read service/engine.py; both engines implement the five calls; make test passes
  - test-tags: UNIT
  - mechanism: 2026-11-09T01:26:47Z @kj service/engine.py holds the Engine Protocol and EngineError; registry.py builds the engines by name; app.py calls only the interface
  - log: 2026-11-09T01:26:47Z @kj added
  - log: 2026-11-09T01:29:44Z @kj closed: verified
- [x] `ACC-ENGINE-2-S2PRO` **S2 Pro by name** - HIGH; POST /speak with text, engine s2pro and voice grimaldus returns audio/mpeg
  - evidence: tmp/workflows/goal-trackers/engine-run/result.json: engine s2pro returned 200 audio/mpeg, 44413 bytes in 26.4 s
  - test: start the service on GPU 0, POST /speak with engine s2pro and voice grimaldus, assert 200 and audio/mpeg
  - test-tags: FUNCTIONAL
  - log: 2026-11-09T01:29:03Z @kj added
  - log: 2026-11-09T01:29:44Z @kj closed: verified
- [x] `ACC-ENGINE-3-AUK` **AuK-Flash by name** - HIGH; POST /speak with text, engine auk-flash and voice grimaldus returns audio/mpeg
  - evidence: tmp/workflows/goal-trackers/engine-run/result.json: engine auk-flash returned 200 audio/mpeg, 39717 bytes in 65.2 s; ffprobe MP3 24 kHz mono 4.488 s
  - test: start the service where .venv-auk exists, POST /speak with engine auk-flash, assert 200 and audio/mpeg
  - test-tags: FUNCTIONAL
  - log: 2026-11-09T01:29:03Z @kj added
  - log: 2026-11-09T01:29:45Z @kj closed: verified
- [x] `ACC-ENGINE-4-DEFAULT` **Default engine from ENGINE** - HIGH; POST /speak without an engine field uses ENGINE from the service environment; ENGINE=s2pro sends it to s2pro
  - evidence: tmp/workflows/goal-trackers/engine-run/result.json: a request without engine after auk-flash went to s2pro, 200 audio/mpeg 47804 bytes; test_absent_engine_uses_the_environment_default passes
  - test: start with ENGINE=s2pro, POST without engine and assert the s2pro engine spoke; unit-test the fallback with stubs
  - test-tags: FUNCTIONAL, UNIT
  - mechanism: 2026-11-09T01:29:04Z @kj app.py resolves request.engine or DEFAULT_ENGINE, read from ENGINE at import
  - log: 2026-11-09T01:29:04Z @kj added
  - log: 2026-11-09T01:29:45Z @kj closed: verified
- [x] `ACC-ENGINE-5-UNKNOWN` **Unknown engine names the known ones** - MEDIUM; an unknown engine returns 4xx with a message listing the installed engines
  - evidence: tmp/workflows/goal-trackers/engine-run/result.json: engine nope returned 404 with available: ['auk-flash', 's2pro']; test_unknown_engine_is_4xx_and_lists_the_known_ones passes
  - test: POST /speak with engine nope, assert 4xx and both known names in the body
  - test-tags: FUNCTIONAL, UNIT
  - log: 2026-11-09T01:29:04Z @kj added
  - log: 2026-11-09T01:29:45Z @kj closed: verified
- [x] `ACC-ENGINE-6-VOICES` **Voices per engine** - HIGH; GET /voices lists each installed engine and the voices it can speak
  - evidence: tmp/workflows/goal-trackers/engine-run/result.json: /voices returned the map s2pro to grimaldus and auk-flash to grimaldus; test_voices_lists_every_engine passes
  - test: GET /voices, assert the map of engine to voice list
  - test-tags: FUNCTIONAL, UNIT
  - log: 2026-11-09T01:29:04Z @kj added
  - log: 2026-11-09T01:29:45Z @kj closed: verified
- [x] `ACC-ENGINE-7-CHILD` **AuK-Flash runs as a child process** - HIGH; AuK-Flash runs as a child process of .venv-auk and is not imported into the service interpreter; the engine interface hides the process
  - evidence: tmp/workflows/goal-trackers/engine-run/result.json: .venv-auk/bin/python service/auk_worker.py was resident while auk-flash spoke and gone after the switch and the stop; no AuK import in service modules
  - test: ps during an auk-flash synthesis shows .venv-auk/bin/python service/auk_worker.py; grep the service modules for an AuK import
  - test-tags: INTEGRATION
  - mechanism: 2026-11-09T01:29:04Z @kj AukEngine spawns .venv-auk/bin/python service/auk_worker.py and speaks over JSON lines; the service interpreter never imports AuK
  - log: 2026-11-09T01:29:04Z @kj added
  - log: 2026-11-09T01:29:45Z @kj closed: verified
- [x] `ACC-ENGINE-8-STUB` **Stub engine gate without a GPU** - HIGH; stub engines select, fall back to ENGINE and return the unknown-engine error with no GPU and no model
  - evidence: make test: 6 passed in 3.51 s with stub engines, no GPU and no model (tmp/workflows/goal-trackers/unit.log)
  - test: make test with only stub engines, no GPU and no model
  - test-tags: UNIT
  - log: 2026-11-09T01:29:04Z @kj added
  - log: 2026-11-09T01:29:45Z @kj closed: verified
- [x] `ACC-ENGINE-9-API-UNCHANGED` **Third model needs no API change** - MEDIUM; adding AuK-Flash changed no file of the API layer; a third model needs service/engine_<name>.py, one line in service/registry.py and a worker script if it runs elsewhere
  - evidence: service/README.md: a third model needs service/engine_<name>.py, one registry line and a worker script; service/app.py needs no change; engine_auk.py and auk_worker.py were added for auk-flash
  - test: grep service/app.py for engine names; list the files engine_auk.py and auk_worker.py and the registry line
  - test-tags: MANUAL
  - log: 2026-11-09T01:29:05Z @kj added
  - log: 2026-11-09T01:29:46Z @kj closed: verified
- [x] `ACC-ENGINE-10-LICENCE` **AuK licence recorded** - MEDIUM; service/README.md states the AuK weights are MIT and the Qwen2.5-Omni-3B text encoder is non-commercial
  - evidence: service/README.md line 28: AuK weights are MIT; its text encoder, Qwen2.5-Omni-3B, is non-commercial
  - test: grep -n 'Qwen2.5-Omni-3B' service/README.md
  - test-tags: MANUAL
  - log: 2026-11-09T01:29:05Z @kj added
  - log: 2026-11-09T01:29:46Z @kj closed: verified

## Renderer `RENDER`

The S2 Pro renderer: make -f s2pro.mk speak and the numbers it must keep

- log: 2026-11-09T01:29:05Z @kj category created

- [x] `ACC-RENDER-11-DURATION` **Duration within 2 %** - HIGH; make -f s2pro.mk speak VOICE=grimaldus renders the status text within 2 % of the winner's 95.6 s
  - evidence: wip/s2pro-service/verify/r1-measure.json: fresh render 95.62 s against the winner's 95.62 s, within 2 %
  - test: make -f s2pro.mk speak VOICE=grimaldus FILE=tmp/workflows/ming-status/status-plain.txt OUT=out/status-grimaldus.mp3; ffprobe the duration
  - test-tags: FUNCTIONAL
  - log: 2026-11-09T01:29:05Z @kj added
  - log: 2026-11-09T01:29:46Z @kj closed: verified
- [x] `ACC-RENDER-12-PARAGRAPH` **Paragraph level range at most 1.5 dB** - HIGH; the worst paragraph level range of that render is at most 1.5 dB; the +3 dB hiss cap leaves a quiet sentence low, so the loud sentences of its paragraph are trimmed by attenuation only
  - mechanism: 2026-11-09T21:03:51Z @kj sentence_gains caps a positive gain at MAX_BOOST_DB and trims each paragraph's loud pieces to MAX_PARA_SPREAD_DB; both constants live in src/fish/speak_s2pro.py
  - evidence: tmp/workflows/release/repro-measure.json: worst paragraph level range 1.3 dB against the 1.5 dB bar on the repaired capped render; the verifier's word-window measure reads 1.32 dB; four loud pieces of paragraph 2 trimmed by 0.43 to 0.44 dB
  - test: measure each paragraph's level in the render and take the worst range
  - test-tags: FUNCTIONAL
  - log: 2026-11-09T01:29:05Z @kj added
  - log: 2026-11-09T01:29:46Z @kj closed: verified
  - log: 2026-11-09T21:03:51Z @kj amended title "Paragraph level range at most 1 dB" -> "Paragraph level range at most 1.5 dB"; text "the worst paragraph level range of that render is at most 1 dB" -> "the worst paragraph level range of that render is at most 1.5 dB; the +3 dB hiss cap leaves a quiet sentence low, so the loud sentences of its paragraph are trimmed by attenuation only"; reason: the owner's brief of 2026-11-09 accepts the +3 dB hiss cap and a paragraph spread of at most 1.5 dB, replacing the 1 dB bar
  - log: 2026-11-09T21:03:51Z @kj edited evidence "wip/s2pro-service/verify/r1-measure.json: worst paragraph level range 0.4 dB against the 1 dB bar" -> "tmp/workflows/release/repro-measure.json: worst paragraph level range 1.3 dB against the 1.5 dB bar on the repaired capped render; the verifier's word-window measure reads 1.32 dB; four loud pieces of paragraph 2 trimmed by 0.43 to 0.44 dB"; reason: re-evidenced on the repaired capped render
- [-] `ACC-RENDER-13-FILE` **File level range at most 1 dB** - HIGH; the file level range of that render is at most 1 dB
  - test: measure the sentence levels over the file and take the range
  - test-tags: FUNCTIONAL
  - log: 2026-11-09T01:29:06Z @kj added
  - log: 2026-11-09T01:29:46Z @kj closed: verified
  - log: 2026-11-09T21:03:53Z @kj rejected: superseded: the owner's +3 dB hiss decision (brief, 2026-11-09) accepts the capped renderer's level ranges and sets a per-paragraph bar of 1.5 dB in ACC-RENDER-12-PARAGRAPH; it sets no file-range bar, so this 1 dB file criterion no longer describes the renderer. The capped render's file range is 1.8 dB, stated in references/fish-audio-s2-pro.md; evidence retired: wip/s2pro-service/verify/r1-measure.json: file level range 0.6 dB against the 1 dB bar; reason: the owner's brief accepts the capped renderer's wider level ranges and sets a per-paragraph bar; no file-range bar replaces this one
- [x] `ACC-RENDER-14-WER` **Word error rate at most 2 %** - HIGH; the Nemotron word error rate of that render is at most 2 %
  - evidence: wip/s2pro-service/verify/r1-measure.json: Nemotron word error rate 0.0 against the 0.02 bar
  - test: transcribe the render with Nemotron through tmp/workflows/gpu-queue.sh 63000 and score the words
  - test-tags: FUNCTIONAL
  - log: 2026-11-09T01:29:06Z @kj added
  - log: 2026-11-09T01:29:46Z @kj closed: verified
- [x] `ACC-RENDER-15-ECAPA` **ECAPA to grimaldus is highest** - HIGH; the ECAPA similarity to grimaldus is above every other voice on that render
  - evidence: wip/s2pro-service/verify/r1-measure.json: ECAPA grimaldus 0.782, next dijkstra 0.356, own_highest true
  - test: score the render with ECAPA against every voice centroid
  - test-tags: FUNCTIONAL
  - log: 2026-11-09T01:29:06Z @kj added
  - log: 2026-11-09T01:29:47Z @kj closed: verified

## Service `SERVE`

The HTTP API: POST /speak, GET /health, GET /voices, errors, one-synthesis lock and idle unload

code SERVE: pm-tools caps a category code at six letters, so the brief's SERVICE is written SERVE

- log: 2026-11-09T01:29:28Z @kj category created
- log: 2026-11-09T01:30:44Z @kj added note "code SERVE: pm-tools caps a category code at six letters, so the brief's SERVICE is written SERVE"

- [x] `ACC-SERVE-16-SPEAK` **POST /speak returns an MP3** - CRITICAL; POST /speak with text and voice returns audio/mpeg
  - evidence: tmp/workflows/goal-trackers/engine-run/result.json: POST /speak with text and voice returned 200 audio/mpeg 44413 bytes; wip/s2pro-service/verify/r1-native_test.json 200 audio/mpeg
  - test: start the service, POST /speak with text and voice, assert 200 and audio/mpeg
  - test-tags: FUNCTIONAL
  - log: 2026-11-09T01:29:28Z @kj added
  - log: 2026-11-09T01:29:47Z @kj closed: verified
- [x] `ACC-SERVE-17-HEALTH` **GET /health answers** - HIGH; GET /health answers 200 with loaded, engine, busy and seconds_until_unload, also while unloaded and before the model loads
  - evidence: test_health_answers_while_the_default_engine_loads passes; engine-run/result.json /health 200 loaded true busy false seconds_until_unload 557; r1-native_test.json loaded false and null after idle
  - test: GET /health loaded, unloaded and during the startup load; assert 200 and the fields
  - test-tags: FUNCTIONAL, UNIT
  - log: 2026-11-09T01:29:28Z @kj added
  - log: 2026-11-09T01:29:47Z @kj closed: verified
- [x] `ACC-SERVE-18-EMPTY` **Empty text is 4xx with a message** - MEDIUM; empty text returns 4xx with a message
  - evidence: wip/s2pro-service/verify/r1-native_test.json and r1-container_test.json: empty text returned 422 with detail 'text is empty'
  - test: POST /speak with text of zero length, assert 4xx and a message
  - test-tags: FUNCTIONAL
  - log: 2026-11-09T01:29:28Z @kj added
  - log: 2026-11-09T01:29:47Z @kj closed: verified
- [x] `ACC-SERVE-19-TOO-LONG` **Too long text is 4xx with a message** - MEDIUM; text over MAX_TEXT_CHARS returns 4xx with a message naming the limit
  - evidence: wip/s2pro-service/verify/r1-native_test.json: 3999 characters returned 422 with detail 'text has 3999 characters; the limit is 3000'
  - test: POST /speak with 3001 characters, assert 4xx and the 3000 limit in the message
  - test-tags: FUNCTIONAL
  - log: 2026-11-09T01:29:28Z @kj added
  - log: 2026-11-09T01:29:47Z @kj closed: verified
- [x] `ACC-SERVE-20-UNKNOWN-VOICE` **Unknown voice is 4xx with a message** - MEDIUM; an unknown voice returns 4xx with a message naming the engine's voices
  - evidence: wip/s2pro-service/verify/r1-native_test.json and r1-container_test.json: unknown voice 'nobody' returned 404 with available: ['grimaldus']
  - test: POST /speak with voice nobody, assert 4xx and grimaldus in the message
  - test-tags: FUNCTIONAL
  - log: 2026-11-09T01:29:29Z @kj added
  - log: 2026-11-09T01:29:47Z @kj closed: verified
- [x] `ACC-SERVE-21-SERIAL` **One synthesis at a time** - HIGH; a second POST /speak waits for the running synthesis; no two syntheses run at once
  - evidence: tests/unit/test_serial.py::test_one_synthesis_at_a_time: two 0.3 s stub requests, max_active 1, serial; make test 29 passed (tmp/workflows/goal-trackers/unit-green.log)
  - test: send two /speak requests at once; the app log shows the second synthesis after the first ends
  - test-tags: FUNCTIONAL, UNIT
  - mechanism: 2026-11-09T01:29:39Z @kj one threading lock covers load, engine switch, synthesis and unload; a second request waits on it
  - log: 2026-11-09T01:29:39Z @kj added
  - log: 2026-11-09T02:02:58Z @kj edited test-tags "FUNCTIONAL" -> "FUNCTIONAL, UNIT"; reason: the unit suite now proves the lock with stubs
  - log: 2026-11-09T02:02:58Z @kj closed: verified by the unit suite
- [x] `ACC-SERVE-22-LOAD-ONCE` **Model loads once per residency** - HIGH; the model loads once per residency and serves every request until the idle unload
  - evidence: tmp/workflows/goal-trackers/engine-run/uvicorn.log: one load per residency - s2pro at 42 s served the first request, auk-flash at 47 s served its request, s2pro reloaded at 43 s only after the switch; test_switching_engines_unloads_the_previous_one passes
  - test: send two requests inside the idle window; the log shows one engine load per engine
  - test-tags: FUNCTIONAL
  - log: 2026-11-09T01:29:39Z @kj added
  - log: 2026-11-09T01:29:47Z @kj closed: verified
  - log: 2026-11-09T01:31:12Z @kj edited evidence "tmp/workflows/goal-trackers/engine-run/uvicorn.log: one s2pro load at 42 s and one auk-flash load at 47 s, one load per residency; test_switching_engines_unloads_the_previous_one passes" -> "tmp/workflows/goal-trackers/engine-run/uvicorn.log: one load per residency - s2pro at 42 s served the first request, auk-flash at 47 s served its request, s2pro reloaded at 43 s only after the switch; test_switching_engines_unloads_the_previous_one passes"
- [x] `ACC-SERVE-23-IDLE` **Unload after IDLE_UNLOAD_SECONDS** - HIGH; after IDLE_UNLOAD_SECONDS without a request the model unloads; /health reports loaded false and seconds_until_unload null and the next request reloads
  - evidence: test_idle_unload_and_reload green: after 15 s idle /health loaded false and seconds null; the next request reloaded in 43 s and returned audio/mpeg (tmp/workflows/goal-trackers/functional-green.log)
  - test: start with IDLE_UNLOAD_SECONDS=5, wait, assert /health loaded false; send a request and assert a reload
  - test-tags: FUNCTIONAL, UNIT
  - mechanism: 2026-11-09T01:29:40Z @kj a watcher thread wakes every 5 s and unloads the resident engine once IDLE_UNLOAD_SECONDS have passed since the last request
  - log: 2026-11-09T01:29:40Z @kj added
  - log: 2026-11-09T02:02:58Z @kj closed: verified by the functional suite
- [x] `ACC-SERVE-24-NO-UNLOAD` **Unload never during a synthesis** - HIGH; the idle unload never runs during a synthesis; the idle timer restarts after it
  - evidence: test_no_unload_during_a_synthesis green: a synthesis longer than the 15 s idle window kept /health loaded and busy throughout (tmp/workflows/goal-trackers/functional-green.log)
  - test: start with IDLE_UNLOAD_SECONDS=1, make a long synthesis; /health stays loaded and busy, no unload line, then the model unloads after it
  - test-tags: FUNCTIONAL, UNIT
  - mechanism: 2026-11-09T01:29:40Z @kj the watcher takes the lock without blocking, skips its turn while a synthesis holds it, and rechecks the idle time
  - log: 2026-11-09T01:29:40Z @kj added
  - log: 2026-11-09T02:02:58Z @kj closed: verified by the functional suite
- [x] `ACC-SERVE-25-WER` **Service MP3 word error rate at most 2 %** - HIGH; every service MP3 is transcribed by Nemotron and measures at most 2 % word error rate
  - evidence: all four service MP3 paths transcribed exactly, WER 0.0 (bar 0.02): compose-speak 19 words, keepalive-speak 12, the byte-identical functional-native/container pair 11; Nemotron ran as gpu-queue.sh 63000 on GPU 2 with no wait, the per-job threshold not gpu2-queue.sh's under-2000-MiB wait; tmp/workflows/release/criteria-measure.json, criteria-asr.json, suite-asr.json, criteria-asr.log
  - test: transcribe every service MP3 with Nemotron through tmp/workflows/gpu-queue.sh 63000 and score it
  - test-tags: FUNCTIONAL
  - mechanism: 2026-11-09T01:29:40Z @kj gpu-queue.sh takes the MiB per job, so the 63000 MiB Nemotron job waits only for the A5000; gpu2-queue.sh's fixed 2000 MiB on GPU 2 was blocked by MLflow's 2.7 GiB for 49 min; do not use a smaller checkpoint
  - log: 2026-11-09T01:29:40Z @kj added
  - log: 2026-11-09T09:32:13Z @kj closed: verified
  - log: 2026-11-09T09:34:16Z @kj edited evidence "compose-speak.mp3 (19 words) and keepalive-speak.mp3 (12 words) transcribed exactly, WER 0.0 against the posted text (bar 0.02); Nemotron ran as gpu-queue.sh 63000 on GPU 2 with no wait - the per-job threshold waits for 63000 MiB free, not gpu2-queue.sh's under-2000-MiB-used wait that MLflow's 2.7 GiB blocked; tmp/workflows/release/criteria-measure.json, criteria-asr.json, criteria-asr.log" -> "all four service MP3 paths transcribed exactly, WER 0.0 (bar 0.02): compose-speak 19 words, keepalive-speak 12, the byte-identical functional-native/container pair 11; Nemotron ran as gpu-queue.sh 63000 on GPU 2 with no wait, the per-job threshold not gpu2-queue.sh's under-2000-MiB wait; tmp/workflows/release/criteria-measure.json, criteria-asr.json, suite-asr.json, criteria-asr.log"

## Output `OUTPUT`

MP3 files and levels: every render an MP3, no decode above full scale, the service's MP3

- log: 2026-11-09T01:29:40Z @kj category created

- [x] `ACC-OUTPUT-26-MP3-ONLY` **Every render in out/ is an MP3** - HIGH; find out -name '*.wav' -not -path '*/.ipynb_checkpoints/*' prints nothing
  - evidence: find out -name '*.wav' -not -path '*/.ipynb_checkpoints/*' prints nothing; 35 MP3s under out/; tmp/workflows/goal-trackers/fixes-evidence.txt
  - test: find out -name '*.wav' -not -path '*/.ipynb_checkpoints/*'
  - test-tags: FUNCTIONAL
  - log: 2026-11-09T01:29:40Z @kj added
  - log: 2026-11-09T02:42:04Z @kj closed: closed: the three WAVs restored for the regeneration were converted and moved to the trash
  - log: 2026-11-09T03:03:20Z @kj edited evidence "find out -name '*.wav' -not -path '*/.ipynb_checkpoints/*' prints nothing; 34 MP3s under out/; tmp/workflows/goal-trackers/fixes-evidence.txt" -> "find out -name '*.wav' -not -path '*/.ipynb_checkpoints/*' prints nothing; 35 MP3s under out/; tmp/workflows/goal-trackers/fixes-evidence.txt"; reason: the Fish render fix added the 35th MP3 after this evidence was written
- [x] `ACC-OUTPUT-27-PEAK` **No MP3 decodes above full scale** - HIGH; every MP3 in out/ decodes with a peak at most 1.0
  - evidence: soundfile over all 35 MP3s in out/ (no .ipynb_checkpoints): max peak 0.9962, none above 1.0; repaired files 0.9228, 0.8977, 0.9156; tmp/workflows/goal-trackers/peaks-after.txt
  - test: decode every MP3 in out/ except .ipynb_checkpoints with soundfile in .venv-tools and assert the peak is at most 1.0
  - test-tags: FUNCTIONAL
  - log: 2026-11-09T01:29:40Z @kj added
  - log: 2026-11-09T01:30:43Z @kj edited test "decode every MP3 in out/ with ffmpeg and take the peak sample" -> "decode every MP3 in out/ except .ipynb_checkpoints with soundfile in .venv-tools and assert the peak is at most 1.0"
  - log: 2026-11-09T02:42:04Z @kj closed: closed: every MP3 in out/ decodes at most 1.0 after the -1 dBFS headroom fix
  - log: 2026-11-09T02:44:12Z @kj edited evidence "soundfile over all 34 MP3s in out/ (no .ipynb_checkpoints): max peak 0.9962, none above 1.0; repaired files 0.9228, 0.8977, 0.9156; tmp/workflows/goal-trackers/peaks-after.txt" -> "soundfile over all 35 MP3s in out/ (no .ipynb_checkpoints): max peak 0.9962, none above 1.0; repaired files 0.9228, 0.8977, 0.9156; tmp/workflows/goal-trackers/peaks-after.txt"; reason: the new Fish render adds one MP3 to the ones measured
- [x] `ACC-OUTPUT-28-SERVICE-FILE` **Service MP3 plays and transcribes** - HIGH; the service's MP3 is an MP3 stream in ffprobe and transcribes back with at most 2 % word error rate
  - evidence: compose-speak.mp3 plays and transcribes: ffprobe format_name mp3, duration 6.90 s; ffmpeg decodes it with no error; Nemotron transcript matches the posted 19-word text at WER 0.0; tmp/workflows/release/criteria-measure.json, compose-speak.mp3
  - test: ffprobe the service MP3; transcribe it with Nemotron and score it
  - test-tags: FUNCTIONAL
  - log: 2026-11-09T01:29:41Z @kj added
  - log: 2026-11-09T09:32:17Z @kj closed: verified

## Docker `DOCKER`

The image, its compose stack and the make targets that build, run and configure them

- log: 2026-11-09T01:29:41Z @kj category created

- [x] `ACC-DOCKER-29-BUILD` **docker-build leaves the image** - HIGH; make -f s2pro.mk docker-build leaves IMAGE:VERSION in docker images
  - evidence: make -f s2pro.mk docker-build on 2026-11-11 reused all 22 cached steps and tagged registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts:0.2.0 id dd3a0d393663; wip/compose-rename/logs/docker-build.log ends Successfully tagged; wip/compose-rename/logs/docker-images.txt
  - test: make -f s2pro.mk docker-build; docker images shows IMAGE:VERSION
  - test-tags: FUNCTIONAL
  - log: 2026-11-09T01:29:41Z @kj added
  - log: 2026-11-09T01:29:48Z @kj closed: verified
  - log: 2026-11-09T02:42:13Z @kj edited evidence "docker images: s2pro-tts:0.1.0 id 0fd810729ba9, 18.7 GB; tmp/workflows/goal-trackers/logs/goal-trackers-docker-build.log ends Successfully tagged" -> "docker images: s2pro-tts:0.1.0 id d9de9bcd531e, 18.7 GB (rebuilt with the MP3 headroom fix); tmp/workflows/goal-trackers/fix1-docker-build.log ends Successfully tagged"; reason: the image was rebuilt after the audio_out.py fix, so the recorded id changed
  - log: 2026-11-09T07:47:58Z @kj edited evidence "docker images: s2pro-tts:0.1.0 id d9de9bcd531e, 18.7 GB (rebuilt with the MP3 headroom fix); tmp/workflows/goal-trackers/fix1-docker-build.log ends Successfully tagged" -> "docker images: s2pro-tts:0.1.0 id 99b7e0f0fd61, 18.7 GB (rebuilt with the Hugging Face pull); tmp/workflows/hf-pull/logs/docker-rebuild.log ends Successfully tagged"; reason: the image was rebuilt after the Dockerfile change, so the recorded id changed
  - log: 2026-11-09T21:03:59Z @kj edited evidence "docker images: s2pro-tts:0.1.0 id 99b7e0f0fd61, 18.7 GB (rebuilt with the Hugging Face pull); tmp/workflows/hf-pull/logs/docker-rebuild.log ends Successfully tagged" -> "docker images: registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice/s2pro-tts:0.2.0 id d334ef340da3, 18.7 GB, built 2026-11-09T12:00:41Z in 107 s from the reviewed tree; tmp/workflows/post-review/docker-build.log ends Successfully tagged"; reason: VERSION is 0.2.0 and the image list now shows the 0.2.0 build, not the superseded 0.1.0 id
  - log: 2026-11-11T23:00:42Z @kj edited evidence "docker images: registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice/s2pro-tts:0.2.0 id d334ef340da3, 18.7 GB, built 2026-11-09T12:00:41Z in 107 s from the reviewed tree; tmp/workflows/post-review/docker-build.log ends Successfully tagged" -> "make -f s2pro.mk docker-build on 2026-11-11 reused all 22 cached steps and tagged registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts:0.2.0 id dd3a0d393663; wip/compose-rename/logs/docker-build.log ends Successfully tagged; wip/compose-rename/logs/docker-images.txt"; reason: the earlier evidence named the superseded s2pro-tts image and the post-review build, not the rename build
- [x] `ACC-DOCKER-30-RUN` **docker run serves the same requests** - HIGH; docker run with the GPU serves /health, /voices and an audio/mpeg /speak response
  - evidence: make test-functional: the container answered /health during the 169 s download and the model load, listed s2pro in /voices, answered 404 for auk-flash, and served 200 audio/mpeg 44413 bytes; tmp/workflows/goal-trackers/logs/functional-container-cold.json
  - test: docker run --gpus device=0 and send /health, /voices and /speak; assert the MP3
  - test-tags: FUNCTIONAL
  - log: 2026-11-09T01:29:41Z @kj added
  - log: 2026-11-09T01:29:48Z @kj closed: verified
  - log: 2026-11-09T07:48:06Z @kj edited evidence "tmp/workflows/goal-trackers/engine-run/container_check.sh: the container returned 200 audio/mpeg 44413 bytes for engine s2pro, listed s2pro in /voices, answered 404 for auk-flash and /health 11 s after start" -> "make test-functional: the container answered /health during the 169 s download and the model load, listed s2pro in /voices, answered 404 for auk-flash, and served 200 audio/mpeg 44413 bytes; tmp/workflows/goal-trackers/logs/functional-container-cold.json"; reason: the container check was rerun on the rebuilt image with the Hugging Face pull
- [x] `ACC-DOCKER-31-COMPOSE` **compose starts the same service** - HIGH; docker compose up -d from service/ with no .env starts the same service
  - evidence: wip/release/verify/compose-0.2.0.json: on 0.2.0 the compose stack moved down/loading/ready in 269 s and POST /speak returned 200 audio/mpeg, 79781 bytes, ffprobe mp3 6.896 s; the 0.2.0 fresh-volume start is the functional cold record (downloading/loading/ready 443 s, 165 s download, 11012039247 bytes); the MP3 sha256 equals the recorded compose-speak.mp3
  - test: cd service; docker compose up -d --remove-orphans with a fresh data volume; the first start downloads from Hugging Face; curl /health; curl /speak
  - test-tags: FUNCTIONAL
  - log: 2026-11-09T01:29:41Z @kj added
  - log: 2026-11-09T07:47:53Z @kj edited test "cd service; docker compose --env-file .env up -d; curl /health; curl /speak" -> "cd service; docker compose --env-file .env up -d with a fresh s2pro-hf-cache volume; the first start downloads from Hugging Face; curl /health; curl /speak"
  - log: 2026-11-09T09:32:17Z @kj closed: verified
  - log: 2026-11-09T21:03:59Z @kj edited evidence "cd service; docker compose --env-file .env up -d on a fresh s2pro-hf-cache volume: states down, downloading, loading, ready in 593 s, the volume holds 11011983136 bytes; /health ready with engine s2pro; POST /speak returned 200 audio/mpeg, 79781 bytes, ffprobe mp3 6.90 s; tmp/workflows/release/compose-check.json" -> "wip/release/verify/compose-0.2.0.json: on 0.2.0 the compose stack moved down/loading/ready in 269 s and POST /speak returned 200 audio/mpeg, 79781 bytes, ffprobe mp3 6.896 s; the MP3 sha256 equals the recorded compose-speak.mp3"; reason: the verifier re-ran compose on the released 0.2.0 image; the earlier evidence named 0.1.0
  - log: 2026-11-09T21:07:05Z @kj edited evidence "wip/release/verify/compose-0.2.0.json: on 0.2.0 the compose stack moved down/loading/ready in 269 s and POST /speak returned 200 audio/mpeg, 79781 bytes, ffprobe mp3 6.896 s; the MP3 sha256 equals the recorded compose-speak.mp3" -> "wip/release/verify/compose-0.2.0.json: on 0.2.0 the compose stack moved down/loading/ready in 269 s and POST /speak returned 200 audio/mpeg, 79781 bytes, ffprobe mp3 6.896 s; the 0.2.0 fresh-volume start is the functional cold record (downloading/loading/ready 443 s, 165 s download, 11012039247 bytes); the MP3 sha256 equals the recorded compose-speak.mp3"; reason: the re-run used a warm volume; the test also requires a cold first start, which the functional record covers on 0.2.0
  - log: 2026-11-11T22:21:00Z @kj edited text "docker compose --env-file .env up -d from service/ starts the same service" -> "docker compose up -d from service/ with no .env starts the same service"; test "cd service; docker compose --env-file .env up -d with a fresh s2pro-hf-cache volume; the first start downloads from Hugging Face; curl /health; curl /speak" -> "cd service; docker compose up -d with a fresh data volume; the first start downloads from Hugging Face; curl /health; curl /speak"
  - log: 2026-11-11T23:00:14Z @kj edited test "cd service; docker compose up -d with a fresh data volume; the first start downloads from Hugging Face; curl /health; curl /speak" -> "cd service; docker compose up -d --remove-orphans with a fresh data volume; the first start downloads from Hugging Face; curl /health; curl /speak"
- [x] `ACC-DOCKER-32-WEIGHTS` **Weights pulled from Hugging Face into a named volume** - HIGH; the image ships no weights; on a fresh named volume the first start downloads them from Hugging Face into /data/huggingface and /health reports downloading then loading then ready; a restart on the same volume downloads nothing and loads from it; with the network off and an empty volume /health reports the error and /speak answers 500
  - evidence: make test-functional: 14 passed in 968.88 s; cold volume 11,012,031,917 bytes, download 169 s, /health downloading then loading then ready 473 s after start, /speak 200 audio/mpeg 44413 bytes; warm start ready in 282 s with no download; network-off error after 10 s and /speak 500; tmp/workflows/goal-trackers/logs/functional-container-{cold,warm,no-network}.json, tmp/workflows/hf-pull/hf-pull.json
  - test: tests/functional/test_container.py: a fresh named volume logs downloading fishaudio/s2-pro and /health moves downloading to ready; a restart on the same volume logs no download; --network none with an empty volume reports error on /health and 500 on /speak; docker run --rm IMAGE test ! -e /data/huggingface before the first start
  - test-tags: FUNCTIONAL
  - log: 2026-11-09T01:29:42Z @kj added
  - log: 2026-11-09T01:29:48Z @kj closed: verified
  - log: 2026-11-09T07:47:50Z @kj edited title "Weights from the HF cache, offline" -> "Weights pulled from Hugging Face into a named volume"; text "the weights mount from the Hugging Face cache read-only and HF_HUB_OFFLINE=1 is set" -> "the image ships no weights; on a fresh named volume the first start downloads them from Hugging Face into /root/.cache/huggingface and /health reports downloading then loading then ready; a restart on the same volume downloads nothing and loads from it; with the network off and an empty volume /health reports the error and /speak answers 500"; test "docker inspect the image Env for HF_HUB_OFFLINE and the mount; run the container offline" -> "tests/functional/test_container.py: a fresh named volume logs downloading fishaudio/s2-pro and /health moves downloading to ready; a restart on the same volume logs no download; --network none with an empty volume reports error on /health and 500 on /speak; docker run --rm IMAGE du -sb /root/.cache/huggingface is empty before the first start"; evidence "service/Dockerfile ENV HF_HUB_OFFLINE=1; service/compose.yml mounts ${HF_CACHE}:/root/.cache/huggingface:ro; wip/s2pro-service/verify/r1-container_test.json served from the mounted cache" -> "make test-functional: 14 passed in 968.88 s; cold volume 11,012,031,917 bytes, download 169 s, /health downloading then loading then ready 473 s after start, /speak 200 audio/mpeg 44413 bytes; warm start ready in 282 s with no download; network-off error after 10 s and /speak 500; tmp/workflows/goal-trackers/logs/functional-container-{cold,warm,no-network}.json, tmp/workflows/hf-pull/hf-pull.json"; reason: the owner ordered the image to pull the model from Hugging Face instead of mounting a host cache
  - log: 2026-11-11T23:00:44Z @kj edited text "the image ships no weights; on a fresh named volume the first start downloads them from Hugging Face into /root/.cache/huggingface and /health reports downloading then loading then ready; a restart on the same volume downloads nothing and loads from it; with the network off and an empty volume /health reports the error and /speak answers 500" -> "the image ships no weights; on a fresh named volume the first start downloads them from Hugging Face into /data/huggingface and /health reports downloading then loading then ready; a restart on the same volume downloads nothing and loads from it; with the network off and an empty volume /health reports the error and /speak answers 500"; test "tests/functional/test_container.py: a fresh named volume logs downloading fishaudio/s2-pro and /health moves downloading to ready; a restart on the same volume logs no download; --network none with an empty volume reports error on /health and 500 on /speak; docker run --rm IMAGE du -sb /root/.cache/huggingface is empty before the first start" -> "tests/functional/test_container.py: a fresh named volume logs downloading fishaudio/s2-pro and /health moves downloading to ready; a restart on the same volume logs no download; --network none with an empty volume reports error on /health and 500 on /speak; docker run --rm IMAGE du -sb /data/huggingface is empty before the first start"; reason: the image moved its Hugging Face cache to /data/huggingface, so the /root/.cache path names a directory the container does not use
  - log: 2026-11-11T23:28:27Z @kj edited test "tests/functional/test_container.py: a fresh named volume logs downloading fishaudio/s2-pro and /health moves downloading to ready; a restart on the same volume logs no download; --network none with an empty volume reports error on /health and 500 on /speak; docker run --rm IMAGE du -sb /data/huggingface is empty before the first start" -> "tests/functional/test_container.py: a fresh named volume logs downloading fishaudio/s2-pro and /health moves downloading to ready; a restart on the same volume logs no download; --network none with an empty volume reports error on /health and 500 on /speak; docker run --rm IMAGE test ! -e /data/huggingface before the first start"; reason: the image creates /data/huggingface only at the first download, so du exits 1 with no such file; absence is the pre-start fact
- [x] `ACC-DOCKER-33-HEALTHY` **Healthy during and after the load** - HIGH; docker ps reports healthy, not starting, while the weights download and the model loads
  - evidence: make test-functional: the container reported healthy through the 473 s cold start (169 s download, 292 s model build) and the 282 s warm start (docker inspect .State.Health.Status); tmp/workflows/goal-trackers/logs/functional-container-cold.json
  - test: docker run the image, watch docker ps during the download and the model load; assert healthy before the model is ready
  - test-tags: FUNCTIONAL
  - mechanism: 2026-11-09T07:47:53Z @kj the default engine loads in a background thread, so /health answers 200 from the first seconds; the HEALTHCHECK passes during the download and the model load without relying on start_period
  - log: 2026-11-09T01:29:42Z @kj added
  - log: 2026-11-09T01:29:48Z @kj closed: verified
  - log: 2026-11-09T01:30:43Z @kj edited evidence "tmp/workflows/goal-trackers/engines.json: docker ps reported healthy during the load; service/Dockerfile HEALTHCHECK start-period 300 s against the 266 s in-container load in r1-container_test.json" -> "tmp/workflows/goal-trackers/engines.json: docker ps reported healthy during the load; Dockerfile and compose start_period 300 s cover the measured 266 to 292 s container loads (r1-container_test.json, verifier round 0)"
  - log: 2026-11-09T07:47:53Z @kj edited text "docker ps reports healthy, not starting, by the time the model has loaded; start_period covers the measured 292 s in-container load" -> "docker ps reports healthy, not starting, while the weights download and the model loads"; evidence "tmp/workflows/goal-trackers/engines.json: docker ps reported healthy during the load; Dockerfile and compose start_period 300 s cover the measured 266 to 292 s container loads (r1-container_test.json, verifier round 0)" -> "make test-functional: the container reported healthy through the 473 s cold start (169 s download, 292 s model build) and the 282 s warm start (docker inspect .State.Health.Status); tmp/workflows/goal-trackers/logs/functional-container-cold.json"; reason: the cold start now includes the download; /health answers 200 throughout, so start_period no longer needs to cover the load
  - log: 2026-11-09T07:47:53Z @kj mechanism updated "2026-11-09T01:29:42Z @kj the default engine loads in a background thread, so /health answers 200 during the load; start_period 300 s covers the measured 292 s container load" -> "the default engine loads in a background thread, so /health answers 200 from the first seconds; the HEALTHCHECK passes during the download and the model load without relying on start_period"
  - log: 2026-11-09T07:48:06Z @kj edited test "docker run the image, watch docker ps; compare start_period with the measured load" -> "docker run the image, watch docker ps during the download and the model load; assert healthy before the model is ready"
- [x] `ACC-DOCKER-34-EARLY-HEALTH` **/health answers before the model loads** - HIGH; GET /health answers 200 before the model is loaded, so a probe passes during the load
  - evidence: test_health_answers_while_the_default_engine_loads passes (200, loaded false); tmp/workflows/goal-trackers/logs/goal-trackers-container-check-final.log line 1: early /health after 11 s with loaded false during the container load
  - test: docker run the image and GET /health during the load; assert 200 and loaded false
  - test-tags: FUNCTIONAL, UNIT
  - log: 2026-11-09T01:29:42Z @kj added
  - log: 2026-11-09T01:29:48Z @kj closed: verified
  - log: 2026-11-09T03:03:23Z @kj edited evidence "test_health_answers_while_the_default_engine_loads passes; engine-run/result.json /health 200 at 11 s with loaded false during the container load" -> "test_health_answers_while_the_default_engine_loads passes (200, loaded false); tmp/workflows/goal-trackers/logs/goal-trackers-container-check-final.log line 1: early /health after 11 s with loaded false during the container load"; reason: the early-health record is in the container check log, not in engine-run/result.json
- [x] `ACC-DOCKER-35-CONFIG` **Every runtime setting is an ENV default** - HIGH; the image accepts every runtime setting as an environment variable and declares each default with ENV; service/README.md gives the docker run -e line and the literal values in compose.yml
  - evidence: docker image inspect registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts:0.2.0 lists VOICES_DIR=/data/voices, ENGINE=s2pro, IDLE_UNLOAD_SECONDS=3600, MAX_TEXT_CHARS=3000; docker run without -e prints the same and -e IDLE_UNLOAD_SECONDS=10 MAX_TEXT_CHARS=2000 overrides them to 10 and 2000; wip/compose-adv-fix/logs/image-env.json, env-override.txt
  - test: docker inspect --format '{{json .Config.Env}}' IMAGE lists each setting; run with and without -e
  - test-tags: FUNCTIONAL, MANUAL
  - mechanism: 2026-11-09T01:29:42Z @kj app.py reads VOICES_DIR, ENGINE, MAX_TEXT_CHARS and IDLE_UNLOAD_SECONDS; the image must declare each with ENV so docker run without -e shows the documented value
  - log: 2026-11-09T01:29:42Z @kj added
  - log: 2026-11-09T09:32:17Z @kj closed: verified
  - log: 2026-11-09T21:03:59Z @kj edited evidence "docker image inspect 363a81acbb6e lists VOICES_DIR=/app/voices, ENGINE=s2pro, IDLE_UNLOAD_SECONDS=3600, MAX_TEXT_CHARS=3000; docker run without -e prints the same; -e IDLE_UNLOAD_SECONDS=10 MAX_TEXT_CHARS=2000 prints 10 and 2000; tmp/workflows/release/docker-env.txt" -> "docker image inspect registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice/s2pro-tts:0.2.0 lists VOICES_DIR=/app/voices, ENGINE=s2pro, IDLE_UNLOAD_SECONDS=3600, MAX_TEXT_CHARS=3000; docker run without -e prints the same and -e IDLE_UNLOAD_SECONDS=10 MAX_TEXT_CHARS=2000 overrides them; tmp/workflows/release/docker-env-0.2.0.txt"; reason: re-evidenced on the released 0.2.0 image; the earlier inspect named 0.1.0
  - log: 2026-11-11T23:00:47Z @kj edited text "the image accepts every runtime setting as an environment variable and declares each default with ENV; service/README.md gives the docker run -e line and the compose variable" -> "the image accepts every runtime setting as an environment variable and declares each default with ENV; service/README.md gives the docker run -e line and the literal values in compose.yml"; evidence "docker image inspect registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice/s2pro-tts:0.2.0 lists VOICES_DIR=/app/voices, ENGINE=s2pro, IDLE_UNLOAD_SECONDS=3600, MAX_TEXT_CHARS=3000; docker run without -e prints the same and -e IDLE_UNLOAD_SECONDS=10 MAX_TEXT_CHARS=2000 overrides them; tmp/workflows/release/docker-env-0.2.0.txt" -> "docker image inspect registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts:0.2.0 lists VOICES_DIR=/data/voices, ENGINE=s2pro, IDLE_UNLOAD_SECONDS=3600, MAX_TEXT_CHARS=3000; docker run without -e prints the same and -e IDLE_UNLOAD_SECONDS=10 MAX_TEXT_CHARS=2000 overrides them to 10 and 2000; wip/compose-adv-fix/logs/image-env.json, env-override.txt"; reason: the hardcoded compose change removed the variable this text promised, and the image reports VOICES_DIR at /data/voices
- [x] `ACC-DOCKER-36-KEEPALIVE` **Keep-alive configurable in the image** - HIGH; docker run -e IDLE_UNLOAD_SECONDS=<n> unloads the model after n seconds without a request, /health reports it unloaded and the next request reloads
  - evidence: wip/release/verify/keepalive-0.2.0.json: on 0.2.0 with -e IDLE_UNLOAD_SECONDS=10 the model unloaded 9 s after ready (/health loaded false, seconds_until_unload null, engine null); the next /speak returned 200 audio/mpeg 47649 bytes in 281 s and /health loaded true after
  - test: docker run -e IDLE_UNLOAD_SECONDS=10; wait 15 s; GET /health loaded false; POST /speak returns 200
  - test-tags: FUNCTIONAL
  - log: 2026-11-09T01:29:42Z @kj added
  - log: 2026-11-09T09:32:17Z @kj closed: verified
  - log: 2026-11-09T21:03:59Z @kj edited evidence "docker run -e IDLE_UNLOAD_SECONDS=10: ready in 298 s, /health loaded false 11 s later with seconds_until_unload null and engine null, the log has the unload line; the next POST /speak reloaded in 267 s and returned 200 audio/mpeg, 47649 bytes, ffprobe mp3 3.94 s; tmp/workflows/release/keepalive-check.json, keepalive-container.log" -> "wip/release/verify/keepalive-0.2.0.json: on 0.2.0 with -e IDLE_UNLOAD_SECONDS=10 the model unloaded 9 s after ready (/health loaded false, seconds_until_unload null, engine null); the next /speak returned 200 audio/mpeg 47649 bytes in 281 s and /health loaded true after"; reason: the verifier re-ran keepalive on the released 0.2.0 image; the earlier evidence named 0.1.0
- [x] `ACC-DOCKER-53-DATA` **One data volume** - HIGH; the single named volume `leftenant-voice-tts-service-data` at `/data` holds the Hugging Face cache (`/data/huggingface`) and the voices (`/data/voices`); compose, `docker-run`, the functional tests and the README agree, and a container on the migrated volume becomes ready with no download
  - evidence: image sha256:375ae2f9a41e; env HF_HOME=/data/huggingface VOICES_DIR=/data/voices; compose and docker-run mount data:/data, no build key, README one volume; s2pro-hf-cache copied (11011983136 bytes, 41 files) and empty s2pro-voices equal at copy; offline container on data ready 281 s, no downloading, grimaldus; test 64, functional 21 in 1058.63 s EXIT=0 tmp/workflows/one-volume/logs/functional-full.log
  - test: docker compose config from service/ mounts only leftenant-voice-tts-service-data at /data with no build key; the image carries HF_HOME=/data/huggingface and VOICES_DIR=/data/voices; a container on it with HF_HUB_OFFLINE=1 reaches ready with no download
  - test-tags: FUNCTIONAL
  - log: 2026-11-10T22:32:48Z @kj added
  - log: 2026-11-10T22:50:51Z @kj closed: closed: verified
  - log: 2026-11-11T22:21:02Z @kj edited test "docker compose --env-file .env config from service/ mounts only data at /data with no build key; the image carries HF_HOME=/data/huggingface and VOICES_DIR=/data/voices; a container on data with HF_HUB_OFFLINE=1 reaches ready with no download" -> "docker compose config from service/ mounts only data at /data with no build key; the image carries HF_HOME=/data/huggingface and VOICES_DIR=/data/voices; a container on data with HF_HUB_OFFLINE=1 reaches ready with no download"
  - log: 2026-11-13T18:38:02Z @kj edited text "the single named volume `data` at `/data` holds the Hugging Face cache (`/data/huggingface`) and the voices (`/data/voices`); compose, `docker-run`, the functional tests and the README agree, and a container on the migrated volume becomes ready with no download" -> "the single named volume `leftenant-voice-tts-service-data` at `/data` holds the Hugging Face cache (`/data/huggingface`) and the voices (`/data/voices`); compose, `docker-run`, the functional tests and the README agree, and a container on the migrated volume becomes ready with no download"; test "docker compose config from service/ mounts only data at /data with no build key; the image carries HF_HOME=/data/huggingface and VOICES_DIR=/data/voices; a container on data with HF_HUB_OFFLINE=1 reaches ready with no download" -> "docker compose config from service/ mounts only leftenant-voice-tts-service-data at /data with no build key; the image carries HF_HOME=/data/huggingface and VOICES_DIR=/data/voices; a container on it with HF_HUB_OFFLINE=1 reaches ready with no download"
- [x] `ACC-DOCKER-62-COMPOSE-HARDCODED` **Compose values hardcoded** - HIGH; compose.yml names the image leftenant-voice-tts:latest, container port 8000 on a daemon-assigned loopback host port, GPU 0, engine s2pro, idle 3600 s and max 3000 chars as literals; no .env file is read or shipped; the README has no --env-file step
  - evidence: compose.yml has no variable reference and literal image leftenant-voice-tts:latest, port 127.0.0.1::8000, GPU 0, engine s2pro, idle 3600, max 3000; docker compose config shows host_ip 127.0.0.1, target 8000, no published; no .env files; README no --env-file; unit 90 passed; logs wip/compose-rename/logs/
  - test: cd service && docker compose config; ls -a service shows no .env; compose.yml and README.md hold no --env-file and compose.yml no ${
  - test-tags: FUNCTIONAL
  - log: 2026-11-11T22:06:22Z @kj added
  - log: 2026-11-11T22:09:36Z @kj edited text "compose.yml names the image voice-tts:latest, port 8000, GPU 0, engine s2pro, idle 3600 s and max 3000 chars as literals; no .env file is read or shipped; the README has no --env-file step" -> "compose.yml names the image voice-tts:latest, container port 8000 on a daemon-assigned loopback host port, GPU 0, engine s2pro, idle 3600 s and max 3000 chars as literals; no .env file is read or shipped; the README has no --env-file step"
  - log: 2026-11-11T22:14:04Z @kj closed
  - log: 2026-11-11T22:28:51Z @kj edited text "compose.yml names the image voice-tts:latest, container port 8000 on a daemon-assigned loopback host port, GPU 0, engine s2pro, idle 3600 s and max 3000 chars as literals; no .env file is read or shipped; the README has no --env-file step" -> "compose.yml names the image leftenant-voice-tts:latest, container port 8000 on a daemon-assigned loopback host port, GPU 0, engine s2pro, idle 3600 s and max 3000 chars as literals; no .env file is read or shipped; the README has no --env-file step"
  - log: 2026-11-11T22:29:01Z @kj edited evidence "compose.yml has no ${ or variable and literal image voice-tts:latest, port 127.0.0.1::8000, GPU 0, engine s2pro, idle 3600, max 3000; docker compose config shows host_ip 127.0.0.1, target 8000, no published; no .env files; README no --env-file; unit 90 passed; logs wip/compose-hardcoded/logs/" -> "compose.yml has no variable reference and literal image leftenant-voice-tts:latest, port 127.0.0.1::8000, GPU 0, engine s2pro, idle 3600, max 3000; docker compose config shows host_ip 127.0.0.1, target 8000, no published; no .env files; README no --env-file; unit 90 passed; logs wip/compose-rename/logs/"
- [x] `ACC-DOCKER-63-COMPOSE-PLAIN` **Plain compose start** - HIGH; with the password seeded at /home/lab/.cache/voice-tts/password.txt, docker compose up -d starts leftenant-voice-tts-service with no --env-file and no override; docker compose port names the published port; /health answers; POST /login 200 and GET /session true; down leaves no container
  - evidence: docker compose up -d started leftenant-voice-tts-service with no --env-file; port 127.0.0.1:61619 not 8000; /health 200; POST /login 200; GET /session authenticated true; down left ps -a empty; logs wip/compose-rename/logs/
  - test: cd service; docker compose up -d --remove-orphans; docker compose port leftenant-voice-tts-service 8000; exec curl /health; login; session; down
  - test-tags: FUNCTIONAL
  - log: 2026-11-11T22:06:29Z @kj added
  - log: 2026-11-11T22:09:41Z @kj edited text "with the password seeded at /home/lab/.cache/voice-tts/password.txt, docker compose up -d starts voice-tts-service with no --env-file and no override; /health answers; POST /login 200 and GET /session true; down leaves no container" -> "with the password seeded at /home/lab/.cache/voice-tts/password.txt, docker compose up -d starts voice-tts-service with no --env-file and no override; docker compose port names the published port; /health answers; POST /login 200 and GET /session true; down leaves no container"; test "cd service; docker compose up -d; docker compose exec voice-tts-service curl /health; login; session; down" -> "cd service; docker compose up -d; docker compose port voice-tts-service 8000; exec curl /health; login; session; down"
  - log: 2026-11-11T22:14:06Z @kj closed
  - log: 2026-11-11T22:28:51Z @kj edited text "with the password seeded at /home/lab/.cache/voice-tts/password.txt, docker compose up -d starts voice-tts-service with no --env-file and no override; docker compose port names the published port; /health answers; POST /login 200 and GET /session true; down leaves no container" -> "with the password seeded at /home/lab/.cache/voice-tts/password.txt, docker compose up -d starts leftenant-voice-tts-service with no --env-file and no override; docker compose port names the published port; /health answers; POST /login 200 and GET /session true; down leaves no container"; test "cd service; docker compose up -d; docker compose port voice-tts-service 8000; exec curl /health; login; session; down" -> "cd service; docker compose up -d; docker compose port leftenant-voice-tts-service 8000; exec curl /health; login; session; down"
  - log: 2026-11-11T22:29:02Z @kj edited evidence "docker compose up -d started voice-tts-service with no --env-file; port 127.0.0.1:60662 not 8000; /health 200; POST /login 200; GET /session authenticated true; down left ps -a empty; logs wip/compose-hardcoded/logs/" -> "docker compose up -d started leftenant-voice-tts-service with no --env-file; port 127.0.0.1:61619 not 8000; /health 200; POST /login 200; GET /session authenticated true; down left ps -a empty; logs wip/compose-rename/logs/"
  - log: 2026-11-11T23:00:14Z @kj edited test "cd service; docker compose up -d; docker compose port leftenant-voice-tts-service 8000; exec curl /health; login; session; down" -> "cd service; docker compose up -d --remove-orphans; docker compose port leftenant-voice-tts-service 8000; exec curl /health; login; session; down"

## Registry `IMAGE`

The NAS GitLab registry: tag, push and pull-back of the service image

code IMAGE: pm-tools caps a category code at six letters, so the brief's REGISTRY is written IMAGE

- log: 2026-11-09T01:29:43Z @kj category created
- log: 2026-11-09T01:30:44Z @kj added note "code IMAGE: pm-tools caps a category code at six letters, so the brief's REGISTRY is written IMAGE"

- [x] `ACC-IMAGE-37-PUSH` **docker-push pushes latest only** - HIGH; make -f s2pro.mk docker-push pushes only IMAGE:latest to registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts; make -f s2pro.mk docker-prune deletes every other tag, so the registry keeps only latest
  - evidence: release 2026-11-15: docker-push pushed latest at sha256:37f7c8f2979de4789fa1b31d90f8ee164dba708483d7cc3cd1ec4bb592b18584; docker-prune deleted 0.2.0 and 0.3.0 (HTTP 200 each); docker pull latest reports that digest, Image is up to date; the GitLab API lists only latest (wip/release/logs/docker-push.log, docker-prune.log, pull-check.log)
  - test: docker pull registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts:latest is up to date; the GitLab registry API lists only the tag latest
  - test-tags: MANUAL
  - log: 2026-11-09T01:29:43Z @kj added
  - log: 2026-11-09T20:04:33Z @kj closed: verified in 0.2.0
  - log: 2026-11-11T22:28:52Z @kj edited text "make -f s2pro.mk docker-push pushes IMAGE:VERSION and IMAGE:latest to registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice/s2pro-tts" -> "make -f s2pro.mk docker-push pushes IMAGE:VERSION and IMAGE:latest to registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts"
  - log: 2026-11-11T23:00:49Z @kj edited evidence "docker push 0.2.0 printed digest sha256:d334ef340da3 (48 s) and latest the same digest (1 s); the private project konrad.jelen/leftenant-voice was created (lookup 404, create 201); release-push.log, gitlab-project.json" -> "the recorded push digest sha256:d334ef340da3 and the project konrad.jelen/leftenant-voice belong to the superseded project; make -n -f s2pro.mk docker-push names the two pushes to registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts (wip/compose-rename/logs/docker-push-dryrun.txt) and they have not run; the push awaits the owner approval"; reason: the push evidence belongs to the superseded registry project, so the criterion now states the new path has not been pushed
  - log: 2026-11-11T23:00:54Z @kj edited evidence "the recorded push digest sha256:d334ef340da3 and the project konrad.jelen/leftenant-voice belong to the superseded project; make -n -f s2pro.mk docker-push names the two pushes to registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts (wip/compose-rename/logs/docker-push-dryrun.txt) and they have not run; the push awaits the owner approval" -> "the recorded push digest sha256:d334ef340da3 and the project konrad.jelen/leftenant-voice belong to the superseded project; make -n -f s2pro.mk docker-push names the two pushes to registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts (wip/compose-rename/logs/docker-push-dryrun.txt) and they have not run; the push awaits the owner's approval"; reason: write the plan wording exactly
  - log: 2026-11-12T08:50:01Z @kj edited test "make -n -f s2pro.mk docker-push shows both pushes; run it only with the owner's approval" -> "docker pull registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts:0.2.0 and :latest report digest sha256:dd3a0d3936631048e21c721dab62f0df82a265f8890ea04c5114066bd8ab365b"; evidence "the recorded push digest sha256:d334ef340da3 and the project konrad.jelen/leftenant-voice belong to the superseded project; make -n -f s2pro.mk docker-push names the two pushes to registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts (wip/compose-rename/logs/docker-push-dryrun.txt) and they have not run; the push awaits the owner's approval" -> "push run 2026-11-12: docker-push pushed 0.2.0 and latest to registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts, both digest sha256:dd3a0d3936631048e21c721dab62f0df82a265f8890ea04c5114066bd8ab365b; docker pull reports both up to date with the same digest; the GitLab API lists both tags (wip/registry-push/logs/docker-push.log, registry-pull-check.log, registry-tags.json); project konrad.jelen/leftenant-voice-tts created (id 88)"
  - log: 2026-11-15T21:19:23Z @kj amended title "docker-push pushes both tags" -> "docker-push pushes latest only"; text "make -f s2pro.mk docker-push pushes IMAGE:VERSION and IMAGE:latest to registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts" -> "HIGH; make -f s2pro.mk docker-push pushes only IMAGE:latest to registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts; make -f s2pro.mk docker-prune deletes every other tag, so the registry keeps only latest"; reason: owner order 2026-11-15: releases push latest only and the registry keeps no other tag
  - log: 2026-11-15T21:19:23Z @kj edited test "docker pull registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts:0.2.0 and :latest report digest sha256:dd3a0d3936631048e21c721dab62f0df82a265f8890ea04c5114066bd8ab365b" -> "docker pull registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts:latest is up to date; the GitLab registry API lists only the tag latest"; evidence "push run 2026-11-12: docker-push pushed 0.2.0 and latest to registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts, both digest sha256:dd3a0d3936631048e21c721dab62f0df82a265f8890ea04c5114066bd8ab365b; docker pull reports both up to date with the same digest; the GitLab API lists both tags (wip/registry-push/logs/docker-push.log, registry-pull-check.log, registry-tags.json); project konrad.jelen/leftenant-voice-tts created (id 88)" -> "release 2026-11-15: docker-push pushed latest at sha256:37f7c8f2979de4789fa1b31d90f8ee164dba708483d7cc3cd1ec4bb592b18584; docker-prune deleted 0.2.0 and 0.3.0 (HTTP 200 each); docker pull latest reports that digest, Image is up to date; the GitLab API lists only latest (wip/release/logs/docker-push.log, docker-prune.log, pull-check.log)"; reason: the criterion now states the latest-only release
- [x] `ACC-IMAGE-38-PULL` **Pull-back serves an MP3** - HIGH; a docker pull of the pushed tag, run back on a fresh named volume, downloads from Hugging Face and serves an MP3
  - evidence: docker rmi then docker pull 0.2.0 returned Digest sha256:d334ef340da3 in 1 s and image id d334ef340da3; the fresh-volume run on GPU 0 was ready in 473 s and POST /speak returned 200 audio/mpeg 44413 bytes, ffprobe mp3 3.657 s, WER 0.0; pull-check.json, pull-measure.json
  - test: docker pull IMAGE:VERSION; docker run --gpus device=0 with a fresh named volume at /data/huggingface; /health reaches ready after the Hugging Face download; POST /speak; assert audio/mpeg
  - test-tags: FUNCTIONAL
  - log: 2026-11-09T01:29:43Z @kj added
  - log: 2026-11-09T07:47:58Z @kj edited text "a docker pull of the pushed tag, run back, serves an MP3" -> "a docker pull of the pushed tag, run back on a fresh named volume, downloads from Hugging Face and serves an MP3"; test "docker pull IMAGE:VERSION; docker run --gpus device=0; POST /speak; assert audio/mpeg" -> "docker pull IMAGE:VERSION; docker run --gpus device=0 with a fresh named volume at /root/.cache/huggingface; /health reaches ready after the Hugging Face download; POST /speak; assert audio/mpeg"
  - log: 2026-11-09T20:04:35Z @kj closed: verified in 0.2.0
  - log: 2026-11-11T23:00:56Z @kj edited test "docker pull IMAGE:VERSION; docker run --gpus device=0 with a fresh named volume at /root/.cache/huggingface; /health reaches ready after the Hugging Face download; POST /speak; assert audio/mpeg" -> "docker pull IMAGE:VERSION; docker run --gpus device=0 with a fresh named volume at /data/huggingface; /health reaches ready after the Hugging Face download; POST /speak; assert audio/mpeg"; reason: the fresh volume mounts at /data/huggingface now, so the old path tested nothing
- [x] `ACC-IMAGE-39-ENGINE-IMAGE` **Engine-layer image pushed under the owner's approval** - HIGH; the image at :0.2.0 is built with the engine layer, the +3 dB hiss cap and the four ENV defaults; the owner approved its push to the NAS registry on 2026-11-09
  - evidence: engine-layer image 0.2.0 id sha256:d334ef340da3, 18.7 GB, carrying the hiss cap and the four ENV defaults, was pushed under the owner's approval and pulled back on a fresh volume serving a 44413-byte MP3 with WER 0.0 on GPU 0; release-digests.json
  - test: docker manifest inspect --insecure registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts:0.2.0 and :latest show digest sha256:dd3a0d3936631048e21c721dab62f0df82a265f8890ea04c5114066bd8ab365b; docker pull 0.2.0; run it on GPU 0 and POST /speak; assert audio/mpeg
  - test-tags: MANUAL
  - log: 2026-11-09T01:29:43Z @kj added
  - log: 2026-11-09T02:42:13Z @kj edited test "docker images shows s2pro-tts:0.1.0 id 0fd810729ba9; the container check serves an MP3; do not run docker-push" -> "docker images shows s2pro-tts:0.1.0 id d9de9bcd531e; the container check serves an MP3; do not run docker-push"; reason: the image was rebuilt with the MP3 headroom fix
  - log: 2026-11-09T07:47:58Z @kj edited test "docker images shows s2pro-tts:0.1.0 id d9de9bcd531e; the container check serves an MP3; do not run docker-push" -> "docker images shows s2pro-tts:0.1.0 id 99b7e0f0fd61; a container on a fresh named volume downloads from Hugging Face and serves an MP3; do not run docker-push"
  - log: 2026-11-09T20:04:38Z @kj closed: verified in 0.2.0
  - log: 2026-11-09T21:04:02Z @kj amended title "Engine-layer image awaits the owner's push" -> "Engine-layer image pushed under the owner's approval"; text "the image at :0.1.0 is built and tested locally with the engine layer; no push is made until the owner approves" -> "the image at :0.2.0 is built with the engine layer, the +3 dB hiss cap and the four ENV defaults; the owner approved its push to the NAS registry on 2026-11-09"; reason: the image at 0.2.0 was pushed under the owner's approval on 2026-11-09, so the awaiting-push text and the 0.1.0 test were stale
  - log: 2026-11-09T21:04:03Z @kj edited test "docker images shows s2pro-tts:0.1.0 id 99b7e0f0fd61; a container on a fresh named volume downloads from Hugging Face and serves an MP3; do not run docker-push" -> "docker manifest inspect --insecure registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice/s2pro-tts:0.2.0 and :latest show the same digest sha256:d334ef340da3d3ad4a51d3f19972107eb55980dd9e098a1dab9415463720398a; docker pull 0.2.0; run it on GPU 0 and POST /speak; assert audio/mpeg"; reason: the old test named the superseded 0.1.0 image id, which docker images does not have
  - log: 2026-11-11T23:00:58Z @kj edited test "docker manifest inspect --insecure registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice/s2pro-tts:0.2.0 and :latest show the same digest sha256:d334ef340da3d3ad4a51d3f19972107eb55980dd9e098a1dab9415463720398a; docker pull 0.2.0; run it on GPU 0 and POST /speak; assert audio/mpeg" -> "docker manifest inspect --insecure registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice/s2pro-tts:0.2.0 and :latest show the same digest sha256:d334ef340da3d3ad4a51d3f19972107eb55980dd9e098a1dab9415463720398a for the pre-rename image path; the renamed repository's push awaits the owner's approval, so its manifest inspect runs after that; docker pull 0.2.0; run it on GPU 0 and POST /speak; assert audio/mpeg"; reason: the manifest path is the pre-rename image, and the renamed repository has not been pushed
  - log: 2026-11-12T08:50:01Z @kj edited test "docker manifest inspect --insecure registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice/s2pro-tts:0.2.0 and :latest show the same digest sha256:d334ef340da3d3ad4a51d3f19972107eb55980dd9e098a1dab9415463720398a for the pre-rename image path; the renamed repository's push awaits the owner's approval, so its manifest inspect runs after that; docker pull 0.2.0; run it on GPU 0 and POST /speak; assert audio/mpeg" -> "docker manifest inspect --insecure registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts:0.2.0 and :latest show digest sha256:dd3a0d3936631048e21c721dab62f0df82a265f8890ea04c5114066bd8ab365b; docker pull 0.2.0; run it on GPU 0 and POST /speak; assert audio/mpeg"
- [x] `ACC-IMAGE-64-RENAMED` **Image and service renamed** - HIGH; the image is registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts and the compose service and container are leftenant-voice-tts-service in compose.yml, s2pro.mk, the README and tests/functional/support.py; make docker-build and docker-tag produce it locally
  - evidence: docker build from cache tagged leftenant-voice-tts:0.2.0 id dd3a0d393663; docker-tag made :latest at the same id; docker compose config names service and container leftenant-voice-tts-service and image registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts:latest; make -n -f s2pro.mk docker-push shows both pushes under the new path; compose start healthy, port 61619, login 200, session true; unit 90; wip/compose-rename/logs/
  - test: make -f s2pro.mk docker-build docker-tag; docker images | grep leftenant-voice-tts; cd service && docker compose config
  - test-tags: FUNCTIONAL
  - log: 2026-11-11T22:28:54Z @kj added
  - log: 2026-11-11T22:29:04Z @kj closed

## Tests `TESTS`

The unit and functional suites: how they run, what they cover and that they can fail

- log: 2026-11-09T01:29:43Z @kj category created

- [x] `ACC-TESTS-40-UNIT` **make test runs the unit suite** - HIGH; make test runs the text splitter, sentence join and level match, voice loader, API with a stub speaker, error paths and settings including IDLE_UNLOAD_SECONDS; no GPU, under a minute, and exits 0
  - evidence: make test: 29 passed in 18.36 s, no GPU and no model (tmp/workflows/goal-trackers/unit-green.log)
  - test: make test; set IDLE_UNLOAD_SECONDS and assert the reported seconds-until-unload changes
  - test-tags: UNIT
  - log: 2026-11-09T01:29:43Z @kj added
  - log: 2026-11-09T01:31:39Z @kj edited text "make test runs the text splitter, sentence join and level match, voice loader, API with a stub speaker, error paths and settings including IDLE_UNLOAD_SECONDS; no GPU, under a minute" -> "make test runs the text splitter, sentence join and level match, voice loader, API with a stub speaker, error paths and settings including IDLE_UNLOAD_SECONDS; no GPU, under a minute, and exits 0"
  - log: 2026-11-09T02:03:02Z @kj closed: verified by the suite
- [x] `ACC-TESTS-41-FUNCTIONAL` **make test-functional runs the functional suite** - HIGH; make test-functional boots the real service natively and the image where the daemon allows GPU containers, sends real requests, checks the MP3, error codes, idle unload and reload, and exits 0
  - evidence: make test-functional: 11 passed in 430.20 s, native service and image, exit 0 (tmp/workflows/goal-trackers/functional-green.log)
  - test: make test-functional
  - test-tags: FUNCTIONAL
  - log: 2026-11-09T01:29:44Z @kj added
  - log: 2026-11-09T01:31:39Z @kj edited text "make test-functional boots the real service natively and the image where the daemon allows GPU containers, sends real requests and checks the MP3, error codes, idle unload and reload" -> "make test-functional boots the real service natively and the image where the daemon allows GPU containers, sends real requests, checks the MP3, error codes, idle unload and reload, and exits 0"
  - log: 2026-11-09T02:03:02Z @kj closed: verified by the suite
- [x] `ACC-TESTS-42-CAN-FAIL` **Both suites can fail** - HIGH; a deliberately wrong assertion makes each suite exit non-zero; one failing run of each is recorded before the green run
  - evidence: unit-red.log: 1 failed of 29, exit 2; functional-red.log: 1 failed in 49.12 s, exit 2; both restored and green after
  - test: break one assertion in each suite, run it, record the non-zero exit, then restore
  - test-tags: UNIT, FUNCTIONAL
  - log: 2026-11-09T01:29:44Z @kj added
  - log: 2026-11-09T02:03:02Z @kj closed: verified by the two failing runs
- [x] `ACC-TESTS-43-LEFTOVER` **Functional suite leaves nothing behind** - MEDIUM; after make test-functional no test uvicorn process and no s2pro-tts container remain
  - evidence: test_no_test_service_process and test_no_test_container green in the functional run: native pid gone, port closed, no s2pro-functional-test container (tmp/workflows/goal-trackers/functional-green.log)
  - test: after make test-functional run pgrep -f uvicorn and docker ps; expect no test process or s2pro-tts container
  - test-tags: FUNCTIONAL
  - log: 2026-11-09T01:29:44Z @kj added
  - log: 2026-11-09T02:03:02Z @kj closed: verified after the functional run
- [x] `ACC-TESTS-52-WEB` **Unit and functional coverage of the web page** - HIGH; the unit suite covers the page, settings, upload, delete, seed and the token path, and the functional suite covers the page, settings, upload, speak and delete against the real service and image
  - evidence: make -f s2pro.mk test 2026-11-10: 64 passed in 17.31 s including 22 in tests/unit/test_webapp.py; make -f s2pro.mk test-functional 2026-11-10: 21 passed in 883.22 s, exit 0, log tmp/workflows/webapp-rebuild/logs/functional-full.log on image sha256:315138ebf821; the source hashes in tmp/workflows/webapp-rebuild/logs/tree-state.txt equal the tree
  - test: make test and make test-functional
  - test-tags: UNIT, FUNCTIONAL
  - log: 2026-11-10T16:41:33Z @kj added
  - log: 2026-11-10T17:31:53Z @kj closed
  - log: 2026-11-10T18:51:02Z @kj edited evidence "make -f s2pro.mk test 2026-11-10: 63 passed in 17.10 s including 21 in tests/unit/test_webapp.py; make -f s2pro.mk test-functional 2026-11-10: 21 passed in 877.56 s, exit 0, log tmp/workflows/webapp/logs/functional-full.log, the source hashes in logs/tree-state-run2.txt equal the current tree" -> "make -f s2pro.mk test 2026-11-10: 64 passed in 17.31 s including 21 in tests/unit/test_webapp.py; make -f s2pro.mk test-functional 2026-11-10: 21 passed in 883.22 s, exit 0, log tmp/workflows/webapp-rebuild/logs/functional-full.log on image sha256:315138ebf821; the source hashes in tmp/workflows/webapp-rebuild/logs/tree-state.txt equal the tree"
  - log: 2026-11-10T19:01:11Z @kj edited evidence "make -f s2pro.mk test 2026-11-10: 64 passed in 17.31 s including 21 in tests/unit/test_webapp.py; make -f s2pro.mk test-functional 2026-11-10: 21 passed in 883.22 s, exit 0, log tmp/workflows/webapp-rebuild/logs/functional-full.log on image sha256:315138ebf821; the source hashes in tmp/workflows/webapp-rebuild/logs/tree-state.txt equal the tree" -> "make -f s2pro.mk test 2026-11-10: 64 passed in 17.31 s including 22 in tests/unit/test_webapp.py; make -f s2pro.mk test-functional 2026-11-10: 21 passed in 883.22 s, exit 0, log tmp/workflows/webapp-rebuild/logs/functional-full.log on image sha256:315138ebf821; the source hashes in tmp/workflows/webapp-rebuild/logs/tree-state.txt equal the tree"; reason: the reviewed tests/unit/test_webapp.py collects and passes 22 tests; the evidence carried 21 from the pre-review 63-test run

## Web `WEB`

The page served at /, the session token, the writable voice folder and the upload and delete endpoints

- log: 2026-11-10T16:41:24Z @kj category created

- [x] `ACC-WEB-44-PAGE` **GET / serves the page** - HIGH; GET / returns the page as text/html; its stylesheet and script come from /static (app.css, app.js); every element id the script uses is in the page
  - evidence: make test 2026-11-10: 63 passed in 17.66 s; tests/unit/test_webapp.py::test_the_page_is_served green (GET / 200 text/html, all 16 page ids present)
  - test: GET / is 200 text/html and contains the page ids; the functional suite checks the container page
  - test-tags: UNIT, FUNCTIONAL
  - log: 2026-11-10T16:41:24Z @kj added
  - log: 2026-11-10T16:41:38Z @kj closed
  - log: 2026-11-17T07:55:51Z @kj amended text "GET / returns the self-contained page as text/html with every element id the page script uses" -> "GET / returns the page as text/html; its stylesheet and script come from /static (app.css, app.js); every element id the script uses is in the page"
- [x] `ACC-WEB-45-TOKEN` **Settings token in memory, never echoed, download uses it** - HIGH; POST /settings/hf-token keeps the token in the service process's memory only after Hugging Face whoami accepts it; GET /settings reports whether it is set and its account name; no response echoes it; the engines pass it to their Hugging Face downloads at load time
  - evidence: make test 2026-11-10: 63 passed in 17.66 s; test_the_token_is_set_cleared_and_never_echoed, test_the_engine_passes_the_token_to_both_downloads and test_available_engines_passes_the_token_through green
  - test: unit settings and engine-token tests
  - test-tags: UNIT
  - log: 2026-11-10T16:41:27Z @kj added
  - log: 2026-11-10T16:41:38Z @kj closed
  - log: 2026-11-17T07:55:51Z @kj amended text "POST /settings/hf-token stores the token in the service process's memory for the session; GET /settings reports only whether it is set; no response echoes it; the S2 Pro engine passes it to both Hugging Face calls at load time" -> "POST /settings/hf-token keeps the token in the service process's memory only after Hugging Face whoami accepts it; GET /settings reports whether it is set and its account name; no response echoes it; the engines pass it to their Hugging Face downloads at load time"
- [x] `ACC-WEB-46-STATUS` **The page shows /health state and refresh** - HIGH; the top bar shows the speech and transcription states polled from GET /health every 2 s as badges, with engine, busy, seconds_until_unload and the error text in the speech badge's tooltip; a load error also shows on the render page; a waiting transcription shows the load steps
  - evidence: make test 2026-11-10: 63 passed in 17.66 s; test_the_page_is_served finds service-status and the /health state tests test_health_reports_ready_after_a_load and test_health_reports_a_failed_load_and_speak_answers_500 pass
  - test: unit page ids and /health fields; the functional page test
  - test-tags: UNIT, FUNCTIONAL
  - log: 2026-11-10T16:41:27Z @kj added
  - log: 2026-11-10T16:41:38Z @kj closed
  - log: 2026-11-17T12:09:32Z @kj amended text "the page shows the load state polled from GET /health every 2 s, the engine, busy and seconds_until_unload, a progress bar while the model downloads or loads, and the error text" -> "the top bar shows the speech and transcription states polled from GET /health every 2 s as badges, with engine, busy, seconds_until_unload and the error text in the speech badge's tooltip; a load error also shows on the render page; a waiting transcription shows the load steps"
- [x] `ACC-WEB-47-PLAY` **The page generates an MP3 and plays it** - HIGH; the page posts text, voice and engine to POST /speak, plays the returned audio/mpeg in the page and offers it as speech.mp3
  - evidence: verifier 2026-11-10: Playwright at 1280x900 reached state ready; the page set and cleared the session token, uploaded verify-page and deleted it, then POST /speak gave #player a blob: source with duration 3.90 s and a speech.mp3 download link, zero console errors; screenshots wip/webapp/verify/page.png and wip/webapp/verify/page-generate.png
  - test: the verifier generates in a browser and reads the player's source and duration
  - test-tags: FUNCTIONAL
  - log: 2026-11-10T16:41:29Z @kj added
  - log: 2026-11-10T17:29:11Z @kj closed
- [x] `ACC-WEB-48-UPLOAD` **Reference upload clones a new voice** - HIGH; POST /voices accepts a name, a transcript and a reference WAV and clones the voice at once; the limits are the name rule, 1 to 1000 characters, 25 MB, 3 to 30 s, mono output
  - evidence: make -f s2pro.mk test-functional 2026-11-10: 21 passed in 877.56 s, exit 0 (tmp/workflows/webapp/logs/functional-full.log); test_upload_reference and test_speak_with_the_uploaded_voice green - the uploaded name appears under s2pro and in uploaded, and POST /speak gave audio/mpeg, W/functional-upload.mp3 reads mp3 3.944 s by ffprobe; unit upload tests green in make test 63 passed
  - test: unit upload tests; the functional suite uploads and speaks the new voice
  - test-tags: UNIT, FUNCTIONAL
  - log: 2026-11-10T16:41:29Z @kj added
  - log: 2026-11-10T17:31:50Z @kj closed
- [x] `ACC-WEB-49-DELETE` **Delete rules 200/409/404** - HIGH; DELETE /voices/{name} deletes an uploaded voice and its transcript, refuses a bundled voice with 409 and an unknown name with 404
  - evidence: make -f s2pro.mk test-functional 2026-11-10: 21 passed in 877.56 s, exit 0; test_delete_rules green on the real service - an uploaded voice 200 and gone from /voices, bundled grimaldus 409, unknown 404; unit delete tests green in make test 63 passed
  - test: unit delete tests; the functional suite deletes an upload and checks the codes
  - test-tags: UNIT, FUNCTIONAL
  - log: 2026-11-10T16:41:29Z @kj added
  - log: 2026-11-10T17:31:50Z @kj closed
- [x] `ACC-WEB-50-SEED` **Seed at start, volume persistence, re-encode on mtime** - HIGH; the service copies SEED_VOICES_DIR into the writable VOICES_DIR at start, overwrites bundled files, leaves uploaded files in place, and re-encodes a voice whose WAV modification time changed
  - evidence: image sha256:315138ebf821 rebuilt 2026-11-10 from the reviewed tree; make -f s2pro.mk test 2026-11-10: 64 passed including test_seed_copies_refreshes_and_leaves_uploads; make -f s2pro.mk test-functional 2026-11-10: 21 passed in 883.22 s, exit 0, log tmp/workflows/webapp-rebuild/logs/functional-full.log; test_service_voices_is_unchanged green and the container seeded grimaldus; voice folder moved from s2pro-voices:/app/voices to data:/data/voices
  - test: unit seed and mtime tests; the functional suite leaves the repository voices unchanged
  - test-tags: UNIT, FUNCTIONAL
  - log: 2026-11-10T16:41:32Z @kj added
  - log: 2026-11-10T16:41:38Z @kj closed
  - log: 2026-11-10T18:51:05Z @kj edited evidence "make test 2026-11-10: 63 passed in 17.66 s; test_seed_copies_refreshes_and_leaves_uploads, test_seed_does_nothing_when_the_folders_are_the_same and test_the_voice_cache_re_encodes_when_the_wav_changes green" -> "image sha256:315138ebf821 rebuilt 2026-11-10 from the reviewed tree; make -f s2pro.mk test 2026-11-10: 64 passed including test_seed_copies_refreshes_and_leaves_uploads; make -f s2pro.mk test-functional 2026-11-10: 21 passed in 883.22 s, exit 0, log tmp/workflows/webapp-rebuild/logs/functional-full.log; test_service_voices_is_unchanged green and the container seeded grimaldus"
  - log: 2026-11-10T22:51:00Z @kj edited evidence "image sha256:315138ebf821 rebuilt 2026-11-10 from the reviewed tree; make -f s2pro.mk test 2026-11-10: 64 passed including test_seed_copies_refreshes_and_leaves_uploads; make -f s2pro.mk test-functional 2026-11-10: 21 passed in 883.22 s, exit 0, log tmp/workflows/webapp-rebuild/logs/functional-full.log; test_service_voices_is_unchanged green and the container seeded grimaldus" -> "image sha256:315138ebf821 rebuilt 2026-11-10 from the reviewed tree; make -f s2pro.mk test 2026-11-10: 64 passed including test_seed_copies_refreshes_and_leaves_uploads; make -f s2pro.mk test-functional 2026-11-10: 21 passed in 883.22 s, exit 0, log tmp/workflows/webapp-rebuild/logs/functional-full.log; test_service_voices_is_unchanged green and the container seeded grimaldus; voice folder moved from s2pro-voices:/app/voices to data:/data/voices"
- [x] `ACC-WEB-51-IMAGE` **The rebuilt image serves page, settings, upload** - HIGH; the rebuilt image seeds /app/seed-voices into /app/voices and serves the page, GET /settings and POST /voices
  - evidence: image registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice/s2pro-tts:0.2.0 sha256:315138ebf821 built 2026-11-10T18:35:15Z with the classic builder, 18714696453 bytes, in-image sha256 equals the tree for app.py, index.html, engine_s2pro.py, registry.py and speak_s2pro.py; make -f s2pro.mk test-functional 2026-11-10: 21 passed in 883.22 s, exit 0, log tmp/workflows/webapp-rebuild/logs/functional-full.log, test_container_serves_the_page_and_the_settings green; voice folder moved from s2pro-voices:/app/voices to data:/data/voices
  - test: the functional container page test
  - test-tags: FUNCTIONAL
  - log: 2026-11-10T16:41:33Z @kj added
  - log: 2026-11-10T17:31:53Z @kj closed
  - log: 2026-11-10T18:51:07Z @kj edited evidence "image registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice/s2pro-tts:0.2.0 sha256:8ac6fb676197 built 2026-11-10T16:55:43Z with the classic builder, 18714697913 bytes; /app/seed-voices/grimaldus.wav, /app/voices and /app/service/static/index.html present, python-multipart 0.0.33; test_container_serves_the_page_and_the_settings green in the 21-test functional run - GET / 200 text/html with all page ids, hf_token_set false, grimaldus under s2pro with uploaded empty" -> "image registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice/s2pro-tts:0.2.0 sha256:315138ebf821 built 2026-11-10T18:35:15Z with the classic builder, 18714696453 bytes, in-image sha256 equals the tree for app.py, index.html, engine_s2pro.py, registry.py and speak_s2pro.py; make -f s2pro.mk test-functional 2026-11-10: 21 passed in 883.22 s, exit 0, log tmp/workflows/webapp-rebuild/logs/functional-full.log, test_container_serves_the_page_and_the_settings green"
  - log: 2026-11-10T22:51:00Z @kj edited evidence "image registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice/s2pro-tts:0.2.0 sha256:315138ebf821 built 2026-11-10T18:35:15Z with the classic builder, 18714696453 bytes, in-image sha256 equals the tree for app.py, index.html, engine_s2pro.py, registry.py and speak_s2pro.py; make -f s2pro.mk test-functional 2026-11-10: 21 passed in 883.22 s, exit 0, log tmp/workflows/webapp-rebuild/logs/functional-full.log, test_container_serves_the_page_and_the_settings green" -> "image registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice/s2pro-tts:0.2.0 sha256:315138ebf821 built 2026-11-10T18:35:15Z with the classic builder, 18714696453 bytes, in-image sha256 equals the tree for app.py, index.html, engine_s2pro.py, registry.py and speak_s2pro.py; make -f s2pro.mk test-functional 2026-11-10: 21 passed in 883.22 s, exit 0, log tmp/workflows/webapp-rebuild/logs/functional-full.log, test_container_serves_the_page_and_the_settings green; voice folder moved from s2pro-voices:/app/voices to data:/data/voices"
- [x] `ACC-WEB-65-SWAGGER` **Swagger explorer names the auth** - MEDIUM; the image serves /docs, /redoc and /openapi.json; the schema declares HTTPBearer for /speak and /voices and the sid cookie for the session endpoints, so an API client learns the auth from it
  - evidence: workflow wf_fd6fc77b-796: 94 unit passed, image rebuilt b287651f8ba2 tagged 0.2.0 and latest, container smoke /docs 200 text/html, /redoc 200, /openapi.json with HTTPBearer and the sid cookie scheme and /speak security; verifier independent pass (wip/swagger-docs)
  - test: docker run the image, GET /docs 200 text/html and /openapi.json with both schemes and /speak security
  - test-tags: UNIT, MANUAL
  - log: 2026-11-12T10:32:21Z @kj added
  - log: 2026-11-12T10:32:21Z @kj closed
- [x] `ACC-WEB-75-PLATFORM-PAGES` **Separate Voice rendering, Transcription and Settings pages** - HIGH; one portal shell: a sidebar with Operations (Voice rendering, Transcription) and Settings apart, each page and Settings tab at its own address; logged out shows only the login box; a 401 returns to it with a message
  - evidence: tests/functional/test_browser.py reaches every page and Settings tab by address and reload, login and 401 return; screens in wip/voice-portal-build/screens/; wf_594fe8f6-a22 verifier pass, review SHIP wf_aca86707-e16, make test 134 green, make test-functional 30 passed wf_e1e4629c-166
  - test: functional: each page reachable from the navigation; logged out sees only login
  - test-tags: FUNCTIONAL
  - log: 2026-11-17T07:13:59Z @kj added
  - log: 2026-11-17T07:55:52Z @kj built and verified locally with stub engines, wf_65bb7f94-0d7: 134 unit green, verifier browser run 23/23; deployed container still serves the old page
  - log: 2026-11-17T12:09:32Z @kj amended title "Separate Speak, Transcribe and Settings pages" -> "Separate Voice rendering, Transcription and Settings pages"; text "one app shell with navigation between Speak, Transcribe and Settings; logged out shows only the login box; a 401 returns to it with a message" -> "one portal shell: a sidebar with Operations (Voice rendering, Transcription) and Settings apart, each page and Settings tab at its own address; logged out shows only the login box; a 401 returns to it with a message"
  - log: 2026-11-17T14:13:17Z @kj closed
- [x] `ACC-WEB-76-DESIGN-SYSTEM` **Portal look of the approved mockup** - HIGH; colours and type use the extension design-system tokens; layout and shapes follow the mockup tmp/artefacts/voice-portal/voice-portal.html (sidebar, 6 px controls, 10 px cards, pill badges); light and dark themes; phone width with a bottom bar; text contrast at least 4.5:1
  - evidence: verifier compared every page with the mockup screens: layout, colours, spacing match; lowest text contrast 4.6:1; 0 px overflow at 390 px light and dark; wf_594fe8f6-a22 verifier pass, review SHIP wf_aca86707-e16, make test 134 green, make test-functional 30 passed wf_e1e4629c-166
  - test: screenshots light, dark and 390 px wide
  - test-tags: FUNCTIONAL, MANUAL
  - log: 2026-11-17T07:13:59Z @kj added
  - log: 2026-11-17T07:55:52Z @kj built and verified locally with stub engines, wf_65bb7f94-0d7: 134 unit green, verifier browser run 23/23; deployed container still serves the old page
  - log: 2026-11-17T12:09:32Z @kj amended title "Styled on the extension design system" -> "Portal look of the approved mockup"; text "colours, type, sections, buttons, inputs, badges and banners follow ~/.claude/skills/jupyterlab-extension/design-system; light and dark themes; works at phone width" -> "colours and type use the extension design-system tokens; layout and shapes follow the mockup tmp/artefacts/voice-portal/voice-portal.html (sidebar, 6 px controls, 10 px cards, pill badges); light and dark themes; phone width with a bottom bar; text contrast at least 4.5:1"
  - log: 2026-11-17T14:13:17Z @kj closed
- [x] `ACC-WEB-77-ACTION-RESULT` **Every action shows its result** - HIGH; each action shows running, done or the server's reason beside its control (a refused login in the banner above the password field); nothing fails silently
  - evidence: verifier drove every action against the stub service: running, done or the server's detail beside each control; wf_594fe8f6-a22 verifier pass, review SHIP wf_aca86707-e16, make test 134 green, make test-functional 30 passed wf_e1e4629c-166
  - test: functional: a refused save shows the server's detail text
  - test-tags: UNIT, FUNCTIONAL
  - log: 2026-11-17T07:13:59Z @kj added
  - log: 2026-11-17T07:55:52Z @kj built and verified locally with stub engines, wf_65bb7f94-0d7: 134 unit green, verifier browser run 23/23; deployed container still serves the old page
  - log: 2026-11-17T12:09:32Z @kj amended text "each button shows done or the server's reason next to it; nothing fails silently" -> "each action shows running, done or the server's reason beside its control (a refused login in the banner above the password field); nothing fails silently"
  - log: 2026-11-17T14:13:17Z @kj closed
- [x] `ACC-WEB-78-HF-CHECK` **Hugging Face token checked on save** - HIGH; Save asks Hugging Face whoami with the token; kept only when valid; the page shows the account name or the error
  - evidence: whoami unit tests (Bearer header, 10 s timeout, valid, refused, timeout, 5xx) and the functional token test green; wf_594fe8f6-a22 verifier pass, review SHIP wf_aca86707-e16, make test 134 green, make test-functional 30 passed wf_e1e4629c-166
  - test: unit: whoami stubbed valid and invalid
  - test-tags: UNIT
  - log: 2026-11-17T07:13:59Z @kj added
  - log: 2026-11-17T07:55:52Z @kj built and verified locally with stub engines, wf_65bb7f94-0d7: 134 unit green, verifier browser run 23/23; deployed container still serves the old page
  - log: 2026-11-17T14:13:18Z @kj closed
- [x] `ACC-WEB-79-TOKEN-CREATE` **API token shown once with copy** - MEDIUM; Create token shows the new token once with a copy button; existing tokens listed by name with delete
  - evidence: tests/functional/test_browser.py: create shows the token once, Copy, Bearer use on /voices, delete then 401; wf_594fe8f6-a22 verifier pass, review SHIP wf_aca86707-e16, make test 134 green, make test-functional 30 passed wf_e1e4629c-166
  - test: functional: create, copy shown, listed, delete
  - test-tags: FUNCTIONAL
  - log: 2026-11-17T07:14:00Z @kj added
  - log: 2026-11-17T07:55:52Z @kj built and verified locally with stub engines, wf_65bb7f94-0d7: 134 unit green, verifier browser run 23/23; deployed container still serves the old page
  - log: 2026-11-17T14:13:18Z @kj closed

## Authentication `AUTH`

Password login for the page, API tokens for clients, and the password supplied by environment or file secret

- log: 2026-11-10T22:41:11Z @kj category created

- [x] `ACC-AUTH-54-PASSWORD` **Password required at start** - CRITICAL; The service starts only when S2PRO_PASSWORD_FILE or S2PRO_PASSWORD holds the password; the file's first line wins with trailing whitespace stripped. With neither it exits at start with an error naming both. POST /login with the right password starts a session; a wrong one is 401.
  - evidence: make -f s2pro.mk test 2026-11-11: 90 passed in 20.16 s (tmp/workflows/auth/logs/unit.log), test_the_password_comes_from_the_environment, test_the_password_file_wins_and_only_the_first_line_counts, test_no_password_is_the_startup_error, test_an_empty_password_is_the_startup_error, test_login_sets_a_strict_httponly_cookie and test_a_wrong_or_empty_password_is_401 green; make -f s2pro.mk test-functional 2026-11-11: 26 passed in 940.63 s, EXIT=0 (tmp/workflows/auth/logs/functional-full.log), container test_a_start_without_a_password_stops_with_the_message green
  - test: start with each source and with neither; POST /login with the right and a wrong password
  - test-tags: UNIT, FUNCTIONAL
  - log: 2026-11-10T22:41:11Z @kj added
  - log: 2026-11-10T23:43:56Z @kj closed: verified
- [x] `ACC-AUTH-55-PASSFILE` **Password comes from a compose file secret** - CRITICAL; compose mounts a file secret at /run/secrets/s2pro_password and sets S2PRO_PASSWORD_FILE; the password appears in no committed file, image layer, command line or log.
  - evidence: docker compose up -d with no --env-file started leftenant-voice-tts-service from registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts:latest with the s2pro_password secret at /run/secrets/s2pro_password; /health 200; POST /login 200 and GET /session true through docker compose exec with the JSON on stdin; docker compose down left ps -a empty; make -f s2pro.mk test 90 passed (wip/compose-rename/logs/)
  - test: test ! -e service/.env; no ${ in compose.yml; grep the image history, container inspect and logs for the test password
  - test-tags: FUNCTIONAL
  - log: 2026-11-10T22:41:11Z @kj added
  - log: 2026-11-10T23:44:03Z @kj closed: verified
  - log: 2026-11-11T00:32:11Z @kj edited evidence "docker compose --env-file .env config 2026-11-11 renders service voice-tts-service with the s2pro_password secret at /run/secrets/s2pro_password and S2PRO_PASSWORD_FILE (tmp/workflows/auth/logs/compose-config.log); service/.env, service/.env.example and docker history --no-trunc of image sha256:dd3a0d393663 contain no password; the image env has no password variable and /run/secrets is absent" -> "VERSION=0.2.0 docker compose --env-file .env up -d 2026-11-11 started voice-tts-service from voice-tts:0.2.0 with the s2pro_password secret read from /home/lab/.cache/voice-tts/password.txt seeded through the README one-shot container; the container sees /run/secrets/s2pro_password as a regular file (48 bytes, mode 600), /health 200 {"status":"ok"}, POST /login 200 and GET /session {"authenticated":true} through docker compose exec with the JSON on stdin; no IsADirectoryError in the container log; docker compose down left no container; make -f s2pro.mk test 90 passed (tmp/workflows/auth-fixes/logs/compose-run.log, wip/auth-fixes/logs/unit.log)"; reason: replace the config-only evidence with the real compose start, secret mount and login
  - log: 2026-11-11T00:42:00Z @kj edited evidence "VERSION=0.2.0 docker compose --env-file .env up -d 2026-11-11 started voice-tts-service from voice-tts:0.2.0 with the s2pro_password secret read from /home/lab/.cache/voice-tts/password.txt seeded through the README one-shot container; the container sees /run/secrets/s2pro_password as a regular file (48 bytes, mode 600), /health 200 {"status":"ok"}, POST /login 200 and GET /session {"authenticated":true} through docker compose exec with the JSON on stdin; no IsADirectoryError in the container log; docker compose down left no container; make -f s2pro.mk test 90 passed (tmp/workflows/auth-fixes/logs/compose-run.log, wip/auth-fixes/logs/unit.log)" -> "VERSION=0.2.0 docker compose --env-file .env up -d 2026-11-11 started voice-tts-service from voice-tts:0.2.0 with the s2pro_password secret read from /home/lab/.cache/voice-tts/password.txt seeded through the README one-shot container; the container sees /run/secrets/s2pro_password as a regular file (48 bytes, mode 600), /health 200 {"status":"ok"}, POST /login 200 and GET /session {"authenticated":true} through docker compose exec with the JSON on stdin; no IsADirectoryError in the container log; docker compose down left no container; make -f s2pro.mk test 90 passed (wip/auth-fixes/logs/compose-run.log, wip/auth-fixes/logs/unit.log)"; reason: correct the compose-run.log path: the log is under wip/auth-fixes/logs, not tmp/workflows/auth-fixes/logs
  - log: 2026-11-11T22:21:04Z @kj edited text "compose mounts a file secret at /run/secrets/s2pro_password and sets S2PRO_PASSWORD_FILE; the password appears in no .env, image layer, command line or log." -> "compose mounts a file secret at /run/secrets/s2pro_password and sets S2PRO_PASSWORD_FILE; the password appears in no committed file, image layer, command line or log."
  - log: 2026-11-11T23:01:00Z @kj edited test "docker compose config; grep .env, image history, container inspect and logs for the test password" -> "test ! -e service/.env; no ${ in compose.yml; grep the image history, container inspect and logs for the test password"; evidence "VERSION=0.2.0 docker compose --env-file .env up -d 2026-11-11 started voice-tts-service from voice-tts:0.2.0 with the s2pro_password secret read from /home/lab/.cache/voice-tts/password.txt seeded through the README one-shot container; the container sees /run/secrets/s2pro_password as a regular file (48 bytes, mode 600), /health 200 {"status":"ok"}, POST /login 200 and GET /session {"authenticated":true} through docker compose exec with the JSON on stdin; no IsADirectoryError in the container log; docker compose down left no container; make -f s2pro.mk test 90 passed (wip/auth-fixes/logs/compose-run.log, wip/auth-fixes/logs/unit.log)" -> "docker compose up -d with no --env-file started leftenant-voice-tts-service from registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts:latest with the s2pro_password secret at /run/secrets/s2pro_password; /health 200; POST /login 200 and GET /session true through docker compose exec with the JSON on stdin; docker compose down left ps -a empty; make -f s2pro.mk test 90 passed (wip/compose-rename/logs/)"; reason: the evidence named the deleted .env start and the pre-rename image and service
- [x] `ACC-AUTH-56-SESSION` **Login session** - HIGH; A successful login sets an HttpOnly, SameSite=Strict session cookie backed by a server-side store; POST /logout clears it; sessions end when the service restarts.
  - evidence: unit test_login_sets_a_strict_httponly_cookie: sid HttpOnly SameSite=Strict path=/ max-age=43200, GET /session true; test_logout_ends_the_session_and_clears_the_cookie; 90 passed in 20.16 s (tmp/workflows/auth/logs/unit.log); functional test_the_page_starts_on_the_login_form and the container login and logout checks green in 26 passed, EXIT=0 (tmp/workflows/auth/logs/functional-full.log)
  - test: login, call a protected endpoint with the cookie, log out, call it again
  - test-tags: UNIT, FUNCTIONAL
  - log: 2026-11-10T22:41:11Z @kj added
  - log: 2026-11-10T23:44:03Z @kj closed: verified
- [x] `ACC-AUTH-57-PROTECTED` **Endpoints require credentials** - CRITICAL; Every endpoint except GET /health, POST /login, the page and its /static files requires a valid session cookie or a Bearer token; missing or invalid credentials are 401. /health stays public for the healthcheck
  - evidence: unit test_every_protected_endpoint_is_401_without_credentials (9 endpoints), test_the_voice_upload_is_401_without_credentials, test_a_forged_session_and_an_unknown_token_are_401 and test_the_public_endpoints_answer_without_credentials green in 90 passed; functional test_no_credentials_is_401 and the container test_container_serves_the_page_and_the_settings (GET /voices 401 without login, 200 with, /health public) green in 26 passed, EXIT=0 (tmp/workflows/auth/logs/functional-full.log)
  - test: call each endpoint with no credentials, a forged session and an unknown token
  - test-tags: UNIT, FUNCTIONAL
  - log: 2026-11-10T22:41:11Z @kj added
  - log: 2026-11-10T23:44:05Z @kj closed: verified
  - log: 2026-11-17T07:55:51Z @kj amended text "Every endpoint except GET /health, POST /login and the static page requires a valid session cookie or a Bearer token; missing or invalid credentials are 401. /health stays public for the healthcheck." -> "Every endpoint except GET /health, POST /login, the page and its /static files requires a valid session cookie or a Bearer token; missing or invalid credentials are 401. /health stays public for the healthcheck"
- [x] `ACC-AUTH-58-TOKENS` **API tokens live encrypted in the data volume** - HIGH; With a session, Settings creates a named token shown once, lists names with prefix and date, and revokes by name. /data/tokens.json is encrypted with an AES-GCM key derived from the password by salted scrypt; a wrong password stops the service at start.
  - evidence: unit test_a_created_token_is_shown_once_listed_and_stored_encrypted (the store bytes contain neither token, prefix nor password), test_tokens_survive_a_reload and test_a_store_written_with_one_password_does_not_load_with_another green in 90 passed (tmp/workflows/auth/logs/unit.log); functional test_api_token_round_trip and the container cold and warm starts green in 26 passed, EXIT=0 (tmp/workflows/auth/logs/functional-full.log); the store is /data/tokens.json
  - test: create a token, restart, list it; start with a wrong password and assert the refusal
  - test-tags: UNIT, FUNCTIONAL
  - log: 2026-11-10T22:41:12Z @kj added
  - log: 2026-11-10T23:44:06Z @kj closed: verified
- [x] `ACC-AUTH-59-BEARER` **Bearer tokens for the API** - CRITICAL; POST /speak, GET /voices, POST /voices and DELETE /voices/{name} accept Authorization: Bearer <token>; an unknown or revoked token is 401. Settings and token management refuse a Bearer token and need the session.
  - evidence: unit test_a_token_works_as_a_bearer, test_a_revoked_token_is_401_and_an_unknown_delete_is_404 and test_token_management_needs_the_session_not_a_bearer (/settings and /tokens 401 with Bearer) green in 90 passed (tmp/workflows/auth/logs/unit.log); functional test_a_token_speaks_and_revoking_it_refuses and test_api_token_round_trip green in 26 passed, EXIT=0 (tmp/workflows/auth/logs/functional-full.log)
  - test: curl each endpoint with a created token, again after revoke, and Settings with the token
  - test-tags: UNIT, FUNCTIONAL
  - log: 2026-11-10T22:41:12Z @kj added
  - log: 2026-11-10T23:44:09Z @kj closed: verified
- [x] `ACC-AUTH-60-WEBLOGIN` **The page logs in with the password** - HIGH; The page opens on a password form; after login it shows the Voice rendering, Transcription and Settings pages, Settings holding the Hugging Face token, API token create and delete, voices and models; a wrong password shows an error and logout returns to the form
  - evidence: functional test_page_is_served (every PAGE_IDS id including login-form, app-section and api-token-*), test_the_page_starts_on_the_login_form (form first, wrong password 401, the sections after login) and test_api_token_round_trip green; 26 passed in 940.63 s, EXIT=0 (tmp/workflows/auth/logs/functional-full.log); logout ends the session per the unit logout test
  - test: open the page without a session, log in, use each section, log out
  - test-tags: FUNCTIONAL
  - log: 2026-11-10T22:41:12Z @kj added
  - log: 2026-11-10T23:44:09Z @kj closed: verified
  - log: 2026-11-17T07:55:52Z @kj amended text "The page opens on a password form; after login it shows status, settings with token create and revoke, voices and generate; a wrong password shows an error and logout returns to the form." -> "The page opens on a password form; after login it shows the Speak, Transcribe and Settings pages, Settings holding the Hugging Face token, API token create and delete, voices and models; a wrong password shows an error and logout returns to the form"
  - log: 2026-11-17T12:09:32Z @kj amended text "The page opens on a password form; after login it shows the Speak, Transcribe and Settings pages, Settings holding the Hugging Face token, API token create and delete, voices and models; a wrong password shows an error and logout returns to the form" -> "The page opens on a password form; after login it shows the Voice rendering, Transcription and Settings pages, Settings holding the Hugging Face token, API token create and delete, voices and models; a wrong password shows an error and logout returns to the form"
- [x] `ACC-AUTH-61-TESTING` **Auth tests and no secret leakage** - MEDIUM; Unit and functional tests cover startup with no password, passfile reading, login success and failure, 401 on each protected endpoint, logout, and token create, use, list, revoke and persistence; no password or token appears in a response or log.
  - evidence: make -f s2pro.mk test 2026-11-11: 90 passed in 20.16 s (tmp/workflows/auth/logs/unit.log); make -f s2pro.mk test-functional 2026-11-11: 26 passed in 940.63 s, EXIT=0 (tmp/workflows/auth/logs/functional-full.log); grep of both logs, the goal-trackers logs and the token store found no test password, token or vtts_ value
  - test: make test and make test-functional green; grep responses and logs for the test password and token
  - test-tags: UNIT, FUNCTIONAL
  - log: 2026-11-10T22:41:12Z @kj added
  - log: 2026-11-10T23:44:09Z @kj closed: verified

## Transcription `ASR`

Speech-to-text and model cache management: the /transcribe endpoint with language and wording, the page panel, and deleting a downloaded model

- log: 2026-11-13T18:03:04Z @kj category created

- [x] `ACC-ASR-66-ENDPOINT` **Transcribe endpoint** - MEDIUM; POST /transcribe takes an audio upload (mp3, m4a, wav, flac, ogg through ffmpeg), a language (as spoken or one of the 40), the wording (verbatim or readable) and optional context terms, and returns the transcript; auth like /speak
  - evidence: wf_c18fa67c-0cb: POST /transcribe decodes mp3, m4a, wav, flac and ogg through ffmpeg, validates language, wording and context, and transcribes 2-minute windows through the Nemotron worker; 13 tests in tests/unit/test_transcribe.py; 107 unit green; verifier pass
  - test: unit: stub the transcriber, upload a wav, assert the text; 401 without auth; 422 for bad audio
  - test-tags: UNIT
  - log: 2026-11-13T18:03:04Z @kj added
  - log: 2026-11-13T18:28:21Z @kj closed
  - log: 2026-11-15T21:02:14Z @kj review round 1: a request in error with no worker running starts the background load and answers 503 Retry-After 30, as in down; patch-2, test parametrized over down and error
- [x] `ACC-ASR-67-PAGE` **Transcribe panel** - MEDIUM; the page has a transcribe panel: choose an audio file (mp3, m4a, wav), the language from as spoken plus the 40, verbatim or readable, optional context terms, submit, read the transcript; errors shown
  - evidence: wf_347ba7ab-2dc: the page has the Transcribe section (file input mp3/m4a/wav/flac/ogg, 41 language options equal to asr.LANGUAGES plus as spoken, readable/verbatim wording, context, FormData to /transcribe, transcript shown, 67.5 GB busy note); 3 tests in test_webapp.py; 117 unit green; verifier pass
  - test: unit: page contains the form; functional: upload a wav and read the text
  - test-tags: UNIT, FUNCTIONAL
  - log: 2026-11-13T18:03:04Z @kj added
  - log: 2026-11-13T18:37:31Z @kj closed
  - log: 2026-11-15T21:02:14Z @kj review round 1-2: Transcribe button enabled in ready, down and error (a press in down or error starts the load); busy text now 'Transcribing. This can take minutes.'; patch-1 and patch-5
- [x] `ACC-ASR-68-LANGUAGE` **Language in the prompt** - MEDIUM; the model has no language parameter: the prompt carries Language: as spoken (auto) or the chosen language; the list is the 40 languages with ASR support in the model card
  - evidence: the 40 ASR languages from the model card matrix in service/asr.py in card order; build_prompt matches the card byte for byte; a named language replaces only the language clause; an unknown language is 422; unit tested in wf_c18fa67c-0cb
  - test: unit: every language value builds its prompt; an unknown language is refused
  - test-tags: UNIT
  - log: 2026-11-13T18:03:04Z @kj added
  - log: 2026-11-13T18:28:21Z @kj closed
- [x] `ACC-ASR-69-RUNTIME` **Nemotron bf16 on GPU 2** - HIGH; Nemotron 3.5 Transcribe 30B runs bf16 in the single /opt/venv worker on host GPU 2 via ASR_GPU_INDEX=2; compose reserves GPUs 0 and 2; container init downloads the weights to /data/huggingface (67.5 GB)
  - evidence: E2E wf_99f566ae-33c on image 29bf480f77c5: nvidia-smi shows S2 Pro on GPU 0 (13,990 MiB) and the ASR worker on GPU 2 (64,657 MiB); init downloaded 67,515,776,086 bytes and asr became ready in 21m42s; unit 125 green
  - test: docker compose up, POST /transcribe, assert a transcript; record the run
  - test-tags: MANUAL
  - log: 2026-11-13T18:03:04Z @kj added
  - log: 2026-11-13T19:01:16Z @kj closed
  - log: 2026-11-13T21:25:54Z @kj edited text "Nemotron 3.5 Transcribe 30B runs bf16 in its own venv worker on the second visible GPU (host GPU 2); compose reserves GPUs 0 and 2; the weights download to /data/huggingface at the first transcription (67.5 GB)" -> "Nemotron 3.5 Transcribe 30B runs bf16 in the single /opt/venv worker on host GPU 2 via ASR_GPU_INDEX=2; compose reserves GPUs 0 and 2; container init downloads the weights to /data/huggingface (67.5 GB)"; evidence "wf_a41d7078-145: image 2f7d4df8335a 31.4 GB with /opt/venv-asr (Python 3.11.18, torch 2.7.1+cu128, transformers 5.23.0.dev0 at 826edb7, librosa 0.11.0); in-image import check; compose device_ids 0 and 2; /health asr available true and /openapi.json lists the routes; 117 unit green; verifier pass" -> "E2E wf_99f566ae-33c on image 29bf480f77c5: nvidia-smi shows S2 Pro on GPU 0 (13,990 MiB) and the ASR worker on GPU 2 (64,657 MiB); init downloaded 67,515,776,086 bytes and asr became ready in 21m42s; unit 125 green"
- [x] `ACC-ASR-70-MODELS-API` **List and delete models** - HIGH; GET /models lists the cached models with sizes and load state; DELETE /models/{name} unloads the resident model and removes its cache so the next use re-downloads it; session auth
  - evidence: wf_b1db3a5e-c43 plus fix wf_e691bdd0-34b: GET /models lists s2pro and nemotron with bytes and loaded; DELETE unloads under the engine lock then removes the cache and reports freed bytes; DEF-ASR-5-SYMLINK-BYTES fixed so symlinks count once; 114 unit green
  - test: unit: temp cache, delete removes the dir and reports bytes; 401 without session; 404 unknown
  - test-tags: UNIT
  - log: 2026-11-13T18:03:04Z @kj added
  - log: 2026-11-13T18:28:21Z @kj closed
  - log: 2026-11-13T18:28:24Z @kj edited evidence "wf_b1db3a5e-c43 plus fix wf_e691bdd0-34b: GET /models lists s2pro and nemotron with bytes and loaded; DELETE unloads under the engine lock then removes the cache and reports freed bytes; DEF-ASR-5 fixed so symlinks count once; 114 unit green" -> "wf_b1db3a5e-c43 plus fix wf_e691bdd0-34b: GET /models lists s2pro and nemotron with bytes and loaded; DELETE unloads under the engine lock then removes the cache and reports freed bytes; DEF-ASR-5-SYMLINK-BYTES fixed so symlinks count once; 114 unit green"
- [x] `ACC-ASR-71-MODELS-PAGE` **Delete models on the page** - MEDIUM; Settings lists the models with their sizes and load state; Delete asks for confirmation, calls the API and shows the freed space and that the next use downloads again
  - evidence: wf_347ba7ab-2dc: Settings lists the models from GET /models with size and loaded; a two-step Delete calls DELETE /models/{name}, reports the freed bytes and the re-download, and refreshes; tests assert the list and the fetch targets; 117 unit green; verifier pass
  - test: unit: page contains the list and delete control; functional: delete a fake cache entry
  - test-tags: UNIT, FUNCTIONAL
  - log: 2026-11-13T18:03:05Z @kj added
  - log: 2026-11-13T18:37:31Z @kj closed
- [x] `ACC-ASR-72-DOCS` **Transcription and model docs** - LOW; service/README.md documents the endpoint, the page panel, the language list, GPU 2 and the 67.5 GB download, and the model deletion; the OpenAPI schema covers /transcribe and /models
  - evidence: README covers POST /transcribe, the page panel, the 40 languages, GPU 2, the 67.5 GB first download and GET/DELETE /models; /openapi.json lists /transcribe, /models and /models/{name}; the page, models and image workflows each verified their section
  - test: check docs and the OpenAPI schema list the endpoints
  - test-tags: UNIT
  - log: 2026-11-13T18:03:05Z @kj added
  - log: 2026-11-13T19:01:16Z @kj closed
- [x] `ACC-ASR-73-E2E` **Recorded real-model run** - HIGH; one recorded run: the compose service with GPUs 0 and 2 transcribes an mp3 and returns text; then DELETE /models/nemotron frees the cache and the status shows it uncached
  - evidence: wf_99f566ae-33c pass: cold start downloaded both models (21m42s to ready); speak 200 MP3 3.474 s; transcribe WER 0.0; DELETE /models/nemotron freed 67,515,776,086 bytes, state down, next request 503 Retry-After 30 and started a real re-download; worker on GPU 2
  - test: manual run with the real weights, recorded under wip/
  - test-tags: MANUAL
  - log: 2026-11-13T18:03:05Z @kj added
  - log: 2026-11-13T21:25:54Z @kj closed
- [x] `ACC-ASR-74-PAGE-TOKEN` **Page token reaches the transcription download** - MEDIUM; a Hugging Face token saved on the page reaches the Nemotron download as HF_TOKEN in the worker environment, read when the worker starts; with no page token the container HF_TOKEN is used
  - evidence: owner decision 2026-11-15 on review round 1; tmp/workflows/asr-token/patch-4.diff; unit suite 129 passed; review SHIP at round 3 wf_27075147-de9
  - test: tests/unit/test_transcribe.py parametrized worker-env test: page token, container token, no token
  - test-tags: UNIT
  - log: 2026-11-15T21:02:13Z @kj added
  - log: 2026-11-15T21:02:14Z @kj closed

