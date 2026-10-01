"""Fabric textures generated with Z-Image-Turbo (Tongyi-MAI, Apache-2.0):
crimson velvet with gold goldwork, the Cog Mechanicum, Latin, and the wear
of centuries. Each job writes its candidates to wip/gen/<stem>_<seed>.png
(skipped when present); `apply` turns the chosen one into resources/assets/<stem>.png
and its gold mask resources/assets/<stem>_gold.png, the pair embroidered() reads in
src/mechanicum.py. Parchments stay with src/textures.py, whose Latin is exact.

Run with the project's ML venv, GPU chosen by nvidia-smi index:
    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 \\
        .venv-moge/bin/python src/gentextures.py gen antependium
    .venv-moge/bin/python src/gentextures.py apply antependium 3
"""
import os, sys
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "resources", "assets")
GEN = os.path.join(ROOT, "wip", "gen")

STYLE = ("grimdark gothic Warhammer 40,000 Adeptus Mechanicus relic, centuries old and heavily worn: "
         "threadbare patches where the velvet pile is rubbed away, moth holes, dark candle soot and grime "
         "worked into the cloth, drips of old wax, brown water stains, the gold thread tarnished dark and "
         "broken in places, frayed and darned edges, dust in the pile. Museum textile scan, flat frontal "
         "orthographic view, evenly lit, no shadows, no background: the textile fills the whole frame edge to edge")

JOBS = {
    # stem: (width, height, prompt)
    "antependium": (1536, 832,
        "An antique altar frontal hanging of deep crimson silk velvet covered in dense raised gold goldwork "
        "embroidery: in the centre a large gold cog wheel enclosing a skull that is half bone and half machine "
        "with a round lens eye, two smaller cog-skull emblems to the left and right, beneath them the Latin "
        "motto embroidered in gold capitals, spelled exactly: 'IN CALCULO SALVATIO', an ornate gold border of scrollwork, "
        "filigree, gears and small skulls, a heavy gold bullion fringe along the bottom edge. " + STYLE),
    "drape": (832, 2048,
        "A tall crimson velvet curtain panel: a tone-on-tone damask pattern of small cogs and skulls woven into "
        "the velvet, a wide band of dense gold goldwork embroidery down both long edges with scrollwork, gears "
        "and tiny skulls, above the hem a band of Latin in gold capitals, spelled exactly: "
        "'DEUS IN MACHINA', and a gold bullion fringe along the bottom edge. " + STYLE),
}
# the model cannot spell CALCULUM (nine drafts of "CALCILUM"), so banner 0 carries AVE OMNISSIAH
for n, words in enumerate(("AVE OMNISSIAH", "LABOR FIDES MACHINA AETERNA", "IN CALCULO SALVATIO",
                           "DEUS IN MACHINA", "OMNISSIAH VULT", "SCIENTIA AD ASTRA")):
    JOBS[f"banner_{n}"] = (704, 1936,
        "A tall vertical processional banner of crimson velvet filling the frame: at the top a gold embroidered "
        "Cog Mechanicum, a cog wheel enclosing a skull that is half bone and half machine with a round lens eye; "
        "below it the Latin motto in large gold capitals, one word per line, spelled exactly: '" + words + "'; "
        "a gold border of scrollwork and gears, small cog-skull devices, a gold bullion fringe at the bottom. " + STYLE)
for n, words in enumerate(("OMNISSIAH VULT", "AVE OMNISSIAH")):
    JOBS[f"hanging_{n}"] = (1024, 1120,
        "A crimson velvet altar hanging filling the frame: a large gold embroidered Cog Mechanicum, a cog wheel "
        "enclosing a skull that is half bone and half machine with a round lens eye, above it the Latin words in "
        "gold capitals, spelled exactly: '" + words + "', a gold scrollwork border, a gold fringe at the bottom. " + STYLE)

METAL = ("grimdark gothic Warhammer 40,000 Adeptus Mechanicus relic, centuries old: black grime packed into every "
         "recess, soot, verdigris and rust blooms, the raised edges worn bright, fine scratches. Flat frontal "
         "orthographic view, evenly lit, no shadows, no background: the object fills the whole frame edge to edge")
PLAQUES = [("IN CALCULO", "SALVATIO"), ("DEUS EX", "MACHINA"), ("SANCTUM", "SILICIUM"), ("AVE", "OMNISSIAH"),
           ("MACHINA", "VULT"), ("FIDES IN", "NUMERIS"), ("SPIRITUS", "MACHINAE"), ("PRO", "OMNISSIAH"),
           ("OMNIS", "COMPUTAT"), ("NIHIL SINE", "CALCULO"), ("CALCULUS", "SANCTUS"), ("MEMORIA", "AETERNA")]
for n, (a, b) in enumerate(PLAQUES):
    JOBS[f"plaque_{n:02d}"] = (1024, 512,
        "A blackened iron plaque with a gothic moulded frame, rivets and small cogs at the corners, the Latin "
        "words cast in raised capitals in two lines, spelled exactly: '" + a + "' and '" + b + "', beside them "
        "a small Cog Mechanicum, a cog wheel enclosing a half-machine skull. " + METAL)
for n, what in enumerate((
        "a row of pointed gothic arch niches, each holding a small robed and hooded tech-priest statue, with "
        "tracery, crockets and pinnacles between them",
        "gothic tracery panels of quatrefoils and trefoils, interlocking cog wheels, small skulls and bands "
        "of binary code and Latin script",
        "stacked gothic ornament: a frieze of skulls, a band of cogs, pointed arch panels with cog-skull "
        "emblems, rivets and pipes")):
    JOBS[f"relief_{n}"] = (1024, 1024, "A bas-relief wall panel of blackened pewter and iron: " + what + ". " + METAL)
GLASS = ("tall gothic lancet stained glass window with a pointed arch top, filling the whole frame: thick black "
         "lead cames between hundreds of small pieces of glass in cobalt blue, ruby red, amber gold, violet and "
         "emerald, strongly backlit and glowing, painted details on the glass, grime and soot at the edges of the "
         "panes, Warhammer 40,000 Adeptus Mechanicus cathedral, flat frontal view, no frame, no wall")
for n, what in enumerate((
        "a towering tech-priest saint of the Omnissiah in crimson robes with a mechanical skull face and a glowing "
        "green lens, arms raised, a great cog halo and a golden sunburst behind the head, planets and stars around, "
        "small red-robed acolytes kneeling at the feet",
        "the Machine God as a radiant golden figure holding a glowing computing engine, a cog wheel halo, rays of "
        "light, servo-skulls and cherubs around, hooded tech-priests praying below",
        "a hooded Magos of the Adeptus Mechanicus holding up a sacred graphics card that radiates light, a cog "
        "halo, circuit patterns and binary code in the borders, a Cog Mechanicum emblem at the base")):
    JOBS[f"window_{n}"] = (768, 1792, "A " + GLASS + ", depicting " + what + ".")
SURFACE = ("seamless tileable texture, flat top-down photograph, evenly lit, no shadows, no perspective, "
           "no objects, the surface fills the whole frame")
for stem, what in (
        ("mat_steel", "heavily worn gunmetal steel plate: fine scratches in all directions, scuffs, black grime in "
                      "streaks, small dents, specks of orange rust, oily smudges"),
        ("mat_brass", "old tarnished brass: dark brown tarnish with patches of bright worn gold brass, green "
                      "verdigris in spots, fine scratches, grime"),
        ("mat_skin", "pale weathered human skin of an old sick man: visible pores, fine wrinkles, blue-purple veins, "
                     "yellowish and red blotches, small scars and scabs, grime rubbed in"),
        ("mat_wool", "coarse hand-woven dark oxblood red wool cloth: visible weave, pilling, frayed threads, dust, "
                     "grease stains and soot, darker worn patches")):
    JOBS[stem] = (1024, 1024, "A " + SURFACE + " of " + what + ".")

PIPE = None


def generate(stem, seeds=(1, 2, 3, 4)):
    import torch
    from diffusers import ZImagePipeline
    os.makedirs(GEN, exist_ok=True)
    todo = [s for s in seeds if not os.path.exists(os.path.join(GEN, f"{stem}_{s}.png"))]
    if not todo:
        return
    global PIPE
    if PIPE is None:
        PIPE = ZImagePipeline.from_pretrained("Tongyi-MAI/Z-Image-Turbo", torch_dtype=torch.bfloat16).to("cuda")
    pipe = PIPE
    w, h, prompt = JOBS[stem]
    for s in todo:
        im = pipe(prompt=prompt, width=w, height=h, num_inference_steps=9, guidance_scale=0.0,
                  generator=torch.Generator("cuda").manual_seed(s)).images[0]
        im.save(os.path.join(GEN, f"{stem}_{s}.png"))
        print("wrote", stem, s, flush=True)


def gold_mask(im):
    """White where the image shows gold: warm hue, some saturation, bright
    enough to be metal thread rather than brown grime."""
    hsv = np.asarray(im.convert("HSV")).astype(float) / 255
    hue, sat, val = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
    m = np.clip((sat - 0.25) / 0.2, 0, 1) * np.clip((val - 0.30) / 0.2, 0, 1) * ((hue > 22) & (hue < 60))
    return Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))


# Latin on sanctified calculation, stitched exactly (the model misspells)
# over the plain velvet the drafts leave between motto and fringe
SANCTA = ["SANCTA EST OMNIS COMPUTATIO", "BENEDICTUS SIT CALCULUS", "NUMERI NON MENTIUNTUR",
          "SANCTIFICETUR COMPUTATIO", "IN CALCULO SALVATIO", "OMNISSIAH OMNIA COMPUTAT",
          "PER CALCULUM AD ASTRA", "FIDES IN NUMERIS", "IN NUMERO VERITAS", "NIHIL SINE CALCULO",
          "SUMMA SANCTA EST", "COMPUTATIO SACRA"]
LATIN = {"banner_0": SANCTA[0:3:2], "banner_1": SANCTA[1:3], "banner_2": SANCTA[3:5], "banner_3": SANCTA[5:8:2],
         "banner_4": SANCTA[10:5:-4], "banner_5": SANCTA[11:8:-2], "drape": SANCTA[:8],
         "hanging_0": SANCTA[8:10], "hanging_1": SANCTA[0:2]}
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"


def plain_rows(g, alpha):
    """The widest band of plain velvet: columns inside the gold side borders,
    rows below the top sixth with almost no gold across that span."""
    col = (g * (alpha > 0.5)).mean(0)
    w = len(col)
    x0 = x1 = w // 2
    while x0 > 0 and col[x0 - 1] < 0.42:
        x0 -= 1
    while x1 < w - 1 and col[x1 + 1] < 0.42:
        x1 += 1
    if x1 - x0 < w // 3:                         # no plain span: the design fills the cloth
        return 0, 0, 0, 0
    x0, x1 = x0 + (x1 - x0) // 14, x1 - (x1 - x0) // 14
    row = np.convolve((g[:, x0:x1] > 0.3).mean(1) + (alpha[:, x0:x1] < 0.5).mean(1), np.ones(9) / 9, "same")
    best, y = (0, 0, 0), g.shape[0] // 30
    while y < g.shape[0]:
        if row[y] < 0.02:
            e = y
            while e < g.shape[0] and row[e] < 0.02:
                e += 1
            best = max(best, (e - y, y, e))
            y = e
        y += 1
    n, y0, y1 = best
    pad = max(n // 14, 40)
    return x0, y0 + pad, x1, y1 - pad


def stitch(im, g, phrases, seed=0):
    """Gold couched embroidery of `phrases` over the plain velvet of `im`
    (RGBA), written into the gold mask `g` too, so the shader raises it and
    makes it metal: satin ridges, a dark couching cord at the edges, a
    shadow on the pile below, tarnish, and stitches worn through."""
    from PIL import ImageDraw, ImageFont
    import cv2
    rgb = np.asarray(im.convert("RGB")).astype(float) / 255
    alpha = np.asarray(im.getchannel("A")).astype(float) / 255
    x0, y0, x1, y1 = plain_rows(g, alpha)
    if y1 - y0 < 120:
        return g
    lines = []                                   # one or two words a line, a gap between phrases
    for ph in phrases:
        words, cur = ph.split(), ""
        for wd in words:
            if cur and len(cur) + 1 + len(wd) > 11:
                lines.append(cur)
                cur = wd
            else:
                cur = f"{cur} {wd}".strip()
        lines += [cur, None]
    lines = lines[:-1]
    probe = ImageFont.truetype(SERIF, 100)
    widest = max(probe.getlength(t) for t in lines if t)
    rows = sum(1.25 if t else 0.8 for t in lines)
    size = int(min(100 * 0.9 * (x1 - x0) / widest, (y1 - y0) / rows / 0.95, 110))
    font = ImageFont.truetype(SERIF, size)
    M = Image.new("L", im.size, 0)
    d = ImageDraw.Draw(M)
    bold = max(1, size // 22)                    # padded satin stitch is fatter than the type
    y = y0 + ((y1 - y0) - rows * size * 0.95) / 2
    for t in lines:
        if t is None:                            # a small gold lozenge between phrases
            cx, cy, r = (x0 + x1) / 2, y + size * 0.36, size * 0.13
            d.polygon([(cx - r, cy), (cx, cy - r), (cx + r, cy), (cx, cy + r)], fill=255)
            for s in (-1, 1):
                d.line([(cx + s * r * 2, cy), (cx + s * r * 5, cy)], fill=255, width=max(2, size // 20))
            y += size * 0.95 * 0.8
            continue
        d.text(((x0 + x1) / 2, y), t, font=font, fill=255, anchor="mt", stroke_width=bold, stroke_fill=255)
        y += size * 0.95 * 1.25
    m = np.asarray(M).astype(float) / 255
    rng = np.random.default_rng(seed)
    h, w = m.shape
    yy, xx = np.mgrid[0:h, 0:w]
    satin = 0.5 + 0.5 * np.sin((xx * 0.8 + yy * 0.6) * 2 * np.pi / 2.3 + rng.random((h, w)) * 1.2)
    low = cv2.resize(rng.random((h // 48 + 2, w // 48 + 2)), (w, h), interpolation=cv2.INTER_CUBIC)
    tarnish = np.clip(0.7 + 0.5 * low, 0.65, 1.0)
    worn = cv2.resize(rng.random((h // 6 + 2, w // 6 + 2)), (w, h), interpolation=cv2.INTER_NEAREST) < 0.035
    base = rgb[g > 0.8].mean(0) if (g > 0.8).any() else np.array([0.78, 0.58, 0.22])
    # the padding under the satin raises each stroke: lit on its upper left, shaded lower right
    hgt = cv2.GaussianBlur(m, (0, 0), size / 22 + 0.5)
    gy, gx = np.gradient(hgt)
    shade = 1 + 1.6 * (0.6 * gx + 0.8 * gy) / (np.abs(0.6 * gx + 0.8 * gy).max() + 1e-6)
    thread = base * 1.25 * (0.8 + 0.3 * satin[..., None]) * tarnish[..., None] * shade[..., None]
    thread = np.clip(thread, 0, 1)
    core = cv2.erode(m, np.ones((3, 3), np.uint8), iterations=max(1, size // 40))
    cord = np.clip(m - core, 0, 1)
    thread = thread * (1 - 0.55 * cord[..., None])
    shadow = cv2.GaussianBlur(np.roll(m, (size // 18 + 2, size // 30 + 1), (0, 1)), (0, 0), size / 30 + 1)
    m = m * ~worn
    out = rgb * (1 - 0.6 * shadow[..., None])
    out = out * (1 - m[..., None]) + thread * m[..., None]
    im.paste(Image.fromarray((out * 255).astype(np.uint8)), (0, 0))
    return np.maximum(g, m * np.clip(tarnish + 0.2, 0, 1))


# the drafts chosen by eye: correct Latin, richest work. Plaques with a
# misspelt word are left out and the good ones repeat.
CHOICES = {"antependium": 6, "banner_0": 10, "banner_1": 1, "banner_2": 1, "banner_3": 2, "banner_4": 2,
           "banner_5": 3, "hanging_0": 1, "hanging_1": 1, "drape": 5,
           "relief_0": 1, "relief_1": 2, "relief_2": 1, "window_0": 1, "window_1": 1, "window_2": 2,
           "mat_steel": 3, "mat_brass": 1, "mat_skin": 3, "mat_wool": 2}
GOOD_PLAQUES = [("plaque_03", 1), ("plaque_04", 1), ("plaque_06", 1), ("plaque_07", 1), ("plaque_11", 1),
                ("plaque_02", 1), ("plaque_03", 2), ("plaque_04", 2), ("plaque_07", 2), ("plaque_11", 2),
                ("plaque_02", 2), ("plaque_07", 1)]


def cutout(im):
    """RGBA: the studio backdrop around the textile (pale, unsaturated, joined
    to the image border) becomes transparent, so tabs and fringe strands
    stand free; then cropped to what is left."""
    import cv2
    hsv = np.asarray(im.convert("HSV")).astype(float) / 255
    cand = ((hsv[..., 1] < 0.18) & (hsv[..., 2] > 0.55)).astype(np.uint8)
    h, w = cand.shape
    bg = np.zeros((h + 2, w + 2), np.uint8)
    for x, y in [(x, 0) for x in range(0, w, 8)] + [(x, h - 1) for x in range(0, w, 8)] + \
                [(0, y) for y in range(0, h, 8)] + [(w - 1, y) for y in range(0, h, 8)]:
        if cand[y, x] and not bg[y + 1, x + 1]:
            cv2.floodFill(cand, bg, (x, y), 2, flags=4 | (255 << 8) | cv2.FLOODFILL_MASK_ONLY)
    alpha = np.where(bg[1:-1, 1:-1] > 0, 0, 255).astype(np.uint8)
    alpha[: h // 18][cand[: h // 18] > 0] = 0                   # the gaps between hanging tabs, closed off by the rod
    alpha = cv2.GaussianBlur(alpha, (3, 3), 0)
    out = im.convert("RGB")
    out.putalpha(Image.fromarray(alpha))
    ys, xs = np.nonzero(alpha > 128)
    return out.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))


def apply(stem, seed, size=None, out=None, cut=True):
    im = Image.open(os.path.join(GEN, f"{stem}_{seed}.png")).convert("RGB")
    im = cutout(im) if cut else im
    if stem.startswith("mat_"):                  # surface swatches come framed like a plate: keep the middle
        w, h = im.size
        im = im.crop((w // 8, h // 8, w - w // 8, h - h // 8))
    if size:
        im = im.resize(size, Image.LANCZOS)
    g = np.asarray(gold_mask(im.convert("RGB"))).astype(float) / 255
    if stem in LATIN:
        g = stitch(im, g, LATIN[stem], seed)
    im.save(os.path.join(A, f"{out or stem}.png"))
    Image.fromarray((g * 255).astype(np.uint8)).save(os.path.join(A, f"{out or stem}_gold.png"))


def apply_all():
    for stem, seed in CHOICES.items():
        apply(stem, seed, cut=not stem.startswith(("relief", "window", "mat_")))
    for n, (stem, seed) in enumerate(GOOD_PLAQUES):
        apply(stem, seed, out=f"plaque_{n:02d}", cut=False)


if __name__ == "__main__":
    cmd, stem = sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "all"
    if cmd == "apply" and stem == "all":
        apply_all()
    elif cmd == "gen":
        for st in (JOBS if stem == "all" else [stem]):
            generate(st, tuple(int(a) for a in sys.argv[3:]) or (1, 2, 3, 4))
    else:
        apply(stem, int(sys.argv[3]))
