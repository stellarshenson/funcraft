"""A plate with its moving figures removed, for the actor rigs (src/actors.py).

The priests and the things they carry (masks wip/scene3d/<name>_seg.npz, grown
by HOLE px to take their rim light too) are painted over by Z-Image-Turbo's
inpainting pipeline from a prompt describing the empty scene. MoGe-2 then
measures the clean plate; its depth, scaled to the original on the pixels
both share, replaces the original inside the hole, pushed behind the back
of every actor (the painted scene may put a pillar where a priest stands);
the points are rebuilt with the original intrinsics so the backdrop lines
up with the actors. Writes wip/scene3d/<name>_clean.png, _clean.npz,
_clean_bg.png.

    CUDA_VISIBLE_DEVICES=1 .venv-moge/bin/python src/cleanplate.py <name> <seed>     # paint, then depth
    CUDA_VISIBLE_DEVICES=1 .venv-moge/bin/python src/cleanplate.py <name> 1 2 3      # drafts in wip/gen/
    CUDA_VISIBLE_DEVICES=1 .venv-moge/bin/python src/cleanplate.py <name> depth      # depth again, same paint
"""
import os, sys
import numpy as np, cv2, torch
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import motion as M

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOLE = 12
FILL = 25                  # as in src/img2geometry.py
EMPTY = {
    "foundry": "Empty interior of a gothic forge temple, nobody present. Bare dark flagstone and iron floor "
               "with rails and scattered slag, carved black iron wall panels, crimson banners with gold cog emblems, "
               "drifting smoke, dim warm light, dark, highly detailed, photograph",
    "choir": "Empty gothic cathedral nave, nobody present. Polished dark stone floor tiles, carved stone pillars, "
             "wooden choir stalls, crimson and gold processional banners on poles, stained glass windows, candles, "
             "incense smoke, dim warm candlelight, dark, highly detailed, photograph",
}


def hole_of(name):
    """The actors' masks together, grown by HOLE px."""
    seg = np.load(os.path.join(ROOT, "wip", "scene3d", name + "_seg.npz"))
    hole = None
    for el in M.MAPS[name]:
        if el["kind"] != "stream":                                    # streams stay in the plate
            m = seg[el["id"]].astype(np.uint8)
            hole = m if hole is None else hole | m
    k = 2 * HOLE + 1
    return cv2.dilate(hole, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))


def paint(name, seed, draft):
    from diffusers import ZImageInpaintPipeline
    stem = os.path.join(ROOT, "wip", "scene3d", name)
    plate = Image.open(stem + ".png").convert("RGB")
    W, H = plate.size
    hole = hole_of(name)
    pipe = ZImageInpaintPipeline.from_pretrained("Tongyi-MAI/Z-Image-Turbo", torch_dtype=torch.bfloat16).to("cuda")
    gen = pipe(prompt=EMPTY[name], image=plate, mask_image=Image.fromarray(hole * 255), strength=1.0,
               height=H, width=W, num_inference_steps=9, guidance_scale=0.0,
               generator=torch.Generator("cuda").manual_seed(seed)).images[0]
    a = cv2.GaussianBlur(hole.astype(np.float32), (0, 0), 3)[..., None]
    clean = (np.asarray(plate, np.float32) * (1 - a) + np.asarray(gen, np.float32) * a).astype(np.uint8)
    if draft:
        Image.fromarray(clean).save(os.path.join(ROOT, "wip", "gen", f"clean_{name}_s{seed}.png"))
        return
    Image.fromarray(clean).save(stem + "_clean.png")
    del pipe
    torch.cuda.empty_cache()


def geometry(name):
    import actors as A
    from moge.model.v2 import MoGeModel
    stem = os.path.join(ROOT, "wip", "scene3d", name)
    clean = np.asarray(Image.open(stem + "_clean.png").convert("RGB"))
    H, W = clean.shape[:2]
    hole = hole_of(name)
    model = MoGeModel.from_pretrained("Ruicheng/moge-2-vitl-normal").cuda().eval()
    x = torch.from_numpy(clean.astype(np.float32) / 255).permute(2, 0, 1).cuda()
    with torch.no_grad():
        out = {k: v.cpu().numpy() for k, v in model.infer(x).items() if torch.is_tensor(v)}
    d = dict(np.load(stem + ".npz"))
    ring = (cv2.dilate(hole, np.ones((61, 61), np.uint8)) > 0) & (hole == 0) & d["mask"] & out["mask"]
    s = float(np.median(d["depth"][ring] / out["depth"][ring]))
    w = cv2.GaussianBlur(hole.astype(np.float32), (0, 0), 4)            # feathered seam, in log depth
    depth = np.exp(np.log(d["depth"]) * (1 - w) + np.log(out["depth"] * s) * w).astype(np.float32)
    k = 2 * HOLE + 1
    for el in A.layout(name)[0]:                     # the backdrop passes behind every actor's back
        near = cv2.dilate(el["mask"].astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))) > 0
        depth[near] = np.maximum(depth[near], 1.05 * (el["z"] + 2 * el["rm"])[near])
    K = d["intrinsics"]
    u = (np.arange(W) + 0.5) / W
    v = (np.arange(H) + 0.5) / H
    ray = np.stack(np.broadcast_arrays((u[None, :] - K[0, 2]) / K[0, 0], (v[:, None] - K[1, 2]) / K[1, 1],
                                       np.ones((H, W))), -1).astype(np.float32)
    far = cv2.dilate(depth, np.ones((FILL, FILL), np.uint8))
    near = cv2.dilate((depth < 0.92 * far).astype(np.uint8) * 255, np.ones((5, 5), np.uint8))
    bgr = cv2.cvtColor(clean, cv2.COLOR_RGB2BGR)
    cv2.imwrite(stem + "_clean_bg.png", cv2.inpaint(bgr, near, 9, cv2.INPAINT_TELEA))
    np.savez_compressed(stem + "_clean.npz", points=ray * depth[..., None], depth=depth, intrinsics=K,
                        mask=d["mask"] | (hole > 0), normal=d["normal"], bg_depth=far)
    print(f"CLEAN_DONE {name}: hole {hole.mean():.1%} of the plate, depth scale {s:.3f}")


if __name__ == "__main__":
    name, seeds = sys.argv[1], [int(a) for a in sys.argv[2:] if a != "depth"]
    for sd in seeds:
        paint(name, sd, draft=len(seeds) > 1)    # several seeds: drafts in wip/gen/ to choose from
    if len(seeds) < 2:                           # one seed or `depth`: the final plate's geometry
        geometry(name)
