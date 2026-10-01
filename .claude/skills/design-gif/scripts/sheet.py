"""Stack one frame of each GIF or PNG at GIF size into a single PNG, to look
at before sending.

    python3 sheet.py A.gif [B.gif | C.png ...] -o sheet.png [--frame N]
                     [--crop X0 Y0 X1 Y1] [--zoom 2] [--size 1140x360]

GIFs give frame N; PNGs (full-size renders) are downscaled to --size first.
--crop takes GIF-size coordinates.
"""
import argparse
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("files", nargs="+")
ap.add_argument("-o", "--out", required=True)
ap.add_argument("--frame", type=int, default=0)
ap.add_argument("--crop", type=int, nargs=4)
ap.add_argument("--zoom", type=float, default=1.0)
ap.add_argument("--size", default="1140x360")
a = ap.parse_args()

W, H = (int(v) for v in a.size.split("x"))
tiles = []
for f in a.files:
    im = Image.open(f)
    if getattr(im, "n_frames", 1) > 1:
        im.seek(min(a.frame, im.n_frames - 1))
    im = im.convert("RGB")
    if im.size != (W, H):
        im = im.resize((W, H), Image.LANCZOS)
    if a.crop:
        im = im.crop(tuple(a.crop))
    if a.zoom != 1.0:
        im = im.resize((round(im.width * a.zoom), round(im.height * a.zoom)), Image.LANCZOS)
    tiles.append(im)

gap = 4
sheet = Image.new("RGB", (max(t.width for t in tiles), sum(t.height for t in tiles) + gap * (len(tiles) - 1)), "white")
y = 0
for t in tiles:
    sheet.paste(t, (0, y))
    y += t.height + gap
sheet.save(a.out)
print("wrote", a.out, sheet.size)
