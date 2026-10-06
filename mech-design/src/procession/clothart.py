"""The picture of the Mad Cat's cloth banner (src/procession/cloth.py): a holy
cloth in the two colours of the household, red velvet embroidered with bone
thread, 1 m wide and 3 m long, with a forked lower end.

`layout` draws where the thread lies, from the top down:

    AVE OMNISSIAH
    a cog wheel that holds the mark of Stellars Tech, the two halves of
    resources/assets/stellars_tech_ai_lab_gh_behemoth_logo.svg without its
    lettering. The wheel's disc is parted as the Machina Opus is: the left
    half of the mark is bone on red, the right half red on bone
    STELLARS in binary, eight bytes in two rows
    PER CALCULUM AD ASTRA
    the cog with the skull of resources/assets/zl789e1341kd1.jpg between two
    stars of the mark
    DEUS IN MACHINA
    three small cogs, a star in a lozenge, a star in each tail of the fork
    and in each corner of the wheel's square

and a border of two lines with cog teeth between them and a chain of beads
inside it. The inscriptions are
set in type, so every letter is right.

`embroider` turns the layout into the picture. The velvet is a picture that
Z-Image-Turbo paints (`velvet`: worn silk velvet alone, no ornament), set to
the household's red and made dirtier towards the lower end. The image model
does not paint the embroidery: asked to paint the layout again, it changes
letters and the mark. The thread is laid in ridges that follow the outline
of every shape, stands over the velvet, is lit from the upper left, has a
darker cord along its edges and throws a shadow on the pile; a few stitches
are worn through.

    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=2 HF_HUB_OFFLINE=1 \\
        ../w40k-mechanicum/.venv-moge/bin/python src/procession/clothart.py velvet [seeds]   # wip/gen/cloth_velvet_<seed>.png, wip/preview/procession/cloth-velvet.jpg
    python3 src/procession/clothart.py [seed]     # resources/assets/cloth-madcat.png (with the fork cut out) and
                                                  # cloth-madcat_silk.png (where the thread is); wip/preview/procession/cloth-madcat.png
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
A = os.path.join(ROOT, "resources", "assets")
W, H = 800, 2400                   # the picture; 800 pixels are 1 m
K = 2                              # the layout is drawn K times as large and reduced
FORK = 260                         # how far the notch of the lower end reaches up
RED, BONE = (124, 29, 24), (177, 166, 142)                 # the household's red and bone of src/procession/cloth.py, as sRGB
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
MONO = "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"
GEN = os.path.join(ROOT, "wip", "gen")
VELVET = 4                         # the draft of the velvet in use
PROMPT = ("A length of antique deep crimson silk velvet, centuries old: the pile crushed and rubbed thin in patches, faint creases, "
          "dust and candle soot worked into the cloth, a faint tone-on-tone damask of small cog wheels woven into the pile. One "
          "colour only. Museum textile scan, flat frontal orthographic view, evenly lit, no shadows, no background: the cloth "
          "fills the whole frame edge to edge. No embroidery, no ornament in another colour, no text, no border.")


def velvet(seeds):
    """Drafts of the velvet alone, painted by Z-Image-Turbo."""
    import torch
    from diffusers import ZImagePipeline
    pipe = ZImagePipeline.from_pretrained("Tongyi-MAI/Z-Image-Turbo", torch_dtype=torch.bfloat16).to("cuda")
    sheet = Image.new("RGB", (len(seeds) * 400, 1200))
    for k, seed in enumerate(seeds):
        im = pipe(prompt=PROMPT, width=W, height=H, num_inference_steps=9, guidance_scale=0.0, generator=torch.Generator("cuda").manual_seed(seed)).images[0]
        im.save(os.path.join(GEN, f"cloth_velvet_{seed}.png"))
        sheet.paste(im.resize((400, 1200), Image.LANCZOS), (400 * k, 0))
        print("velvet", seed, flush=True)
    sheet.save(os.path.join(ROOT, "wip", "preview", "procession", "cloth-velvet.jpg"), quality=90)


def _polygons(path):
    """The closed outlines of an SVG path, as arrays of points."""
    from svgelements import Path, Move
    out = []
    for sub in path.as_subpaths():
        pts = [(seg.point(t).x, seg.point(t).y) for seg in Path(sub) if not isinstance(seg, Move) for t in np.linspace(0.0, 1.0, 9)]
        out.append(np.array(pts))
    return out


def _fill(size, polygons):
    """A mask of `size` pixels: inside an odd number of the outlines."""
    m = np.zeros(size[::-1], bool)
    for p in polygons:
        one = Image.new("1", size, 0)
        ImageDraw.Draw(one).polygon([tuple(q) for q in p], fill=1)
        m ^= np.asarray(one)
    return m


def mark(width):
    """The mark of Stellars Tech, `width` pixels wide: the mask of its left
    half, the mask of its right half, the column of the gap between them,
    and the outline of its star about the star's centre, at that size."""
    from svgelements import SVG, Path                      # the environment that paints the velvet does not have it
    svg = SVG.parse(os.path.join(A, "stellars_tech_ai_lab_gh_behemoth_logo.svg"))
    part = {e.id: _polygons(e) for e in svg.elements() if isinstance(e, Path) and e.id in ("path2", "path3", "path5", "path6", "path7", "path8")}
    pts = np.concatenate([p for ps in part.values() for p in ps])
    lo, s = pts.min(0), width / np.ptp(pts[:, 0])
    size = (width, int(np.ptp(pts[:, 1]) * s) + 1)
    fit = lambda ps: [(p - lo) * s for p in ps]
    left = _fill(size, fit(part["path2"]))                 # the gear half; its second outline is the star, which stays open
    right = _fill(size, fit(part["path3"])) | _fill(size, fit(part["path5"] + part["path6"] + part["path7"] + part["path8"]))
    gap = ((part["path2"][0][:, 0].max() + part["path3"][0][:, 0].min()) / 2 - lo[0]) * s
    star = fit(part["path2"])[1]
    return left, right, gap, star - star.mean(0)


def _cog(r, teeth, rim, scale):
    """The outline of a cog wheel about the origin: its teeth reach `r`, and
    the gaps between them lie 0.55 `rim` lower; both times `scale`."""
    a = np.linspace(0.0, 2 * np.pi, teeth * 40, endpoint=False)
    rad = np.where((a * teeth / (2 * np.pi)) % 1.0 < 0.5, r, r - rim * 0.55) * scale
    return rad * np.sin(a), -rad * np.cos(a)


def wheel(r):
    """The cog wheel with the mark of Stellars Tech on a square of 2 r
    pixels, its teeth reaching the square's edge: where the thread lies (the
    rim, the left half of the mark, and the right half of the disc without
    the mark's right half), where the wheel is, and the outline of the
    mark's star at that size. src/sigil.py makes a badge of it."""
    k = r / 334                                            # the measures below are those of a wheel of 334 pixels
    im = Image.new("L", (2 * r, 2 * r), 0)
    d = ImageDraw.Draw(im)
    x, y = _cog(334, 16, 62, k)
    d.polygon(list(zip(r + x, r + y)), fill=255)
    body = np.asarray(im) > 0
    d.ellipse([r - 266 * k, r - 266 * k, r + 266 * k, r + 266 * k], fill=0)
    thread = np.asarray(im) > 0
    left, right, gap, star = mark(round(360 * k))
    yy, xx = np.mgrid[:2 * r, :2 * r]
    x0, y0 = int(r - gap), int(r - left.shape[0] / 2)
    half = np.zeros_like(thread)
    half[y0:y0 + right.shape[0], x0:x0 + right.shape[1]] = right
    thread |= (np.hypot(xx - r, yy - r) <= 250 * k) & (xx > r + 4 * k) & ~half      # the disc's right half, with the mark's right half left open
    half[:] = False
    half[y0:y0 + left.shape[0], x0:x0 + left.shape[1]] = left
    thread |= half & (xx < r - 4 * k)
    return thread, body, star


def layout():
    """Where the thread lies and where the cloth is, as two masks of W x H
    pixels with values from 0 to 1."""
    w, h = W * K, H * K
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    cx = w / 2
    serif = lambda size: ImageFont.truetype(SERIF, size * K)

    def words(y, text, size, font=None):
        d.text((cx, y * K), text, font=font or serif(size), fill=255, anchor="mt", stroke_width=max(1, size * K // 30), stroke_fill=255)

    def lozenge(x, y, r):
        d.polygon([((x - r) * K, y * K), (x * K, (y - r) * K), ((x + r) * K, y * K), (x * K, (y + r) * K)], fill=255)

    def rule(y, x0=90, x1=W - 90):
        for a, b in ((x0, W / 2 - 34), (W / 2 + 34, x1)):
            d.rectangle([a * K, (y - 3) * K, b * K, (y + 3) * K], fill=255)
        lozenge(W / 2, y, 16)

    def cog(x, y, r, teeth, rim, hole):
        """A cog wheel: its teeth reach `r`, its rim is `rim` wide inside them, `hole` is the radius of what it leaves open."""
        px, py = _cog(r, teeth, rim, K)
        d.polygon(list(zip(x * K + px, y * K + py)), fill=255)
        d.ellipse([(x - hole) * K, (y - hole) * K, (x + hole) * K, (y + hole) * K], fill=0)

    ring, _, star = wheel(334 * K)

    def stars(x, y, size, fill=255):
        s = star * size / 360
        d.polygon([(x * K + p[0], y * K + p[1]) for p in s], fill=fill)

    words(84, "AVE OMNISSIAH", 62)
    rule(176)
    for x in (128, W - 128):                               # a star in every corner of the wheel's square
        for y in (252, 808):
            stars(x, y, 96)

    wy = 530                                               # the wheel with the mark
    canvas = np.asarray(im).copy()
    canvas[(wy - 334) * K:(wy + 334) * K, w // 2 - 334 * K:w // 2 + 334 * K][ring] = 255
    im = Image.fromarray(canvas)
    d = ImageDraw.Draw(im)

    mono = ImageFont.truetype(MONO, 30 * K)
    bits = [format(ord(c), "08b") for c in "STELLARS"]
    for row in range(2):
        d.text((cx, (896 + 42 * row) * K), " ".join(bits[4 * row:4 * row + 4]), font=mono, fill=255, anchor="mt", stroke_width=K, stroke_fill=255)
    rule(1000)
    words(1026, "PER CALCULUM", 78)
    words(1112, "AD ASTRA", 116)
    rule(1250)

    # the cog with the skull, its black as thread, between two stars
    g = Image.open(os.path.join(A, "zl789e1341kd1.jpg")).convert("L").resize((330 * K, 330 * K), Image.LANCZOS)
    im.paste(255, (int(cx - 165 * K), 1275 * K), g.point(lambda v: 255 if v < 128 else 0))
    for x in (118, W - 118):
        stars(x, 1440, 150)
    rule(1630)
    words(1656, "DEUS IN", 100)
    words(1762, "MACHINA", 100)
    rule(1888)
    for x in (W / 2 - 170, W / 2, W / 2 + 170):
        cog(x, 1975, 58, 10, 26, 22)
        d.ellipse([(x - 9) * K, (1975 - 9) * K, (x + 9) * K, (1975 + 9) * K], fill=255)
    lozenge(W / 2, 2086, 40)
    stars(W / 2, 2086, 52, fill=0)
    for x in (150, W - 150):
        stars(x, 2215, 120)

    # the cloth: a rectangle with a notch in its lower end; the border follows its edge
    yy, xx = np.mgrid[:h, :w]
    cloth = Image.new("L", (w, h), 0)
    ImageDraw.Draw(cloth).polygon([(0, 0), (w, 0), (w, h), (cx, h - FORK * K), (0, h)], fill=255)
    edge = ndimage.distance_transform_edt(np.pad(np.asarray(cloth) > 0, 1))[1:-1, 1:-1] / K     # pixels of the picture to the cloth's edge
    lines = ((edge >= 14) & (edge < 21)) | ((edge >= 43) & (edge < 48))
    straight = yy < (h - (FORK + 60) * K)                                      # teeth along the two sides and the upper edge only
    side = (np.minimum(xx, w - 1 - xx) < yy) & straight
    teeth = (edge >= 21) & (edge < 34) & np.where(side, (yy // (13 * K)) % 2 == 0, (xx // (13 * K)) % 2 == 0) & (straight | (yy < 60 * K))
    beads = (np.abs(edge - 62) < 5) & (np.hypot((xx / K) % 34 - 17, (yy / K) % 34 - 17) < 6) & straight       # a chain of beads inside the border
    canvas = np.asarray(im).copy()
    canvas[lines | teeth | beads] = 255
    canvas[edge < 14] = 0
    small = lambda a: np.asarray(Image.fromarray(a).resize((W, H), Image.LANCZOS), np.float32) / 255
    return small(canvas), small(np.asarray(cloth))


def embroider(thread, cloth, draft, seed=7):
    """The picture (RGBA) and the mask of the thread, from the two masks of
    `layout` and the draft `draft` of the velvet."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[:H, :W].astype(np.float32)
    smooth = lambda cell: np.asarray(Image.fromarray(rng.random((H // cell + 2, W // cell + 2)).astype(np.float32)).resize((W, H), Image.BICUBIC))
    stitched = thread > 0.5
    worn = np.clip((smooth(3) - 0.90) * 9.0, 0, 1) * (smooth(110) > 0.66)      # a few stitches worn through, in patches
    m = thread * (1 - worn)

    soot = 1.0 - 0.32 * (yy / H) ** 2                                          # dirtier towards the lower end
    pile = Image.open(os.path.join(GEN, f"cloth_velvet_{draft}.png")).convert("RGB")
    pile = pile.crop((int(0.10 * W), int(0.03 * H), int(0.90 * W), int(0.97 * H))).resize((W, H), Image.LANCZOS)     # a draft has a white margin
    pile = np.asarray(pile.convert("L"), np.float32) / 255                     # its brightness alone: the cloth has one red
    velvet = np.array(RED, np.float32) / 255 * (np.clip(pile / pile.mean(), 0.6, 1.45) ** 0.55 * soot)[..., None]

    depth = ndimage.distance_transform_edt(stitched)                           # pixels from the edge of a shape into it
    echo = 0.5 + 0.5 * np.sin(depth * 2 * np.pi / 3.4 + 1.5 * smooth(6))       # ridges that follow the outline
    satin = 0.5 + 0.5 * np.sin((xx * 0.8 + yy * 0.6) * 2 * np.pi / 2.3 + rng.random((H, W)) * 1.2)
    height = ndimage.gaussian_filter(m, 1.6) + 0.10 * echo * m                 # the thread stands over the velvet
    gy, gx = np.gradient(height)
    lit = 1.0 - 1.5 * (0.6 * gx + 0.8 * gy)                                    # light from the upper left
    tarnish = np.clip(0.72 + 0.45 * smooth(60), 0.7, 1.05)
    cord = np.clip(1.0 - depth / 2.2, 0, 1) * stitched                         # a darker cord along the edge of every shape
    silk = np.array(BONE, np.float32) / 255 * ((0.74 + 0.16 * echo + 0.14 * satin) * tarnish * soot * lit * (1 - 0.45 * cord))[..., None]
    shadow = ndimage.gaussian_filter(np.roll(m, (4, 3), (0, 1)), 2.5)
    rgb = velvet * (1 - 0.55 * shadow[..., None]) * (1 - m[..., None]) + silk * m[..., None]
    rgba = np.dstack([np.clip(rgb, 0, 1), cloth])
    return Image.fromarray((rgba * 255).astype(np.uint8), "RGBA"), Image.fromarray((np.clip(m * tarnish, 0, 1) * 255).astype(np.uint8))


if __name__ == "__main__":
    if sys.argv[1:2] == ["velvet"]:
        velvet([int(a) for a in sys.argv[2:]] or [1, 2, 3, 4])
        sys.exit()
    picture, silk = embroider(*layout(), int(sys.argv[1]) if len(sys.argv) > 1 else VELVET)
    picture.save(os.path.join(A, "cloth-madcat.png"))
    silk.save(os.path.join(A, "cloth-madcat_silk.png"))
    sheet = Image.new("RGB", (W + 80, H + 80), (22, 22, 26))
    sheet.paste(picture, (40, 40), picture)
    sheet.save(os.path.join(ROOT, "wip", "preview", "procession", "cloth-madcat.png"))
    print("CLOTH madcat", picture.size)
