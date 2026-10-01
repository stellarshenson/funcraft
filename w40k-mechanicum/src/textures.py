"""Generate the flat artwork the scene uses as image textures.

Run after src/emblem.py:
    python3 src/textures.py

Writes to resources/assets/:
  banner_<n>.png   red velvet banners: gold border, the medallion, a motto,
                   a swallowtail with a gold fringe (shape in the alpha channel)
  plaque.png       engraved motto on dark iron, for the altar
  screen_<k>.png   the altar screen, one image per compute tick (10): a
                   scrolling column of hex and "CALCULATING" with k % 5 dots,
                   so state 10 would equal state 0 and the loop closes
"""
import math, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "resources", "assets")
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SERIF_IT = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
MONO = "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"
GOLD = (222, 176, 92)
GOLD_DK = (150, 104, 44)
TICKS = 10

MOTTOS = [
    (["OMNIA", "PER", "CALCULUM"], ["Ave Omnissiah,", "spiritus machinae", "benedic nobis"]),
    (["LABOR", "FIDES", "MACHINA", "AETERNA"], ["Et machina dedit", "calculum aeternum"]),
    (["IN CALCULO", "SALVATIO"], ["Silicium sanctum", "ex tenebris", "ad lucem perducit"]),
    (["DEUS IN", "MACHINA"], ["Sancta machina,", "ora pro nobis"]),
    (["OMNISSIAH", "VULT"], ["Gloria Omnissiah", "in saecula", "saeculorum"]),
    (["SCIENTIA", "AD ASTRA"], ["Per calculum", "ad astra, per fidem", "ad victoriam"]),
]

PRAYERS = [
    ["Ave Omnissiah,", "spiritus machinae,", "benedic calculo", "nostro.", "", "Libera nos", "a errore", "et a calore.", "Amen."],
    ["Sancta machina,", "ora pro nobis.", "", "Deus in silicio,", "miserere nobis.", "", "Omnissiah vult."],
    ["Fides et calculus", "unum sunt.", "", "Ex numeris", "veritas,", "ex veritate", "salus.", "", "+++"],
    ["Per calculum", "ad astra.", "", "Machina aeterna,", "custodi nos", "in tenebris.", "Amen."],
]

FRIEZE = ["OMNISSIAH VULT", "DEUS IN MACHINA", "SPIRITUS MACHINAE LAUDETUR", "IN CALCULO SALVATIO",
          "SCIENTIA POTENTIA EST", "AVE OMNISSIAH"]


def velvet(w, h, seed):
    rnd = random.Random(seed)
    im = Image.new("RGB", (w, h), (112, 14, 11))
    px = im.load()
    streak = [rnd.uniform(-1, 1) for _ in range(w)]
    for x in range(1, w):
        streak[x] = 0.85 * streak[x - 1] + 0.15 * streak[x]
    for y in range(h):
        for x in range(w):
            v = 1.0 + 0.16 * streak[x] + rnd.uniform(-0.035, 0.035)
            px[x, y] = tuple(max(0, min(255, int(c * v))) for c in (112, 14, 11))
    return im


def cog(d, cx, cy, r, teeth, fill, hole=0.45, bg=None):
    """A gear outline: `teeth` square teeth around a disc with a round hole."""
    pts = []
    for k in range(teeth * 4):
        a = 2 * math.pi * k / (teeth * 4)
        rr = r if (k % 4) in (1, 2) else r * 0.82
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=fill)
    if bg is not None:
        d.ellipse([cx - r * hole, cy - r * hole, cx + r * hole, cy + r * hole], fill=bg)


def device(im, g, cx, cy, size):
    """The Cog Mechanicum in gold relief (resources/assets/emblem.png, rendered from the
    medallion model by src/emblem.py) centred at (cx, cy), `size` across; its
    alpha goes into the gold mask image `g` when one is given."""
    emb = Image.open(os.path.join(A, "emblem.png")).convert("RGBA").resize((size, size), Image.LANCZOS)
    im.paste(emb, (int(cx - size / 2), int(cy - size / 2)), emb)
    if g is not None:
        a = emb.getchannel("A")
        g.paste(Image.new("L", (size, size), 255), (int(cx - size / 2), int(cy - size / 2)), a)


def stitch(im, mask, seed):
    """Make the gold areas look embroidered: fine diagonal thread lines, each
    stitch row a little brighter or darker, on top of the flat gold."""
    a = np.asarray(im).astype(float)
    m = np.asarray(mask).astype(float)[..., None] / 255.0
    h, w = m.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    thread = 0.78 + 0.22 * np.sin((xx + yy) * 1.9) ** 2
    rng = np.random.default_rng(seed)
    rows = rng.uniform(0.85, 1.15, size=(h // 3 + 1, 1))
    band = np.repeat(rows, 3, axis=0)[:h]
    shade = (thread * band)[..., None]
    out = a * (1 - m) + a * shade * m
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def banner(n, motto, verse, w=640, h=1760):
    """A red velvet banner embroidered in gold: patterned border, corner cogs,
    the medallion in a sunburst, the motto, a Latin verse, a cog-skull device,
    a swallowtail with a fringe. Also writes banner_<n>_gold.png, white where
    the embroidery is, for the metal and bump of the material."""
    im = velvet(w, h, n)
    gold = Image.new("L", (w, h), 0)
    d, g = ImageDraw.Draw(im), ImageDraw.Draw(gold)

    def both(fn, *args, **kw):
        getattr(d, fn)(*args, **kw)
        kw = {k: (255 if k in ("fill", "outline") and v is not None else v) for k, v in kw.items()}
        getattr(g, fn)(*args, **kw)

    tail = 190
    body = h - tail
    # border: a broad band of lozenges between two lines, following the swallowtail
    outline = [(22, 22), (w - 22, 22), (w - 22, h - 70), (w // 2, body - 10), (22, h - 70), (22, 22)]
    both("line", outline, fill=GOLD, width=5, joint="curve")
    inner = [(52, 52), (w - 52, 52), (w - 52, h - 110), (w // 2, body - 52), (52, h - 110), (52, 52)]
    both("line", inner, fill=GOLD_DK, width=3, joint="curve")
    for (x0, y0), (x1, y1) in zip(outline[:-1], outline[1:]):
        ln = math.hypot(x1 - x0, y1 - y0)
        for k in range(int(ln // 26)):
            t = (k + 0.5) * 26 / ln
            cx = x0 + (x1 - x0) * t + (15 if x0 == x1 == 22 else -15 if x0 == x1 else 0)
            cy = y0 + (y1 - y0) * t + (15 if y0 == y1 == 22 else 0)
            if x0 != x1 and y0 != y1:                    # the slanted tail edges
                cy -= 15
            both("polygon", [(cx, cy - 8), (cx + 6, cy), (cx, cy + 8), (cx - 6, cy)], fill=GOLD)
    for cx, cy in ((37, 37), (w - 37, 37)):
        cog(d, cx, cy, 26, 10, GOLD, bg=(112, 14, 11))
        cog(g, cx, cy, 26, 10, 255, bg=0)
    # the medallion in an embroidered sunburst
    cx, cy = w // 2, 300
    for k in range(48):
        a = 2 * math.pi * k / 48
        r0, r1 = 190, 250 if k % 2 == 0 else 225
        both("line", [(cx + r0 * math.cos(a), cy + r0 * math.sin(a)), (cx + r1 * math.cos(a), cy + r1 * math.sin(a))],
             fill=GOLD, width=4)
    both("ellipse", [cx - 196, cy - 196, cx + 196, cy + 196], outline=GOLD, width=6)
    emb = Image.open(os.path.join(A, "emblem.png")).convert("RGBA").resize((360, 360), Image.LANCZOS)
    im.paste(emb, (cx - 180, cy - 180), emb)
    g.ellipse([cx - 178, cy - 178, cx + 178, cy + 178], fill=200)
    # the motto
    font = ImageFont.truetype(SERIF, 70 if max(len(s) for s in motto) < 9 else 58)
    y = 590
    for line in motto:
        tw = d.textlength(line, font=font)
        d.text(((w - tw) / 2 + 3, y + 3), line, font=font, fill=(40, 4, 3))
        both("text", ((w - tw) / 2, y), line, font=font, fill=GOLD)
        y += 92
    # a divider, then a verse in italic
    both("line", [(120, y + 20), (w - 120, y + 20)], fill=GOLD_DK, width=3)
    cog(d, w // 2, y + 20, 16, 8, GOLD, bg=(112, 14, 11))
    cog(g, w // 2, y + 20, 16, 8, 255, bg=0)
    vfont = ImageFont.truetype(SERIF_IT, 34)
    y += 60
    for line in verse:
        tw = d.textlength(line, font=vfont)
        both("text", ((w - tw) / 2, y), line, font=vfont, fill=(214, 170, 96))
        y += 44
    # a cog-skull device above the tail
    cy2 = min(y + 110, body - 150)
    device(im, gold, w // 2, cy2, 170)
    im = stitch(im, gold, n)
    # alpha: rectangle with a swallowtail notch, fringe tassels along the edges
    alpha = Image.new("L", (w, h), 0)
    ad = ImageDraw.Draw(alpha)
    ad.polygon([(0, 0), (w, 0), (w, h), (w // 2, body), (0, h)], fill=255)
    d = ImageDraw.Draw(im)
    rnd = random.Random(100 + n)
    for x in range(0, w, 7):
        edge = h - abs(x - w / 2) / (w / 2) * tail
        ln = rnd.randint(30, 48)
        ad.line([(x, edge - 6), (x + rnd.uniform(-2, 2), edge + ln)], fill=255, width=4)
        d.line([(x, edge - 30), (x, edge + ln)], fill=GOLD if x % 14 else GOLD_DK, width=4)
        g.line([(x, edge - 30), (x, edge + ln)], fill=255, width=4)
    im.putalpha(alpha)
    im.save(os.path.join(A, f"banner_{n}.png"))
    gold.save(os.path.join(A, f"banner_{n}_gold.png"))


LITANY = ["Ave Omnissiah", "Deus in Machina", "Spiritus machinae, audi nos", "A calore, libera nos",
          "A fractura, libera nos", "Ab errore numeri, libera nos", "Per lucem cogitationis", "Sanctus calculus",
          "Gloria Machinae", "In silicio fides", "Fiat computatio", "Ora pro nobis", "Laudetur Machina",
          "Ex nihilo, numerus", "Omnia per calculum", "Benedicta sit ventilatio", "Mens in metallo",
          "Oleum sanctum, unge nos", "Et in terra calculus", "Semper fidelis Machinae"]


def parchment(n, lines, w=256, h=1024):
    """A strip of aged parchment for the purity seals, written from top to
    bottom: the prayer `lines`, then the litany, in brown ink with red
    rubrics, cog marks and a line of binary; foxed, water-stained, creased,
    darkened at the edges, torn at the foot and ragged at the sides."""
    rng = np.random.default_rng(300 + n)
    rnd = random.Random(300 + n)
    yy, xx = np.mgrid[0:h, 0:w]
    base = np.array((218, 196, 150), float)
    low = Image.fromarray(((rng.normal(0, 1, (h // 32 + 1, w // 32 + 1)) + 4) * 32).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    tone = 1.0 + 0.06 * (np.asarray(low, float) / 32 - 4)
    tone += 0.03 * rng.normal(0, 1, (h, w))
    edge = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy))
    tone *= 0.72 + 0.28 * np.clip(edge / 22.0, 0, 1)
    for _ in range(3):                                           # water stains: darker rings
        cx, cy, r = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(30, 90)
        d = np.hypot(xx - cx, (yy - cy) * 0.8)
        tone *= 1 - 0.10 * np.exp(-((d - r) / 5.0) ** 2) - 0.05 * (d < r)
    for cy in range(h // 4, h, h // 4):                           # fold creases
        tone *= 1 - 0.08 * np.exp(-((yy - cy - rng.uniform(-8, 8)) / 2.5) ** 2)
    a = base[None, None, :] * tone[..., None]
    for _ in range(90):                                          # foxing
        cx, cy, r = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(1.5, 5.0)
        m = np.hypot(xx - cx, yy - cy) < r
        a[m] *= (0.78, 0.66, 0.52)
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(SERIF_IT, 22)
    fr = ImageFont.truetype(SERIF, 21)
    fm = ImageFont.truetype(MONO, 15)
    ink, red = (58, 30, 18), (130, 18, 12)
    text = list(lines) + [""] + [rnd.choice(LITANY) for _ in range(40)]
    y, k = 16, 0
    while y < h - 60:
        line = text[k % len(text)]
        k += 1
        if not line:
            cog(d, w // 2, y + 12, 11, 8, red, bg=tuple(int(c) for c in base * 0.95))
            y += 30
            continue
        if k % 7 == 1:                                           # a red rubric
            d.text((12 + rnd.randint(0, 6), y), "+ " + line + " +", font=fr, fill=red)
        elif k % 11 == 5:
            d.text((12, y + 4), " ".join(f"{rnd.randrange(256):08b}" for _ in range(2)), font=fm, fill=ink)
        else:
            shade = rnd.uniform(0.75, 1.15)
            d.text((12 + rnd.randint(0, 8), y), line, font=f, fill=tuple(int(c * shade) for c in ink))
        y += 31
    # torn foot, ragged sides
    alpha = Image.new("L", (w, h), 255)
    ad = ImageDraw.Draw(alpha)
    ad.polygon([(0, h)] + [(x, h - rnd.randint(0, 40)) for x in range(0, w + 1, 10)] + [(w, h)], fill=0)
    for yy0 in range(0, h, 14):
        ad.rectangle([0, yy0, rnd.randint(0, 4), yy0 + 14], fill=0)
        ad.rectangle([w - rnd.randint(1, 5), yy0, w, yy0 + 14], fill=0)
    im.putalpha(alpha)
    im.save(os.path.join(A, f"parchment_{n}.png"))


def drape(w=512, h=2048):
    """Velvet for the altar drapes: a tone-on-tone damask of cogs, gold
    embroidered bands down both edges and along the hem. Writes drape.png and
    drape_gold.png."""
    im = velvet(w, h, 42)
    gold = Image.new("L", (w, h), 0)
    d, g = ImageDraw.Draw(im), ImageDraw.Draw(gold)
    dark = (84, 9, 7)
    for row, y in enumerate(range(60, h, 120)):
        for x in range(60 + (row % 2) * 60, w, 120):
            cog(d, x, y, 30, 10, dark, bg=(112, 14, 11))
            d.polygon([(x, y - 52), (x + 10, y - 40), (x, y - 28), (x - 10, y - 40)], fill=dark)
    for x0 in (14, w - 44):
        d.rectangle([x0, 0, x0 + 30, h], fill=GOLD_DK)
        g.rectangle([x0, 0, x0 + 30, h], fill=255)
        for y in range(10, h, 24):
            d.polygon([(x0 + 15, y), (x0 + 25, y + 10), (x0 + 15, y + 20), (x0 + 5, y + 10)], fill=GOLD)
    d.rectangle([0, h - 120, w, h - 70], fill=GOLD_DK)
    g.rectangle([0, h - 120, w, h - 70], fill=255)
    for x in range(20, w, 44):
        cog(d, x, h - 95, 18, 8, GOLD, bg=GOLD_DK)
    im = stitch(im, gold, 42)
    im.save(os.path.join(A, "drape.png"))
    gold.save(os.path.join(A, "drape_gold.png"))


PLAQUES = [
    ["IN CALCULO", "SALVATIO"], ["DEUS EX", "MACHINA"], ["SANCTUM", "SILICIUM"], ["AVE", "OMNISSIAH"],
    ["MACHINA", "VULT"], ["FIDES IN", "NUMERIS"], ["SPIRITUS", "MACHINAE"], ["PRO", "OMNISSIAH"],
    ["OMNIS", "COMPUTAT"], ["NIHIL SINE", "CALCULO"], ["CALCULUS", "SANCTUS I"], ["MEMORIA", "AETERNA II"],
]


def distress(im, seed, amount=1.0):
    """Wear a plate: dark grime pooling towards the edges, pits, scratches."""
    a = np.asarray(im).astype(float)
    h, w = a.shape[:2]
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w]
    edge = np.minimum.reduce([xx, w - 1 - xx, yy, h - 1 - yy]) / max(8.0, min(h, w) * 0.12)
    grime = 0.62 + 0.38 * np.clip(edge, 0, 1)
    blot = rng.normal(0, 1, (h // 16 + 2, w // 16 + 2))
    blot = np.kron(blot, np.ones((16, 16)))[:h, :w]
    grime *= 1 - 0.12 * amount * np.clip(blot, 0, 2)
    a *= grime[..., None]
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    rnd = random.Random(seed)
    for _ in range(int(60 * amount * w * h / 250000) + 8):          # scratches
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        ang, ln = rnd.uniform(0, math.pi), rnd.uniform(10, 70)
        c = rnd.choice([(40, 30, 18), (235, 200, 130)])
        d.line([(x, y), (x + ln * math.cos(ang), y + ln * math.sin(ang))], fill=c, width=1)
    for _ in range(int(300 * amount * w * h / 250000) + 20):         # pits
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        r = rnd.uniform(0.5, 2.2)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(26, 20, 14))
    return img


def plaque_set(w=768, h=384):
    """Brass plates engraved with Latin, each with rivets and a small cog."""
    font = ImageFont.truetype(SERIF, 92)
    for n, lines in enumerate(PLAQUES):
        im = Image.new("RGB", (w, h), (150, 108, 48))
        d = ImageDraw.Draw(im)
        d.rectangle([10, 10, w - 11, h - 11], outline=(90, 62, 26), width=8)
        d.rectangle([28, 28, w - 29, h - 29], outline=(214, 170, 96), width=3)
        for cx, cy in ((24, 24), (w - 24, 24), (24, h - 24), (w - 24, h - 24)):
            d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(214, 172, 100), outline=(70, 48, 20), width=2)
        y = (h - len(lines) * 110) // 2
        for line in lines:
            tw = d.textlength(line, font=font)
            d.text(((w - tw) / 2 + 3, y + 3), line, font=font, fill=(58, 38, 14))       # engraved shadow
            d.text(((w - tw) / 2, y), line, font=font, fill=(96, 64, 24))
            y += 110
        distress(im, 500 + n).save(os.path.join(A, f"plaque_{n:02d}.png"))


def icons(size=512):
    """Mechanicum devices on a dark ground, for small shields and plates:
    0 cog-skull, 1 half-skull cog, 2 machine eye, 3 lightning cog,
    4 cog with the binary of 'OMNIA', 5 cog-and-triangle."""
    G = (214, 170, 96)
    for n in range(6):
        im = Image.new("RGB", (size, size), (26, 22, 20))
        d = ImageDraw.Draw(im)
        c = size // 2
        r = size * 0.30
        if n in (0, 1):                                        # the Cog Mechanicum itself
            device(im, None, c, c, int(size * 0.94))
            if n == 1:                                         # a darker, tarnished copy
                im = Image.eval(im, lambda v: int(v * 0.7))
            distress(im, 700 + n, 0.6).save(os.path.join(A, f"icon_{n}.png"))
            continue
        cog(d, c, c, size * 0.44, 16, G, bg=(26, 22, 20), hole=0.72)
        if n == 2:
            d.ellipse([c - r, c - r * 0.55, c + r, c + r * 0.55], fill=G)
            d.ellipse([c - r * 0.42, c - r * 0.42, c + r * 0.42, c + r * 0.42], fill=(26, 22, 20))
            d.ellipse([c - r * 0.2, c - r * 0.2, c + r * 0.2, c + r * 0.2], fill=(200, 30, 20))
        elif n == 3:
            pts = [(c + r * 0.15, c - r), (c - r * 0.45, c + r * 0.1), (c - r * 0.02, c + r * 0.1),
                   (c - r * 0.2, c + r), (c + r * 0.5, c - r * 0.15), (c + r * 0.05, c - r * 0.15)]
            d.polygon(pts, fill=G)
        elif n == 4:
            f = ImageFont.truetype(MONO, int(size * 0.075))
            for k, word in enumerate(("01001111", "01001101", "01001110", "01001001", "01000001")):
                tw = d.textlength(word, font=f)
                d.text((c - tw / 2, c - r * 0.9 + k * r * 0.38), word, font=f, fill=G)
        else:
            d.polygon([(c, c - r), (c + r * 0.9, c + r * 0.6), (c - r * 0.9, c + r * 0.6)], outline=G, width=10)
            d.ellipse([c - r * 0.25, c - r * 0.05, c + r * 0.25, c + r * 0.45], fill=G)
        distress(im, 700 + n, 0.6).save(os.path.join(A, f"icon_{n}.png"))


def antependium(w=1024, h=560):
    """The embroidered cloth hung on the altar table's front: gold borders of
    lozenges, the medallion, a motto, cog-skull devices, a fringed hem.
    Writes antependium.png and antependium_gold.png."""
    im = velvet(w, h, 77)
    gold = Image.new("L", (w, h), 0)
    d, g = ImageDraw.Draw(im), ImageDraw.Draw(gold)
    for x0, y0, x1, y1 in ((14, 14, w - 14, 44), (14, h - 110, w - 14, h - 80), (14, 14, 44, h - 80), (w - 44, 14, w - 14, h - 80)):
        d.rectangle([x0, y0, x1, y1], fill=GOLD_DK)
        g.rectangle([x0, y0, x1, y1], fill=255)
    for x in range(30, w - 20, 26):
        for y in (29, h - 95):
            d.polygon([(x, y - 10), (x + 8, y), (x, y + 10), (x - 8, y)], fill=GOLD)
    emb = Image.open(os.path.join(A, "emblem.png")).convert("RGBA").resize((250, 250), Image.LANCZOS)
    im.paste(emb, (w // 2 - 125, 70), emb)
    g.ellipse([w // 2 - 124, 71, w // 2 + 124, 319], fill=210)
    for s in (-1, 1):
        device(im, gold, w // 2 + s * 300, 190, 190)
    font = ImageFont.truetype(SERIF, 64)
    line = "IN CALCULO SALVATIO"
    tw = d.textlength(line, font=font)
    d.text(((w - tw) / 2, 350), line, font=font, fill=GOLD)
    g.text(((w - tw) / 2, 350), line, font=font, fill=255)
    rnd = random.Random(9)
    for x in range(20, w - 16, 9):                                 # fringe
        ln = rnd.randint(40, 70)
        d.line([(x, h - 80), (x, h - 80 + ln)], fill=GOLD if x % 18 else GOLD_DK, width=5)
        g.line([(x, h - 80), (x, h - 80 + ln)], fill=255, width=5)
    im = stitch(im, gold, 77)
    alpha = Image.new("L", (w, h), 0)
    ImageDraw.Draw(alpha).rectangle([0, 0, w, h - 80], fill=255)
    for x in range(20, w - 16, 9):
        ImageDraw.Draw(alpha).line([(x, h - 80), (x, h - 12)], fill=255, width=5)
    im.putalpha(alpha)
    im.save(os.path.join(A, "antependium.png"))
    gold.save(os.path.join(A, "antependium_gold.png"))


def binary_band(w=4096, h=96):
    """A strip of brass with the binary of a Latin prayer, for conduits and trims."""
    im = Image.new("RGB", (w, h), (120, 86, 38))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(MONO, 60)
    text = " ".join(format(ord(ch), "08b") for ch in "AVE OMNISSIAH SPIRITUS MACHINAE ")
    x = 10
    while x < w:
        d.text((x, 14), text, font=f, fill=(52, 34, 12))
        x += d.textlength(text, font=f) + 40
    distress(im, 900, 0.7).save(os.path.join(A, "binary.png"))


def frieze(text, w=4096, h=160):
    """A band of gold capitals on dark stone, cog dividers between the phrases."""
    im = Image.new("RGB", (w, h), (30, 27, 25))
    d = ImageDraw.Draw(im)
    rnd = random.Random(5)
    for _ in range(12000):
        x, y = rnd.randrange(w), rnd.randrange(h)
        c = rnd.randint(20, 44)
        d.point((x, y), fill=(c, c - 2, c - 4))
    d.line([(0, 10), (w, 10)], fill=GOLD_DK, width=6)
    d.line([(0, h - 10), (w, h - 10)], fill=GOLD_DK, width=6)
    font = ImageFont.truetype(SERIF, 96)
    x = 30
    while x < w:
        for phrase in text:
            tw = d.textlength(phrase, font=font)
            d.text((x, 24), phrase, font=font, fill=GOLD)
            x += tw + 40
            cog(d, x + 20, h // 2, 34, 10, GOLD, bg=(30, 27, 25))
            x += 90
            if x >= w:
                break
    im.save(os.path.join(A, "frieze.png"))


def plaque(lines=("OMNISSIAH", "COMPUTAT", "OMNIA"), w=1024, h=620):
    im = Image.new("RGB", (w, h), (34, 30, 28))
    d = ImageDraw.Draw(im)
    rnd = random.Random(7)
    for _ in range(9000):                          # pitted iron
        x, y = rnd.randrange(w), rnd.randrange(h)
        g = rnd.randint(18, 48)
        d.point((x, y), fill=(g, g - 3, g - 5))
    d.rectangle([14, 14, w - 15, h - 15], outline=GOLD, width=10)
    d.rectangle([34, 34, w - 35, h - 35], outline=GOLD_DK, width=3)
    font = ImageFont.truetype(SERIF, 132)
    y = 70
    for line in lines:
        tw = d.textlength(line, font=font)
        d.text(((w - tw) / 2, y), line, font=font, fill=GOLD)
        y += 160
    im.filter(ImageFilter.SMOOTH).save(os.path.join(A, "plaque.png"))


def screens(w=640, h=400):
    rnd = random.Random(11)
    hexlines = [" ".join(f"{rnd.randrange(65536):04X}" for _ in range(6)) for _ in range(TICKS)]
    big = ImageFont.truetype(MONO, 40)
    small = ImageFont.truetype(MONO, 26)
    green, dim = (120, 255, 150), (40, 130, 60)
    for k in range(TICKS):
        im = Image.new("RGB", (w, h), (4, 12, 6))
        d = ImageDraw.Draw(im)
        d.text((28, 22), "CALCULATING" + "." * (k % 5), font=big, fill=green)
        d.text((28, 74), "FOR A BRIGHTER IMPERIUM", font=small, fill=green)
        for r in range(6):
            d.text((28, 128 + r * 34), hexlines[(k + r) % TICKS], font=small, fill=dim)
        d.text((28, h - 46), "+++ OMNIA PER CALCULUM +++", font=small, fill=green)
        for y in range(0, h, 4):                   # scanlines
            d.line([(0, y), (w, y)], fill=(0, 0, 0), width=1)
        im.save(os.path.join(A, f"screen_{k:02d}.png"))


if __name__ == "__main__":
    for n, (motto, verse) in enumerate(MOTTOS):
        banner(n, motto, verse)
    for n, lines in enumerate(PRAYERS):
        parchment(n, lines)
    frieze(FRIEZE)
    drape()
    plaque_set()
    icons()
    antependium()
    binary_band()
    plaque()
    screens()
    print("textures written to", A)
