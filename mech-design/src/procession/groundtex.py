"""The surface of the moving ground of the procession scene: a pavement
seen from straight above, generated with Z-Image-Turbo as the textures of
w40k-mechanicum are (src/procession/gen.py), and the maps the ground
material reads.

A draft is 2048 x 512 pixels. `maps` cuts a band of rows out of it: the
piece, which stands for LENGTH = 7.5 m along the way and about 43 m across.
The scene lays the piece mirrored in both directions (piece, mirror image,
piece, ...), so no seam shows and the pattern repeats every 15 m along the
way: the ground's travel per loop.

    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 HF_HUB_OFFLINE=1 \\
        ../w40k-mechanicum/.venv-moge/bin/python src/procession/groundtex.py gen all 1 2 3 4   # wip/gen/ground_<name>_<seed>.png
    ../w40k-mechanicum/.venv-moge/bin/python src/procession/groundtex.py sheet                 # wip/preview/procession/ground-<name>.jpg
    ../w40k-mechanicum/.venv-moge/bin/python src/procession/groundtex.py maps <name> <seed> <row0> <row1>   # wip/procession/ground/

maps.png: red = brass (metal, smooth, raised), green = glow (light from
below), blue = height (dark joints low).
"""
import os, sys, glob, json
import numpy as np
from PIL import Image, ImageFilter
from gen import G, ROOT, PREVIEW

LENGTH = 7.5                       # metres along the way that one piece stands for: the ground's travel per gait cycle (frame.STEP)
OUT = os.path.join(ROOT, "wip", "procession", "ground")

VIEW = ("Flat top-down orthographic photograph looking straight down at a floor, evenly lit, no perspective, no "
        "shadows, no horizon, no objects standing on it, no people, no text. The floor fills the whole frame. ")
STYLE = (" Grimdark gothic Warhammer 40,000 Adeptus Mechanicus, centuries old: worn, cracked, soot and oil in "
         "every joint, wet patches, extremely detailed, sharp focus")
GROUNDS = {
    "basalt": "The pavement of a processional way: large black basalt flagstones in a regular grid with deep "
              "joints, crossed by wide bands of tarnished brass inlaid with a pattern of cog teeth, a row of large "
              "round brass medallions each showing a cog wheel with a skull, narrow iron grates between the slabs "
              "with red furnace glow beneath, riveted iron cable channels.",
    "iron": "The deck of a forge-temple: heavy riveted plates of blackened iron in a regular grid, brass cog "
            "wheels inlaid flush into the plates, long iron grates with orange-red molten glow beneath them, "
            "embedded rails of worn bright steel, cable ducts under iron covers, brass borders with a cog-tooth "
            "pattern.",
    "marble": "The floor of a cathedral plaza of Holy Terra: slabs of black and dark oxblood red marble in a "
              "regular grid, inlaid with fine gold lines, gold cog wheels, gold skulls in laurel wreaths and gold "
              "fleurs-de-lys, wide gold border bands with a cog-tooth pattern, small iron grates with red glow "
              "beneath.",
}
for name, what in GROUNDS.items():
    G.JOBS[f"ground_{name}"] = (2048, 512, VIEW + what + STYLE)


def sheet():
    os.makedirs(PREVIEW, exist_ok=True)
    for name in GROUNDS:
        fs = sorted(glob.glob(os.path.join(G.GEN, f"ground_{name}_*.png")))
        if not fs:
            continue
        out = Image.new("RGB", (1520, 380 * len(fs)))
        for k, f in enumerate(fs):
            out.paste(Image.open(f).convert("RGB").resize((1520, 380), Image.LANCZOS), (0, 380 * k))
        out.save(os.path.join(PREVIEW, f"ground-{name}.jpg"), quality=88)
        print("sheet", name, len(fs))


def maps(name, seed, row0, row1):
    """Cut the rows row0..row1 out of a draft as the piece that stands for
    LENGTH metres along the way, and write its maps. Choose both rows on the
    centre line of a band, so that the mirror image continues the band."""
    im = Image.open(os.path.join(G.GEN, f"ground_{name}_{seed}.png")).convert("RGB").crop((0, row0, 2048, row1))
    a = np.asarray(im).astype(np.float32) / 255
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    brass = np.asarray(G.gold_mask(im)).astype(np.float32) / 255
    glow = np.clip((r - 0.55) / 0.25, 0, 1) * np.clip((r - 1.6 * b - 0.15) / 0.2, 0, 1) * np.clip((0.75 * r - g) / 0.1 + 1, 0, 1)
    glow = np.asarray(Image.fromarray((glow * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255
    brass = brass * (1 - glow)
    lum = 0.3 * r + 0.55 * g + 0.15 * b
    wide = np.asarray(Image.fromarray((lum * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(24))).astype(np.float32) / 255
    height = np.clip(0.5 + 1.6 * (lum - wide) + 0.25 * brass, 0, 1)       # local: joints low, inlays high
    os.makedirs(OUT, exist_ok=True)
    im.save(os.path.join(OUT, "colour.png"))
    Image.fromarray((np.stack([brass, glow, height], -1) * 255).astype(np.uint8)).save(os.path.join(OUT, "maps.png"))
    width = 2048 * LENGTH / (row1 - row0)
    json.dump(dict(draft=f"ground_{name}_{seed}", rows=[row0, row1], width=width, length=LENGTH), open(os.path.join(OUT, "meta.json"), "w"))
    print(f"MAPS {name} {seed}: piece {width:.1f} m across, {LENGTH} m along; brass {brass.mean() * 100:.1f} %, glow {glow.mean() * 100:.2f} %")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "gen":
        for n in (GROUNDS if sys.argv[2] == "all" else sys.argv[2].split(",")):
            G.generate(f"ground_{n}", tuple(int(s) for s in sys.argv[3:]) or (1, 2, 3, 4))
    elif cmd == "sheet":
        sheet()
    elif cmd == "maps":
        maps(sys.argv[2], *(int(v) for v in sys.argv[3:6]))
