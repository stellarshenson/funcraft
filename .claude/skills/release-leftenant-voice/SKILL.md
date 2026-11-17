---
name: release-leftenant-voice
description: Build the leftenant-voice-tts image and release the `latest` tag to the NAS GitLab registry, which keeps no other tag. Use when asked to release the leftenant-voice image, push or publish the voice TTS image, or on /release-leftenant-voice.
---

# Release leftenant-voice

The `latest` tag only of `registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts`, the private GitLab project `konrad.jelen/leftenant-voice-tts`. The registry repository keeps no other tag.

Invoking this command in a turn is the owner's approval for the push in that run only. Never push from another task, and never treat an earlier run's approval as standing.

## Steps

From `leftenant_voice/` (`ROOT=$(git rev-parse --show-toplevel)`, then `cd "$ROOT/leftenant_voice"`):

1. `jupyterlab-passkey vault status` must say `state: unlocked`; the push reads `gitlab/api`. When locked, stop and tell the owner to click Unlock vault in the JupyterLab tab, then run the command again.
2. `make -f s2pro.mk test` - stop on any failure; nothing is released until the suite is green.
3. `make -f s2pro.mk docker-build`, then `make -f s2pro.mk docker-tag`; note the image id of the `latest` tag with `docker image inspect --format '{{.Id}}' registry.nas.stellars-tech.eu:8443/konrad.jelen/leftenant-voice-tts:latest`.
4. GitLab project guard, with the token in a curl config file and never on argv (`printf` writes it, `shred -u` removes it): `GET https://gitlab.nas.stellars-tech.eu:8443/api/v4/projects/konrad.jelen%2Fleftenant-voice-tts` (`insecure` for the self-signed certificate); on 404 create it private with name and path `leftenant-voice-tts`.
5. `make -f s2pro.mk docker-push` pushes `latest`; the target reads the vault token on stdin through a temporary `DOCKER_CONFIG` and logs out afterwards.
6. `make -f s2pro.mk docker-prune` deletes every other tag through the GitLab API and prints one line per deleted tag with its HTTP code. Deleting a tag can remove other tags that share its manifest, so it runs after the push and the pull check follows it.
7. Verify: log in to a temporary `DOCKER_CONFIG` and `docker pull` `latest`; it must print one digest and `Image is up to date`. Record the digest. List the remaining tags through the same GitLab API (`GET .../registry/repositories/<id>/tags`, the token in the curl config); only `latest` may remain. If `latest` is gone after the prune, run `docker-push` again.
8. Write `docker-build.log`, `docker-push.log`, `docker-prune.log` and `pull-check.log` under `wip/release/logs/`, report the image id, the tag and the digest, then append a journal entry through the journal plugin.

A failed step stops the run and is reported with its command and output; the local tags stay.

## Never

- The token or the service password on argv, in a log, in the report or in a file that survives the run
- A git commit, a git tag or a `service/VERSION` bump as part of the release
- A push after any failed step, or on a turn where the owner did not invoke this command

`docker manifest inspect` needs `--insecure` against this registry (self-signed certificate); the pull check above already proves `latest`.
