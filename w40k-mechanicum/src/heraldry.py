"""The sigils on the banners of a plate. The image model paints an emblem of its own on every banner; this script
takes that emblem out and lays an exact sigil in its place: the Machina Opus of the Adeptus Mechanicus, or the cog
wheel with the mark of Stellars Tech.

    python3 src/heraldry.py glyphs                           # resources/assets/sigil-<name>-ink.png, from ../mech-design
    python3 src/heraldry.py clear <scene> <plate> <out>              # the banners of BANNERS[scene] without emblems
    python3 src/heraldry.py lay <scene> <cleared> <out> <plate>      # the sigils on them, in the gold of <plate>
    python3 src/heraldry.py check <scene> <plate> <out>              # wip/preview/sigils-<scene>.png: every banner before and after

The image model paints the cloth and the script lays the sigil. Asked to paint a sigil again, the model changes the
mark (../mech-design/src/procession/clothart.py), so no sigil passes through it.

- **Two inks** - a sigil is a map of two inks, light and dark. On a banner both are gold thread: the light ink bright
  gold, the dark ink old dark gold. A first version laid bone and black thread on a disc of plain cloth; the owner:
  the sigil "has a plain red envelope around it that stands out, while it should be just the glyph - likely in
  gold; the rest is the canvas of the banner"
- **Canvas** - where the model's emblem was, the banner's own cloth goes on: column by column, the colour of the
  cloth over the emblem runs into the colour of the cloth under it, and the weave of both is laid on. The folds of
  a banner run down it, so they run on through the place of the emblem
- **Colours of the plate** - the gold is as bright as the bright part of the emblem the model painted on that banner
  and takes a fifth of its colour. A far banner stands in haze, so its gold is paler: the sigil stands at the
  depth of its banner
- **Shading of the cloth** - the folds of the cloth, light and dark, run across the sigil
- **Wear** - a first sigil had even, bright thread with a clean edge on a banner that is stained, scorched and torn;
  the owner: "sigils are too clean compared to the rest of the banners". The thread is now as worn as its cloth
  (WEAR): tarnished, darkened by soot in patches and in streaks that run down the cloth, worn through to the cloth
  in patches and frayed at the edges of the glyph, and on a large sigil a scorched hole goes through cloth and
  thread, off its middle. `lay` writes the holes as the alpha of its picture
"""
import os, sys
import numpy as np, cv2
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "resources", "assets")
MECH = os.path.join(os.path.dirname(ROOT), "mech-design")
INK = 512                                  # side of a stored ink map in pixels
LIGHT, DARK = 255, 128                     # the values of the two inks in an ink map; 0 is no ink
SEAM = 18                                  # the rows of cloth over and under an emblem whose weave goes on in its place
GOLD = (228, 156, 48)                      # gold thread in the warm light of a plate
OLD = 0.5                                  # the dark ink is gold thread this bright against the light ink
# the wear of the thread: how bright it is against new thread and the share of its colour that is dirt; how much soot
# takes of its light where it is thickest; the share of thread lost in a worn patch and at a frayed edge; the radius
# of a scorched hole against that of the sigil, between two values, and the smallest sigil that has one
WEAR = dict(tarnish=(0.92, 0.2), soot=0.4, lost=(0.6, 0.7), hole=(0.05, 0.08), least=20)

# per scene, the banners that carry a sigil: (sigil, x, y, r, (ex, ey, rx, ry)). x, y, r: centre and radius of the sigil
# in plate pixels; the ellipse round the emblem the model painted, which is taken out
BANNERS = {
    "muster": [
        ("mechanicum", 326, 190, 40, (326, 190, 47, 49)), ("mechanicum", 610, 261, 28, (610, 261, 34, 35)),
        ("mechanicum", 730, 300, 21, (730, 300, 26, 27)), ("mechanicum", 824, 324, 17, (824, 324, 21, 22)),
        ("mechanicum", 908, 343, 12, (908, 343, 15, 16)), ("mechanicum", 953, 362, 9, (953, 362, 12, 13)),
        ("stellars", 1868, 303, 18, (1868, 303, 25, 27)), ("stellars", 2018, 284, 22, (2018, 286, 30, 34)),
        ("stellars", 2125, 262, 25, (2125, 264, 34, 37)), ("stellars", 2220, 236, 31, (2220, 240, 42, 44)),
        ("stellars", 2385, 198, 35, (2385, 200, 48, 60)),
    ],
}
# per scene, painted lights in the sky that are taken out: (x, y, radius)
STRAY = {"muster": [(2262, 163, 10)]}
CLOTH = ("A close view of an old war banner of heavy plain crimson cloth hanging from an iron crossbar: plain red fabric "
         "with soft folds, scorch marks, soot stains and small holes. No emblem, no symbol, no ornament. Smoke and dust "
         "haze, a frame from a war film, muted colours, grime")


def glyphs():
    """The ink maps of the two sigils, from the drawings of ../mech-design: the Machina Opus of its reference glyph
    (black is the dark ink, the white it encloses the light ink) and the cog wheel with the mark of Stellars Tech
    (the thread is the light ink, the rest of the wheel the dark ink)."""
    sys.path[:0] = [os.path.join(MECH, "src"), os.path.join(MECH, "src", "procession")]
    import sigil, clothart
    black, white = sigil.masks()
    ys, xs = np.where(black | white)
    side = max(np.ptp(xs), np.ptp(ys)) + 1
    opus = np.zeros((side, side), np.uint8)
    y0, x0 = (side - np.ptp(ys) - 1) // 2, (side - np.ptp(xs) - 1) // 2
    cut = (slice(ys.min(), ys.max() + 1), slice(xs.min(), xs.max() + 1))
    opus[y0:y0 + np.ptp(ys) + 1, x0:x0 + np.ptp(xs) + 1] = np.where(white[cut], LIGHT, np.where(black[cut], DARK, 0))
    thread, body, _ = clothart.wheel(INK)
    wheel = np.where(thread, LIGHT, np.where(body, DARK, 0)).astype(np.uint8)
    for name, ink in (("mechanicum", opus), ("stellars", wheel)):
        Image.fromarray(ink).resize((INK, INK), Image.NEAREST).save(os.path.join(ASSETS, f"sigil-{name}-ink.png"))
        print("wrote", f"sigil-{name}-ink.png")


def ellipse(shape, e, grow=0.0):
    """1 inside the ellipse e = (x, y, rx, ry) grown by `grow` pixels, on a picture of `shape`."""
    m = np.zeros(shape[:2], np.uint8)
    cv2.ellipse(m, (int(e[0]), int(e[1])), (int(e[2] + grow), int(e[3] + grow)), 0, 0, 360, 1, -1)
    return m


def fill(colour, known):
    """The colours of the known pixels, carried smoothly into the rest: each level of a pyramid holds the mean of the
    known pixels under it, and a pixel that is not known takes the colour of the level over it."""
    levels = [(colour * known[..., None], known.astype(np.float32))]
    while min(levels[-1][1].shape) > 2:
        c, k = levels[-1]
        size = (max(k.shape[1] // 2, 1), max(k.shape[0] // 2, 1))
        levels.append((cv2.resize(c, size, interpolation=cv2.INTER_AREA), cv2.resize(k, size, interpolation=cv2.INTER_AREA)))
    c, k = levels[-1]
    out = np.ones_like(c) * c.sum((0, 1)) / max(k.sum(), 1e-6)
    for c, k in reversed(levels):
        out = cv2.resize(out, (k.shape[1], k.shape[0]), interpolation=cv2.INTER_LINEAR)
        out = out * (1 - k[..., None]) + c
    return out


def clear(scene, src, out, cloth=None):
    """The plate without the emblems on its banners. In the ellipse of each emblem the banner's own cloth goes on.
    `cloth` is a picture that is not 0 where a banner's cloth is.

    Down each column of the ellipse the colour of the cloth over it runs into the colour of the cloth under it, and
    the weave of the SEAM rows of cloth next to it, over and under, is laid on, turned back and forth. The folds of
    a banner run down it, so they pass through. Three other ways failed: the cloth the image model painted there had
    folds of its own that ran out from the middle and a brighter tone, and stood as a pale disc; the weave of the
    cloth under the emblem, laid on top, brought that cloth's holes; the colours of the ring round the ellipse,
    carried in from all sides with a grain, stood as a plain disc that the owner saw at once."""
    plate = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
    H, W = plate.shape[:2]
    woven = np.asarray(Image.open(cloth)) > 0 if cloth else np.ones((H, W), bool)
    for x, y, r in STRAY.get(scene, []):
        plate = cv2.inpaint(plate.astype(np.uint8), ellipse(plate.shape, (x, y, r, r)), 5, cv2.INPAINT_TELEA).astype(np.float32)
    soft, fine = cv2.GaussianBlur(plate, (0, 0), 3), plate - cv2.GaussianBlur(plate, (0, 0), 4)
    for k, (_, x, y, r, e) in enumerate(BANNERS[scene]):
        hole = (ellipse(plate.shape, e, grow=3) > 0) & woven
        good = woven & ~(cv2.dilate(hole.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0)      # cloth that is no emblem
        new = plate.copy()
        for col in np.flatnonzero(hole.any(0)):
            rows = np.flatnonzero(hole[:, col])
            ya, yb = rows[0], rows[-1]
            sides = []
            for edge, step in ((ya - 3, -1), (yb + 3, 1)):            # the cloth over the emblem, and under it
                n = 0
                while n < SEAM and 0 <= edge + step * n < H and good[edge + step * n, col]:
                    n += 1
                sides.append((edge, step, n))
            if not max(n for _, _, n in sides) >= 4:
                continue                                              # no cloth beside this column: it stays
            t = (np.arange(ya, yb + 1) - ya + 0.5) / (yb - ya + 1)
            t = t * t * (3 - 2 * t)
            share = np.stack([1 - t, t], 1) * np.array([n >= 4 for _, _, n in sides])
            share /= share.sum(1, keepdims=True)
            run = np.zeros((yb - ya + 1, 3), np.float32)
            for (edge, step, n), w, far in zip(sides, share.T, (np.arange(ya, yb + 1) - ya, yb - np.arange(ya, yb + 1))):
                if n >= 4:
                    back = np.abs((far % (2 * n - 2)) - (n - 1))      # through the rows of cloth and back again
                    run += w[:, None] * (soft[edge, col] + fine[edge + step * back, col])
            new[ya:yb + 1, col] = run
        a = cv2.GaussianBlur(hole.astype(np.float32), (0, 0), 1.2)[..., None]
        plate = plate * (1 - a) + cv2.GaussianBlur(new, (0, 0), 0.5) * a
        print(f"CLEARED banner {k + 1} at ({x}, {y})", flush=True)
    Image.fromarray(np.clip(plate, 0, 255).astype(np.uint8)).save(out)
    print("CLEAR_DONE", out)


def inks(name, r):
    """The light and the dark ink of a sigil on a square of 2 r pixels, each from 0 to 1."""
    ink = np.asarray(Image.open(os.path.join(ASSETS, f"sigil-{name}-ink.png")))
    small = lambda m: cv2.resize(m.astype(np.float32), (2 * r, 2 * r), interpolation=cv2.INTER_AREA)
    return small(ink == LIGHT), small(ink == DARK)


def lay(scene, src, out, source, seed=5):
    """The sigils on the cleared plate `src`, in gold thread, on each banner as bright as the bright part of the
    emblem that the plate `source` shows there, and a little of its colour, which carries the haze."""
    plate = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
    first = np.asarray(Image.open(source).convert("RGB")).astype(np.float32)
    lum = lambda a: a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    gold = np.array(GOLD, np.float32) / lum(np.array(GOLD, np.float32))
    rng = np.random.default_rng(seed)
    H, W = plate.shape[:2]
    through = np.zeros((H, W), np.float32)                             # where a hole goes through a banner
    for k, (name, x, y, r, e) in enumerate(BANNERS[scene]):
        # the colours of this banner: the bright part of the painted emblem, and the darkest iron beside the banner
        old = first[ellipse(first.shape, e) > 0]
        bone = np.median(old[lum(old) >= np.percentile(lum(old), 80)], 0)             # how bright thread is on this banner, and how hazy
        bright = 1.3 * (0.85 * gold * lum(bone) + 0.15 * bone)
        bright = WEAR["tarnish"][0] * (bright * (1 - WEAR["tarnish"][1]) + lum(bright) * np.array([1.18, 0.96, 0.78], np.float32) * WEAR["tarnish"][1])
        dull = OLD * bright
        x0, y0 = x - r, y - r
        box = (slice(max(y0, 0), min(y0 + 2 * r, H)), slice(max(x0, 0), min(x0 + 2 * r, W)))
        part = (slice(box[0].start - y0, box[0].stop - y0), slice(box[1].start - x0, box[1].stop - x0))
        cloth = plate[box]
        light, dark = (m[part] for m in inks(name, r))
        # the folds of the cloth across the sigil
        soft = cv2.GaussianBlur(lum(cloth), (0, 0), 0.05 * r + 0.8)
        shade = np.clip((soft / np.median(soft)) ** 1.3, 0.5, 1.35)[..., None]
        grain = lambda cell: cv2.resize(rng.random((2 * r // cell + 2, 2 * r // cell + 2)).astype(np.float32), (2 * r, 2 * r),
                                        interpolation=cv2.INTER_CUBIC)[part]
        # soot in patches and in streaks down the cloth
        streaks = cv2.GaussianBlur(rng.random((2 * r, 2 * r)).astype(np.float32), (0, 0), sigmaX=0.7, sigmaY=0.5 * r)[part]
        streaks = np.clip((streaks - np.quantile(streaks, 0.6)) / (np.quantile(streaks, 0.97) - np.quantile(streaks, 0.6)), 0, 1)
        soot = 1 - WEAR["soot"] * np.maximum(np.clip(grain(max(2 * r // 5, 2)) * 1.7 - 0.45, 0, 1), 0.8 * streaks)[..., None]
        # thread worn through to the cloth in patches, and frayed where the glyph ends
        worn = np.clip((grain(max(r // 5, 2)) - 0.64) * 5, 0, 1)
        edge = 1 - np.clip((cv2.GaussianBlur(np.clip(light + dark, 0, 1), (0, 0), 0.05 * r + 0.6) - 0.45) / 0.4, 0, 1)
        kept = 1 - np.maximum(WEAR["lost"][0] * worn, WEAR["lost"][1] * edge * np.clip((grain(max(r // 9, 1)) - 0.3) * 3, 0, 1))
        light, dark = light * kept, dark * kept
        # a shadow of the thread on the cloth, below and to the right
        body = np.clip(light + dark, 0, 1)
        shadow = cv2.GaussianBlur(np.roll(body, (1, 1), (0, 1)), (0, 0), 1.2) * (1 - body)
        cloth = cloth * (1 - 0.30 * shadow[..., None])
        laid = cloth * (1 - light - dark)[..., None] + (bright * light[..., None] + dull * dark[..., None]) * shade * soot
        # as sharp as the plate round it, and no sharper
        a = cv2.GaussianBlur(body, (0, 0), 0.8)[..., None]
        laid = cv2.GaussianBlur(laid, (0, 0), 0.55) * a + laid * (1 - a)
        # scorched holes through cloth and thread: an uneven edge, the cloth dark round it
        yy, xx = np.mgrid[box[0], box[1]]
        for _ in range(r >= WEAR["least"]):                           # in the outer part of the sigil: its middle stays whole
            far, turn, size = r * rng.uniform(0.55, 0.9), 2.4 * k + rng.uniform(-0.4, 0.4), r * rng.uniform(*WEAR["hole"])      # on another side on every banner
            away = np.hypot(xx - (x + far * np.cos(turn)), (yy - (y + far * np.sin(turn))) / 1.4) / size      # taller than wide, as the holes of the cloth
            away = away * (0.75 + 0.5 * grain(max(r // 8, 1)))
            laid *= (1 - 0.6 * np.clip(2.2 - away, 0, 1) ** 2)[..., None]
            through[box] = np.maximum(through[box], np.clip((1.0 - away) * size / 0.8, 0, 1))
        plate[box] = laid
        print(f"SIGIL {name} on banner {k + 1} at ({x}, {y}), radius {r}: gold {bright.round().astype(int).tolist()}, "
              f"old gold {dull.round().astype(int).tolist()}", flush=True)
    Image.fromarray(np.dstack([np.clip(plate, 0, 255), 255 * (1 - through)]).astype(np.uint8), "RGBA").save(out)
    print("LAY_DONE", out)


def check(scene, src, out, zoom=4):
    """Every banner before and after, enlarged, in wip/preview/sigils-<scene>.png."""
    a, b = np.asarray(Image.open(src).convert("RGB")), np.asarray(Image.open(out).convert("RGBA")).astype(np.float32)
    b = (b[..., :3] * b[..., 3:] / 255 + np.array([150, 120, 100]) * (1 - b[..., 3:] / 255)).astype(np.uint8)      # a hole shows the air behind
    rows = []
    for _, x, y, r, e in BANNERS[scene]:
        half = int(2.2 * max(e[2], e[3]))
        y0, x0 = max(y - half, 0), min(max(x - half, 0), a.shape[1] - 2 * half)
        pair = np.concatenate([m[y0:y0 + 2 * half, x0:x0 + 2 * half] for m in (a, b)], 1)
        rows.append(cv2.resize(pair, (2 * 260, 260), interpolation=cv2.INTER_CUBIC))
    cols = [np.concatenate(rows[k::2], 0) for k in (0, 1)]
    tall = max(c.shape[0] for c in cols)
    cols = [np.pad(c, ((0, tall - c.shape[0]), (0, 0), (0, 0))) for c in cols]
    path = os.path.join(ROOT, "wip", "preview", f"sigils-{scene}.png")
    Image.fromarray(np.concatenate(cols, 1)).save(path)
    print("wrote", path)


if __name__ == "__main__":
    {"glyphs": glyphs, "clear": clear, "lay": lay, "check": check}[sys.argv[1]](*sys.argv[2:])
