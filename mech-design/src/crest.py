"""The crest of the welcome page: the Machina Opus, the sign of the Adeptus
Mechanicus, painted anew by Z-Image-Turbo from a reference glyph and given
relief with MoGe-2.

The reference is references/web/machina-opus.png (its source is in
references/web/SOURCE.txt): a skull, its left half an iron machine with a
grilled eye and hoses, its right half bone, on a disc that is bone white on
the left and black on the right, in a steel cog ring. `gen` lets the model
paint the picture again from that start (ZImageImg2ImgPipeline), so the
layout of the sign stays and the paint is new; a higher strength changes
more. `relief` takes the chosen draft, cuts the medallion out of its
background and has MoGe-2 estimate its depth, for src/crest3d.py.

Runs in the environment of the sibling project w40k-mechanicum:

    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 HF_HUB_OFFLINE=1 \\
        ../w40k-mechanicum/.venv-moge/bin/python src/crest.py gen [seeds]      # wip/gen/crest_<seed>_<n>.png, wip/preview/crest.jpg
        ../w40k-mechanicum/.venv-moge/bin/python src/crest.py relief <seed>_<n>  # wip/crest/crest.png, wip/crest/crest.npz
"""
import os, sys, glob
import numpy as np
import torch
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN, OUT = os.path.join(ROOT, "wip", "gen"), os.path.join(ROOT, "wip", "crest")
SIDE = 1024
STRENGTHS = (0.45, 0.6, 0.75)
PROMPT = ("The Machina Opus, emblem of the Adeptus Mechanicus of Warhammer 40,000: one round medallion seen exactly from the "
          "front, centred, on a pure black background. A cog wheel ring of blue-grey steel with square teeth. Inside the ring "
          "a disc split down the middle: its left half bone white, its right half deep black. In the centre a skull split "
          "down the middle: its left half a black iron machine mask with a round grilled lens eye that glows red, bolts, "
          "ribbed hoses and cables; its right half a bone white human skull with a dark eye socket and teeth. Painted "
          "enamel and worn steel in bas-relief, strong light from the upper left, deep blacks, bright bone, vivid red "
          "glow, high contrast, crisp edges, sharp focus, extremely detailed. No text.")


def gen(seeds):
    from diffusers import ZImageImg2ImgPipeline
    ref = Image.open(os.path.join(ROOT, "references", "web", "machina-opus.png")).convert("RGBA")
    start = Image.new("RGB", ref.size)
    start.paste(ref, mask=ref.getchannel("A"))
    start = start.resize((SIDE, SIDE), Image.LANCZOS)
    pipe = ZImageImg2ImgPipeline.from_pretrained("Tongyi-MAI/Z-Image-Turbo", torch_dtype=torch.bfloat16).to("cuda")
    os.makedirs(GEN, exist_ok=True)
    for seed in seeds:
        for n, st in enumerate(STRENGTHS, 1):
            out = pipe(prompt=PROMPT, image=start, strength=st, width=SIDE, height=SIDE, num_inference_steps=12,
                       guidance_scale=0.0, generator=torch.Generator("cuda").manual_seed(seed)).images[0]
            out.save(os.path.join(GEN, f"crest_{seed}_{n}.png"))
            print("crest", seed, st, flush=True)
    fs = sorted(glob.glob(os.path.join(GEN, "crest_*.png")))
    sheet = Image.new("RGB", (len(STRENGTHS) * 384, -(-len(fs) // len(STRENGTHS)) * 384))
    for k, f in enumerate(fs):
        sheet.paste(Image.open(f).convert("RGB").resize((384, 384), Image.LANCZOS), ((k % len(STRENGTHS)) * 384, (k // len(STRENGTHS)) * 384))
    sheet.save(os.path.join(ROOT, "wip", "preview", "crest.jpg"), quality=90)
    print("sheet", [os.path.basename(f)[6:-4] for f in fs])


def relief(draft):
    """Cut the medallion of draft `draft` out of its background and estimate
    its relief: the height of every pixel over the medallion's own plane, as
    a share of the medallion's diameter."""
    import cv2
    from moge.model.v2 import MoGeModel
    rgb = Image.open(os.path.join(GEN, f"crest_{draft}.png")).convert("RGB")
    a = np.asarray(rgb, np.float32) / 255
    # the medallion is a circle; its black half is as dark as the background, so the circle comes from the three
    # sides the bright half and the rim give: left, top and bottom
    lit = cv2.GaussianBlur(a.max(-1), (0, 0), 2) > 0.10
    ys, xs = np.nonzero(lit)
    r = (ys.max() - ys.min()) / 2
    cy, cx = (ys.max() + ys.min()) / 2, xs.min() + r
    yy, xx = np.mgrid[:SIDE, :SIDE].astype(np.float32)
    dist = np.hypot(yy - cy, xx - cx)
    alpha = np.clip(r - 2 - dist, 0, 1)
    model = MoGeModel.from_pretrained("Ruicheng/moge-2-vitl-normal").cuda().eval()
    with torch.no_grad():
        out = model.infer(torch.from_numpy(a).permute(2, 0, 1).cuda())
    depth = out["depth"].cpu().numpy()
    on = (dist < 0.97 * r) & np.isfinite(depth)
    A = np.stack([xx[on], yy[on], np.ones(on.sum())], 1)
    plane = np.linalg.lstsq(A, depth[on], rcond=None)[0]                 # the medallion's plane, by least squares
    height = (plane[0] * xx + plane[1] * yy + plane[2]) - np.where(np.isfinite(depth), depth, 0)
    height = np.where(on, height, 0.0)
    lo, hi = np.percentile(height[on], [1, 99.5])
    height = np.clip((height - lo) / (hi - lo), 0, 1) * (dist < r)
    height = cv2.GaussianBlur(height.astype(np.float32), (0, 0), 1.5)
    os.makedirs(OUT, exist_ok=True)
    Image.fromarray(np.dstack([a, alpha]).__mul__(255).astype(np.uint8), "RGBA").save(os.path.join(OUT, "crest.png"))
    np.savez_compressed(os.path.join(OUT, "crest.npz"), height=height, centre=np.array([cx, cy]), radius=r)
    Image.fromarray((height * 255).astype(np.uint8)).save(os.path.join(ROOT, "wip", "preview", "crest-height.png"))
    print(f"RELIEF {draft}: centre {cx:.0f}, {cy:.0f}, radius {r:.0f} px; depth range over the plane {hi - lo:.4f} of MoGe-2's units")


if __name__ == "__main__":
    if sys.argv[1] == "gen":
        gen([int(s) for s in sys.argv[2:]] or [1, 2, 3, 4])
    else:
        relief(sys.argv[2])
