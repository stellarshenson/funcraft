"""Draws the walk of a mech's armature alone, as lines: its leg bones, the
soles of its feet, its pelvis and the height of its body, from the left side and from the front, at
every frame of a gait cycle. This is where a gait of src/procession/gait.py
is judged before the models are rendered with it.

    blender -b -P src/procession/gait.py -- <chassis>     # wip/procession/skeleton-<chassis>.json
    python3 src/procession/skeleton.py <chassis>          # wip/preview/procession/skeleton-<chassis>.png (every fourth frame, side view)
                                                          # and skeleton-<chassis>.avif (all frames, side and front view)

It also prints the largest change of speed between two frames of each ankle
and of the body's height: a jump shows there as a large number.
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PREVIEW = os.path.join(ROOT, "wip", "preview", "procession")
SCALE, W, H, FLOOR = 34.0, 640, 520, 40                    # pixels per metre, tile size, the ground's row from the bottom
COLOUR = dict(thigh=(255, 190, 60), shin=(120, 220, 120), foot=(120, 170, 255), sole=(240, 240, 240))

if __name__ == "__main__":
    name = sys.argv[1]
    data = json.load(open(os.path.join(ROOT, "wip", "procession", f"skeleton-{name}.json")))
    frames = []
    for i, row in enumerate(data["frames"]):
        im = Image.new("RGB", (2 * W, H), (24, 24, 28))
        d = ImageDraw.Draw(im)
        for tile, axis in enumerate((1, 0)):               # side view: forward is on the left; front view: the mech's left is on the right
            pt = lambda v: (tile * W + W / 2 - v[axis] * SCALE, H - FLOOR - v[2] * SCALE)
            d.line([(tile * W + 20, H - FLOOR), ((tile + 1) * W - 20, H - FLOOR)], fill=(90, 90, 90))
            for side, dim in (("R", 0.55), ("L", 1.0)):    # the right leg darker
                for bone, colour in COLOUR.items():
                    a, b = row[f"{bone}.{side}"]
                    d.line([pt(a), pt(b)], fill=tuple(int(c * dim) for c in colour), width=5)
            d.line([pt(row["thigh.L"][0]), pt(row["thigh.R"][0])], fill=(230, 90, 90), width=5)
            body = row["body"]
            d.line([pt(body), pt([body[0], body[1], body[2] + 4.0])], fill=(230, 230, 230), width=5)
        d.text((10, 8), f"{name}   frame {i:02d} of {len(data['frames'])}   left side | front", fill=(255, 255, 0))
        frames.append(im)
    frames[0].save(os.path.join(PREVIEW, f"skeleton-{name}.avif"), save_all=True, append_images=frames[1:], duration=33, loop=0, quality=80)
    picked = frames[::4]
    sheet = Image.new("RGB", (W * len(picked), H))
    for k, im in enumerate(picked):
        sheet.paste(im.crop((0, 0, W, H)), (k * W, 0))
    sheet.resize((sheet.width // 3, H // 3), Image.LANCZOS).save(os.path.join(PREVIEW, f"skeleton-{name}.png"))
    t = np.array([r["foot.L"][0] + r["foot.R"][0] + [r["body"][2]] for r in data["frames"]])
    jump = np.abs(np.diff(np.vstack([t, t[:2]]), 2, axis=0)).max(0)
    print(f"SKELETON {name}: crouch {data['crouch']:.2f} m; largest change of speed between frames, in metres: "
          f"left ankle {jump[:3].round(3)}, right ankle {jump[3:6].round(3)}, body height {jump[6]:.3f}")
