"""Where a rendered loop flickers: the share of frames in which each pixel lies more than FAR from the mean of its two
neighbours in time (as src/muster/flicker.py), drawn over the first frame: wip/preview/<stem>-flicker.png.

    python3 src/warhound/flickmap.py <folder of frames> <stem> [x0,y0,x1,y1]
"""
import glob, os, sys
import numpy as np
from PIL import Image

LUM = np.array([0.2126, 0.7152, 0.0722], np.float32)
FAR = 12
folder, stem = sys.argv[1], sys.argv[2]
x0, y0, x1, y1 = map(int, sys.argv[3].split(",")) if len(sys.argv) > 3 else (0, 0, None, None)
files = sorted(glob.glob(os.path.join(folder, "f[0-9]*.png")))
rgb0 = np.asarray(Image.open(files[0]).convert("RGB"))[y0:y1, x0:x1]
lum = np.stack([np.asarray(Image.open(f).convert("RGB"), np.float32)[y0:y1, x0:x1] @ LUM for f in files])
share = (np.abs(lum - 0.5 * (np.roll(lum, 1, 0) + np.roll(lum, -1, 0))) > FAR).mean(0)
heat = np.clip(share / 0.2, 0, 1)[..., None]
out = (rgb0 * 0.45 * (1 - heat) + heat * np.array([255, 40, 20])).astype(np.uint8)
Image.fromarray(out).save(f"wip/preview/{stem}-flicker.png")
print("share of frames flickering: mean", round(float(share.mean()), 4), "pixels over 5.6 %:", int((share > 0.056).sum()))
