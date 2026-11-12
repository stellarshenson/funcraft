"""Write the sidecar note and the INDEX.md row of the NAS copy of Fish Audio Drama 3.

Run only after `make -f fish.mk nas` has compared every file (wip/fish/nas.verified exists).

Usage: python3 src/fish/nas_sidecar.py
"""
from pathlib import Path

MODELS = Path("/mnt/nas-shared/models")
FOLDER = "fishaudio--drama-3"
REVISION = "78e5ab79e49aa9a25abe8799eff2c4d73a1c3216"
CODE_COMMIT = "0f8a12e8a651062fdee9c33a894bdccd3a8513f1"
LICENCE = (
    "Fish Audio Community License v1.0; private non-commercial use permitted, commercial use below USD 500,000 annual revenue; "
    "no speech imitating an identifiable person without consent. https://huggingface.co/fishaudio/drama-3/blob/main/LICENSE"
)


def main() -> None:
    """Write `<folder>.md` and insert the row into INDEX.md in folder order."""
    if not Path("wip/fish/nas.verified").exists():
        raise SystemExit("wip/fish/nas.verified is missing: run `make -f fish.mk nas` first")
    files = sorted((p for p in (MODELS / FOLDER).rglob("*") if p.is_file() and ".cache" not in p.parts), key=lambda p: p.name)
    total = sum(p.stat().st_size for p in files)
    listing = "\n".join(f"  - {p.relative_to(MODELS / FOLDER)} · {p.stat().st_size:,} B" for p in files)
    (MODELS / f"{FOLDER}.md").write_text(f"""# fishaudio/drama-3

- source: https://huggingface.co/fishaudio/drama-3
- revision: {REVISION} (2026-10-13)
- code: https://github.com/fishaudio/fish-speech at commit {CODE_COMMIT}
- copied: 2026-11-06 from the local Hugging Face cache
- licence: {LICENCE}
- size: {len(files)} files · {total:,} bytes ({total / 1e9:.2f} GB)
- verification: every copied file is byte-identical to the cache file (cmp)
- used for: multi-speaker and voice-cloning text-to-speech with sound tags, 44.1 kHz output, on the RTX PRO 6000 (leftenant_voice project, trial beside Ming)
- run command: in the funcraft project, `cd leftenant_voice && make -f fish.mk install && make -f fish.mk speak VOICE=<name> FILE=<text> OUT=<wav>`; the code reads the weights directory as `--checkpoint-path`
- contents:
{listing}
""")
    index = MODELS / "INDEX.md"
    row = f"| {FOLDER} | {len(files)} | {total / 1e9:.2f} GB | {LICENCE} | 2026-11-06 |"
    lines = [l for l in index.read_text().splitlines() if not l.startswith(f"| {FOLDER} |")]
    rows = [i for i, l in enumerate(lines) if l.startswith("| ") and not l.startswith(("| Folder", "| ---"))]
    after = next((i for i in rows if lines[i].split("|")[1].strip().lower() > FOLDER.lower()), rows[-1] + 1)
    lines.insert(after, row)
    index.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
