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
    CUDA_VISIBLE_DEVICES=1 .venv-moge/bin/python src/cleanplate.py <name> desmoke    # painted smoke out of the plate

Painted smoke. A wisp painted into the plate stays where it is when its
candle moves, and lies at the background's depth. `desmoke` paints it over
in the plate itself, inside the boxes of motion.WISPS: smoke there is pale,
unsaturated, and brighter than what is behind it. The plate as generated is
kept in wip/gen/plate_<name>_smoky.png. The smoke comes back simulated
(src/smoke.py).
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
    "forge": "A cluttered workbench in a dark gothic forge, nobody present. Riveted iron table with tools, cogs, glass "
             "bottles and wax, brass articulated arms, crimson velvet cloth, a gothic window and iron machinery behind, "
             "cold blue mist outside, warm lamplight, dark, highly detailed, photograph",
    "vault": "Interior of a gothic data vault, nobody present. Black iron server racks behind pointed golden arches, "
             "crimson and gold embroidered panels with brass cog wheels, dark polished floor, dim green and warm light, "
             "dark, highly detailed, photograph",
    "street": "A gothic cathedral street at dusk, nobody present. Towering black iron and stone facades with gold "
              "ornaments, a stone bridge between spires, wet cobblestones, iron lamp posts, pale sky, dark, highly "
              "detailed, photograph",
    "saint": "A gothic chapel wall, nobody present. An empty golden carved niche with a sunburst, stained glass "
             "windows, dark stone wall, iron candle stands, gold ornaments, dim warm light, dark, highly detailed, "
             "photograph",
    "hall": "A long gothic cathedral hall, nobody present. Bare black carved stone walls and pillars, pointed vaults, "
            "a far window with a shaft of light, dark polished floor, iron lanterns along the walls, dark, highly "
            "detailed, photograph",
    "reliquary": "A gothic altar table, nobody present. A golden reliquary shrine holding a black graphics card, crimson "
                 "velvet cloth with gold embroidery, brass candlesticks, a brass censer, a skull, a dark stone chapel "
                 "behind, clear air, dim warm light, dark, highly detailed, photograph",
    "scriptorium": "A candle-lit gothic scriptorium, nobody present. Dark wooden shelves packed with books and scrolls, "
                   "lecterns draped in crimson velvet with open books, brass instruments, dark, highly detailed, "
                   "photograph",
    "voidshrine": "A gothic shrine on a starship, nobody present. Dark riveted iron walls, a round stained glass window "
                  "with a skull, an altar with crimson cloth and brass candlesticks, a great arched window to space "
                  "with stars and an orange nebula, dark, highly detailed, photograph",
    "foundry": "Empty interior of a gothic forge temple, nobody present. Bare dark flagstone and iron floor "
               "with rails and scattered slag, carved black iron wall panels, crimson banners with gold cog emblems, "
               "dim warm light, dark, highly detailed, photograph",
    "choir": "Empty gothic cathedral nave, nobody present. Polished dark stone floor tiles, carved stone pillars, "
             "wooden choir stalls, crimson and gold processional banners on poles, stained glass windows, "
             "clear air, dim warm light, dark, highly detailed, photograph",
}


def hole_of(name):
    """The actors' masks together, grown by HOLE px."""
    seg = np.load(os.path.join(ROOT, "wip", "scene3d", name + "_seg.npz"))
    hole = None
    for el in M.MAPS[name]:
        if el["kind"] not in ("stream", "smoke"):                     # streams stay in the plate; smoke has no mask
            m = seg[el["id"]].astype(np.uint8)
            hole = m if hole is None else hole | m
    for k in seg.files:                                               # flames are elements of their own
        if k.startswith("f") and k != "flames":
            hole = seg[k].astype(np.uint8) if hole is None else hole | seg[k].astype(np.uint8)
    k = 2 * HOLE + 1
    return cv2.dilate(hole, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))


def wisps(name, plate):
    """The painted smoke inside the boxes of motion.WISPS, outside every
    actor, found in the image file `plate`: the plate as generated. Found in
    a plate whose smoke is already painted over, the mask is empty, and the
    paint then leaves the smoke in."""
    stem = os.path.join(ROOT, "wip", "scene3d", name)
    bgr = cv2.imread(plate)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    behind = cv2.morphologyEx(hsv[..., 2], cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (61, 61)))
    m = np.zeros(bgr.shape[:2], np.uint8)
    for x0, y0, x1, y1 in M.WISPS.get(name, []):
        box = (slice(y0, y1), slice(x0, x1))
        m[box] = (hsv[box][..., 1] < 75) & (hsv[box][..., 2].astype(int) > behind[box].astype(int) + 22)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    sam = np.load(stem + "_sam.npz")
    kind = {el["id"]: el["kind"] for el in M.MAPS[name]}
    for k in sam.files:                              # figures and what they hold keep their pixels; banners behind smoke do not
        if kind.get(k) in ("priest", "carry"):
            m[cv2.dilate(sam[k].astype(np.uint8), np.ones((7, 7), np.uint8)) > 0] = 0
    return m


def desmoke(name, seed=1):
    import shutil
    from diffusers import ZImageInpaintPipeline
    if name not in M.WISPS:
        return
    stem = os.path.join(ROOT, "wip", "scene3d", name)
    keep = os.path.join(ROOT, "wip", "gen", f"plate_{name}_smoky.png")
    if not os.path.exists(keep):
        shutil.copy(stem + ".png", keep)
    plate = Image.open(keep).convert("RGB")
    W, H = plate.size
    hole = wisps(name, keep)
    pipe = ZImageInpaintPipeline.from_pretrained("Tongyi-MAI/Z-Image-Turbo", torch_dtype=torch.bfloat16).to("cuda")
    gen = pipe(prompt=EMPTY[name], image=plate, mask_image=Image.fromarray(hole * 255), strength=1.0,
               height=H, width=W, num_inference_steps=9, guidance_scale=0.0,
               generator=torch.Generator("cuda").manual_seed(seed)).images[0]
    a = cv2.GaussianBlur(hole.astype(np.float32), (0, 0), 2)[..., None]
    out = (np.asarray(plate, np.float32) * (1 - a) + np.asarray(gen, np.float32) * a).astype(np.uint8)
    Image.fromarray(out).save(stem + ".png")
    print(f"DESMOKE_DONE {name}: {hole.mean():.1%} of the plate")


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
    for z in (d["depth"], out["depth"]):             # sky has no depth: put it on a far dome, as src/backdrop.py does
        z[~(np.isfinite(z) & (z > 0))] = 2 * np.nanmax(z[np.isfinite(z)])
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
    seg = np.load(stem + "_seg.npz")                 # flames with a mesh of their own leave the plate
    lit = np.zeros((H, W), np.uint8)
    for k in seg.files:
        if k.startswith("f") and k != "flames":
            lit |= seg[k].astype(np.uint8)
    if lit.any():
        bgr = cv2.inpaint(bgr, cv2.dilate(lit, np.ones((5, 5), np.uint8)) * 255, 5, cv2.INPAINT_TELEA)
        cv2.imwrite(stem + "_clean.png", bgr)
    cv2.imwrite(stem + "_clean_bg.png", cv2.inpaint(bgr, near, 9, cv2.INPAINT_TELEA))
    np.savez_compressed(stem + "_clean.npz", points=ray * depth[..., None], depth=depth, intrinsics=K,
                        mask=np.ones((H, W), bool), normal=d["normal"], bg_depth=far)
    print(f"CLEAN_DONE {name}: hole {hole.mean():.1%} of the plate, depth scale {s:.3f}")


if __name__ == "__main__":
    name, seeds = sys.argv[1], [int(a) for a in sys.argv[2:] if a.isdigit()]
    if "desmoke" in sys.argv:
        desmoke(name, *seeds[:1])
        sys.exit()
    for sd in seeds:
        paint(name, sd, draft=len(seeds) > 1)    # several seeds: drafts in wip/gen/ to choose from
    if len(seeds) < 2:                           # one seed or `depth`: the final plate's geometry
        geometry(name)
