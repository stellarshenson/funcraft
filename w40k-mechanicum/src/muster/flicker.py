"""Whole-frame checks of a rendered loop of any scene: does it close, and where does a pixel change for one frame only.

    python3 src/muster/flicker.py <folder of frames> [x0,y0,x1,y1 of a part to count on its own]

A pixel flickers in a frame when its luminance lies more than FAR from the mean of its two neighbours in time. Prints
the count per frame over the whole picture, the regions where pixels do so in more than OFTEN of the frames, and the
same count inside the given part.
"""
import glob, os, sys
import numpy as np, cv2
from PIL import Image

LUM = np.array([0.2126, 0.7152, 0.0722], np.float32)
FAR, OFTEN = 12, 20 / 360

if __name__ == "__main__":
    folder = sys.argv[1]
    files = sorted(glob.glob(os.path.join(folder, "f[0-9]*.png")))
    n = len(files)
    lum = np.stack([np.asarray(Image.open(f).convert("RGB"), np.float32) @ LUM for f in files])
    seam = np.asarray(Image.open(os.path.join(folder, "seam-check.png")).convert("RGB"), np.float32) @ LUM
    d = np.abs(seam - lum[0])
    print(f"{n} frames; the frame after the last against the first: mean {d.mean():.3f}, greatest {d.max():.1f} of 255, {int((d > 4).sum())} px over 4")
    step = np.abs(np.roll(lum, -1, 0) - lum).mean((1, 2))
    print(f"change from frame to frame: mean {step.mean():.3f}, least {step.min():.3f}, greatest {step.max():.3f} (at frame {int(step.argmax())})")
    flick = np.abs(lum - 0.5 * (np.roll(lum, 1, 0) + np.roll(lum, -1, 0))) > FAR
    often = flick.mean(0) > OFTEN
    print(f"pixels that flicker in a frame: mean {flick.sum((1, 2)).mean():.0f}, greatest {int(flick.sum((1, 2)).max())}; pixels that do so in more than {OFTEN:.1%} of the frames: {int(often.sum())}")
    stats = cv2.connectedComponentsWithStats(cv2.dilate(often.astype(np.uint8), np.ones((25, 25), np.uint8)), connectivity=8)[2][1:]
    for s in sorted(stats, key=lambda s: -often[s[1]:s[1] + s[3], s[0]:s[0] + s[2]].sum()):
        print(f"  region columns {s[0]}-{s[0] + s[2]}, rows {s[1]}-{s[1] + s[3]}: {int(often[s[1]:s[1] + s[3], s[0]:s[0] + s[2]].sum())} px")
    for box in sys.argv[2:]:
        x0, y0, x1, y1 = (int(v) for v in box.split(","))
        part = flick[:, y0:y1, x0:x1]
        print(f"part {box}: pixels that flicker in a frame: mean {part.sum((1, 2)).mean():.1f}, greatest {int(part.sum((1, 2)).max())}; in more than {OFTEN:.1%} of the frames: {int(often[y0:y1, x0:x1].sum())}; "
              f"greatest change from frame to frame there {np.abs(np.roll(lum, -1, 0) - lum)[:, y0:y1, x0:x1].max():.1f}")
