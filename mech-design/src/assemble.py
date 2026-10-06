"""Turn wip/frames/*.png into a looping animation: an animated AVIF in full
colour at 30 frames per second when the output name ends in .avif, else a
GIF of 224 colours at 50 ms per frame."""
import os, sys, glob
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "wip", "frames")
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "out", "03-banner-models.gif")
W, H = 1140, 360
QUALITY = 88               # AVIF quality, 0 to 100; at 70 with halved colour resolution, fine red and gold lines blur
FPS = 30                   # of an AVIF: the frame time of src/procession/frame.py
files = sorted(glob.glob(os.path.join(src, "f*.png")))
assert files, f"no frames in {src}"
frames = [Image.open(f).convert("RGB").resize((W, H), Image.LANCZOS) for f in files]
if out.endswith(".avif"):
    ends = [round(1000 * (k + 1) / FPS) for k in range(len(frames))]     # an AVIF frame lasts whole milliseconds: 33 or 34
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=[b - a for a, b in zip([0] + ends, ends)],
                   quality=QUALITY, speed=4, subsampling="4:4:4")
else:
    pal = frames[0].quantize(colors=224, method=Image.MEDIANCUT)
    q = [f.quantize(palette=pal, dither=Image.FLOYDSTEINBERG) for f in frames]
    q[0].save(out, save_all=True, append_images=q[1:], duration=50, loop=0,
              optimize=True, disposal=1)
print("wrote", out, len(files), "frames", round(os.path.getsize(out)/1e6, 2), "MB")
