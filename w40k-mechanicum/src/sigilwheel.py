"""The Stellars Tech sigil in place of the saint scene's sun-gear. The owner: "make the big circle on the right to be
the stellars-tech sigil, let it be still, but have the star inside it blink red". The sun-gear is wheel element 4 of
the motion map (src/motion.py), a disc on its fitted plane (src/actors.py); with `picture` and `glow` it shows this
sigil instead of the plate's gear and stands still, and src/rig.py lights its star red in pulses.

A first sigil of plain raised gold over flat enamel was rejected: "so flat and without any embroidery and delicacy
while other parts of the image are intrinsicly complicated". It is now goldsmith's work, every part inside the glyph's
own regions (resources/assets/sigil-stellars-ink.png: its white parts gold, its grey parts red enamel):

- **Gold** - every gold part has a polished, bevelled rim and a fine engraved double line inside it; within that rim
  relief is chased into the gold: round the ring a frieze of acanthus scroll and small cog wheels between beaded
  borders, in the fields a flowing acanthus scrollwork; both are height maps the image model drew (`motifs`), the
  frieze mirrored every second time round so its ends meet
- **Ring** - a row of gold beads along its inner edge, a domed boss on every tooth
- **Enamel** - translucent red over a wavy sunburst engraved in the ground beneath it (guilloche)
- **Jewels** - the star of the brain's half is a faceted ruby; each node of the circuit holds a pearl
- **Light** - from the upper left and from above, as the plate's gilding is lit; the engraving's hollows darker; worn
  unevenly
- **Warhammer 40,000** - the owner: "you may use image generator to generate the sigil in a very w40k style". The
  drawn sigil is only the start: the generator paints over it in the scene's surroundings (`generate`, strengths
  0.45 to 0.75); at 0.45 it keeps the sign (gear, split disc, half-brain with its star, circuit with pearls) and adds
  skulls on the teeth, crushed velvet and worn gilding, and folds the half-brain as a real brain. The chosen picture
  (`choose`) keeps what differs from the surroundings near the sigil's outline; the drawn ruby, sooted as the rest,
  is laid back where the red light shines. The owner: "make it disturbed gold, slightly charred (or smoked)", "dirty
  gold": the drawn gold is sooted before the generator paints (`sooted`) and the generator is asked for tarnished,
  soot-blackened, slightly charred gold
- **Star** - its own picture is where the red light shows: only the star's centre, no halo. The owner: "the light
  in the star must be smaller and only the inner part of the star must glow and pulse"

    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 HF_HUB_OFFLINE=1 .venv-moge/bin/python src/sigilwheel.py motifs
                                   # wip/gen/sigil-band-<seed>.png, sigil-scroll-<seed>.png: the relief motifs
    python3 src/sigilwheel.py      # wip/scene3d/saint_sigil.png (RGBA) and saint_sigil_star.png; wip/preview/sigilwheel.png
    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 HF_HUB_OFFLINE=1 .venv-moge/bin/python src/sigilwheel.py generate
                                   # the generator over the drawn sigil: wip/gen/sigil-gen-<strength>-<seed>.png
    python3 src/sigilwheel.py choose sigil-gen-<strength>-<seed>.png    # that candidate as wip/scene3d/saint_sigil.png
"""
import os, json
import numpy as np, cv2
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INK = os.path.join(ROOT, "resources", "assets", "sigil-stellars-ink.png")
BAND = os.path.join(ROOT, "wip", "gen", "sigil-band-2.png")          # the relief motifs (`motifs`): the ring's frieze
SCROLL = os.path.join(ROOT, "wip", "gen", "sigil-scroll-1.png")      # and the gold fields' scrollwork
OUT = os.path.join(ROOT, "wip", "scene3d", "saint_sigil.png")
STAR = os.path.join(ROOT, "wip", "scene3d", "saint_sigil_star.png")
S, SIZE = 2048, 1024                     # drawn at S pixels square, kept at SIZE
STAR_AT = (0.36, 0.50)                   # a point inside the star, in shares of the sigil's width and height
CORE = (10, 22)                          # the red light rises from 10 to 22 px (of SIZE) inside the star's edge
FILL = 0.84                              # the sigil's share of the picture's width: what the generator adds round its
                                         # teeth stays inside the round disc that shows the picture
DARK, MID, BRIGHT = (np.array(c, np.float32) for c in ((96, 58, 18), (206, 150, 58), (255, 230, 160)))   # the goldwork's tones
VELVET = np.array([112, 7, 16], np.float32)
RUBY, PEARL = np.array([170, 10, 26], np.float32), np.array([228, 216, 196], np.float32)
REPEATS = 4                              # the frieze round the ring, every second one mirrored
FIELD = 2000                             # canvas pixels the scrollwork spans, centred on the sigil
ROW, TIE, CORD, PAD = 20.0, 52.0, 14.0, 18.0  # canvas pixels: rows of couched thread, the stitches that tie a row,
                                         # the width of the cord along every edge, the reach of the padding


# relief motifs drawn by the image model as height maps, in the words of mech-design/src/procession/motifs.py
ALPHA = ("Grayscale height map for sculpting, a ZBrush alpha: pure black flat background, the relief in shades of grey, "
         "white is the highest. Bas-relief seen exactly from the front, no perspective, no lighting, no shadows, no "
         "colour, no text, no letters. Crisp, deep, finely chiselled gothic detail in the style of Warhammer 40,000 "
         "Adeptus Mechanicus ornament. ")
MOTIFS = {"band": (1536, 384, "A long horizontal frieze band filling the picture from edge to edge: a running scroll of "
                               "curling acanthus leaves and tendrils on one wavy stem, repeated evenly, small cog wheels "
                               "in the curls, between two thin beaded borders along the top and the bottom edge."),
          "scroll": (768, 768, "Seamless pattern that fills the whole picture edge to edge, with no grid, no squares and "
                               "no panels: dense flowing gothic acanthus scrollwork, curling vines and leaves turning in "
                               "every direction, tiny cog wheels woven in.")}


def motifs(seeds=(1, 2)):
    import torch
    from diffusers import ZImagePipeline
    pipe = ZImagePipeline.from_pretrained("Tongyi-MAI/Z-Image-Turbo", torch_dtype=torch.bfloat16).to("cuda")
    for name, (w, h, what) in MOTIFS.items():
        for seed in seeds:
            im = pipe(prompt=ALPHA + what, width=w, height=h, num_inference_steps=9, guidance_scale=0.0,
                      generator=torch.Generator("cuda").manual_seed(seed)).images[0]
            im.convert("L").save(os.path.join(ROOT, "wip", "gen", f"sigil-{name}-{seed}.png"))
            print("MOTIF", name, seed, flush=True)


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def parts():
    """The glyph's regions at S pixels: the outer gear, the inner gold, its teeth, the enamel, the star, the pearls'
    places (the small round enamel inside the circuit's ring nodes), the radius of the ring's inner edge."""
    n = round(S * FILL)
    ink = np.zeros((S, S), np.uint8)
    ink[(S - n) // 2:(S - n) // 2 + n, (S - n) // 2:(S - n) // 2 + n] = cv2.resize(np.asarray(Image.open(INK).convert("L")), (n, n),
                                                                                   interpolation=cv2.INTER_CUBIC)
    gold, enamel = ink > 190, (ink > 64) & (ink <= 190)
    yy, xx = np.mgrid[:S, :S].astype(np.float32)
    rad, ang = np.hypot(xx - S / 2, yy - S / 2), np.arctan2(yy - S / 2, xx - S / 2)
    _, lab = cv2.connectedComponents(gold.astype(np.uint8))
    ring = lab == lab[np.unravel_index(np.argmax(np.where(gold, rad, 0)), rad.shape)]
    sector = (ang * 90 / np.pi).astype(int)                  # 180 sectors of 2 degrees
    near = np.array([rad[ring & (sector == k)].min() for k in range(-90, 90) if (ring & (sector == k)).any()])
    far = np.array([rad[ring & (sector == k)].max() for k in range(-90, 90) if (ring & (sector == k)).any()])
    r_in, r_foot = float(np.median(near)), float(np.percentile(far, 10))
    _, elab, stats, cents = cv2.connectedComponentsWithStats(enamel.astype(np.uint8))
    star = elab == elab[int(S / 2 + (STAR_AT[1] - 0.5) * n), int(S / 2 + (STAR_AT[0] - 0.5) * n)]
    pearls = [(cents[k], 0.5 * min(stats[k, 2], stats[k, 3])) for k in range(1, len(stats))
              if stats[k, 4] < 0.002 * S * S and stats[k, 4] > 0.6 * np.pi * (max(stats[k, 2], stats[k, 3]) / 2) ** 2]
    return dict(ink=ink, gold=gold, enamel=enamel, ring=ring, inner=gold & ~ring, teeth=ring & (rad > r_foot + 3),
                star=star, pearls=pearls, rad=rad, ang=ang, xx=xx, yy=yy, r_in=r_in, r_foot=r_foot)


def contours(mask, soft=2.0):
    """Inside a region: the distance to its edge, and the unit direction along its contours, which the couched
    threads follow."""
    d = cv2.distanceTransform(mask.astype(np.uint8), cv2.DIST_L2, 5)
    gy, gx = np.gradient(cv2.GaussianBlur(d, (0, 0), soft))
    n = np.hypot(gx, gy) + 1e-6
    return d, -gy / n, gx / n


def embroidery(p):
    """The gold as raised goldwork: padded so that it rounds up from every edge, the large parts carrying a second,
    higher layer of padded relief (the ring's frieze, the fields' scrollwork), every part laid with gold threads that
    follow its contours and are tied down by small stitches in a brick pattern, a twisted cord along every edge, a
    padded boss on every tooth and beads of purl along the ring's inner edge. Returns the height, the gold, the
    threads' direction, the rows of thread, the couching stitches and the pearls."""
    rad, ang, xx, yy = p["rad"], p["ang"], p["xx"], p["yy"]
    band = cv2.imread(BAND, cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255
    rows = np.flatnonzero(band.mean(1) > 0.15)                # the frieze between its black margins
    band = band[rows.min():rows.max() + 1]
    u = (ang + np.pi) / (2 * np.pi) * REPEATS
    f = u - np.floor(u)
    f = np.where(np.floor(u).astype(int) % 2 == 1, 1 - f, f)  # mirrored every second time: no seam where they meet
    frieze = cv2.remap(band, (f * (band.shape[1] - 1)).astype(np.float32),
                       np.clip((rad - p["r_in"]) / (p["r_foot"] - p["r_in"]), 0, 1).astype(np.float32) * (band.shape[0] - 1),
                       cv2.INTER_LINEAR)
    scroll = cv2.imread(SCROLL, cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255
    k = scroll.shape[0] / FIELD
    fields = cv2.remap(scroll, ((xx - S / 2) * k + scroll.shape[1] / 2).astype(np.float32),
                       ((yy - S / 2) * k + scroll.shape[0] / 2).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    gold = p["gold"].copy()
    r = p["r_in"] - 14                                       # purl beads along the ring's inner edge, where velvet lies
    for i in range(int(2 * np.pi * r / 24)):
        t = 2 * np.pi * i / int(2 * np.pi * r / 24)
        cx, cy = S / 2 + r * np.cos(t), S / 2 + r * np.sin(t)
        if p["enamel"][int(cy), int(cx)]:
            gold |= (xx - cx) ** 2 + (yy - cy) ** 2 < 9.0 ** 2
    d, tx, ty = contours(gold)
    big = (p["ring"] & ~p["teeth"]) | p["inner"]
    motif = np.where(p["ring"] & ~p["teeth"], frieze, np.where(p["inner"], fields, 0.0))
    raised = gold & (motif > 0.45) & (d > CORD + 4) & big
    dm, mx, my = contours(raised, 1.5)
    H = gold * (0.45 * (1 - np.exp(-d / PAD)) + raised * 0.4 * (1 - np.exp(-dm / 3.0)))
    _, tlab, stats, cents = cv2.connectedComponentsWithStats(p["teeth"].astype(np.uint8))
    for i in range(1, len(stats)):                           # a padded boss on every tooth
        rb = 0.3 * min(stats[i, 2], stats[i, 3])
        H = np.where(tlab == i, H + 0.35 * np.sqrt(np.clip(1 - ((xx - cents[i][0]) ** 2 + (yy - cents[i][1]) ** 2) / rb ** 2, 0, 1)), H)
    phase = np.where(raised, dm, d)
    tx, ty = np.where(raised, mx, tx), np.where(raised, my, ty)
    row = np.floor(phase / ROW)
    lines = 0.5 + 0.5 * np.cos(2 * np.pi * phase / ROW)      # the rows of thread, a groove between each two
    along = xx * tx + yy * ty                                 # the place along a row, near enough for its stitches
    couch = gold & (d > CORD) & (np.cos(2 * np.pi * (along / TIE + 0.5 * row)) > 0.94) & (lines > 0.4)
    cord = gold & (d <= CORD)
    twist = 0.5 + 0.5 * np.cos(2 * np.pi * (along + d) / CORD)
    H = H + cord * 0.3 * np.sin(np.pi * np.clip(d, 0, CORD) / CORD) + gold * 0.09 * np.where(cord, twist, lines) ** 0.6
    pearl = np.zeros((S, S), bool)
    for (cx, cy), rp in p["pearls"]:                         # a pearl sewn into every node of the circuit
        dome = np.sqrt(np.clip(1 - ((xx - cx) ** 2 + (yy - cy) ** 2) / (0.8 * rp) ** 2, 0, 1))
        H = np.where(dome > 0, np.maximum(H, 0.35 + 0.4 * dome), H)
        pearl |= dome > 0
    return H, gold & ~pearl, tx, ty, np.where(cord, twist, lines), couch, pearl, d


def velvet(p, H, gold):
    """Deep crimson velvet: a fine pile and an uneven nap, lighter towards the upper left, pressed down beside the
    gold that is sewn into it, and in the shadow the raised gold casts to the lower right."""
    rng = np.random.default_rng(7)
    noise = lambda sigma: cv2.GaussianBlur(rng.standard_normal((S, S)).astype(np.float32), (0, 0), sigma) * sigma
    pile = 1 + 0.06 * noise(0.7) / 0.7 * 0.5 + 0.10 * np.tanh(noise(14) / 14 * 6) + 0.12 * np.tanh(noise(60) / 60 * 12)
    side = 0.72 + 0.4 * (1 - (p["xx"] + p["yy"]) / (2 * S))
    lift = cv2.GaussianBlur(np.roll(np.roll(H * gold, 12, 0), 10, 1), (0, 0), 7)
    shade = 1 - 0.7 * np.clip(lift * 2.2, 0, 1)
    out = cv2.distanceTransform((~gold).astype(np.uint8), cv2.DIST_L2, 5)
    pressed = 1 - 0.3 * np.exp(-out / 5)
    return VELVET * (pile * side * shade * pressed)[..., None]


def gilt(H, tx, ty, lines, couch, strength=110.0):
    """The gold threads' light: Lambert on the padded relief, the threads' own sheen, which is brightest where they
    lie across the light, the grooves between rows, the tying stitches darker; toned between the dark, middle and
    bright gold of the plate's goldwork."""
    gy, gx = np.gradient(cv2.GaussianBlur(H, (0, 0), 0.8))
    n = np.dstack([-gx * strength, -gy * strength, np.ones_like(H)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    L = np.array([-0.5, -0.65, 0.58])
    L /= np.linalg.norm(L)
    half = (L + [0, 0, 1]) / np.linalg.norm(L + [0, 0, 1])
    lam = np.clip(n @ L, 0, 1)
    across = np.clip(1 - (tx * half[0] + ty * half[1]) ** 2, 0, 1)
    sheen = across ** 30 * np.clip(n @ half, 0, 1) ** 4
    g = np.clip(0.12 + 0.85 * lam, 0, 1) * (0.42 + 0.58 * lines ** 0.7)
    tone = np.where(g[..., None] < 0.5, DARK + (MID - DARK) * (g / 0.5)[..., None],
                    MID + (BRIGHT - MID) * ((g - 0.5) / 0.5)[..., None])
    tone = tone * np.where(couch, 0.5, 1.0)[..., None]
    return tone + np.array([255, 244, 200], np.float32) * (0.9 * sheen * lines ** 2)[..., None], lam


def ruby(p, lam_flat):
    """The star as a cut ruby: each arm a ridge along its axis, its two facets tilted to either side and down to the
    tip, lit from the upper left; a bright sparkle near the middle."""
    ys, xs = np.nonzero(p["star"])
    cx, cy = xs.mean(), ys.mean()
    dx, dy = p["xx"] - cx, p["yy"] - cy
    horiz = np.abs(dx) >= np.abs(dy)
    nx = np.where(horiz, np.sign(dx) * 0.35, np.sign(dx) * 0.6)
    ny = np.where(horiz, np.sign(dy) * 0.6, np.sign(dy) * 0.35)
    n = np.dstack([nx, ny, np.ones_like(nx)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    L = np.array([-0.5, -0.65, 0.58]) / np.linalg.norm([-0.5, -0.65, 0.58])
    lam = np.clip(n @ L, 0, 1)
    sparkle = np.exp(-((dx + 0.08 * (xs.max() - xs.min())) ** 2 + (dy + 0.08 * (ys.max() - ys.min())) ** 2) / 60.0)
    return RUBY * (0.3 + 1.0 * lam)[..., None] + np.array([255, 200, 200], np.float32) * (0.9 * sparkle + 0.35 * lam ** 8)[..., None]


def main():
    p = parts()
    H, gold, tx, ty, lines, couch, pearl, d = embroidery(p)
    metal, lam = gilt(H, tx, ty, lines, couch)
    cloth = velvet(p, H, gold)
    pearls = PEARL * (0.25 + 0.8 * lam)[..., None]
    colour = np.where(gold[..., None], metal, np.where(pearl[..., None], pearls, cloth))
    colour = np.where(p["star"][..., None], ruby(p, lam), colour)
    alpha = cv2.GaussianBlur((p["ink"] > 64).astype(np.float32), (0, 0), 1.0)
    small = cv2.resize(colour.clip(0, 255), (SIZE, SIZE), interpolation=cv2.INTER_AREA)
    a = cv2.resize(alpha, (SIZE, SIZE), interpolation=cv2.INTER_AREA)
    drawn = np.dstack([small.round().astype(np.uint8), (a * 255).round().astype(np.uint8)])
    Image.fromarray(drawn).save(OUT)
    Image.fromarray(drawn).save(DRAWN)
    star = cv2.resize(p["star"].astype(np.float32), (SIZE, SIZE), interpolation=cv2.INTER_AREA)
    Image.fromarray((star * 255).round().astype(np.uint8)).save(STAR_MASK)
    inside = cv2.distanceTransform((star > 0.5).astype(np.uint8), cv2.DIST_L2, 5)
    t = np.clip((inside - CORE[0]) / (CORE[1] - CORE[0]), 0, 1)
    glow = cv2.GaussianBlur(t * t * (3 - 2 * t), (0, 0), 1.0)
    Image.fromarray((glow * 255).round().astype(np.uint8)).save(STAR)
    back = np.full((SIZE, SIZE, 3), 30, np.float32)
    shown = small * a[..., None] + back * (1 - a[..., None])
    crop = (slice(SIZE // 4, SIZE // 2 + SIZE // 4), slice(SIZE // 8, SIZE // 2 + SIZE // 8))
    plate = cv2.resize(cv2.resize(shown, (336, 336), interpolation=cv2.INTER_AREA), (SIZE, SIZE), interpolation=cv2.INTER_NEAREST)
    sheet = np.concatenate([shown, cv2.resize(shown[crop], (SIZE, SIZE), interpolation=cv2.INTER_CUBIC), plate], 1)
    Image.fromarray(sheet.clip(0, 255).astype(np.uint8)).resize((3 * 640, 640), Image.LANCZOS).save(
        os.path.join(ROOT, "wip", "preview", "sigilwheel.png"))
    print("SIGIL", OUT, STAR, "ring", round(p["r_in"]), round(p["r_foot"]), "pearls", len(p["pearls"]), "star pixels", int(p["star"].sum()))


# the owner: "you may use image generator to generate the sigil in a very w40k style": the generator paints over the
# drawn sigil in the scene's own surroundings; the star it may change is laid back from the drawing
W40K = ("A sacred emblem of the Adeptus Mechanicus in Warhammer 40,000, a heavy relic of the Machine God hanging in a dark "
        "gothic cathedral: a great cog wheel with sixteen square teeth of ancient gilded gold, deeply embossed with "
        "baroque filigree, tiny skulls and rivets, around a round disc of deep crimson velvet split down the middle; "
        "on the left half a gold relief of half a human brain with a red four-pointed star jewel set in it, on the "
        "right half gold circuit lines branching from the middle and ending in small rings with pearls. The gold is "
        "old, tarnished and dirty, blackened by centuries of candle soot and incense smoke, slightly charred, grime "
        "deep in every crevice, dull and disturbed, only the worn high points still catch the light; the velvet "
        "dusty and stained. Grimdark, ornate, sacred, lit warmly by candles, deep shadows, intricate detail")
DRAWN = os.path.join(ROOT, "wip", "gen", "sigil-drawn.png")
STAR_MASK = os.path.join(ROOT, "wip", "gen", "sigil-star.png")
PLACE = (2253, 178, 200)                 # where the sigil's disc stands in the plate (src/motion.py): x, y, radius in pixels


def surroundings():
    """The clean plate behind the sigil, the sigil's disc filling the square."""
    clean = np.asarray(Image.open(os.path.join(ROOT, "wip", "scene3d", "saint_clean.png")).convert("RGB"))
    x, y, r = PLACE
    M = np.array([[2 * r / SIZE, 0, x - r], [0, 2 * r / SIZE, y - r]], np.float32)
    return cv2.warpAffine(clean, M, (SIZE, SIZE), flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)


def sooted(rgb, seed=11):
    """The owner: "make it disturbed gold, slightly charred (or smoked)", "dirty gold": the drawn colours darkened by
    soot in broad patches, more towards the bottom where the candles' smoke rises against it, and dulled towards a
    brown black, before the generator paints over them."""
    rng = np.random.default_rng(seed)
    patches = sum(cv2.resize(rng.random((k, k)).astype(np.float32), (SIZE, SIZE), interpolation=cv2.INTER_CUBIC) / 2 ** i
                  for i, k in enumerate((5, 13, 40))) / 1.75
    rise = np.linspace(0.0, 1.0, SIZE, dtype=np.float32)[:, None] ** 1.5
    soot = np.clip(0.25 + 0.55 * smooth(0.35, 0.75, patches) + 0.3 * rise, 0, 0.85)[..., None]
    dull = rgb.mean(2, keepdims=True) * np.array([1.0, 0.82, 0.6], np.float32)
    return (rgb * (1 - 0.35 * soot) * 0.65 + dull * 0.35 * (1 - 0.35 * soot)) * (1 - 0.55 * soot)


def generate(strengths=(45, 55), seeds=(1, 2)):
    """Candidates: the generator over the drawn sigil in its surroundings, allowed a little beyond its teeth;
    wip/gen/sigil-gen-<strength>-<seed>.png and the sheet wip/preview/sigil-generated.png."""
    import torch
    from diffusers import ZImageInpaintPipeline
    pipe = ZImageInpaintPipeline.from_pretrained("Tongyi-MAI/Z-Image-Turbo", torch_dtype=torch.bfloat16).to("cuda")
    drawn = np.asarray(Image.open(DRAWN)).astype(np.float32)
    a = drawn[..., 3:] / 255
    base = (sooted(drawn[..., :3]) * a + surroundings() * (1 - a)).round().astype(np.uint8)
    mask = cv2.dilate((a[..., 0] > 0.5).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41))) * 255
    tiles = []
    for st in strengths:
        row = []
        for seed in seeds:
            gen = np.asarray(pipe(prompt=W40K, image=Image.fromarray(base), mask_image=Image.fromarray(mask), strength=st / 100,
                                  height=SIZE, width=SIZE, num_inference_steps=9, guidance_scale=0.0,
                                  generator=torch.Generator("cuda").manual_seed(seed)).images[0])
            Image.fromarray(gen).save(os.path.join(ROOT, "wip", "gen", f"sigil-gen-{st}-{seed}.png"))
            row.append(cv2.resize(gen, (512, 512), interpolation=cv2.INTER_AREA))
            print("GENERATED", st, seed, flush=True)
        tiles.append(np.concatenate(row, 1))
    Image.fromarray(np.concatenate(tiles, 0)).save(
        os.path.join(ROOT, "wip", "preview", "sigil-generated.png"))


def choose(name):
    """A candidate as the sigil: where it differs from the surroundings, inside the drawn outline grown a little,
    is the sigil (its alpha); the drawn ruby star is laid back where the red light shines."""
    gen = np.asarray(Image.open(os.path.join(ROOT, "wip", "gen", name)).convert("RGB")).astype(np.float32)
    drawn = np.asarray(Image.open(DRAWN)).astype(np.float32)
    inside = drawn[..., 3] / 255 > 0.5
    grown = cv2.dilate(inside.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41))).astype(bool)
    differs = np.abs(gen - surroundings().astype(np.float32)).max(2) > 40
    shape = cv2.morphologyEx((differs & grown | inside).astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    shape = cv2.morphologyEx(shape, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    alpha = cv2.GaussianBlur(shape.astype(np.float32), (0, 0), 1.0)
    star = np.asarray(Image.open(STAR_MASK)).astype(np.float32)[..., None] / 255
    star = cv2.dilate(star, np.ones((3, 3), np.uint8))[..., None]
    colour = gen * (1 - star) + sooted(drawn[..., :3]) * star
    Image.fromarray(np.dstack([colour, alpha * 255]).clip(0, 255).round().astype(np.uint8)).save(OUT)
    print("CHOSEN", name, "->", OUT)


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1:] or ["draw"]
    {"motifs": motifs, "draw": main, "generate": generate, "choose": lambda: choose(cmd[1])}[cmd[0]]()
