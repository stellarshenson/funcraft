"""The two badges of the welcome page, each an enamel badge in the page's
colours, held by a steel rim.

The sigil is the cog with the skull of resources/assets/zl789e1341kd1.jpg, a
black glyph on white. The glyph has two inks: its black, and the white that
the black encloses (the white round the glyph is no part of it and becomes
transparent). A variant gives each of the two an enamel:

    red-black   black stays black, red takes the place of the white
    red-bone    red takes the place of the black, bone the place of the white

The wheel is the cog wheel with the mark of Stellars Tech that
src/procession/clothart.py embroiders on the Mad Cat's cloth, in red and
bone: what is thread there is bone enamel here.

Steel wire runs along every edge between the two enamels, and a steel rim
runs round the whole shape: without the rim a dark enamel does not show on
the dark page. A badge has relief (the steel stands over the enamel, the
enamel is a little domed) and is shaded by a light from the upper left.

    python3 src/sigil.py                 # wip/crest/sigil-<variant>.png and sigil-stellars.png, 1024 x 1024; wip/preview/sigil.png: all
                                         # three, large and at page size; resources/assets/cog-stellars.png, which src/welcome.py embeds
    python3 src/sigil.py use <variant>   # resources/assets/cog-mechanicum.png, which src/welcome.py embeds
"""
import os, sys
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLYPH = os.path.join(ROOT, "resources", "assets", "zl789e1341kd1.jpg")
OUT = os.path.join(ROOT, "wip", "crest")
WORK, SIDE = 2048, 1024            # the badge is drawn at WORK pixels and reduced to SIDE
MARGIN = 120                       # room round the glyph for the rim, in WORK pixels
RIM, WIRE = (26, 10), 8            # the rim's width outside and inside the glyph's outline, and half the width of a wire
RED, BLACK, BONE, STEEL = (0.84, 0.21, 0.16), (0.03, 0.032, 0.04), (0.85, 0.80, 0.69), (0.62, 0.70, 0.79)   # --red, --bone and --steel of the page, as enamel
VARIANTS = {"red-black": (BLACK, RED), "red-bone": (RED, BONE)}     # the enamel of the glyph's black, of its enclosed white
LIGHT = np.array([-0.45, -0.60, 0.66])                               # towards the light: from the left and from above (y runs down)


def masks():
    """The glyph at WORK pixels: where its black is, and where the white is that the black encloses."""
    g = Image.open(GLYPH).convert("L").resize((WORK - 2 * MARGIN,) * 2, Image.BICUBIC)
    a = np.ones((WORK, WORK), np.float32)
    a[MARGIN:-MARGIN, MARGIN:-MARGIN] = np.asarray(g, np.float32) / 255
    black = ndimage.gaussian_filter(a, 3.0) < 0.5
    lab, _ = ndimage.label(~black)
    outside = np.isin(lab, np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
    return black, ~black & ~outside


def wheel():
    """The cog wheel with the mark of Stellars Tech at WORK pixels: where its
    red is, which stands for the glyph's black, and where its bone is."""
    sys.path.insert(0, os.path.join(ROOT, "src", "procession"))
    import clothart
    thread, body, _ = clothart.wheel(WORK // 2 - MARGIN)
    return np.pad(body & ~thread, MARGIN), np.pad(thread, MARGIN)


def badge(black, white, variant):
    """The badge of a shape with the two inks `black` and `white`, as an
    RGBA picture of SIDE pixels."""
    body = black | white
    out = ndimage.distance_transform_edt(~body)            # outside the glyph: pixels to its outline
    into = ndimage.distance_transform_edt(body)            # inside: pixels to its outline
    seam = np.maximum(ndimage.distance_transform_edt(black), ndimage.distance_transform_edt(~black))   # pixels to the edge of the black
    steel = (body & (into <= RIM[1])) | (~body & (out <= RIM[0])) | (body & (seam <= WIRE))
    alpha = body | (out <= RIM[0])
    field = ndimage.distance_transform_edt(~steel)         # in the enamel: pixels to the nearest steel
    height = np.where(steel, 1.0, 0.5 + 0.14 * (1.0 - np.exp(-field / 45.0)))
    height = ndimage.gaussian_filter(np.where(alpha, height, 0.0).astype(np.float32), 3.5)
    gy, gx = np.gradient(height * 55.0)                    # the relief's slope; 55: how high the steel stands, in pixels
    normal = np.dstack([-gx, -gy, np.ones_like(gx)])
    normal /= np.linalg.norm(normal, axis=2, keepdims=True)
    light = LIGHT / np.linalg.norm(LIGHT)
    lit = np.clip(normal @ light, 0, 1)
    half = light + np.array([0, 0, 1.0])
    gloss = np.clip(normal @ (half / np.linalg.norm(half)), 0, 1)
    ink, paper = VARIANTS[variant]
    colour = np.where(black[..., None], np.array(ink), np.array(paper))
    shade = np.clip(field / 14.0, 0, 1) * 0.3 + 0.7        # the enamel is darker beside the steel
    enamel = colour * (0.55 + 0.55 * lit[..., None]) * shade[..., None] + 0.30 * gloss[..., None] ** 70
    metal = np.array(STEEL) * (0.30 + 0.85 * lit[..., None]) + 0.85 * gloss[..., None] ** 28
    rgb = np.clip(np.where(steel[..., None], metal, enamel), 0, 1)
    im = Image.fromarray((np.dstack([rgb, alpha.astype(np.float32)]) * 255).astype(np.uint8), "RGBA")
    return im.resize((SIDE, SIDE), Image.LANCZOS)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "use":
        Image.open(os.path.join(OUT, f"sigil-{sys.argv[2]}.png")).save(os.path.join(ROOT, "resources", "assets", "cog-mechanicum.png"))
        print("SIGIL in use:", sys.argv[2])
    else:
        os.makedirs(OUT, exist_ok=True)
        # all three on the page's ground with its hazard strip: large, and at the sizes the page shows them at
        sheet = Image.new("RGB", (2100, 760), (15, 20, 27))
        stripe = np.zeros((40, 2100, 3), np.uint8)
        yy, xx = np.mgrid[:40, :2100]
        stripe[:] = np.where((((xx + yy) // 14) % 2 == 0)[..., None], (242, 140, 56), (20, 26, 34))
        for k, (name, shape, variant, size) in enumerate((("red-black", masks, "red-black", 56), ("red-bone", masks, "red-bone", 56), ("stellars", wheel, "red-bone", 54))):
            im = badge(*shape(), variant)
            im.save(os.path.join(OUT, f"sigil-{name}.png"))
            x = 60 + 700 * k
            sheet.paste(Image.fromarray(stripe).crop((0, 0, 620, 40)), (x - 20, 600))
            big = im.resize((520, 520), Image.LANCZOS)
            sheet.paste(big, (x + 30, 40), big)
            small = im.resize((size, size), Image.LANCZOS)
            sheet.paste(small, (x + 290 - size // 2, 620 - size // 2), small)
            print("SIGIL", name)
        im.save(os.path.join(ROOT, "resources", "assets", "cog-stellars.png"))
        sheet.save(os.path.join(ROOT, "wip", "preview", "sigil.png"))
