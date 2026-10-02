"""Turn a folder of rendered frames into a looping GIF.

    python src/assemble.py [frames_dir] [out.gif]

Palette. 224 colours come from a median cut of the first frame. A median
cut gives colours by pixel count, so a small thing of a colour nothing else
has (a red eye lens of 100 pixels) gets none and comes out dull. Up to 32
more colours are therefore taken from the pixels of every tenth frame that
are further than FAR from their nearest palette colour.
"""
import os, sys, glob
import numpy as np
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "wip", "frames")
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "out", "02-mechanicum.gif")
W, H = 1140, 360
FAR = 40                   # on a 0-255 scale, in the colour channel that differs most
files = sorted(glob.glob(os.path.join(src, "f*.png")))
assert files, f"no frames in {src}"
frames = [Image.open(f).convert("RGB").resize((W, H), Image.LANCZOS) for f in files]
pal = frames[0].quantize(colors=224, method=Image.MEDIANCUT)
colours = np.array(pal.getpalette()[:224 * 3], np.uint8).reshape(-1, 3)
missed = []
for f in frames[::10]:
    a = np.asarray(f).reshape(-1, 3)
    near = colours[np.asarray(f.quantize(palette=pal, dither=Image.NONE)).ravel()]
    missed.append(a[np.abs(a.astype(int) - near).max(1) > FAR])
missed = np.concatenate(missed)
if len(missed):
    rare = Image.fromarray(missed.reshape(1, -1, 3)).quantize(colors=32, method=Image.MEDIANCUT)
    used = sorted(set(np.asarray(rare).ravel().tolist()))
    colours = np.concatenate([colours, np.array(rare.getpalette(), np.uint8).reshape(-1, 3)[used]])
    pal = Image.new("P", (1, 1))
    pal.putpalette(colours.ravel().tolist())
q = [f.quantize(palette=pal, dither=Image.FLOYDSTEINBERG) for f in frames]
q[0].save(out, save_all=True, append_images=q[1:], duration=50, loop=0,
          optimize=True, disposal=1)
print("wrote", out, len(files), "frames", len(colours), "colours", round(os.path.getsize(out)/1e6, 2), "MB")
