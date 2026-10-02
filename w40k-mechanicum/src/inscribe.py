"""Exact Latin on the parchments and book pages of a plate, applied as a
texture draped on each sheet's surface.

The model writes illegible script on every sheet. Here the script is taken
out and exact Latin is put in its place, in four steps per sheet:

Surface. MoGe-2 measures an enlarged crop round the sheet: on the whole
plate a sheet is a few dozen pixels and comes out as one flat plane, on the
crop its curl, its waves and a book page's bend into the gutter are
resolved. The surface is then rebuilt from the normals: between two
neighbouring pixels the depth changes by the ratio the normal there
prescribes, and one least-squares solve finds the depth of every pixel of
the sheet, held loosely to the measured depth.

Chart. The surface is flattened without stretching its angles (least
squares conformal map, Levy 2002): every pixel of the sheet gets a place
(u, v) on a flat sheet, in metres. A sheet of parchment does not stretch,
so the chart is the sheet laid flat. It is turned so that u runs along the
lines of the script the model wrote, which are straight on the flat sheet.

Texture. The Latin is written straight on the flat sheet, clear of the
seals and the edges.

Drape. Every pixel of the plate takes the texture's value at its (u, v):
the lines bend with the sheet, shorten where it turns away and follow its
perspective. The ink darkens the sheet, so the sheet's shading stays.

    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 \\
        .venv-moge/bin/python src/inscribe.py <name>

reads the chosen draft, writes wip/scene3d/<name>.png and the check picture
wip/preview/sheets-<name>.png: each sheet with its chart drawn on it (the
lines the text follows, and their crossings) beside the result.
"""
import os
import sys
import cv2
import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont
from scipy import sparse
from scipy.interpolate import LinearNDInterpolator
from scipy.ndimage import gaussian_filter1d, median_filter, percentile_filter
from scipy.sparse.linalg import spsolve
from moge.model.v2 import MoGeModel
import genplates as GP

G = GP.G
el = lambda k: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))


def cutter():
    """SAM 2.1 (facebook/sam2.1-hiera-large): cut(crop, box) is the mask of
    the thing that five points spread over a box of a crop lie on. The
    boxes in PARCHMENTS frame the written part of a sheet; points let the
    mask reach the whole sheet."""
    from transformers import Sam2Model, Sam2Processor
    rid = "facebook/sam2.1-hiera-large"
    proc, sam = Sam2Processor.from_pretrained(rid), Sam2Model.from_pretrained(rid).cuda().eval()

    def cut(crop, box):
        x0, y0, x1, y1 = box
        pts = [[x0 + fx * (x1 - x0), y0 + fy * (y1 - y0)] for fx, fy in ((.5, .5), (.3, .35), (.7, .35), (.3, .7), (.7, .7))]
        inputs = proc(images=Image.fromarray(crop), input_points=[[pts]], input_labels=[[[1] * 5]], return_tensors="pt").to("cuda")
        with torch.no_grad():
            out = sam(**inputs, multimask_output=False)
        mk = (proc.post_process_masks(out.pred_masks.cpu(), inputs["original_sizes"])[0][0, 0].numpy() > 0).astype(np.uint8)
        cnt, lab, stats, _ = cv2.connectedComponentsWithStats(mk)
        return lab == 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA])) if cnt > 1 else mk > 0
    return cut


def sheet(img, region):
    """The sheet inside `region` of a crop: its mask, the part clear of
    seals and edges, and the ink map (0..1) of the script the model wrote."""
    bg = cv2.morphologyEx(img, cv2.MORPH_CLOSE, el(9))               # the sheet without its script
    hsv = cv2.cvtColor(bg, cv2.COLOR_RGB2HSV).astype(np.float32)
    v = hsv[..., 2]
    pale = (v > 0.5 * np.percentile(v[region], 90)) & (hsv[..., 1] < 205) & region
    raw = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(np.float32)
    wax = ((raw[..., 0] < 8) | (raw[..., 0] > 168)) & (raw[..., 1] > 130)           # a red seal, and the shadow at its rim
    pale &= ~(cv2.dilate(cv2.morphologyEx(wax.astype(np.uint8), cv2.MORPH_OPEN, el(5)), el(9)) > 0)
    mask = cv2.morphologyEx(pale.astype(np.uint8), cv2.MORPH_OPEN, el(5))
    inner = cv2.erode(mask, el(7))
    lum = img.astype(np.float32).mean(-1)
    fine = cv2.morphologyEx(lum, cv2.MORPH_CLOSE, el(5))             # strokes only: a fold's shadow is wider than 5 px
    return mask > 0, inner, np.clip((fine - lum) / np.maximum(fine, 1), 0, 1) * inner


def surface(P, N, M):
    """The sheet's surface from its normals. P: measured points (h, w, 3),
    N: normals, M: the sheet's pixels. A point is depth times its ray; the
    step between two neighbours lies in the plane of their normal n, so
    their depths have the ratio (n . ray_a) / (n . ray_b). The logarithm of
    depth is solved from all these ratios, held to the measured depth with
    a twentieth of their weight."""
    h, w = M.shape
    idx = np.full((h, w), -1)
    idx[M] = np.arange(M.sum())
    ray = P / P[..., 2:]
    rows, cols, vals, rhs = [], [], [], []
    n = 0
    for dy, dx in ((0, 1), (1, 0)):
        A, B = (slice(0, h - dy), slice(0, w - dx)), (slice(dy, h), slice(dx, w))
        both = M[A] & M[B]
        nn = N[A][both] + N[B][both]
        g = np.log(np.clip((nn * ray[A][both]).sum(-1) / (nn * ray[B][both]).sum(-1), 0.95, 1.05))
        k = n + np.arange(both.sum())
        rows += [k, k]
        cols += [idx[B][both], idx[A][both]]
        vals += [np.ones(len(k)), -np.ones(len(k))]
        rhs.append(g)
        n += len(k)
    k = n + np.arange(M.sum())
    rows.append(k), cols.append(np.arange(M.sum())), vals.append(np.full(M.sum(), 0.05))
    rhs.append(0.05 * np.log(P[..., 2][M]))
    A = sparse.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(n + M.sum(), M.sum()))
    logz = spsolve((A.T @ A).tocsc(), A.T @ np.concatenate(rhs))
    out = np.zeros_like(P)
    out[M] = np.exp(logz)[:, None] * ray[M]
    return out


def flatten(P, M):
    """The sheet laid flat: a place (u, v) in metres for every pixel of M
    that belongs to its largest connected part, as a complex number u + iv
    (NaN elsewhere), and the mask of those pixels. Least squares conformal
    map: every triangle of the surface keeps its angles, two far-apart
    pixels are pinned, and the chart is scaled so that lengths on it equal
    lengths on the surface."""
    h, w = M.shape
    cell = (M[:-1, :-1] & M[:-1, 1:] & M[1:, :-1] & M[1:, 1:]).astype(np.uint8)
    cnt, lab, stats, _ = cv2.connectedComponentsWithStats(cell, connectivity=4)
    cell = lab == 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    ci, cj = np.nonzero(cell)
    node = lambda i, j: i * w + j
    tri = np.concatenate([np.stack([node(ci, cj), node(ci, cj + 1), node(ci + 1, cj + 1)], 1),
                          np.stack([node(ci, cj), node(ci + 1, cj + 1), node(ci + 1, cj)], 1)])
    used = np.unique(tri)
    idx = np.full(h * w, -1)
    idx[used] = np.arange(len(used))
    tri = idx[tri]
    p = P.reshape(-1, 3)[used].astype(np.float64)
    a, b, c = p[tri[:, 0]], p[tri[:, 1]], p[tri[:, 2]]
    e1 = b - a
    lb = np.linalg.norm(e1, axis=1)
    e1 /= lb[:, None]
    nrm = np.cross(e1, c - a)
    high = np.linalg.norm(nrm, axis=1)
    e2 = np.cross(nrm / high[:, None], e1)
    area2 = lb * high
    q = np.stack([np.zeros(len(tri), complex), lb + 0j, ((c - a) * e1).sum(1) + 1j * ((c - a) * e2).sum(1)], 1)
    Wt = np.stack([q[:, 2] - q[:, 1], q[:, 0] - q[:, 2], q[:, 1] - q[:, 0]], 1) / np.sqrt(area2)[:, None]
    A = sparse.csr_matrix((Wt.ravel(), (np.repeat(np.arange(len(tri)), 3), tri.ravel())), shape=(len(tri), len(used)))
    xs = (used % w).astype(float)
    pin = np.array([int(np.argmin(xs)), int(np.argmax(xs))])
    free = np.setdiff1d(np.arange(len(used)), pin)
    zpin = np.array([0, np.linalg.norm(p[pin[1]] - p[pin[0]])], complex)
    Af, bf = A[:, free], -(A[:, pin] @ zpin)
    R = sparse.bmat([[Af.real, -Af.imag], [Af.imag, Af.real]]).tocsc()          # the complex system as a real one
    sol = spsolve((R.T @ R).tocsc(), R.T @ np.concatenate([bf.real, bf.imag]))
    z = np.zeros(len(used), complex)
    z[pin], z[free] = zpin, sol[:len(free)] + 1j * sol[len(free):]
    z *= lb.sum() / np.abs(z[tri[:, 1]] - z[tri[:, 0]]).sum()
    za, zb, zc = z[tri[:, 0]], z[tri[:, 1]], z[tri[:, 2]]
    stretch = np.abs(((zb - za).conjugate() * (zc - za)).imag) / area2           # area on the chart / area on the surface
    out = np.full(h * w, np.nan, complex)
    out[used] = z
    return out.reshape(h, w), idx.reshape(h, w) >= 0, np.percentile(stretch, [5, 95])


def unwrap(z, ok, scale):
    """The flat sheet as a picture: for a chart z (complex, per pixel) and
    `scale` picture pixels per metre, the picture's size, each plate
    pixel's place on it (complex) and, for every pixel of the picture, the
    plate pixel it shows (two float32 maps for cv2.remap, -1 off the sheet)."""
    c = (z - (np.nanmin(z.real) + 1j * np.nanmin(z.imag))) * scale
    Wc, Hc = int(np.nanmax(c.real)) + 2, int(np.nanmax(c.imag)) + 2
    yy, xx = np.nonzero(ok)
    back = LinearNDInterpolator(np.stack([c[ok].real, c[ok].imag], 1), np.stack([xx, yy], 1).astype(np.float64), fill_value=-1)
    gy, gx = np.mgrid[0:Hc, 0:Wc]
    m = back(np.stack([gx.ravel(), gy.ravel()], 1)).reshape(Hc, Wc, 2).astype(np.float32)
    return (Wc, Hc), c, m[..., 0], m[..., 1]


def waves(flat, limit):
    """How far the top and bottom edges of the flat sheet (a mask) leave
    straight lines, carried into the sheet: for every pixel the number of
    rows the sheet there is shifted, the top edge's wave at the top, the
    bottom edge's at the bottom, a mix by height between. A sheet is cut
    straight, so a wavy edge on the flat chart is warp the surface
    measurement did not resolve. Notches and tabs deeper than `limit` (a
    seal over the edge, a torn corner) are not waves and are bridged. The
    wave is smoothed until it leans no letter by more than 0.35 (19
    degrees), so the Latin stays readable."""
    h, w = flat.shape
    x = np.arange(w)
    has = flat.any(0)
    top, bot = flat.argmax(0).astype(float), h - 1.0 - flat[::-1].argmax(0)
    good = has & (bot - top > 0.5 * np.median((bot - top)[has]))
    lines, devs = [], []
    for pos in (top, bot):
        g = good & (np.abs(pos - np.median(pos[good])) < 2 * limit)
        for _ in range(3):
            line = np.polyval(np.polyfit(x[g], pos[g], 1), x) if g.sum() > 8 else np.full(w, np.median(pos[good]))
            g = good & (np.abs(pos - line) < limit)
        d = np.interp(x, x[g], (pos - line)[g]) if g.sum() > 8 else np.zeros(w)
        lines.append(line)
        d = median_filter(d, size=7, mode="nearest")
        for sigma in np.arange(1.5, 15, 0.5):
            smooth = gaussian_filter1d(d, sigma, mode="nearest")
            if np.abs(np.gradient(smooth)).max() <= 0.35:
                break
        devs.append(smooth)
    t = np.clip((np.arange(h)[:, None] - lines[0]) / np.maximum(lines[1] - lines[0], 1), 0, 1)
    return (1 - t) * devs[0] + t * devs[1]


def script(flat):
    """The lines of the script on the flat sheet's ink map: their tilt in
    degrees and how clearly they show. Evenly spaced
    straight lines are one wave: the strongest peak of the 2D Fourier
    transform among periods of 4 to 16 px and tilts up to 35 degrees."""
    n = 256
    win = np.zeros((n, n), np.float32)
    hh, ww = min(flat.shape[0], n), min(flat.shape[1], n)
    win[:hh, :ww] = (flat - flat[flat > 0].mean() * (flat > 0))[:hh, :ww] if (flat > 0).any() else 0
    F = cv2.GaussianBlur(np.abs(np.fft.fftshift(np.fft.fft2(win))).astype(np.float32), (0, 0), 1.0)
    fy, fx = np.mgrid[-n // 2:n // 2, -n // 2:n // 2] / n
    freq = np.hypot(fx, fy)
    tilt = np.degrees(np.arctan2(-fx, fy))                           # the lines' angle for a wave vector (fx, fy)
    band = (freq > 1 / 16) & (freq < 1 / 4) & (fy > 0) & (np.abs(tilt) <= 35)
    F[~band] = 0
    py, px = np.unravel_index(np.argmax(F), F.shape)
    return float(tilt[py, px]), float(F[py, px] / max(np.median(F[band]), 1e-9))


def block(shape):
    """The largest upright rectangle (x0, y0, x1, y1) inside a mask."""
    h, w = shape.shape
    high, best = np.zeros(w, int), (0, 0, 0, 0, 0)
    for y in range(h):
        high = np.where(shape[y], high + 1, 0)
        stack = []
        for x in range(w + 1):
            cur, start = (high[x] if x < w else 0), x
            while stack and stack[-1][1] >= cur:
                start, top = stack.pop()
                if top * (x - start) > best[0]:
                    best = (top * (x - start), start, y - top + 1, x, y + 1)
            stack.append((start, cur))
    return best[1:]


def write(size, free, rect, band, k):
    """The texture: Latin written straight on the flat sheet (size in
    pixels), in lines of height `band` inside the text block `rect`,
    wherever `free` is clear for the whole height of a line. Returns how
    much light the ink takes per colour (0..1) and the number of words
    written."""
    Wc, Hc = size
    tex = Image.new("RGB", size, (0, 0, 0))
    d = ImageDraw.Draw(tex)
    fsize = int(0.8 * band)
    font = ImageFont.truetype(GP.SERIF, fsize)
    ink, red = tuple(255 - c for c in GP.INK), tuple(255 - c for c in GP.RED)
    words = " ".join(GP.PRAYER[(k * 3 + j) % len(GP.PRAYER)].capitalize() + "." for j in range(120)).split()
    bx0, by0, bx1, by1 = rect
    i, sentence = 0, 0
    for top in np.arange(by0, by1 - band + 1, band):
        clear = free[int(top):int(top + band), bx0:bx1].mean(0) > 0.9
        edges = bx0 + np.flatnonzero(np.diff(np.concatenate([[0], clear.astype(np.int8), [0]])))
        for xa, xb in zip(edges[::2], edges[1::2]):                  # a seal or a mark splits the line into runs
            x = float(xa)
            while i < len(words) and x + font.getlength(words[i]) <= xb:
                wd = words[i]
                first = (i == 0 or words[i - 1].endswith(".")) and sentence % 4 == 0
                d.text((x, top + 0.04 * band), wd[0], font=font, fill=red if first else ink)
                d.text((x + font.getlength(wd[0]), top + 0.04 * band), wd[1:], font=font, fill=ink)
                x += font.getlength(wd + " ")
                sentence += wd.endswith(".")
                i += 1
    return np.asarray(tex).astype(np.float32) / 255, i


def drape(model, cut, im, job, k):
    """One sheet: returns the crop's box in the plate, the crop with the
    Latin draped on the sheet (None if the sheet stays as generated), the
    sheet's pixels in the crop and the check picture."""
    x0, y0, x1, y1, quad = job
    H, W = im.shape[:2]
    m = max(24, max(x1 - x0, y1 - y0) // 2)                          # the surroundings tell the model what the sheet is
    cx0, cy0, cx1, cy1 = max(x0 - m, 0), max(y0 - m, 0), min(x1 + m, W), min(y1 + m, H)
    crop = im[cy0:cy1, cx0:cx1]
    h, w = crop.shape[:2]
    region = np.zeros((h, w), bool)
    if quad is None:                                                 # the whole sheet, not pale things beside it
        region[max(y0 - 12 - cy0, 0):y1 + 12 - cy0, max(x0 - 12 - cx0, 0):x1 + 12 - cx0] = True
        whole = cv2.dilate(cut(crop, (x0 - cx0, y0 - cy0, x1 - cx0, y1 - cy0)).astype(np.uint8), el(5)) > 0
        region = whole if 0.3 * region.sum() < whole.sum() < 4 * region.sum() else region & whole
    else:                                                            # one page of an open book
        region = cv2.dilate(cv2.fillConvexPoly(np.zeros((h, w), np.uint8), (quad - (cx0, cy0)).astype(np.int32), 1),
                            np.ones((5, 5), np.uint8)) > 0
    mask, inner, ink = sheet(crop, region)
    box = (cx0, cy0, cx1, cy1)
    # the old script out: each pen stroke takes the tone of the sheet beside it (of 7 x 7 pixels, the tone three
    # quarters of them are darker than: strokes are the darker minority). The sheet's stains and shading stay.
    # Wide or black marks (a drawn emblem, a pen lying on the page) stay too, and the Latin keeps clear of them
    paper = cv2.GaussianBlur(np.stack([percentile_filter(crop[..., c], 75, size=7) for c in range(3)], -1)
                             .astype(np.float32), (0, 0), 1.0)
    lum = crop.astype(np.float32).mean(-1)
    level = cv2.GaussianBlur(cv2.morphologyEx(lum, cv2.MORPH_CLOSE, el(21)), (0, 0), 3)
    stroke = np.clip((paper.mean(-1) - lum) / np.maximum(paper.mean(-1), 1) / 0.04, 0, 1) * inner * (lum > 0.35 * level)
    wa = cv2.GaussianBlur(cv2.dilate(stroke, np.ones((3, 3), np.uint8)), (0, 0), 1.0)[..., None]
    clean = crop.astype(np.float32) * (1 - wa) + paper * wa
    marks = clean.mean(-1) < 0.4 * level
    blank = inner * (cv2.dilate(marks.astype(np.uint8), el(5)) == 0)
    if inner.sum() < 400:
        print(f"sheet {k}: too small, left as generated")
        return box, None, None, None
    up = int(np.clip(round(800 / max(h, w)), 2, 6))
    big = cv2.resize(crop, (w * up, h * up), interpolation=cv2.INTER_LANCZOS4)
    with torch.no_grad():
        geo = model.infer(torch.from_numpy(big.astype(np.float32) / 255).permute(2, 0, 1).cuda())
    down = lambda a: cv2.resize(np.nan_to_num(a.cpu().numpy(), posinf=0, neginf=0), (w, h), interpolation=cv2.INTER_AREA)
    P, N = down(geo["points"]), down(geo["normal"])
    mask &= P[..., 2] > 0
    wgt = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.5)[..., None]
    N = cv2.GaussianBlur(N * mask[..., None], (0, 0), 1.5) / np.maximum(wgt, 1e-6)   # the sheet is smooth: average within it
    z, ok, stretch = flatten(surface(P, N, mask), mask)
    yy, xx = np.nonzero(ok)
    a, b = z[ok] - z[ok].mean(), (xx + 1j * yy) - (xx + 1j * yy).mean()
    fit = [(a.conjugate() * b).sum(), (a * b).sum()]                 # the chart turned onto the plate, as it is and mirrored
    if abs(fit[1]) > abs(fit[0]):
        z = z.conjugate()
    z = z * (fit[int(abs(fit[1]) > abs(fit[0]))] / max(abs(f) for f in fit))
    dux, duy = np.gradient(z.real, axis=1), np.gradient(z.real, axis=0)
    dvx, dvy = np.gradient(z.imag, axis=1), np.gradient(z.imag, axis=0)
    good = ok & np.isfinite(dux + duy + dvx + dvy)
    J = np.stack([np.stack([dux[good], duy[good]], -1), np.stack([dvx[good], dvy[good]], -1)], -2)
    per_px = np.percentile(np.linalg.svd(J, compute_uv=False)[:, 1], 10)   # metres per plate pixel where the sheet faces the camera
    _, _, mx, my = unwrap(z, ok, 1 / per_px)
    tilt, clear = script(cv2.remap(ink, mx, my, cv2.INTER_LINEAR, borderValue=0))
    if clear < 4:                                                    # no script to go by: the sheet's own edges
        pts = np.stack([z[ok].real, z[ok].imag], 1).astype(np.float32)
        tilt = (cv2.minAreaRect(pts)[2] + 45) % 90 - 45
    z = z * np.exp(-1j * np.radians(tilt))
    wave = 0.0
    if quad is None:                                                 # the warp the edges show and the surface did not: see waves()
        _, c, mx, my = unwrap(z, ok, 1 / per_px)
        flat = cv2.remap(mask.astype(np.float32), mx, my, cv2.INTER_LINEAR, borderValue=0) > 0.5
        limit = 0.08 * np.sqrt(flat.sum())
        dy, dx = waves(flat, limit), waves(flat.T, limit).T
        cc = np.nan_to_num(np.stack([c.real, c.imag], -1), nan=-1).astype(np.float32)
        at = lambda a: cv2.remap(a.astype(np.float32), cc[..., 0], cc[..., 1], cv2.INTER_LINEAR, borderValue=0)
        z = z - (at(dx) + 1j * at(dy)) * per_px
        wave = float(max(np.abs(dx[flat]).max(), np.abs(dy[flat]).max()))
    size, c, mx, my = unwrap(z, ok, up / per_px)
    on = lambda a: cv2.remap(a.astype(np.float32), mx, my, cv2.INTER_LINEAR, borderValue=0)
    # the text block: the largest upright rectangle in the flat sheet's hull, a margin in from its edges; a
    # sheet's seals, marks and torn places do not shape the block, they split its lines
    flat_in = (on(inner) > 0.9).astype(np.uint8)
    hull = cv2.convexHull(np.concatenate(cv2.findContours(flat_in, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]))
    shape = cv2.fillConvexPoly(np.zeros_like(flat_in), hull, 1)
    width = float(np.percentile(shape.sum(1), 90))
    band = float(np.clip(width / (14 if quad is not None else 11), 6 * up, 14 * up))
    shape = cv2.erode(shape, el(2 * int((0 if quad is not None else 0.06 * width) + 0.3 * band) + 1))
    rect = tuple(up * v for v in block(shape[::up, ::up] > 0))
    free = cv2.erode((on(blank) > 0.9).astype(np.uint8), el(2 * int(0.3 * band) + 1)) > 0
    tex, words = write(size, free, rect, band, k)
    unit = N[ok] / np.linalg.norm(N[ok], axis=1, keepdims=True)
    mean = unit.mean(0) / np.linalg.norm(unit.mean(0))
    bend = np.percentile(np.degrees(np.arccos(np.clip(unit @ mean, -1, 1))), 95)     # how far the sheet turns from its mean plane
    note = (f"sheet {k}: enlarged {up}x, bend {bend:.0f} deg, edge waves {wave:.1f} px, chart area/surface area {stretch[0]:.2f}..{stretch[1]:.2f}, script tilt {tilt:.1f} deg "
            f"clearness {clear:.1f}, line height {band / up:.1f} px")
    # each pixel's place on the texture, at the enlarged size; pixels beside the chart take their neighbours' place
    cz, known = np.where(ok, c, 0), ok.copy()
    for _ in range(12):
        s = cv2.blur(np.stack([cz.real, cz.imag], -1) * known[..., None], (3, 3))
        n = cv2.blur(known.astype(np.float64), (3, 3))
        fill = (~known) & (n > 1e-6)
        cz = np.where(fill, (s[..., 0] + 1j * s[..., 1]) / np.maximum(n, 1e-9), cz)
        known |= fill
    cu = cv2.resize(np.stack([cz.real, cz.imag], -1).astype(np.float32), (w * up, h * up), interpolation=cv2.INTER_LINEAR)
    grid = big.copy()
    line = np.floor(cu[..., 1] / band)
    col = np.floor(cu[..., 0] / (2 * band))
    on_sheet = cv2.resize(mask.astype(np.uint8), (w * up, h * up), interpolation=cv2.INTER_NEAREST) > 0
    grid[on_sheet & (np.abs(np.gradient(line, axis=0)) + np.abs(np.gradient(line, axis=1)) > 0)] = (0, 230, 255)
    grid[on_sheet & (np.abs(np.gradient(col, axis=0)) + np.abs(np.gradient(col, axis=1)) > 0)] = (255, 220, 0)
    if words < 8:                                                    # too little room to read as a written sheet
        print(note + f"; {words} words fitted, sheet left as generated")
        return box, None, None, np.concatenate([grid, big], 1)
    took = cv2.remap(cv2.GaussianBlur(tex, (0, 0), 0.6), cu[..., 0], cu[..., 1], cv2.INTER_LINEAR, borderValue=0)
    took *= cv2.GaussianBlur(cv2.resize(inner, (w * up, h * up), interpolation=cv2.INTER_NEAREST).astype(np.float32),
                             (0, 0), up)[..., None]
    took = 0.85 * cv2.resize(took, (w, h), interpolation=cv2.INTER_AREA)
    out = (clean * (1 - took)).clip(0, 255).astype(np.uint8)         # the ink darkens the sheet
    print(note + f", {words} words")
    return box, out, cv2.dilate(mask.astype(np.uint8), el(5)) > 0, np.concatenate(
        [grid, cv2.resize(out, (w * up, h * up), interpolation=cv2.INTER_CUBIC)], 1)


def main(name):
    im = np.asarray(Image.open(os.path.join(G.GEN, f"plate_{name}_{GP.PICKS[name]}.png")).convert("RGB")).copy()
    H, W = im.shape[:2]
    jobs = [(x0, y0, x1, y1, None) for x0, y0, x1, y1, *_ in GP.PARCHMENTS.get(name, [])]
    for quad in GP.PAGES.get(name, []):
        q = np.array(quad)
        jobs.append((int(q[:, 0].min()), int(q[:, 1].min()), int(q[:, 0].max()), int(q[:, 1].max()), q))
    model, cut = MoGeModel.from_pretrained("Ruicheng/moge-2-vitl-normal").cuda().eval(), cutter()
    src, checks, done = im.copy(), [], 0
    for k, job in enumerate(jobs):
        (cx0, cy0, cx1, cy1), out, sel, check = drape(model, cut, src, job, k)
        if out is not None:
            im[cy0:cy1, cx0:cx1][sel] = out[sel]
            done += 1
        if check is not None:
            checks.append(check)
    GP.pick(name)
    Image.fromarray(im).save(os.path.join(G.ROOT, "wip", "scene3d", f"{name}.png"))
    rows = [[]]
    for c in checks:                                                 # the check picture: rows up to 2400 px wide
        c = cv2.resize(c, (int(c.shape[1] * 600 / c.shape[0]), 600), interpolation=cv2.INTER_AREA)
        if rows[-1] and sum(r.shape[1] + 8 for r in rows[-1]) + c.shape[1] > 2400:
            rows.append([])
        rows[-1].append(np.pad(c, ((0, 8), (0, 8), (0, 0))))
    rows = [np.concatenate(r, 1) for r in rows if r]
    if rows:
        wide = max(r.shape[1] for r in rows)
        Image.fromarray(np.concatenate([np.pad(r, ((0, 0), (0, wide - r.shape[1]), (0, 0))) for r in rows])).save(
            os.path.join(G.ROOT, "wip", "preview", f"sheets-{name}.png"))
    print(f"{name}: wrote Latin on {done} of {len(jobs)} sheets")


if __name__ == "__main__":
    main(sys.argv[1])
