"""Stained glass designs for the windows of a plate, drawn piece by piece: coloured glass pieces held by lead lines. The
owner rejected war machines that the image model drew from a prompt alone ("stained glass images are terrible") and
gave pictures of the machines to use. src/repaint.py lays a design into a window's hole and the image model then
works over it at a low strength, so the glass takes the window's light and grain while the shapes stay.

- **Titan** - the machine of the owner's picture, cut from its white ground, its colours sorted into eight glasses and
  every glass split into pieces about a tenth of the machine's width; a gold halo of pieces stands behind it. It
  stands high in the window, above the candle before it
- **Mathematics** - the owner: "the right one should be dedicated to maths and statistics", "sacred distribution /
  statistical calculations": the bell curve of the normal distribution over a histogram at the top, and below it two
  rows of panes with the signs of statistics, all above the candle that stands before the window
- **Ground** - the window's own blue glass: its colours are taken from the old window's blue pieces; the iron bars
  across the old window stay before the new glass
"""
import os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
LEAD = np.array([22, 18, 16], np.float32)
GOLD = [(236, 182, 60), (250, 210, 96), (214, 150, 40), (246, 196, 72)]
RED = [(186, 30, 34), (150, 20, 36), (206, 54, 40)]
AMBER = [(232, 128, 30), (214, 100, 24)]
GREEN = [(40, 130, 70), (30, 104, 60)]
VIOLET = [(96, 46, 140), (120, 60, 160)]
IVORY = [(246, 236, 206), (236, 224, 190)]
SIGNS = ["μ", "σ", "Σ", "∫", "π", "e", "χ²", "√n"]


def cells(shape, spacing, rng):
    """Voronoi cells round the points of a jittered grid: a label for every pixel."""
    h, w = shape
    seeds = np.full((h, w), 255, np.uint8)
    for y in np.arange(spacing / 2, h, spacing):
        for x in np.arange(spacing / 2, w, spacing):
            py, px = int(np.clip(y + rng.uniform(-0.4, 0.4) * spacing, 0, h - 1)), int(np.clip(x + rng.uniform(-0.4, 0.4) * spacing, 0, w - 1))
            seeds[py, px] = 0
    _, labels = cv2.distanceTransformWithLabels(seeds, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_CCOMP)
    return labels


def edges(labels, width):
    """The lead between pieces: where a pixel's label differs from its neighbour's."""
    e = np.zeros(labels.shape, bool)
    e[1:] |= labels[1:] != labels[:-1]
    e[:, 1:] |= labels[:, 1:] != labels[:, :-1]
    return cv2.dilate(e.astype(np.uint8), np.ones((width, width), np.uint8)).astype(bool)


def fill(out, region, labels, colours, rng, vary=0.12):
    """Every piece of the region in one of the colours, each piece a little lighter or darker."""
    for k in np.unique(labels[region]):
        m = region & (labels == k)
        c = np.array(colours[rng.integers(len(colours))], np.float32) * rng.uniform(1 - vary, 1 + vary)
        out[m] = np.clip(c, 0, 255)


def glassy(c):
    """A colour as glass lit from behind: more saturated, and no glass is as dark as painted metal."""
    hsv = cv2.cvtColor(c.reshape(-1, 1, 3).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * 1.3, 0, 255)
    hsv[..., 2] = 95 + 0.7 * hsv[..., 2]
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB).reshape(c.shape).astype(np.float32)


def glyph(size, text, height):
    """The mask of a sign drawn in the serif font, `height` pixels high, centred in an image of `size`."""
    img = Image.new("L", size, 0)
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT, int(height))
    x0, y0, x1, y1 = d.textbbox((0, 0), text, font=font)
    d.text(((size[0] - (x1 - x0)) / 2 - x0, (size[1] - (y1 - y0)) / 2 - y0), text, font=font, fill=255)
    return np.asarray(img) > 127


def cutout(path):
    """The machine of a picture on a white ground: its colours and where it is."""
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    thing = np.sqrt(((255 - a) ** 2).sum(-1)) > 45
    thing = cv2.morphologyEx(thing.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    count, parts = cv2.connectedComponents(thing)
    sizes = np.bincount(parts.ravel())
    sizes[0] = 0
    thing = ndimage.binary_fill_holes(parts == sizes.argmax())
    ys, xs = np.nonzero(thing)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1], thing[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def titan(out, lead, hole, box, reference, rng, s):
    hx0, hy0, hx1, hy1 = box
    W, H = hx1 - hx0, hy1 - hy0
    pic, thing = cutout(reference)
    f = min(0.96 * W / pic.shape[1], 0.78 * H / pic.shape[0])
    w, h = int(pic.shape[1] * f), int(pic.shape[0] * f)
    pic = cv2.resize(pic, (w, h), interpolation=cv2.INTER_AREA)
    thing = cv2.resize(thing.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST).astype(bool)
    x0, y0 = hx0 + (W - w) // 2, hy0 + int(0.1 * H)
    # the halo: a ring of gold pieces round a light gold disc, behind the machine's upper part
    cy, cx, r = y0 + int(0.25 * h), hx0 + W // 2, int(0.48 * W)
    yy, xx = np.mgrid[:out.shape[0], :out.shape[1]]
    d = np.hypot(yy - cy, xx - cx)
    ring, disc = hole & (d < r) & (d >= 0.8 * r), hole & (d < 0.8 * r)
    ang = ((np.arctan2(yy - cy, xx - cx) + np.pi) / (2 * np.pi) * 24).astype(int)
    fill(out, ring, ang, GOLD[2:] + AMBER, rng)
    lead |= ring & edges(ang, 2 * s)
    lead |= hole & (np.abs(d - r) < s * 1.5) | hole & (np.abs(d - 0.8 * r) < s * 1.5)
    halo = cells(out.shape[:2], 9 * s, rng)
    fill(out, disc, halo, [(252, 222, 120), (246, 206, 98), (255, 232, 150)], rng)
    lead |= disc & edges(halo, s)
    # the machine: its colours sorted into ten glasses, each glass split into pieces
    px = pic[thing].reshape(-1, 3)
    _, lab, centres = cv2.kmeans(px, 8, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5), 3, cv2.KMEANS_PP_CENTERS)
    glass = np.zeros((h, w), np.uint8)
    glass[thing] = lab.ravel() + 1
    glass = cv2.medianBlur(glass, 5) * thing
    piece = glass.astype(np.int64) * 100000 + cells((h, w), max(8, int(0.09 * w)), rng)
    colour = np.zeros((h, w, 3), np.float32)
    for k in np.unique(piece[thing]):
        m = thing & (piece == k)
        colour[m] = pic[m].mean(0)
    colour = glassy(colour)
    region = np.zeros(out.shape[:2], bool)
    region[y0:y0 + h, x0:x0 + w] = thing
    region &= hole
    sub = out[y0:y0 + h, x0:x0 + w]
    sub[thing] = colour[thing]
    out[y0:y0 + h, x0:x0 + w] = np.where(hole[y0:y0 + h, x0:x0 + w, None], sub, out[y0:y0 + h, x0:x0 + w])
    inner = np.zeros(out.shape[:2], bool)
    inner[y0:y0 + h, x0:x0 + w] = edges(np.where(thing, piece, -1), max(2, s))
    outline = np.zeros(out.shape[:2], bool)
    outline[y0:y0 + h, x0:x0 + w] = edges(thing.astype(np.int64), 2 * s)
    return lead | (inner & region) | (outline & hole)


def maths(out, lead, hole, box, rng, s, exact):
    hx0, hy0, hx1, hy1 = box
    W, H = hx1 - hx0, hy1 - hy0
    yy, xx = np.mgrid[:out.shape[0], :out.shape[1]]
    cx = hx0 + W // 2
    # the bell curve of the normal distribution, a thick gold band, over a histogram of thirteen bars
    top, base = hy0 + int(0.14 * H), hy0 + int(0.34 * H)
    left, right = hx0 + int(0.04 * W), hx1 - int(0.04 * W)
    sd = 0.19 * (right - left)
    curve = lambda x: base - (base - top) * np.exp(-0.5 * ((x - cx) / sd) ** 2)
    edges_x = np.linspace(left, right, 14)
    bars = np.zeros(out.shape[:2], np.int64)
    for i in range(13):
        a, b = int(edges_x[i]), int(edges_x[i + 1])
        bars[int(curve((a + b) / 2)) + 4 * s:base, a:b] = i + 1
    inside = hole & (bars > 0)
    for i in range(1, 14):
        fill(out, inside & (bars == i), cells(out.shape[:2], 10 * s, rng), [RED, AMBER][i % 2], rng, 0.08)
    lead |= inside & edges(bars * 1000 + cells(out.shape[:2], 10 * s, rng), s) | hole & edges(bars, 2 * s)
    band = hole & (np.abs(yy - curve(xx)) < 5 * s) & (xx >= left) & (xx <= right)
    fill(out, band, cells(out.shape[:2], 8 * s, rng), GOLD, rng, 0.05)
    lead |= hole & edges(band.astype(np.int64), s)
    lead |= hole & (np.abs(yy - base) < 1.5 * s) & (xx >= left) & (xx <= right)
    # panes with the signs of statistics, two rows of four
    py0, py1 = hy0 + int(0.41 * H), hy0 + int(0.69 * H)
    ph, pw = (py1 - py0) // 2, (hx1 - hx0 - int(0.08 * W)) // 4
    for k, text in enumerate(SIGNS):
        x0, y0 = hx0 + int(0.04 * W) + (k % 4) * pw, py0 + (k // 4) * ph
        pane = np.zeros(out.shape[:2], bool)
        pane[y0:y0 + ph, x0:x0 + pw] = True
        pane &= hole
        out[pane] = np.array([RED, GREEN, VIOLET][(k + k // 4) % 3][0], np.float32)
        mark = np.zeros(out.shape[:2], bool)
        mark[y0:y0 + ph, x0:x0 + pw] = glyph((pw, ph), text, min(0.6 * ph, (0.55 if len(text) == 1 else 0.36) * pw * 1.6))
        mark &= pane
        out[mark] = np.array(IVORY[0], np.float32)
        exact |= cv2.dilate(mark.astype(np.uint8), np.ones((2 * s + 1,) * 2, np.uint8)).astype(bool)
        lead |= hole & edges(pane.astype(np.int64), 2 * s) | edges(mark.astype(np.int64), max(2, s)) & pane
    return lead


def design(crop, hole, s, kind, reference=None, seed=0, panes=0):
    """The window's crop at `s` times the plate's scale with the new glass in its hole, and where the signs lie: the image
    model drew other letters over them at a strength of 0.2, so they are laid over its result again."""
    rng = np.random.default_rng(seed)
    h, w = crop.shape[:2]
    big = cv2.resize(crop, (w * s, h * s), interpolation=cv2.INTER_CUBIC).astype(np.float32)
    m = cv2.resize(hole.astype(np.uint8), (w * s, h * s), interpolation=cv2.INTER_NEAREST).astype(bool)
    ys, xs = np.nonzero(m)
    box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
    px = crop[hole].astype(np.float32)
    blue = px[(px[:, 2] > px[:, 0] + 30) & (px[:, 2] > px[:, 1] + 10) & (px.sum(1) > 200)]
    blues = [tuple(c) for c in blue[rng.integers(0, len(blue), 24)]]
    out = big.copy()
    ground = cells(out.shape[:2], 13 * s, rng)
    fill(out, m, ground, blues, rng, 0.1)
    lead = m & edges(ground, max(2, s))
    exact = np.zeros(m.shape, bool)                 # signs that the image model must not change
    if kind == "titan":
        lead = titan(out, lead, m, box, reference, rng, s)
    else:
        lead = maths(out, lead, m, box, rng, s, exact)
    if panes:
        # a column of border panes along the left side, red and blue in turn, as the old window's border
        x0, x1 = box[0], box[0] + (panes - 2) * s
        for k, y in enumerate(range(box[1], box[3], (panes - 2) * s)):
            pane = np.zeros(m.shape, bool)
            pane[y:y + (panes - 2) * s, x0:x1] = True
            pane &= m
            out[pane] = np.array([RED[0], (40, 90, 200)][k % 2], np.float32)
            lead |= m & edges(pane.astype(np.int64), max(2, s))
        lead[box[1]:box[3], x1:x1 + s] |= m[box[1]:box[3], x1:x1 + s]
    out[lead & m] = LEAD
    # the iron bars across the old window stay before the glass: rows where most of the hole is dark
    lum = crop.astype(np.float32) @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    dark = np.array([hole[y].sum() > 20 and (lum[y][hole[y]] < 45).mean() > 0.7 for y in range(h)])
    runs, y = [], 0
    while y < h:                                             # a bar is at most 4 rows thick; a thicker dark run is
        if dark[y]:                                          # the old picture, not a bar
            e = y
            while e < h and dark[e]:
                e += 1
            runs += list(range(y, e)) if e - y <= 4 else []
            y = e
        else:
            y += 1
    for y in runs:
        band = np.zeros(out.shape[:2], bool)
        band[y * s:(y + 1) * s] = True
        out[band & m] = LEAD
    return out.clip(0, 255).astype(np.uint8), exact
