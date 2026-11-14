"""Single figures for the crowd of the muster plate: Mechanicum personnel, each as a picture of its own with a
transparent ground. src/muster/host.py sets thousands of them on the walks.

    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 HF_HUB_OFFLINE=1 .venv-moge/bin/python src/muster/figures.py gen [sheet[:seed] ...]
    python3 src/muster/figures.py cut        # wip/muster/figures/<sheet><seed>_<n>.png, wip/preview/muster-figures.png

A sheet is a kind of personnel in a view: `adepts` is the side view, `adepts-away` the same kind in the view `away`.
The user on a crowd of side views: "must face the direction of walk, not right or left". A figure that walks along a
walk is seen from behind or from the front, a little from its side: VIEWS holds those views. The image model draws
the rear view and the front view. Asked for a three-quarter rear view it drew plain rear views, and asked for a
three-quarter front view it drew front views, a few of them turned a little.

The image model draws one row of figures per sheet on a black ground, or on a white one against the prompt; `cut`
takes the ground out, whichever it is, and saves every figure, TALL pixels tall. DROP names figures that are not one
whole figure in side view; FLIP names figures that walk to the left and are mirrored.

The sheet `bearers` holds figures that carry a tall standard: the user on a crowd of figures of one height: "it is
uniformly flat". A bearer is cut with its standard as one picture, LONG pixels tall.
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
GEN, OUT = os.path.join(ROOT, "wip", "gen"), os.path.join(ROOT, "wip", "muster", "figures")
TALL, LONG = 256, 640
SEEDS = (1, 2)
ROW = ("Character line-up, concept art sheet: a single row of eight separate full-body figures of the Adeptus Mechanicus "
       "from Warhammer 40,000, {view}, evenly spaced "
       "with a gap between them, not touching, each whole figure visible from head to feet. {who} Flat even studio "
       "light, no cast shadows, isolated on a pure black background, nothing else in the frame, no text")
VIEWS = {
    "": "each shown in strict side view, in profile, walking towards the right",
    "away": "each shown from behind, in rear view, with its back to the viewer, walking straight away from the viewer; no face is visible",
    "near": "each shown from the front in three-quarter front view: the figure walks towards the viewer and "
            "towards the right, its body and its head turned a little to the right",
}
SHEETS = {
    "adepts": "They are hooded tech-priest adepts in long crimson robes: most robes battered, torn at the hem, patched "
              "and stained with soot and oil, two robes clean and bright red; some carry a staff with a cog wheel on "
              "top, some have cables and a brass pack on the back.",
    "workers": "They are forge workers and menials: bare-headed or in leather caps and goggles, in grey and brown rags "
               "and leather aprons with tool belts, carrying wrenches, hammers and sacks; dirty and tired.",
    "skitarii": "They are skitarii soldiers in long dusty red-brown coats, rounded steel helmets and breathing masks, "
                "each with a long lance held upright, and servitors with metal arms and legs.",
    "magi": "They are enginseers: scorched and oil-stained red robes over heavy mechanical bodies, extra mechanical "
            "arms on the back, a great cog-toothed axe held upright, a smoking censer on a chain.",
    "bearers": "They are standard bearers: each a hooded tech-priest in a battered crimson robe, small at the bottom of "
               "the picture, who holds upright one very tall thin iron pole, three times as tall as he is. On top of "
               "each pole a different thing: a great brass cog wheel with a skull in it, a narrow tattered red banner "
               "on a crossbar, a smoking brass censer on chains, an iron lantern cage with a flame, a winged cog icon, "
               "a long red pennant, a brass sunburst, a skull with cables.",
}
# names of figures, as "adepts1_3"; the bearers of seed 1 stand on a ground that is not one colour and are cut badly
DROP, FLIP = {"bearers1_1", "bearers1_2", "bearers1_4"}, set()


def gen(*names):
    import gentextures as G
    for name in names or SHEETS:
        name, _, seed = name.partition(":")
        kind, _, view = name.partition("-")
        G.JOBS[f"figures_{name}"] = (2432, 768, ROW.format(view=VIEWS[view], who=SHEETS[kind]))
        G.generate(f"figures_{name}", (int(seed),) if seed else SEEDS)


def bare(image, near=38):
    """The sheet without its ground, with transparency. The ground is the area that touches the border and has the
    colour of the border, black or white, within `near`. On a white ground, the white that a figure encloses is
    ground as well: the inside of a cog wheel, the room between an arm and a body. On a black ground it is kept,
    because a figure has black parts of its own."""
    from scipy import ndimage
    from PIL import ImageFilter
    a = np.asarray(image, np.int16)
    edge = np.median(np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]]), 0)
    regions, _ = ndimage.label(np.abs(a - edge).max(2) < near)
    border = np.unique(np.concatenate([regions[0], regions[-1], regions[:, 0], regions[:, -1]]))
    ground = np.isin(regions, border[border > 0])
    if edge.mean() > 200:
        ground |= ndimage.binary_opening(np.abs(a - edge).max(2) < near // 2, iterations=2)
    out = image.copy()
    out.putalpha(Image.fromarray(np.where(ground, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0)))
    return out


def cut():
    from scipy import ndimage
    os.makedirs(OUT, exist_ok=True)
    for old in os.listdir(OUT):
        os.remove(os.path.join(OUT, old))
    kept = []
    for name in [kind + "-" * bool(view) + view for view in VIEWS for kind in SHEETS]:
        for seed in SEEDS:
            if not os.path.exists(os.path.join(GEN, f"figures_{name}_{seed}.png")):
                continue
            sheet = bare(Image.open(os.path.join(GEN, f"figures_{name}_{seed}.png")).convert("RGB"))
            alpha = np.asarray(sheet.getchannel("A")) > 40
            parts, count = ndimage.label(alpha)
            boxes = [b for b in ndimage.find_objects(parts) if b[0].stop - b[0].start > 0.55 * sheet.height]
            for n, (rows, cols) in enumerate(sorted(boxes, key=lambda b: b[1].start), 1):
                key = f"{name}{seed}_{n}"
                wide, high = cols.stop - cols.start, rows.stop - rows.start
                if key in DROP or not (0.08 if name.startswith("bearers") else 0.18) < wide / high < 0.8:
                    continue
                figure = sheet.crop((cols.start, rows.start, cols.stop, rows.stop))
                one = np.asarray(figure).copy()
                one[..., 3] = np.where(parts[rows, cols] == parts[rows, cols][np.asarray(figure.getchannel("A")) > 40][0], one[..., 3], 0)
                tall = LONG if name.startswith("bearers") else TALL
                figure = Image.fromarray(one).resize((max(round(wide * tall / high), 1), tall), Image.LANCZOS)
                if key in FLIP:
                    figure = figure.transpose(Image.FLIP_LEFT_RIGHT)
                figure.save(os.path.join(OUT, key + ".png"))
                kept.append((key, figure))
    font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 16)
    per = 10
    page = Image.new("RGB", (per * 150, ((len(kept) + per - 1) // per) * (TALL + 26)), (60, 60, 66))
    draw = ImageDraw.Draw(page)
    for k, (key, figure) in enumerate(kept):
        x, y = (k % per) * 150, (k // per) * (TALL + 26)
        figure = figure.resize((max(round(figure.width * TALL / figure.height), 1), TALL), Image.LANCZOS)
        page.paste(figure, (x + (150 - figure.width) // 2, y + 22), figure)
        draw.text((x + 4, y + 2), key, fill=(255, 220, 140), font=font)
    page.save(os.path.join(ROOT, "wip", "preview", "muster-figures.png"))
    print(len(kept), "figures; wrote wip/preview/muster-figures.png", page.size)


if __name__ == "__main__":
    {"gen": gen, "cut": cut}[sys.argv[1]](*sys.argv[2:])
