<!-- @import /home/lab/workspace/.claude/CLAUDE.md -->

# Project-Specific Configuration

This file imports workspace-level configuration from `/home/lab/workspace/.claude/CLAUDE.md`.
All workspace rules apply. Project-specific rules below strengthen or extend them.

The workspace `/home/lab/workspace/.claude/` directory contains additional instruction files
(MERMAID.md, NOTEBOOK.md, DATASCIENCE.md, GIT.md, and others) referenced by CLAUDE.md.
Consult workspace CLAUDE.md and the .claude directory to discover all applicable standards.

## Mandatory Bans (Reinforced)

The following workspace rules are STRICTLY ENFORCED for this project:

- **No automatic git tags** - only create tags when user explicitly requests
- **No automatic version changes** - only modify version in package.json/pyproject.toml/etc. when user explicitly requests
- **No automatic publishing** - never run `make publish`, `npm publish`, `twine upload`, or similar without explicit user request
- **No manual package installs if Makefile exists** - use `make install` or equivalent Makefile targets, not direct `pip install`/`uv install`/`npm install`
- **No automatic git commits or pushes** - only when user explicitly requests

## Project Context

`funcraft` contains two animation projects: `mech-design` builds walking-machine banners and a welcome page; `w40k-mechanicum` builds machine-cathedral banners, a 366-day calendar and a sermon page. Python scripts and Makefiles generate the scenes. Blender 4.5 renders the 3D work with Cycles on the GPU; Pillow, NumPy and SciPy support the image and animation pipelines. The project READMEs and design documents describe their current outputs and build commands.

Source and documents are tracked in Git. Local meshes, generated assets, frames and finished media live in each project's `in/`, `resources/`, `wip/` and `out/` folders. Each animation must close its loop; the scene scripts render an extra frame at phase 1.0 for comparison with phase 0.0. Check the project design document and the relevant skill in `.claude/skills/` before changing a scene or page.

## Journal Rules (Project-Specific)

- **APPEND ONLY**: New journal entries MUST be appended at the end of the file, never inserted between existing entries
- Entries maintain strict chronological order by position - the last entry in the file is always the most recent work
- Never reorder, move, or insert entries out of sequence
- The Stellars **journal plugin** is the canonical tool for this file: create via `/journal:create`, append via `/journal:update`, archive via `/journal:archive`. The `journal:journal` skill auto-triggers on any mention of "journal" and runs `journal-tools check` after every write
- Direct edits to `JOURNAL.md` are a last resort - prefer the plugin so modus secundis format, continuous numbering and append-only order are enforced automatically

## Strengthened Rules

- Use each project's Makefile targets for builds and follow its README for required inputs and tools
- Keep generated meshes, textures, frames and deliverables in the documented local folders; do not add them to Git
- Inspect a scene's test frame and loop seam before a full render, then verify the finished animation against the design document
- Set `CUDA_VISIBLE_DEVICES` before GPU work, as required by the workspace instructions
- Read `.claude/RECOVERY-STATE.md` before resuming an interrupted render or scene change
