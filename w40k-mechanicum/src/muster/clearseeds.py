"""Seeds of the image model for clearing the emblems of one cloth (src/goldwork.py clear): paints the cloth's holes
with each seed and measures how far the painted velvet lies from the velvet round the holes: the difference of the
mean colour, of the spread of the light, the share of pixels brighter than the brightest 2 % round the holes, and the
share of pale pixels. Writes wip/preview/frames3d/clearseeds-<scene>-<i>.png.

    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 HF_HUB_OFFLINE=1 .venv-moge/bin/python src/muster/clearseeds.py street 0 1 2 3 4 5 6 7 8
"""
import os, sys
import numpy as np, cv2, torch
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
import goldwork as G
from diffusers import ZImageInpaintPipeline

scene, i, seeds = sys.argv[1], int(sys.argv[2]), [int(s) for s in sys.argv[3:]]
conf, cloth = G.DRAPES[sys.argv[1]], G.DRAPES[sys.argv[1]]["cloths"][int(sys.argv[2])]
plate = G.first(scene)
hole = np.any([G.ellipse(plate.shape, s[4], grow=6) for s in cloth["sigils"]], 0).astype(np.uint8)
x0, y0, x1, y1 = cloth["box"]
crop, part = plate[y0:y1, x0:x1].copy(), hole[y0:y1, x0:x1]
r, g = crop[..., 0].astype(np.float32), crop[..., 1].astype(np.float32)
velvet = (r > 1.5 * g) & (r > 20) & ~G.golden(crop)
ring = (cv2.dilate(part, np.ones((41, 41), np.uint8)) > 0) & (part == 0) & velvet
lum = lambda a: a.astype(np.float32) @ G.LUM
ref = crop[ring].astype(np.float32)
top = np.percentile(lum(ref), 98)
pipe = ZImageInpaintPipeline.from_pretrained("Tongyi-MAI/Z-Image-Turbo", torch_dtype=torch.bfloat16).to("cuda")
cells = [crop]
for seed in seeds:
    top = 64 if y0 == 0 else 0
    big = lambda a: np.pad(a, ((top, 0),) + ((0, 0),) * (a.ndim - 1), mode="reflect")
    up, size = int(os.environ.get("UP", cloth.get("up", 1))), (x1 - x0, y1 - y0 + top)
    wide = lambda a, how: cv2.resize(a, (size[0] * up, size[1] * up), interpolation=how)
    gen = np.asarray(pipe(prompt=conf["prompt"], image=Image.fromarray(wide(big(crop), cv2.INTER_CUBIC)),
                          mask_image=Image.fromarray(wide(big(part) * 255, cv2.INTER_NEAREST)), strength=1.0,
                          height=size[1] * up, width=size[0] * up, num_inference_steps=9, guidance_scale=0.0,
                          generator=torch.Generator("cuda").manual_seed(seed)).images[0])
    gen = cv2.resize(gen, size, interpolation=cv2.INTER_AREA)[top:]
    p = gen[part > 0].astype(np.float32)
    pale = ((p.max(1) - p.min(1)) < 40) & (lum(p) > 90)
    print(f"seed {seed}: mean colour off by {np.abs(p.mean(0) - ref.mean(0)).round().astype(int).tolist()}, spread of light {lum(p).std():.0f} against {lum(ref).std():.0f}, "
          f"brighter than the brightest 2 % round: {(lum(p) > top).mean():.1%}, pale: {pale.mean():.1%}", flush=True)
    a = cv2.GaussianBlur(part.astype(np.float32), (0, 0), 2)[..., None]
    cells.append((crop * (1 - a) + gen * a).astype(np.uint8))
page = np.concatenate([np.pad(c, ((0, 0), (0, 6), (0, 0))) for c in cells], 1)
Image.fromarray(page).save(os.path.join(ROOT, "wip", "preview", "frames3d", f"clearseeds-{scene}-{i}.png"))
print("first picture: before; then the seeds in the order given")
