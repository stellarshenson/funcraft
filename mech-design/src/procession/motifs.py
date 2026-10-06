"""Ornament motifs for the mechs' armour, generated with Z-Image-Turbo as
height maps: grey pictures in which white is raised and black is the flat
ground, the form sculptors call an alpha. src/procession/ornament.py lays
them on the armour plates as relief and gold.

    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 HF_HUB_OFFLINE=1 \\
        ../w40k-mechanicum/.venv-moge/bin/python src/procession/motifs.py gen all 1 2     # wip/gen/motif_<name>_<seed>.png
    ../w40k-mechanicum/.venv-moge/bin/python src/procession/motifs.py sheet               # wip/preview/procession/motifs.jpg
"""
import os, sys, glob
from PIL import Image
from gen import G, PREVIEW

ALPHA = ("Grayscale height map for sculpting, a ZBrush alpha: pure black flat background, the relief in shades of "
         "grey, white is the highest. Bas-relief seen exactly from the front, no perspective, no lighting, no "
         "shadows, no colour, no text, no letters. Crisp, deep, finely chiselled gothic detail in the style of "
         "Warhammer 40,000 Adeptus Mechanicus ornament. ")
ONE = "One single emblem, centred, complete, with a wide black margin all round: "
EMBLEMS = {
    "cogskull": "a cog wheel with twelve square teeth; inside it a human skull seen from the front, the left half "
                "bone, the right half machine with a round lens eye and cables.",
    "aquila": "a double-headed imperial eagle with spread wings, symmetric, each feather chiselled, a small skull "
              "on its breast.",
    "laurelskull": "a human skull seen from the front inside a laurel wreath, a small cog wheel behind the skull.",
    "fleur": "a gothic fleur-de-lys with a small skull at its knot, finely engraved.",
    "wingedskull": "a human skull seen from the front with two spread angel wings, symmetric.",
    "cogaxe": "a cog-toothed axe of the tech-priests crossed with a staff topped by a cog wheel, a skull where they "
              "cross.",
    "chalice": "a gothic chalice with flames rising from it, a cog wheel halo behind it.",
    "hourglass": "a winged hourglass with a skull above it, symmetric.",
    "candle": "three dripping candles on a skull, symmetric.",
    "seal": "a round wax purity seal stamped with a skull in a cog wheel, two long parchment ribbons hanging down "
            "from it covered in fine horizontal lines of script.",
}
TILES = {
    "filigree": "Seamless tileable pattern that fills the whole picture edge to edge: dense gothic filigree "
                "scrollwork of acanthus leaves and thin vines, with small cog wheels and tiny skulls woven in.",
    "circuit": "Seamless tileable pattern that fills the whole picture edge to edge: sacred circuit traces like "
               "engraved wiring, straight lines with right-angle bends ending in small rings, small cog wheels "
               "and skulls among them.",
    "scales": "Seamless tileable pattern that fills the whole picture edge to edge: overlapping engraved feather "
              "scales in neat rows, each with a fine central vein.",
    "damask": "Seamless tileable pattern that fills the whole picture edge to edge: a gothic damask of pointed "
              "quatrefoils in a diamond lattice, a small skull in every second quatrefoil, a cog wheel in the others.",
}
for n, what in EMBLEMS.items():
    G.JOBS[f"motif_{n}"] = (768, 768, ALPHA + ONE + what)
for n, what in TILES.items():
    G.JOBS[f"motif_{n}"] = (768, 768, ALPHA + what)


def sheet():
    fs = sorted(glob.glob(os.path.join(G.GEN, "motif_*.png")))
    cols = 6
    out = Image.new("RGB", (cols * 256, -(-len(fs) // cols) * 256))
    for k, f in enumerate(fs):
        out.paste(Image.open(f).convert("RGB").resize((256, 256), Image.LANCZOS), ((k % cols) * 256, (k // cols) * 256))
    os.makedirs(PREVIEW, exist_ok=True)
    out.save(os.path.join(PREVIEW, "motifs.jpg"), quality=90)
    print("sheet", [os.path.basename(f)[6:-4] for f in fs])


if __name__ == "__main__":
    if sys.argv[1] == "gen":
        for n in (list(EMBLEMS) + list(TILES) if sys.argv[2] == "all" else sys.argv[2].split(",")):
            G.generate(f"motif_{n}", tuple(int(s) for s in sys.argv[3:]) or (1, 2))
    else:
        sheet()
