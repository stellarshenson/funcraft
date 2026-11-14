"""Checks of a rendered loop of the muster scene (wip/frames-muster): does it close, how much does it change from
frame to frame, and where does a part of the picture change for one frame only.

    python3 src/muster/loopcheck.py [folder for close views] [folder of frames]      # prints the measures, writes wip/preview/muster-frames.png, muster-flicker.png
"""
import os, sys, glob
import numpy as np, cv2
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRAMES = os.path.join(ROOT, "wip", "frames-muster")
LUM = np.array([0.2126, 0.7152, 0.0722], np.float32)
FAR, OFTEN = 12, 20 / 360                  # a pixel flickers in a frame when it is this far from the mean of its two neighbours in time; a pixel is listed when it does so in this share of the frames
PARTS = {"left crowd, near": (0, 520, 600, 660), "left crowd, middle": (300, 470, 900, 520), "left crowd, far": (500, 452, 1100, 470),
         "entry at the left edge": (0, 560, 110, 700), "right terrace": (1900, 530, 2432, 620), "banner B1": (255, 55, 400, 428),
         "fire F1": (380, 370, 500, 460), "brazier F5": (1990, 370, 2070, 440), "fire in the gorge": (1280, 630, 1460, 760), "sky": (1100, 40, 1600, 200)}


def main(views=None, frames=FRAMES):
    files = sorted(glob.glob(os.path.join(frames, "f[0-9]*.png")))
    n = len(files)
    first = np.asarray(Image.open(files[0]).convert("RGB"), np.float32)
    open_ = not os.path.exists(os.path.join(frames, "seam-check.png"))      # a part of a loop: its last frame does not lead to its first
    if open_:
        print(f"{n} frames, not a whole loop")
    else:
        seam = np.asarray(Image.open(os.path.join(frames, "seam-check.png")).convert("RGB"), np.float32)
        print(f"{n} frames; the frame at the end of the loop against frame 0: mean difference {np.abs(seam - first).mean():.3f}, greatest {np.abs(seam - first).max():.0f} of 255")
    lum = np.stack([np.asarray(Image.open(f).convert("RGB"), np.float32) @ LUM for f in files])
    step = np.array([np.abs(lum[(i + 1) % n] - lum[i]).mean() for i in range(n)])
    print(f"change from frame to frame: {step.min():.2f} to {step.max():.2f} of 255; from the last frame to the first {step[-1]:.2f}")
    print("a part that changes for one frame only (mean; 99.9 %; a block of 12 x 12 pixels at most; a patch at most, and patches over 3 per frame), and its steady change per frame:")
    for name, (x0, y0, x1, y1) in PARTS.items():
        part = lum[:, y0:y1, x0:x1]
        ring = part if open_ else np.concatenate([part[-1:], part, part[:1]])      # the loop goes round
        j = ring[1:-1] - 0.5 * (ring[:-2] + ring[2:])                 # far from the mean of the frame before and the frame after
        block = max(cv2.blur(f, (12, 12)).max() for f in np.abs(j))
        # an outline that moves faster or slower is lighter on one side and darker on the other: that goes to nothing
        # in the mean over 9 x 9 pixels. A patch that is another figure for one frame stays
        patch = np.abs(np.stack([cv2.blur(f, (9, 9)) for f in j]))
        print(f"  {name:24s} {np.abs(j).mean():5.2f}  {np.quantile(np.abs(j)[::3], 0.999):5.1f}  {block:5.1f}  {patch.max():5.1f} {(patch > 3).sum() / 81 / len(j):6.2f}    {np.abs(ring[2:] - ring[:-2]).mean() / 2:5.2f}")
    # over the whole frame: in how many frames each pixel is far from the mean of the frame before and the frame after.
    # A flicker outside every part above is not measured there: two surfaces at one depth showed in turn at six
    # crossbars. Every region is named by the things of the list at its plate pixels
    ring = lum if open_ else np.concatenate([lum[-1:], lum, lum[:1]])
    count = np.zeros(lum.shape[1:], np.uint16)
    for i in range(1, len(ring) - 1):
        count += np.abs(ring[i] - 0.5 * (ring[i - 1] + ring[i + 1])) > FAR
    often = count >= max(2, round(OFTEN * (len(ring) - 2)))
    made = np.load(os.path.join(ROOT, "wip", "scene3d", "muster_things.npz"))
    ids, parts = [str(v) for v in made["ids"]], cv2.connectedComponents(cv2.dilate(often.astype(np.uint8), np.ones((9, 9), np.uint8)))[1]
    found = []
    for k in range(1, parts.max() + 1):
        ys, xs = np.nonzero((parts == k) & often)
        if len(ys) >= 6:
            names, numbers = np.unique(made["label"][ys, xs], return_counts=True)
            found.append((len(ys), f"columns {xs.min()}-{xs.max()}, rows {ys.min()}-{ys.max()}, in up to {count[ys, xs].max()} frames: "
                          + ", ".join(f"{ids[t - 1] if t else 'far side'} {c}" for c, t in sorted(zip(numbers, names), reverse=True)[:3])))
    print(f"flicker over the whole frame: {int(often.sum())} pixels are more than {FAR} of 255 from the mean of their neighbours in time in {max(2, round(OFTEN * (len(ring) - 2)))} "
          f"or more of {len(ring) - 2} frames; {len(found)} regions of 6 or more such pixels")
    for size, text in sorted(found, reverse=True):
        print(f"  {size:5d} px  {text}")
    Image.fromarray(np.clip(count.astype(np.float32) * 255 / max(count.max(), 1), 0, 255).astype(np.uint8)).save(os.path.join(ROOT, "wip", "preview", "muster-flicker.png"))
    print("wrote wip/preview/muster-flicker.png: the number of such frames for every pixel, white the greatest")
    picks = [0, n // 4, n // 2, 3 * n // 4]
    pages = [Image.open(files[i]).convert("RGB") for i in picks]
    page = Image.new("RGB", (pages[0].width, sum(p.height for p in pages) + 8 * 3), (0, 0, 0))
    for k, p in enumerate(pages):
        page.paste(p, (0, k * (p.height + 8)))
    page.save(os.path.join(ROOT, "wip", "preview", "muster-frames.png"))
    print("wrote wip/preview/muster-frames.png: frames", picks)
    if views and views != "-":
        for name, box, k in (("left", (0, 430, 760, 768), 2), ("right", (1780, 430, 2432, 768), 2), ("fires", (360, 330, 1140, 480), 2), ("gorge", (1240, 600, 1480, 768), 3)):
            a = np.concatenate([np.asarray(pages[i].crop(box)) for i in (0, 2)], 0)
            Image.fromarray(a).resize((a.shape[1] * k, a.shape[0] * k), Image.LANCZOS).save(os.path.join(views, f"loop-{name}.png"))
        pages[2].resize((1520, 480), Image.LANCZOS).save(os.path.join(views, "loop-full.png"))


if __name__ == "__main__":
    main(*sys.argv[1:])
