---
name: release-leftenant-voice
description: Build the leftenant-voice-tts image and release both tags to the NAS GitLab registry. Use when asked to release the leftenant-voice image, push or publish the voice TTS image, or on /release-leftenant-voice.
---

# Release leftenant-voice

Both tags, `$(cat service/VERSION)` and `latest`, of `registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts`, the private GitLab project `konrad.jelen/leftenant-voice-tts`.

Invoking this command in a turn is the owner's approval for the push in that run only. Never push from another task, and never treat an earlier run's approval as standing.

## Steps

From `leftenant_voice/` (`ROOT=$(git rev-parse --show-toplevel)`, then `cd "$ROOT/leftenant_voice"`):

1. `jupyterlab-passkey vault status` must say `state: unlocked`; the push reads `gitlab/api`. When locked, stop and tell the owner to click Unlock vault in the JupyterLab tab, then run the command again.
2. `make -f s2pro.mk test` - stop on any failure; nothing is released until the suite is green.
3. `make -f s2pro.mk docker-build`, then `make -f s2pro.mk docker-tag`; note the image id with `docker image inspect --format '{{.Id}}' registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts:$(cat service/VERSION)`.
4. GitLab project guard, with the token in a curl config file and never on argv (`printf` writes it, `shred -u` removes it): `GET https://gitlab.nas.stellars-tech.eu:8443/api/v4/projects/konrad.jelen%2Fleftenant-voice-tts` (`insecure` for the self-signed certificate); on 404 create it private with name and path `leftenant-voice-tts`.
5. `make -f s2pro.mk docker-push` pushes both tags; the target reads the vault token on stdin through a temporary `DOCKER_CONFIG` and logs out afterwards.
6. Verify: log in to a temporary `DOCKER_CONFIG` and `docker pull` both tags; each must print one digest and `Image is up to date`. Record the digest.
7. Write `docker-build.log`, `docker-push.log` and `pull-check.log` under `wip/release/logs/`, report the image id, both tags and the digest, then append a journal entry through the journal plugin.

A failed step stops the run and is reported with its command and output; the local tags stay.

## Never

- The token or the service password on argv, in a log, in the report or in a file that survives the run
- A git commit, a git tag or a `service/VERSION` bump as part of the release
- A push after any failed step, or on a turn where the owner did not invoke this command

`docker manifest inspect` needs `--insecure` against this registry (self-signed certificate); the pull check above already proves both tags.
