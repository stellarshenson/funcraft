"""Measures the pikes that stand on the far wall of the left terrace in the source picture: thin dark uprights that
rise from the upper edge of the wall. Their columns are given by eye from the enlarged picture (NEAR); the helper
finds for each its own column, the row of its tip, the row of the wall under it and its radius at the wall (from the
width that it covers in the picture, row by row: a pike is thinner than a pixel over most of its height), prints
them as the list PIKES of src/muster.py and writes close views for the check.

    python3 src/muster/pikes.py
"""
import os, sys
import numpy as np, cv2
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
import muster as M

NEAR = [613, 638, 666, 700, 708, 720, 826, 835.5, 842.5, 853.5, 860, 864.5, 874, 883, 895, 904]      # a short one at 888.5 is not apart from the one at 883 in the measure, and is left out
SPAN = (540, 1070)                          # the columns of the wall on which they stand


def found():
    pic = np.asarray(Image.open(M.SCENE + ".png").convert("RGB"), np.float32)
    lum = pic @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    region = np.load(M.SCENE + "_crowd.npz")["region"] == 1
    W = lum.shape[1]
    dark = cv2.morphologyEx(lum, cv2.MORPH_BLACKHAT, np.ones((1, 7), np.uint8))      # how much darker than the row beside it: a dark thing under 7 pixels wide
    beside = cv2.morphologyEx(lum, cv2.MORPH_CLOSE, np.ones((1, 9), np.uint8))      # the picture beside a dark thing under 9 pixels wide
    top = region.argmax(0)                                                # the upper edge of the part behind the crowd, by column
    # the upper edge of the wall in the picture: the first row from above at which a column turns as dark as the wall
    # and stays so for 5 rows; without what rises from it (the lower of the lines within 15 columns)
    edge = np.zeros(W, np.float32)
    for x in range(*SPAN):
        wall, sky = np.median(lum[top[x] + 4:top[x] + 10, x]), np.median(lum[top[x] - 30:top[x] - 12, max(x - 6, 0):x + 7])
        col = lum[top[x] - 20:top[x] + 8, x] < 0.5 * (wall + sky)
        k = next((i for i in range(len(col) - 5) if col[i:i + 5].all()), 20)
        edge[x] = top[x] - 20 + k
    edge[SPAN[0]:SPAN[1]] = cv2.morphologyEx(edge[SPAN[0]:SPAN[1]][None], cv2.MORPH_CLOSE, np.ones((1, 15), np.uint8))[0]
    out = []
    for near in NEAR:
        xs = np.arange(int(round(near)) - 1, int(round(near)) + 2)       # within a pixel of the column given: the next pike stands 4 pixels away
        foot = int(edge[int(round(near))])
        x = int(xs[np.argmax([dark[foot - 8:foot, c].sum() for c in xs])])      # its own column: the darkest of the three
        tip, miss = foot, 0
        for row in range(foot - 1, foot - 30, -1):                        # upwards while it is darker than the picture beside it
            miss = 0 if dark[row, x - 1:x + 2].max() >= 3 else miss + 1
            if miss > 1:
                break
            if miss == 0:
                tip = row
        mids = [(row, x - 3 + float((np.arange(7) * dark[row, x - 3:x + 4]).sum() / max(dark[row, x - 3:x + 4].sum(), 1e-6))) for row in range(tip, foot)]
        lean = float(np.clip(np.polyfit([m[0] for m in mids], [m[1] for m in mids], 1)[0], -0.25, 0.25)) if foot - tip >= 5 else 0.0
        at = float(np.mean([m[1] for m in mids[-3:]]))
        # the width it covers in each row: how far each pixel lies from the picture beside it towards the dark of the
        # wall, summed over 7 columns. A straight taper from a quarter of its radius at the tip covers as much
        wall = np.median(np.sort(lum[foot + 3:foot + 8, x - 3:x + 4].ravel())[:12])
        cover = []
        for row in range(tip, foot):
            c = int(round(at - (foot + 3 - row) * lean))
            cover.append(float(np.clip((beside[row, c - 3:c + 4] - lum[row, c - 3:c + 4]) / np.maximum(beside[row, c - 3:c + 4] - wall, 15), 0, 1).sum()))
        r = np.mean(cover) / 1.25 if len(cover) >= 4 else 0.6            # a pike of under 4 rows: as the thin ones
        out.append((round(at, 1), tip, foot + 3, round(float(np.clip(r, 0.35, 1.6)), 2), round(lean, 2)))      # columns count the middles of the pixels
    return pic, edge, out


if __name__ == "__main__":
    pic, edge, pikes = found()
    print(f"{len(pikes)} pikes: (column of its foot, row of its tip, row of its foot in the wall, radius at the wall, columns it leans to the right per row down)")
    print("PIKES = [" + ", ".join(str(p) for p in pikes) + "]")
    for name, (x0, x1) in {"a": (590, 790), "b": (780, 980)}.items():
        Z, y0, y1 = 10, 420, 462
        a = Image.fromarray(pic[y0:y1, x0:x1].astype(np.uint8)).resize(((x1 - x0) * Z, (y1 - y0) * Z), Image.NEAREST)
        b = a.copy()
        d = ImageDraw.Draw(b)
        for x, tip, foot, r, lean in pikes:
            if x0 <= x < x1:
                d.polygon([((x + 0.5 - (foot - tip) * lean - x0) * Z, (tip - y0) * Z), ((x + 0.5 - r - x0) * Z, (foot - y0) * Z), ((x + 0.5 + r - x0) * Z, (foot - y0) * Z)], outline=(0, 255, 255))
        for x in range(max(x0, SPAN[0]), min(x1, SPAN[1])):
            d.point(((x - x0 + 0.5) * Z, (edge[x] - y0) * Z), fill=(0, 255, 0))
        page = Image.new("RGB", (a.width, 2 * a.height + 6))
        page.paste(a, (0, 0))
        page.paste(b, (0, a.height + 6))
        page.save(os.path.join(ROOT, "wip", "preview", "frames3d", f"pikes-{name}.png"))
        print(f"wrote wip/preview/frames3d/pikes-{name}.png", page.size)
