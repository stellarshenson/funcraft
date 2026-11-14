"""Close views of named parts of the muster scene in several renders, at four places of the camera.

    python3 src/muster/compare.py <prefix of the pictures> <name>=<folder of frames> [<name>=<folder> ...]

Writes one picture per part: a column per frame, a row per render.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

FRAMES = (0, 30, 60, 90)                       # a quarter of a camera cycle apart
PARTS = {                                      # name: (box on the plate, enlargement)
    "brazier": ((1950, 380, 2110, 545), 3),
    "masts-right": ((2130, 60, 2432, 610), 1),
    "feet-right": ((2130, 480, 2432, 610), 2),
    "mast-left": ((220, 0, 440, 110), 2),
    "foot-left": ((320, 470, 440, 610), 3),
    "banners-right": ((1800, 130, 2200, 440), 1),
    "banners-left": ((520, 110, 880, 470), 1),
    "beside-brazier": ((1920, 340, 2130, 450), 2),
    "taken-out-right": ((2160, 230, 2432, 420), 1),
    "taken-out-left": ((220, 330, 320, 450), 3),
}


def sheet(renders, box, zoom):
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    w, h = (box[2] - box[0]) * zoom, (box[3] - box[1]) * zoom
    out = Image.new("RGB", (len(FRAMES) * (w + 6) + 6, len(renders) * (h + 26) + 6), (24, 24, 24))
    draw = ImageDraw.Draw(out)
    for row, (name, folder) in enumerate(renders):
        for col, frame in enumerate(FRAMES):
            cut = Image.open(os.path.join(folder, f"f{frame:03d}.png")).convert("RGB").crop(box).resize((w, h), Image.LANCZOS)
            x, y = 6 + col * (w + 6), 6 + row * (h + 26)
            draw.text((x, y), f"{name}, frame {frame}", (230, 230, 230), font)
            out.paste(cut, (x, y + 20))
    return out


if __name__ == "__main__":
    prefix, renders = sys.argv[1], [a.split("=", 1) for a in sys.argv[2:]]
    for part, (box, zoom) in PARTS.items():
        path = f"{prefix}-{part}.png"
        sheet(renders, box, zoom).save(path)
        print("wrote", path)
