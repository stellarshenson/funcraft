"""Sigils as raised gold embroidery on the draped cloth of a plate, seen from near: the Machina Opus of the Adeptus
Mechanicum and the cog wheel with the mark of Stellars Tech (resources/assets/sigil-<name>-ink.png) in place of the
emblems that the image model painted there.

    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 HF_HUB_OFFLINE=1 .venv-moge/bin/python src/goldwork.py clear forge [seed]
                                     # wip/gen/sigils-forge/cleared.png: the drape without the old emblems
    ... .venv-moge/bin/python src/goldwork.py lay forge    # wip/scene3d/forge_drape.npz: the cloth as an object with its
                                     # embroidery; wip/preview/sigils-forge.png: the old plate, the chart of the cloth
                                     # and the flat cloth with its embroidery
    python3 src/goldwork.py apply forge                    # the cleared velvet into wip/scene3d/forge.png and
                                     # forge_clean.png; the old ones are kept

The cloth is an object of the scene and the embroidery is a texture on it (DESIGN.md section 2.6). The owner: "the
cloth is a 3d cloth object - and the 3d shape is draped; and thus the applied embroidery curves as it is applied as a
texture". Two versions before this one put the glyphs into the picture of the plate: the first as a flat disc that
faced the camera ("sigils are not applied as texture to the fabric but simply painted, flat not draped"), the second
bent through the chart of the cloth but still painted, with a light of its own.

- **Clear** - the image model paints plain velvet where the old emblems were, at the plate's own scale: painted at
  twice that scale its velvet had a glitter of fine creases that the velvet round it does not have, and stood as a
  disc of other cloth. The colours of the velvet round an emblem, carried into its place, stood as a flat dull disc
  without folds
- **Surface** - MoGe-2 measures the normals of an enlarged crop of the cleared drape. The model takes the crop for a
  whole picture, so its normals hold for a camera that looks at the middle of the crop; they are turned into the
  scene's camera. The surface is solved from them on the rays of the scene's camera, held loosely to the depth of
  the scene's own measurement (src/inscribe.py): the mesh of the cloth, a vertex per pixel of the plate
- **Chart** - a least squares conformal map lays that surface flat: every vertex gets a place in metres on the flat
  cloth. It is the second UV map of the mesh; the first is the vertex's pixel in the plate, for the velvet
- **Thread** - the owner: "only the strokes need to be coloured (gold), rest is transparent". One ink of each sigil is
  its strokes, where the thread lies, and the other is cloth that shows through: for the Machina Opus the black of
  its glyph (the dark ink), for the wheel of Stellars Tech its drawn thread (the light ink), as on the cloth of
  ../mech-design/src/procession/clothart.py. Each half of a sigil is the other half with thread and cloth exchanged
- **Texture** - the glyph is exact: no image model draws it. It is drawn on the flat cloth, round and upright on the
  cloth's own way down: where the gold lies. Blender renders it on the draped mesh (src/scenes.py)
- **Gold** - the gold lies in the velvet and takes the velvet's light: every vertex holds the light of the velvet at
  its pixel against the mean light of the velvet round it, so a fold or a crease that darkens the velvet darkens the
  gold on it. The texture adds what the plate's own goldwork shows: strokes rounded over their edges, brighter
  towards the lantern, a darker cord along the edge, satin stitches across every stroke whose sheen turns with
  their direction, a grain of thread and a shadow on the velvet beside them. The light chooses the gold between the
  dark, middle and bright tone of the plate's goldwork. A third version gave the thread a wide padding with rows,
  lit by a lamp at the lantern; the owner: "the sigils are too flat and they don't look like gold-printed, their
  style is too metal-like and they don't drape along wit hthe cloth". Of three looks shown as test frames the owner
  chose this satin goldwork
- **No image model over a sign** - the image model was tried over the laid glyphs, for the grain of real thread. At
  every strength from 0.15 to 0.5 it changed the marks: half of the skull was lost, the mark of Stellars Tech became
  a painted brain, and at 0.35 it drew a skull in a cog wheel of its own
"""
import os, sys
import numpy as np, cv2
from PIL import Image
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "resources", "assets")
THREAD = {"mechanicum": 128, "stellars": 255}      # the value in the ink map of each sigil (src/heraldry.py) where its thread lies
# per scene: `prompt`, the plain cloth the image model paints where the old emblems were; `measure`, the scene's
# measurement whose depth holds the cloth (src/img2geometry.py); `pictures`, the plate files that show the cloth;
# `cloths`, each with `actor` (the element of the motion map that is the cloth, or None for a cloth that becomes an
# object of its own), `box` (the part of the plate the image model sees when it clears the cloth: x0, y0, x1, y1, its
# sides multiples of 16), `region` (the part that holds the cloth, which is measured and laid flat), `toward` (the
# direction towards the light on the flat cloth: right, down), `seed` (of the image model, where another than the
# default painted velvet that matched the velvet round it better: wip/muster/clearseeds.py), `edges` (the long edges
# of a banner that give its own way down; an edge that a thing before it hides is left out) and the sigils: (name, x, y, radius in plate pixels
# where the cloth faces the camera, or across the picture with `across`, (ex, ey, rx, ry) the ellipse round the emblem
# that the model painted there). `across`: each sigil as wide in the picture as the emblem it replaces; the depth of
# the street measures banner 14 as turned about 34 degrees from the camera, and sized along its least shortened way
# the sigils stood narrower than the round emblems the model painted there (the owner chose the emblems' width)
DRAPES = {"forge": dict(prompt="A heavy dark crimson velvet cloth draped over a stand in a dark gothic workshop at night, in dim light: "
                               "smooth deep burgundy velvet with a few broad soft folds, a narrow gold embroidered border along its "
                               "edges. The middle of the cloth is plain smooth velvet without any emblem, symbol, ornament or crease",
                        measure="forge_clean", pictures=("forge.png", "forge_clean.png"),
                        cloths=[dict(actor=None, box=(1344, 0, 1984, 768), region=(1456, 48, 1776, 640), toward=(-0.95, -0.3),
                                     sigils=[("mechanicum", 1637, 192, 86, (1637, 192, 90, 92)), ("stellars", 1609, 354, 66, (1609, 354, 68, 76))])]),
          "street": dict(prompt="A long crimson velvet banner hanging in a gothic street in grey fog light: deep red crushed velvet with "
                                "soft vertical folds between two narrow gold embroidered borders. The middle of the banner is plain "
                                "velvet without any emblem, gear, skull, symbol or ornament",
                         measure="street", pictures=("street.png",), across=True,
                         cloths=[dict(actor="11", box=(128, 0, 448, 320), region=(135, 0, 411, 654), toward=(0.9, -0.45), seed=6, edges=("right",),
                                      sigils=[("mechanicum", 310, 40, 49, (310, 40, 54, 52)), ("stellars", 288, 211, 60, (288, 211, 64, 61))]),
                                 dict(actor="14", box=(1312, 0, 1600, 320), region=(1326, 0, 1571, 652), toward=(-0.9, -0.45), edges=("left", "right"),
                                      sigils=[("mechanicum", 1431, 78, 53, (1431, 78, 57, 57)), ("stellars", 1444, 214, 62, (1444, 214, 66, 70))])])}
RIM = 4                                    # vertices of an element's mesh that its curved rim takes
TEXELS = 4                                 # texels of the texture of the flat cloth in a pixel of the plate
SOFT = 0.5                                 # pixels of the plate: the texture of the gold is evened over this much
AROUND = 24                                # pixels of the plate: the reach of the mean light of the velvet round a place
FOLD = 2.0                                 # pixels of the plate: the light of the velvet is evened over this much, so that
                                           # its folds and creases light the gold and the glints of its pile do not
FOLLOW = 0.8                               # the gold's light is the velvet's light to this power: the gold is smoother
SATIN = 0.5                                # how much the sheen of stitches laid across every stroke changes the gold
RISE = 1.5                                 # pixels of the plate: how far a stroke of gold rounds over from its edge
LUM = np.array([0.2126, 0.7152, 0.0722], np.float32)
UP = 3                                     # the drape is drawn at this many times the plate's size and reduced


def folder(scene):
    path = os.path.join(ROOT, "wip", "gen", f"sigils-{scene}")
    os.makedirs(path, exist_ok=True)
    return path


def ellipse(shape, e, grow=0.0):
    m = np.zeros(shape[:2], np.uint8)
    cv2.ellipse(m, (int(e[0]), int(e[1])), (int(e[2] + grow), int(e[3] + grow)), 0, 0, 360, 1, -1)
    return m


def first(scene):
    """The plate of the scene as it was before its sigils were reworked."""
    kept = os.path.join(ROOT, "wip", "scene3d", "before-sigils", f"{scene}.png")
    return np.asarray(Image.open(kept if os.path.exists(kept) else os.path.join(ROOT, "wip", "scene3d", f"{scene}.png")).convert("RGB"))


def golden(picture):
    """Where a picture shows gold thread: bright, yellow, far from the red of the velvet."""
    r, g, b = (picture[..., k].astype(np.float32) for k in range(3))
    return (r > 110) & (g > 0.52 * r) & (g < 0.95 * r) & (b < 0.6 * r) & (r - b > 55)


def spread(a, known, rounds=24):
    """The values of the known pixels, carried a few pixels beyond them."""
    a, known = np.where(known[..., None], a, 0).astype(np.float64), known.copy()
    for _ in range(rounds):
        s, n = cv2.blur(a * known[..., None], (3, 3)), cv2.blur(known.astype(np.float64), (3, 3))
        more = ~known & (n > 1e-6)
        a = np.where(more[..., None], s / np.maximum(n, 1e-9)[..., None], a)
        known |= more
    return a




def clear(scene, seed=4):
    """The plate with plain velvet where the old emblems were, painted by the image model, one cloth at a time."""
    import torch
    from diffusers import ZImageInpaintPipeline
    conf = DRAPES[scene]
    plate = first(scene).copy()
    pipe = ZImageInpaintPipeline.from_pretrained("Tongyi-MAI/Z-Image-Turbo", torch_dtype=torch.bfloat16).to("cuda")
    for cloth in conf["cloths"]:
        hole = np.any([ellipse(plate.shape, s[4], grow=6) for s in cloth["sigils"]], 0).astype(np.uint8)
        x0, y0, x1, y1 = cloth["box"]
        crop, part = plate[y0:y1, x0:x1].copy(), hole[y0:y1, x0:x1]
        # a hole at the top edge of the plate: the model painted the top of a banner there, with sky above it. The
        # crop is mirrored upwards, so the cloth goes on above the hole
        top = 64 if y0 == 0 else 0
        big = lambda a: np.pad(a, ((top, 0),) + ((0, 0),) * (a.ndim - 1), mode="reflect")
        gen = np.asarray(pipe(prompt=conf["prompt"], image=Image.fromarray(big(crop)), mask_image=Image.fromarray(big(part) * 255), strength=1.0,
                              height=y1 - y0 + top, width=x1 - x0, num_inference_steps=9, guidance_scale=0.0,
                              generator=torch.Generator("cuda").manual_seed(int(cloth.get("seed", seed)))).images[0])[top:]
        a = cv2.GaussianBlur(part.astype(np.float32), (0, 0), 2)[..., None]
        plate[y0:y1, x0:x1] = (crop * (1 - a) + gen * a).astype(np.uint8)
        print(f"CLEARED {cloth['actor'] or 'cloth'} seed {cloth.get('seed', seed)}: {int(hole.sum())} px painted, "
              f"{(golden(plate) & (hole > 0)).sum() / hole.sum():.1%} of them gold again", flush=True)
    Image.fromarray(plate).save(os.path.join(folder(scene), "cleared.png"))
    print("CLEAR_DONE")


def measured(scene, cloth, crop):
    """The cloth in a crop of the cleared plate: its pixels, its surface as points in the space of the scene's camera
    (x right, y down, z away from the camera), its chart, the place of every pixel on the flat cloth in metres (u to
    the right, v down, as a complex number; NaN beside the cloth)."""
    import torch
    from moge.model.v2 import MoGeModel
    import inscribe as I
    h, w = crop.shape[:2]
    r, g = crop[..., 0].astype(np.float32), crop[..., 1].astype(np.float32)
    mask = ((r > 1.5 * g) & (r > 20)) | golden(crop)                      # velvet, and the gold that is worked on it
    mask = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    count, parts = cv2.connectedComponents(mask)
    whole = lambda m: ~ndimage.binary_fill_holes(~ndimage.binary_fill_holes(m)) | ndimage.binary_fill_holes(m)      # with the dark of its deep folds, which the colour test leaves out
    x0, y0 = cloth["region"][:2]
    at = [parts[s[2] - y0, s[1] - x0] for s in cloth["sigils"]]
    if 0 in at or len(set(at)) > 1:
        sys.exit("the sigils do not lie on one piece of cloth")
    mask = whole(parts == at[0])
    model = MoGeModel.from_pretrained("Ruicheng/moge-2-vitl-normal").cuda().eval()
    big = cv2.resize(crop, (w * 2, h * 2), interpolation=cv2.INTER_LANCZOS4)      # enlarged: on the plate's own scale the folds come out fainter
    with torch.no_grad():
        geo = model.infer(torch.from_numpy(big.astype(np.float32) / 255).permute(2, 0, 1).cuda())
    N = cv2.resize(np.nan_to_num(geo["normal"].cpu().numpy(), posinf=0, neginf=0), (w, h), interpolation=cv2.INTER_AREA).astype(np.float64)
    there = np.load(os.path.join(ROOT, "wip", "scene3d", DRAPES[scene]["measure"] + ".npz"))
    K, (H, W) = there["intrinsics"], there["depth"].shape
    S, own = there["points"][y0:y0 + h, x0:x0 + w].astype(np.float64), there["normal"][y0:y0 + h, x0:x0 + w]
    mask &= there["mask"][y0:y0 + h, x0:x0 + w] & (S[..., 2] > 0)
    # the model takes the crop for a whole picture: its normals hold for a camera that looks at the middle of the crop
    ray = np.array([((x0 + w / 2) / W - K[0, 2]) / K[0, 0], ((y0 + h / 2) / H - K[1, 2]) / K[1, 1], 1.0])
    axis = np.cross([0, 0, 1.0], ray / np.linalg.norm(ray))
    N = N @ cv2.Rodrigues(axis / np.linalg.norm(axis) * np.arcsin(np.linalg.norm(axis)))[0].T
    weight = cv2.GaussianBlur(mask.astype(np.float64), (0, 0), 1.5)[..., None]
    N = cv2.GaussianBlur(N * mask[..., None], (0, 0), 1.5) / np.maximum(weight, 1e-6)      # the cloth is smooth: the mean within it
    P = I.surface(S, N, mask)
    z, ok, stretch = I.flatten(P, mask)
    yy, xx = np.nonzero(ok)
    a, b = z[ok] - z[ok].mean(), (xx + 1j * yy) - (xx + 1j * yy).mean()
    fit = [(a.conjugate() * b).sum(), (a * b).sum()]                      # the chart turned onto the plate, as it is and mirrored
    if abs(fit[1]) > abs(fit[0]):
        z = z.conjugate()
    turn = fit[int(abs(fit[1]) > abs(fit[0]))]
    z = z * (turn / abs(turn))
    unit = lambda a: a / np.linalg.norm(a, axis=-1, keepdims=True)
    mean = unit(unit(N[ok]).mean(0))
    bend = np.degrees(np.arccos(np.clip(unit(N[ok]) @ mean, -1, 1)))
    print(f"cloth {cloth['actor'] or ''}: {int(ok.sum())} px measured, {P[..., 2][ok].min():.2f} to {P[..., 2][ok].max():.2f} m from the camera; it leaves its mean plane by "
          f"{np.median(bend):.0f} degrees in the middle and {np.percentile(bend, 95):.0f} at most; its mean normal lies "
          f"{np.degrees(np.arccos(np.clip(mean @ unit(unit(own[ok]).mean(0)), -1, 1))):.0f} degrees from that of the scene's own measurement; "
          f"the surface lies {np.percentile(np.abs(P[..., 2][ok] - S[..., 2][ok]), 95) * 100:.0f} cm from it at most; "
          f"chart area against surface area {stretch[0]:.2f} to {stretch[1]:.2f}", flush=True)
    return ok, P, z


def element_chart(cloth, actors, crop, size):
    """The chart of a cloth that is an element of the motion map, laid flat from that element's own mesh (the front
    sheet that src/actors.py builds, a vertex every second pixel), so that the gold lies on the surface Blender
    renders: the place on the flat cloth of every pixel of the crop (NaN beside the cloth) and of every vertex of the
    element, as complex numbers in metres. A chart from a measure of the crop alone lay up to 60 cm from that surface."""
    import inscribe as I
    H, W = size
    x0, y0 = cloth["region"][:2]
    h, w = crop.shape[:2]
    k = cloth["actor"]
    V, uv = actors[k + "/V"], actors[k + "/uv"]
    n = len(V) // 2                                                       # the front sheet; the back shell has the same pixels
    px, py = np.round(uv[:n, 0] * W - 0.5).astype(int), np.round((1 - uv[:n, 1]) * H - 0.5).astype(int)
    step = int(np.min(np.diff(np.unique(px))))
    gx, gy = (px - px.min()) // step, (py - py.min()) // step
    P = np.zeros((gy.max() + 1, gx.max() + 1, 3))
    known = np.zeros(P.shape[:2], bool)
    P[gy, gx], known[gy, gx] = np.stack([V[:n, 0], -V[:n, 2], V[:n, 1]], 1), True      # the camera's space: x right, y down, z away
    # the rim of the element's mesh curves back (src/actors.py), also along the edges of the plate where the cloth goes
    # on: laid flat with the rest it turned the chart near the top of a banner by up to 10 degrees. The chart is laid
    # flat from the sheet without its rim and carried on to the rim
    inner = cv2.erode(known.astype(np.uint8), np.ones((2 * RIM + 1, 2 * RIM + 1), np.uint8), borderType=cv2.BORDER_CONSTANT, borderValue=0) > 0
    zg, okg, stretch = I.flatten(P, inner)
    zz = spread(np.stack([np.nan_to_num(zg.real), np.nan_to_num(zg.imag)], -1), okg, rounds=2 * RIM + 2)
    zg, okg = np.where(known, zz[..., 0] + 1j * zz[..., 1], np.nan), known
    yy, xx = np.nonzero(okg)
    a, b = zg[okg] - zg[okg].mean(), (xx + 1j * yy) - (xx + 1j * yy).mean()
    fit = [(a.conjugate() * b).sum(), (a * b).sum()]                      # the chart turned onto the plate, as it is and mirrored
    if abs(fit[1]) > abs(fit[0]):
        zg = zg.conjugate()
    turn = fit[int(abs(fit[1]) > abs(fit[0]))]
    zg = zg * (turn / abs(turn))
    at = lambda gi, gj: (ndimage.map_coordinates(np.nan_to_num(zg.real), [gi, gj], order=1, mode="nearest")
                         + 1j * ndimage.map_coordinates(np.nan_to_num(zg.imag), [gi, gj], order=1, mode="nearest"))
    on = ndimage.map_coordinates(okg.astype(np.float32), [gi := (np.arange(h)[:, None] + y0 - py.min()) / step * np.ones((1, w)),
                                                          gj := (np.arange(w)[None, :] + x0 - px.min()) / step * np.ones((h, 1))], order=1, mode="constant") > 0.99
    z = np.where(on, at(gi, gj), np.nan)
    zv = np.full(len(V), np.nan, complex)
    zv[:n] = np.where(okg[gy, gx], zg[gy, gx], np.nan)
    zv[n:] = zv[:n]
    depth = V[:n, 1]
    print(f"element {k}: {n} vertices of its front sheet, {depth.min():.2f} to {depth.max():.2f} m from the camera; chart area against surface area "
          f"{stretch[0]:.2f} to {stretch[1]:.2f}", flush=True)
    return on, z, zv


def glyph(name, r, toward, rng, S=1024):
    """A sigil drawn flat, S pixels square, r plate pixels in radius: where its gold lies; the shading of its strokes,
    each rounded over its edge as couched gold thread (brighter towards the light), a darker cord along the edge,
    satin stitches across every stroke whose sheen turns with their direction, a grain of thread; and the velvet
    beside the gold in its shadow (in pixels of the plate: g pixels of the glyph each)."""
    ink = np.asarray(Image.open(os.path.join(ASSETS, f"sigil-{name}-ink.png")))
    flat = cv2.GaussianBlur(cv2.resize((ink == THREAD[name]).astype(np.float32), (S, S), interpolation=cv2.INTER_CUBIC), (0, 0), 1.2)
    g, solid = (S / 2) / r, flat > 0.5
    inside = cv2.distanceTransform(solid.astype(np.uint8), cv2.DIST_L2, 5) / g
    outside = cv2.distanceTransform((~solid).astype(np.uint8), cv2.DIST_L2, 5) / g
    high = np.sin(np.pi / 2 * np.clip(inside / RISE, 0, 1)).astype(np.float32)
    hx, hy = (cv2.Sobel(high, cv2.CV_32F, dx, dy, ksize=3) / 8 * g * RISE / (np.pi / 2) for dx, dy in ((1, 0), (0, 1)))      # 1 at the steepest
    grain = cv2.GaussianBlur(rng.normal(size=(S, S)).astype(np.float32), (0, 0), 0.5 * g)
    # a stitch across the light shines, one along it does not, so the sheen turns round a ring as on laid goldwork
    sx, sy = (cv2.Sobel(cv2.GaussianBlur(inside.astype(np.float32), (0, 0), 2 * g), cv2.CV_32F, dx, dy, ksize=3) for dx, dy in ((1, 0), (0, 1)))
    along = np.abs(sx * toward[0] + sy * toward[1]) / np.maximum(np.hypot(sx, sy), 1e-6)
    sheen = (1 - along ** 2) ** 4
    shade = -0.5 * (hx * toward[0] + hy * toward[1]) + 0.22 * grain / grain.std() - 0.5 * np.clip(1.6 - inside, 0, 1) + SATIN * sheen
    shade = (shade - shade[solid].mean()) * solid                         # the gold keeps the plate's middle tone on the whole
    ring = 0.6 * np.clip(1.2 - outside, 0, 1) * ~solid
    return np.stack([flat, shade, ring], -1).astype(np.float32)


def lay(scene):
    """The cloths of the scene with their gold (wip/scene3d/<scene>_drape.npz, for src/scenes.py). For every cloth the
    texture of its gold on the flat cloth (`<i>/work`) and the plate's three tones of gold (`<i>/tones`); for a cloth
    that becomes an object, the mesh of its measured surface with the plate's pixel and the place on the flat cloth of
    every vertex (`<i>/V`, `uv`, `chart`, `quads`) and the part of the backdrop it replaces (`<i>/cut`); for a cloth
    that is an element of the motion map, its id (`<i>/actor`) and the place on the flat cloth of every vertex of that
    element (`<i>/chart`). `light`: the velvet's light at every pixel of the plate, for the gold."""
    import inscribe as I
    conf = DRAPES[scene]
    before = first(scene).astype(np.float32)
    plate = np.asarray(Image.open(os.path.join(folder(scene), "cleared.png")).convert("RGB")).astype(np.float32)
    H, W = plate.shape[:2]
    out, light_all = dict(n=len(conf["cloths"])), np.ones((H, W), np.float32)
    actors = np.load(os.path.join(ROOT, "wip", "scene3d", f"{scene}_actors.npz")) if any(c["actor"] for c in conf["cloths"]) else None
    for i, cloth in enumerate(conf["cloths"]):
        x0, y0, x1, y1 = cloth["region"]
        crop = plate[y0:y1, x0:x1]
        h, w = crop.shape[:2]
        if cloth["actor"]:
            ok, z, zv = element_chart(cloth, actors, crop, (H, W))
        else:
            ok, P, z = measured(scene, cloth, crop.astype(np.uint8))
        grad = lambda a: (np.gradient(a, axis=1), np.gradient(a, axis=0))
        (ux, uy), (vx, vy) = grad(z.real), grad(z.imag)
        # metres of cloth in a pixel of the plate where each sigil lies, along the least shortened way; the texture has
        # TEXELS texels per pixel of the plate
        pixel = [np.linalg.svd(np.array([[ux[s[2] - y0, s[1] - x0], uy[s[2] - y0, s[1] - x0]], [vx[s[2] - y0, s[1] - x0], vy[s[2] - y0, s[1] - x0]]]), compute_uv=False)[1]
                 for s in cloth["sigils"]]
        texel = np.mean(pixel) / TEXELS
        t = (z - (np.nanmin(z.real) + 1j * np.nanmin(z.imag))) / texel       # the place of every pixel in the texture, in texels
        Wt, Ht = int(np.nanmax(t.real)) + 2, int(np.nanmax(t.imag)) + 2
        # the sigils stand in a row down the cloth: the line through their places on the flat cloth is the cloth's own
        # way down, and every glyph stands upright on it. Upright in the picture, they stood askew on a cloth that leans
        places = [z[s[2] - y0, s[1] - x0] for s in cloth["sigils"]]
        down = (places[-1] - places[0]) / abs(places[-1] - places[0]) if len(places) > 1 else 1j
        if cloth.get("edges"):
            # a banner's sigil stands upright along the banner's long edges where they run beside it in the picture,
            # carried onto the flat cloth by the chart's slope there. Along the line through the sigils, the upper
            # sigils stood 8 to 10 degrees askew against the edges; along the edges laid flat, 7: the measured mesh
            # turns near the top of the plate where the cloth goes on
            downs = []
            for _, x, y, r, _ in cloth["sigils"]:
                ways = []
                for side in cloth["edges"]:
                    rows = [q for q in range(max(y - r - y0, 0), min(y + r - y0, h)) if ok[q].sum() > 6]
                    xs = [np.nonzero(ok[q])[0].min() if side == "left" else np.nonzero(ok[q])[0].max() for q in rows]
                    k = np.polyfit(rows, xs, 1)[0]                         # columns per row along the edge
                    ways.append(np.array([k, 1.0]) / np.hypot(k, 1.0))
                e = np.mean(ways, 0)
                cx, cy = x - x0, y - y0
                d = (ux[cy, cx] * e[0] + uy[cy, cx] * e[1]) + 1j * (vx[cy, cx] * e[0] + vy[cy, cx] * e[1])
                downs.append(d / abs(d))
            down = downs[0]
        right = down * -1j
        print(f"the cloth's own way down ({down.real:+.4f}{down.imag:+.4f}j on the flat cloth) leans {np.degrees(np.arctan2(-down.real, down.imag)):+.1f} degrees from the picture's", flush=True)
        S, rng = 1024, np.random.default_rng(7)
        toward = np.array(cloth["toward"]) / np.hypot(*cloth["toward"])
        work = np.zeros((Ht, Wt, 3), np.float32)
        for j, ((name, x, y, r, e), size) in enumerate(zip(cloth["sigils"], pixel)):
            if cloth.get("edges"):
                down = downs[j]
                right = down * -1j
                print(f"{name}: its way down leans {np.degrees(np.arctan2(-down.real, down.imag)):+.1f} degrees on the flat cloth", flush=True)
            # its size on the flat cloth: r plate pixels where the cloth faces the camera most, or across the picture
            cx, cy = x - x0, y - y0
            metres = r * (np.hypot(ux[cy, cx], vx[cy, cx]) if DRAPES[scene].get("across") else size)
            k, c = metres / (S / 2) / texel, t[cy, cx]                         # texels per pixel of the glyph, and its middle in the texture
            M = np.float32([[right.real * k, down.real * k, c.real - S / 2 * k * (right.real + down.real)],
                            [right.imag * k, down.imag * k, c.imag - S / 2 * k * (right.imag + down.imag)]])
            work += cv2.warpAffine(glyph(name, r, toward, rng, S), M, (Wt, Ht), flags=cv2.INTER_LINEAR)
            print(f"LAID {name} at ({x}, {y}): {2 * metres * 100:.0f} cm wide on the cloth, {2 * metres / texel:.0f} texels", flush=True)
        # the texture holds nothing finer than a pixel of the plate, as the velvet under it: a pixel that holds finer
        # gold is sampled otherwise at every place of the camera, and the gold changed from frame to frame
        work = cv2.GaussianBlur(work, (0, 0), SOFT * np.mean(pixel) / texel)
        # the gold takes the light of the velvet: at every pixel, the velvet's light against the mean light of the
        # velvet round it (without the plate's goldwork), with the shading of the stroke, chooses the gold between the
        # dark, middle and bright tone of the goldwork that the plate showed where the sigils are (src/scenes.py)
        old = before[np.any([ellipse(before.shape, s[4]) for s in cloth["sigils"]], 0) & golden(before)]
        rank = old @ LUM
        dark, mid, bright = (np.median(old[(rank >= np.percentile(rank, a)) & (rank <= np.percentile(rank, b))], 0) for a, b in ((5, 15), (45, 55), (90, 99)))
        lum = crop @ LUM
        velvet = (ok & ~golden(crop.astype(np.uint8))).astype(np.float32)
        around = cv2.GaussianBlur(lum * velvet, (0, 0), AROUND) / np.maximum(cv2.GaussianBlur(velvet, (0, 0), AROUND), 1e-3)
        light = (cv2.GaussianBlur(lum, (0, 0), FOLD) / np.maximum(around, 1.0)) ** FOLLOW
        light_all[y0:y1, x0:x1] = np.where(ok, light, light_all[y0:y1, x0:x1])
        print(f"the velvet's light against its surroundings: {np.percentile(light[ok], 5):.2f} to {np.percentile(light[ok], 95):.2f} (5 to 95 %); "
              f"gold from {dark.round().astype(int).tolist()} over {mid.round().astype(int).tolist()} to {bright.round().astype(int).tolist()}", flush=True)
        out.update({f"{i}/work": work.astype(np.float16), f"{i}/tones": np.stack([dark, mid, bright])})
        on = lambda tt: np.stack([(tt.real + 0.5) / Wt, 1 - (tt.imag + 0.5) / Ht], -1).astype(np.float32)
        if cloth["actor"]:
            # the element of the motion map that is this cloth: every vertex has its place on the flat cloth; a vertex
            # outside the chart lies far beside the texture and shows no gold
            tv = (zv - (np.nanmin(z.real) + 1j * np.nanmin(z.imag))) / texel
            out.update({f"{i}/actor": cloth["actor"], f"{i}/chart": on(np.where(np.isfinite(tv), tv, -1e6))})
        else:
            # the mesh: a vertex per pixel of the cloth, in the world of src/backdrop.py (x right, y away from the camera, z up)
            idx = np.full((h, w), -1)
            idx[ok] = np.arange(ok.sum())
            cell = ok[:-1, :-1] & ok[:-1, 1:] & ok[1:, :-1] & ok[1:, 1:]
            quads = np.stack([idx[:-1, :-1][cell], idx[1:, :-1][cell], idx[1:, 1:][cell], idx[:-1, 1:][cell]], 1)      # counter-clockwise seen from the camera
            yy, xx = np.nonzero(ok)
            cut = np.zeros((H, W), bool)
            cut[y0:y1, x0:x1] = cv2.erode(ok.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0      # the backdrop stays under the rim of the cloth
            out.update({f"{i}/V": np.stack([P[ok][:, 0], P[ok][:, 2], -P[ok][:, 1]], 1).astype(np.float32),
                        f"{i}/uv": np.stack([(xx + x0 + 0.5) / W, 1 - (yy + y0 + 0.5) / H], 1).astype(np.float32),
                        f"{i}/chart": on(t[ok]), f"{i}/quads": quads.astype(np.int32), f"{i}/cut": cut})
            print(f"cloth object: {int(ok.sum())} vertices, {len(quads)} faces", flush=True)
        # the proof: the old plate, the chart drawn on the cloth, and the flat cloth with its gold. Lines of the chart
        # that stay straight on a cloth drawn in folds mean that the surface holds no folds
        big = lambda a, known: cv2.resize(spread(a, known).astype(np.float32), (w * UP, h * UP), interpolation=cv2.INTER_LINEAR)
        Z, inner = big(np.stack([z.real, z.imag], -1), ok), cv2.resize(ok.astype(np.float32), (w * UP, h * UP), interpolation=cv2.INTER_LINEAR)
        chart = cv2.resize(crop, (w * UP, h * UP), interpolation=cv2.INTER_CUBIC)
        for kk in (0, 1):
            line = np.floor(Z[..., kk] / 0.05)                                  # a line every 5 cm of cloth
            chart[(inner > 0.99) & (np.abs(np.gradient(line, axis=0)) + np.abs(np.gradient(line, axis=1)) > 0)] = (0, 230, 255) if kk else (255, 220, 0)
        scale = 2 * h / (Ht * texel)                                           # the flat cloth as high as the two other pictures
        (Wc, Hc), _, mx, my = I.unwrap(z, ok, scale)
        laid = cv2.remap(crop, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        a = cv2.resize(work[..., 0], (int(round(Wt * texel * scale)), int(round(Ht * texel * scale))), interpolation=cv2.INTER_AREA)[:Hc, :Wc, None]
        laid[:a.shape[0], :a.shape[1]] = laid[:a.shape[0], :a.shape[1]] * (1 - a) + mid * a
        page = [cv2.resize(m, (w * 2, h * 2), interpolation=cv2.INTER_AREA) for m in (cv2.resize(before[y0:y1, x0:x1], (w * UP, h * UP), interpolation=cv2.INTER_CUBIC), chart)]
        page.append(np.pad(laid, ((0, max(0, 2 * h - Hc)), (0, 0), (0, 0)))[:2 * h])
        path = os.path.join(ROOT, "wip", "preview", f"sigils-{scene}.png" if len(conf["cloths"]) == 1 else f"sigils-{scene}-{cloth['actor']}.png")
        Image.fromarray(np.clip(np.concatenate(page, 1), 0, 255).astype(np.uint8)).save(path)
        print("wrote", path, flush=True)
    out["light"] = light_all.astype(np.float16)
    path = os.path.join(ROOT, "wip", "scene3d", f"{scene}_drape.npz")
    np.savez_compressed(path, **out)
    print("LAY_DONE; wrote", path)


def apply(scene):
    """The cleared velvet into the plate files that show the cloths; the old pictures are kept. The gold is not in the
    picture: it lies on the cloth."""
    import shutil
    keep = os.path.join(ROOT, "wip", "scene3d", "before-sigils")
    os.makedirs(keep, exist_ok=True)
    new = np.asarray(Image.open(os.path.join(folder(scene), "cleared.png")).convert("RGB"))
    hole = np.any([ellipse(new.shape, s[4], grow=12) for c in DRAPES[scene]["cloths"] for s in c["sigils"]], 0)      # wider than the part that `clear` painted
    a = cv2.GaussianBlur(hole.astype(np.float32), (0, 0), 2)[..., None]
    for name in DRAPES[scene]["pictures"]:
        file = os.path.join(ROOT, "wip", "scene3d", name)
        if not os.path.exists(os.path.join(keep, name)):
            shutil.copy2(file, os.path.join(keep, name))
        old = np.asarray(Image.open(os.path.join(keep, name)).convert("RGB")).astype(np.float32)
        Image.fromarray((old * (1 - a) + new * a).round().astype(np.uint8)).save(file)
        print("wrote", file)


if __name__ == "__main__":
    {"clear": clear, "lay": lay, "apply": apply}[sys.argv[1]](*sys.argv[2:])
