"""Turn wip/frames/*.png into a looping GIF."""
import os, sys, glob
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "wip", "frames")
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "out", "03-banner-models.gif")
W, H = 1140, 360
files = sorted(glob.glob(os.path.join(src, "f*.png")))
assert files, f"no frames in {src}"
frames = [Image.open(f).convert("RGB").resize((W, H), Image.LANCZOS) for f in files]
pal = frames[0].quantize(colors=224, method=Image.MEDIANCUT)
q = [f.quantize(palette=pal, dither=Image.FLOYDSTEINBERG) for f in frames]
q[0].save(out, save_all=True, append_images=q[1:], duration=50, loop=0,
          optimize=True, disposal=1)
print("wrote", out, len(files), "frames", round(os.path.getsize(out)/1e6, 2), "MB")
