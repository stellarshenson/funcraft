"""Turn a folder of rendered frames into a looping GIF.

    python3 assemble.py FRAMES_DIR OUT.gif [--size 1140x360] [--ms 50] [--colours 224]

Takes f*.png in name order (seam-check.png is left out), downscales with
LANCZOS, builds one median-cut palette from the first frame and dithers every
frame into it.
"""
import argparse, glob, os
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("out")
ap.add_argument("--size", default="1140x360")
ap.add_argument("--ms", type=int, default=50)
ap.add_argument("--colours", type=int, default=224)
a = ap.parse_args()

W, H = (int(v) for v in a.size.split("x"))
files = sorted(glob.glob(os.path.join(a.src, "f*.png")))
assert files, f"no frames in {a.src}"
frames = [Image.open(f).convert("RGB").resize((W, H), Image.LANCZOS) for f in files]
pal = frames[0].quantize(colors=a.colours, method=Image.MEDIANCUT)
q = [f.quantize(palette=pal, dither=Image.FLOYDSTEINBERG) for f in frames]
q[0].save(a.out, save_all=True, append_images=q[1:], duration=a.ms, loop=0, optimize=True, disposal=1)
print("wrote", a.out, len(files), "frames", round(os.path.getsize(a.out) / 1e6, 2), "MB")
