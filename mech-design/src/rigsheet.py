"""Combine the pose-test renders of each chassis into one strip."""
import os, sys
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "wip", "preview", "rig")
for name in sys.argv[1:] or ["madcat", "atlas", "battlemaster"]:
    keys = [f"{p}-{v}" for v in ("side", "front34") for p in ("rest", "stride", "crouch")]
    ims = [Image.open(os.path.join(D, f"{name}-{k}.png")).convert("RGB") for k in keys
           if os.path.exists(os.path.join(D, f"{name}-{k}.png"))]
    w, h = 400, 500
    out = Image.new("RGB", (w * len(ims), h))
    for i, im in enumerate(ims):
        out.paste(im.resize((w, h), Image.LANCZOS), (i * w, 0))
    out.save(os.path.join(D, f"{name}-poses.png"))
    print("poses", name, out.size)
