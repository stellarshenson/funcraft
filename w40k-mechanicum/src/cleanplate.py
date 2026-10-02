"""A plate with its moving figures removed, for the actor rigs (src/actors.py).

The priests and the things they carry (masks wip/scene3d/<name>_seg.npz, grown
by HOLE px to take their rim light too) are painted over by Z-Image-Turbo's
inpainting pipeline from a prompt describing the empty scene. MoGe-2 then
measures the clean plate; its depth, scaled to the original on the pixels
both share, replaces the original inside the hole, pushed behind the back
of every actor (the painted scene may put a pillar where a priest stands);
the points are rebuilt with the original intrinsics so the backdrop lines
up with the actors. The paint is kept in wip/scene3d/<name>_paint.png;
the flames with a mesh of their own are taken out of it (unflame) before
MoGe-2 measures it, and where a flame was the measured depth is used.
Writes wip/scene3d/<name>_clean.png, _clean.npz, _clean_bg.png.

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
import os, sys, json
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
    for fl in json.loads(str(seg["flames"])) if "flames" in seg.files else []:
        if fl["mesh"] and fl["owner"]:                                # the flame of a carried candle goes with its candle.
            m = seg[fl["id"]].astype(np.uint8)                        # A standing candle's flame is taken out in geometry():
            hole = m if hole is None else hole | m                    # painted over here, its candle would go with it
    k = 2 * HOLE + 1
    return cv2.dilate(hole, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))


def candle_under(lum, fl):
    """The standing candle under a flame's wick, as a mask: the columns
    the candle takes three rows below the wick, from the wick down. From
    the wick's column the row is followed to each side as far as it stays
    brighter than 0.15 of the way from the air beside the candle (1 to 1.3
    flame heights to the side) to the candle's top. Within that reach the
    candle ends at the steepest fall of brightness: its outline. A shaded
    side of the candle lies inside the outline and stays candle; bloom on
    the wall lies outside it."""
    (wx, wy), h = fl["wick"], max(fl["wick"][1] - fl["tip"][1], 4.0)
    xi, yi = int(round(wx)), int(wy)
    out = np.zeros(lum.shape, np.float32)
    if yi + 3 >= lum.shape[0]:
        return out
    row = lum[yi + 3]
    off = np.abs(np.arange(len(row)) - xi)
    beside = row[(off > h) & (off < 1.3 * h)]
    if not beside.size or row[xi] <= 1.2 * np.median(beside):
        return out
    air, span = float(np.median(beside)), float(row[xi] - np.median(beside))

    def reach(step, low):
        x = xi
        while 0 < x + step < len(row) - 1 and row[x + step] > air + low * span:
            x += step
        return x

    def outline(step):
        far = reach(step, 0.15)
        xs = np.arange(xi + step, far + 2 * step, step)
        xs = xs[(xs > 0) & (xs < len(row) - 1)]
        if not len(xs):
            return xi
        return int(xs[np.argmax(row[xs - step] - row[xs + step])]) - step      # the last column before the fall

    xl, xr = outline(-1), outline(1)
    if xr - xl < 2 * h:
        out[yi + 1:, max(xl - 1, 0):xr + 2] = 1
    return out


def unflame(bgr, flames, seg):
    """The painted flames, and the bloom close round each, taken out of the
    backdrop: a flame is shown as its own mesh, smaller
    (actors.flame_scale), and the bloom of the large one would hang over it
    as a halo. The flames' pixels are filled from their rims. Round each
    flame the picture is then split into its soft tone (blurred over 0.35
    flame heights) and the detail on it. Within 0.7 heights of the flame's
    axis the tone is replaced by the tone 1.5 heights out and more, above
    the wick, spread inward; between 0.7 and 1.5 heights the two are mixed.
    The detail stays, except within 0.4 heights plus 5 px of the flame:
    there the bloom is steep, and what the split calls detail is the
    flame's bright rim. Standing candles are left as they are, the flame's
    own and its neighbours' (candle_under). A carried candle is an actor
    and is not in the backdrop; where its flame was, the paint tends to put
    a bright patch, which goes with the tone. Below the wick the change
    fades out over one height. The wide, soft light on the wall behind
    stays."""
    H, W = bgr.shape[:2]
    masks = {}
    for fl in flames:
        m = seg[fl["id"]].astype(np.uint8)
        m[int(fl["wick"][1]) + 2:] = 0                                  # the candle below the wick stays
        masks[fl["id"]] = m
    lit = np.maximum.reduce(list(masks.values()))
    out = cv2.inpaint(bgr, cv2.dilate(lit, np.ones((5, 5), np.uint8)) * 255, 5, cv2.INPAINT_TELEA).astype(np.float32)
    lum = out.mean(-1)
    candle = np.zeros((H, W), np.float32)
    for fl in flames:
        if not fl["owner"]:
            candle = np.maximum(candle, candle_under(lum, fl))
    step = lambda v: v * v * (3 - 2 * v)
    for fl in flames:
        (wx, wy), (tx, ty) = fl["wick"], fl["tip"]
        h = max(wy - ty, 4.0)
        r = int(3 * h)
        box = (slice(max(int(ty) - r, 0), min(int(wy) + r + 1, H)), slice(max(int(wx) - r, 0), min(int(wx) + r + 1, W)))
        img, air = out[box], 1.0 - candle[box]
        yy, xx = np.mgrid[box].astype(np.float32)
        t = np.clip(((xx - wx) * (tx - wx) + (yy - wy) * (ty - wy)) / ((tx - wx) ** 2 + (ty - wy) ** 2), 0, 1)
        d = np.hypot(xx - wx - t * (tx - wx), yy - wy - t * (ty - wy))  # distance from the flame's axis
        tone = cv2.GaussianBlur(img * air[..., None], (0, 0), 0.35 * h) / \
            np.maximum(cv2.GaussianBlur(air, (0, 0), 0.35 * h), 1e-3)[..., None]
        out_there = ((d >= 1.5 * h) & (yy <= wy)).astype(np.float32) * air
        far = cv2.GaussianBlur(tone * out_there[..., None], (0, 0), 0.8 * h) / \
            np.maximum(cv2.GaussianBlur(out_there, (0, 0), 0.8 * h), 1e-3)[..., None]
        w = step(np.clip((1.5 * h - d) / (0.8 * h), 0, 1)) * step(np.clip((wy + h - yy) / h, 0, 1))
        w = (w * (1 - cv2.GaussianBlur(candle[box], (0, 0), 1.0)))[..., None]
        k = 2 * int(0.4 * h + 5) + 1
        near = cv2.dilate(masks[fl["id"]][box], cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
        detail = (img - tone) * (1 - cv2.GaussianBlur(near.astype(np.float32), (0, 0), 0.15 * h + 1))[..., None]
        out[box] = img * (1 - w) + (far + detail) * w
    return out.clip(0, 255).astype(np.uint8)


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
    Image.fromarray(clean).save(stem + "_paint.png")
    del pipe
    torch.cuda.empty_cache()


def geometry(name):
    import actors as A
    from moge.model.v2 import MoGeModel
    stem = os.path.join(ROOT, "wip", "scene3d", name)
    clean = np.asarray(Image.open(stem + "_paint.png").convert("RGB"))
    H, W = clean.shape[:2]
    hole = hole_of(name)
    seg = np.load(stem + "_seg.npz")                 # flames with a mesh of their own leave the plate
    flames = [fl for fl in (json.loads(str(seg["flames"])) if "flames" in seg.files else []) if fl["mesh"]]
    lit = np.zeros((H, W), np.uint8)                 # where a flame was: the depth there is the wall's behind it,
    if flames:                                       # or a patch of wall hangs in the air at the candle's depth
        clean = cv2.cvtColor(unflame(cv2.cvtColor(clean, cv2.COLOR_RGB2BGR), flames, seg), cv2.COLOR_BGR2RGB)
        for fl in flames:
            m = seg[fl["id"]].astype(np.uint8)
            m[int(fl["wick"][1]) + 1:] = 0
            lit |= cv2.dilate(m, np.ones((7, 7), np.uint8))
    model = MoGeModel.from_pretrained("Ruicheng/moge-2-vitl-normal").cuda().eval()
    x = torch.from_numpy(clean.astype(np.float32) / 255).permute(2, 0, 1).cuda()
    with torch.no_grad():
        out = {k: v.cpu().numpy() for k, v in model.infer(x).items() if torch.is_tensor(v)}
    d = dict(np.load(stem + ".npz"))
    for z in (d["depth"], out["depth"]):             # sky has no depth: put it on a far dome, as src/backdrop.py does
        z[~(np.isfinite(z) & (z > 0))] = 2 * np.nanmax(z[np.isfinite(z)])
    ring = (cv2.dilate(hole, np.ones((61, 61), np.uint8)) > 0) & (hole == 0) & d["mask"] & out["mask"]
    s = float(np.median(d["depth"][ring] / out["depth"][ring]))
    w = np.maximum(cv2.GaussianBlur(hole.astype(np.float32), (0, 0), 4), lit)   # feathered seam, in log depth
    depth = np.exp(np.log(d["depth"]) * (1 - w) + np.log(out["depth"] * s) * w).astype(np.float32)
    k = 2 * HOLE + 1
    for el in A.layout(name)[0]:                     # the backdrop passes behind every actor's back
        if el["kind"] == "flame":                    # a flame has the wall behind it already; its candle stays in place
            continue
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
