"""Stained glass designs for the windows of a plate, drawn piece by piece: coloured glass pieces held by lead lines. The
owner rejected war machines that the image model drew from a prompt alone ("stained glass images are terrible") and
gave pictures of the machines to use. src/repaint.py lays a design into a window's hole and the image model then
works over it at a low strength, so the glass takes the window's light and grain while the shapes stay.

- **Titan** - the Imperial Knight of the owner's picture (in/reference/imperial-knight.jpg), cut from its white
  ground, its colours sorted into eight glasses and every glass split into pieces about a tenth of the window's width;
  a gold halo of pieces stands behind it. The owner: "titan is too short": it stands as tall as `tall` of the window,
  its feet behind the candelabra before the window, and the window's sides cut what is wider than the window
- **Mathematics** - the owner: "the right one should be dedicated to maths and statistics", "sacred distribution /
  statistical calculations": the bell curve of the normal distribution over a histogram at the top, below it two rows
  of panes with the signs of statistics, and in the lower half, behind the candle that stands before the window, a
  Galton board whose balls pile up in its bins as the binomial distribution (the owner: "lower part of the image
  isn't used why? there should also be something")
- **Upright in the window** - a design is drawn upright on a canvas of the window's own size and warped into the
  window between its leaning sides (the owner: "all image rotated vs window frames")
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


def titan(out, lead, hole, box, reference, rng, s, tall):
    """The machine of the picture standing in the window, `tall` times the window's height, its feet near the
    window's foot; where it is wider than the window, the window's sides cut it."""
    hx0, hy0, hx1, hy1 = box
    W, H = hx1 - hx0, hy1 - hy0
    pic, thing = cutout(reference)
    f = tall * H / pic.shape[0]
    w, h = int(pic.shape[1] * f), int(pic.shape[0] * f)
    pic = cv2.resize(pic, (w, h), interpolation=cv2.INTER_AREA)
    thing = cv2.resize(thing.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST).astype(bool)
    x0, y0 = hx0 + (W - w) // 2, hy1 - h - int(0.05 * H)
    c0, c1 = max(0, hx0 - x0), min(w, hx1 - x0)
    pic, thing, x0, w = pic[:, c0:c1], thing[:, c0:c1], x0 + c0, c1 - c0
    # the halo: a ring of gold pieces round a light gold disc, behind the machine's upper part
    cy, cx, r = y0 + int(0.12 * h), hx0 + W // 2, int(0.62 * W)
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
    top, base = hy0 + int(0.05 * H), hy0 + int(0.25 * H)
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
    py0, py1 = hy0 + int(0.29 * H), hy0 + int(0.50 * H)
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
    return galton(out, lead, hole, (hx0, hy0 + int(0.53 * H), hx1, hy1), rng, s)


def galton(out, lead, hole, box, rng, s, rows=6):
    """A Galton board: balls fall from a funnel through rows of pegs and pile up in the bins below as the binomial
    distribution, the bell of the normal distribution drawn by chance."""
    from math import comb
    x0, y0, x1, y1 = box
    W, H = x1 - x0, y1 - y0
    cx, dx = (x0 + x1) / 2, 0.125 * W
    yy, xx = np.mgrid[:out.shape[0], :out.shape[1]]
    for sx in (-1, 1):                               # the funnel: two gold bands down to an opening over the first peg
        a, b = np.array([cx + sx * 0.42 * W, y0]), np.array([cx + sx * 0.6 * dx, y0 + 0.1 * H])
        t = np.clip(((xx - a[0]) * (b[0] - a[0]) + (yy - a[1]) * (b[1] - a[1])) / ((b - a) ** 2).sum(), 0, 1)
        band = hole & (np.hypot(xx - a[0] - t * (b[0] - a[0]), yy - a[1] - t * (b[1] - a[1])) < 3 * s)
        fill(out, band, cells(out.shape[:2], 8 * s, rng), GOLD, rng, 0.05)
        lead |= hole & edges(band.astype(np.int64), max(2, s))
    pegs = np.zeros(out.shape[:2], bool)
    for r in range(rows):
        for k in range(r + 1):
            pegs |= np.hypot(xx - cx - (k - r / 2) * dx, yy - y0 - (0.15 + 0.07 * r) * H) < 3.5 * s
    pegs &= hole
    out[pegs] = np.array(IVORY[0], np.float32)
    lead |= edges(pegs.astype(np.int64), max(2, s)) & hole
    by0, by1 = y0 + 0.56 * H, y1 - 0.01 * H             # the bins: lead walls, and the balls in them
    for j in range(rows + 2):
        lead |= hole & (np.abs(xx - cx - (j - (rows + 1) / 2) * dx) < s) & (yy >= by0) & (yy < by1)
    lead |= hole & (np.abs(yy - by1) < 1.5 * s) & (np.abs(xx - cx) < (rows + 1) / 2 * dx)
    r_ball = 0.42 * dx
    most = int((by1 - by0) / (2 * r_ball))
    for j in range(rows + 1):
        for i in range(round(comb(rows, j) / comb(rows, rows // 2) * most)):
            ball = hole & (np.hypot(xx - cx - (j - rows / 2) * dx, yy - by1 + r_ball * (1 + 2 * i) + s) < r_ball - s)
            out[ball] = np.array([IVORY, RED, GOLD][(i + j) % 3][0], np.float32)
            lead |= edges(ball.astype(np.int64), max(2, s)) & hole
    return lead


def design(crop, hole, quad, s, kind, reference=None, seed=0, tall=0.84):
    """The window's crop at `s` times the plate's scale with the new glass in its hole, and where the signs lie: the image
    model drew other letters over them at a strength of 0.2, so they are laid over its result again. The design is drawn
    upright on a canvas of the window's own size and warped into the window between its leaning sides: `quad`, the
    corners of the glass in the crop (top left, top right, bottom right, bottom left; x, y in plate pixels)."""
    rng = np.random.default_rng(seed)
    h, w = crop.shape[:2]
    big = cv2.resize(crop, (w * s, h * s), interpolation=cv2.INTER_CUBIC).astype(np.float32)
    m = cv2.resize(hole.astype(np.uint8), (w * s, h * s), interpolation=cv2.INTER_NEAREST).astype(bool)
    (tlx, top), (trx, _), (brx, bottom), (blx, _) = quad
    Hc, Wc = int(round((bottom - top) * s)), int(round((trx - tlx + brx - blx) / 2 * s))
    px = crop[hole].astype(np.float32)
    blue = px[(px[:, 2] > px[:, 0] + 30) & (px[:, 2] > px[:, 1] + 10) & (px.sum(1) > 200)]
    blues = [tuple(c) for c in blue[rng.integers(0, len(blue), 24)]]
    canvas = np.zeros((Hc, Wc, 3), np.float32)
    whole = np.ones((Hc, Wc), bool)
    ground = cells((Hc, Wc), 13 * s, rng)
    fill(canvas, whole, ground, blues, rng, 0.1)
    lead = edges(ground, max(2, s))
    exact = np.zeros((Hc, Wc), bool)                # signs that the image model must not change
    if kind == "titan":
        lead = titan(canvas, lead, whole, (0, 0, Wc, Hc), reference, rng, s, tall)
    else:
        lead = maths(canvas, lead, whole, (0, 0, Wc, Hc), rng, s, exact)
    canvas[lead] = LEAD
    # into the window: a row of the crop is a row of the canvas, and across it the canvas spans the leaning sides
    Y, X = np.mgrid[:h * s, :w * s].astype(np.float32)
    v = (Y / s - top) / (bottom - top)
    xl, xr = tlx + v * (blx - tlx), trx + v * (brx - trx)
    mx, my = ((X / s - xl) / (xr - xl) * Wc).astype(np.float32), (v * Hc).astype(np.float32)
    warped = cv2.remap(canvas, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    out = np.where(m[..., None], warped, big)
    exact = (cv2.remap(exact.astype(np.float32), mx, my, cv2.INTER_LINEAR) > 0.5) & m
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
