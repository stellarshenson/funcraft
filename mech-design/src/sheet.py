"""Combine the look-development stills of each chassis into one strip."""
import os, sys
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "wip", "preview", "lookdev")
VIEWS = ["front34", "front", "side", "rear34", "head"]
names = sys.argv[1:] or ["madcat", "atlas", "battlemaster"]
for name in names:
    ims = [Image.open(os.path.join(D, f"{name}-{v}.png")).convert("RGB") for v in VIEWS
           if os.path.exists(os.path.join(D, f"{name}-{v}.png"))]
    w, h = 480, 600
    out = Image.new("RGB", (w * len(ims), h))
    for i, im in enumerate(ims):
        out.paste(im.resize((w, h), Image.LANCZOS), (i * w, 0))
    out.save(os.path.join(D, f"{name}-sheet.png"))
    print("sheet", name, out.size)
