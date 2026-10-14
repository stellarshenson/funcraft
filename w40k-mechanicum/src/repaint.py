"""Parts of a plate painted anew where the owner asked for other content. In the saint scene: the left window holds the
Imperial Knight of the owner's picture in stained glass, the right window the bell curve of the normal distribution
and the signs of statistics, the skull of the saint has dark eye sockets, a plain nasal hole and a red light in one
socket, and the Warhound Titan of the owner's picture stands in the open entrance on the right.

    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 HF_HUB_OFFLINE=1 .venv-moge/bin/python src/repaint.py paint saint [part] [version ...]
                                     # wip/gen/repaint-saint/<part>-<version>.png and wip/preview/repaint-saint-<part>.png
    python3 src/repaint.py apply saint <part>=<version> ...   # the chosen paint into the plate files; the old ones are
                                     # kept in wip/scene3d/before-repaint/

- **Hole** - only the part that changes is painted: the glass of a window inside its border of coloured panes, and
  never a thing that stands before it (a candelabra, a candle, its flame, a banner); SAM 2.1 cuts the glass and the
  things before it, and every row of the glass is filled out to the window's sides
- **Designs** - war machines that the image model drew from a prompt alone were rejected ("stained glass images are
  terrible"). A window is drawn piece by piece (src/glassdesign.py) and the model works over the design at a strength
  of 0.2 to 0.3 (the versions are strengths in percent); at 0.45 it turned the machines into armoured men. Signs that
  the model would change are laid over its result again
- **Things** - a machine of a picture is cut from its white ground, set at its place in the clean plate in the
  room's light, and the model works over it at a strength of 0.3; a moving thing before it keeps its own pixels
- **Scale** - a part is painted at twice the plate's scale and the skull at four times, then reduced: at the plate's
  scale the model has 60 pixels for a skull and draws no clear socket
- **Pictures** - a window lies on the backdrop: the plate, the clean plate and the clean plate's fill behind breaks
  (`pictures`) change alike, so the window is the same behind a moving banner. The skull is part of the saint, whose
  texture is the plate
"""
import os, sys, shutil
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLASS = ("A gothic cathedral stained glass window, lit from behind, small pieces of deep blue, red and gold glass held "
         "by black lead lines. ")
# per scene, the parts to paint: `box` (the part of the plate the model sees: x0, y0, x1, y1), `scale` (the model
# paints at this many times the plate's size), and the hole: `glass` (a window: its box for SAM, the depth of its
# border of coloured panes in plate pixels that stays, and the row below which its picture begins; `before` the boxes
# of the things that stand before it) or `ellipse` (cx, cy, rx, ry); `pictures`, the plate files that show the part
PARTS = {"saint": {
    # the windows from designs drawn piece by piece (src/glassdesign.py), which the model works over at a low
    # strength; the versions are strengths in percent, 0 is the design alone
    "window-left": dict(box=(112, 0, 384, 576), scale=2, glass=((123, 0, 376, 566), 16, 70), before=[(13, 367, 358, 769)],
                        pictures=("saint.png", "saint_clean.png", "saint_clean_bg.png"),
                        design="titan", reference="out/paste-20261014-160135.png",
                        prompt=GLASS + "In the middle a giant walking war machine of red, gold and grey glass pieces with a gold "
                               "halo of glass behind it, every piece outlined by black lead, glowing with the light behind"),
    "window-right": dict(box=(1232, 0, 1440, 592), scale=2, glass=((1249, 2, 1421, 578), 11, 75), panes=12,
                         before=[(1249, 389, 1530, 766), (1352, 352, 1380, 430)],
                         pictures=("saint.png", "saint_clean.png", "saint_clean_bg.png"), design="maths",
                         prompt=GLASS + "A medallion with the sign of the sum, the bell curve of the normal distribution over "
                                "the bars of a histogram, and small panes with mathematical signs, every piece outlined by "
                                "black lead, glowing with the light behind"),
    # the owner: "the warhound could protrude from the open entrance on the right, as it was standing vigil": the machine
    # of the owner's picture stands in the gilded opening at the right end, its head below the hanging sun-gear and
    # its legs behind the ledge; in the plate the sun-gear (element 4) stays before it
    "warhound": dict(box=(2080, 240, 2432, 592), scale=2, pictures=("saint.png", "saint_clean.png", "saint_clean_bg.png"),
                     thing=dict(reference="out/440px-LegioAudaxWarhound.webp", x=2260, top=332, width=330, ledge=578, light=0.55),
                     under={"saint.png": ["4"]},
                     prompt="A giant Warhound Titan war machine of Warhammer 40,000 standing still in a gilded archway at "
                            "the back of a dark gothic cathedral, dark red armour plates with gold trim, two large guns, "
                            "lit by warm candle light from the front and by the lit room behind it, deep shadows"),
    "skull": dict(box=(736, 96, 848, 208), scale=4, ellipse=(797, 150, 26, 21), pictures=("saint.png",),
                  prompt="Close view of the gilded skull of a statue under a dark hood, gold bone with dark gaps. Two "
                         "deep round empty eye sockets: the right one dark, the left one holds a small bright red "
                         "light that glows deep inside it and lights its rim red. Below them a plain dark nasal hole "
                         "of a human skull, an upside-down heart shape. Gold teeth"),
}}


def plate(scene, name=None):
    """A plate file of the scene as it was before it was painted anew."""
    name = name or f"{scene}.png"
    kept = os.path.join(ROOT, "wip", "scene3d", "before-repaint", name)
    return np.asarray(Image.open(kept if os.path.exists(kept) else os.path.join(ROOT, "wip", "scene3d", name)).convert("RGB"))


def sam(picture, boxes, points=None):
    """SAM 2.1's mask of the thing in each box, one mask over all of them."""
    import torch
    from transformers import Sam2Processor, Sam2Model
    rid = "facebook/sam2.1-hiera-large"
    proc, model = Sam2Processor.from_pretrained(rid), Sam2Model.from_pretrained(rid).to("cuda").eval()
    out = np.zeros(picture.shape[:2], bool)
    for k, b in enumerate(boxes):
        kw = dict(input_boxes=[[list(b)]])
        if points:
            kw.update(input_points=[[[list(points[k])]]], input_labels=[[[1]]])
        inputs = proc(images=Image.fromarray(picture), return_tensors="pt", **kw).to("cuda")
        with torch.no_grad():
            res = model(**inputs, multimask_output=False)
        m = proc.post_process_masks(res.pred_masks.cpu(), inputs["original_sizes"])[0][0, 0].numpy() > 0
        x0, y0, x1, y1 = b
        clip = np.zeros_like(m)
        clip[y0:y1, x0:x1] = True
        out |= m & clip
    return out


def placed(thing, s=1):
    """The machine of a picture, at its place in the plate (at `s` times the plate's scale): x0, y0, its colours, where it
    is. Its colours take the room's light: darker by `light`, warmer."""
    import glassdesign
    pic, where = glassdesign.cutout(os.path.join(ROOT, thing["reference"]))
    w = thing["width"] * s
    h = round(pic.shape[0] * w / pic.shape[1])
    pic = cv2.resize(pic, (w, h), interpolation=cv2.INTER_AREA) * thing["light"] * np.array([1.05, 0.95, 0.85], np.float32)
    where = cv2.resize(where.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST)
    where = cv2.erode(where, np.ones((2 * s + 1,) * 2, np.uint8)).astype(bool)       # without the white rim of its ground
    return thing["x"] * s - w // 2, thing["top"] * s, pic.clip(0, 255), where


def hole(scene, part):
    """Where the part is painted anew, on the whole plate."""
    conf, pic = PARTS[scene][part], plate(scene)
    H, W = pic.shape[:2]
    if "thing" in conf:
        m = np.zeros((H, W), bool)
        put = placed(conf["thing"])
        m[put[1]:put[1] + put[3].shape[0], put[0]:put[0] + put[3].shape[1]] = put[3]
        m[conf["thing"]["ledge"]:] = False
        return cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    if "ellipse" in conf:
        m = np.zeros((H, W), np.uint8)
        cx, cy, rx, ry = conf["ellipse"]
        cv2.ellipse(m, (cx, cy), (rx, ry), 0, 0, 360, 1, -1)
        return m.astype(bool)
    box, border, top = conf["glass"]
    glass = sam(pic, [box], [((box[0] + box[2]) // 2, (box[1] + box[3]) // 3)])
    # SAM leaves out parts of the old picture that do not look like glass, also at the window's sides: below the
    # rosette every row is filled out to the window's sides, its outermost glass over all rows (the box that found the
    # window is wider than the glass, and filled to it the border panes were lost)
    rows = [y for y in np.flatnonzero(glass.any(1)) if y >= top]
    left = int(np.percentile([np.flatnonzero(glass[y]).min() for y in rows], 5))
    right = int(np.percentile([np.flatnonzero(glass[y]).max() for y in rows], 95))
    for y in np.flatnonzero(glass.any(1)):
        xs = np.flatnonzero(glass[y])
        glass[y, xs.min():xs.max() + 1] = True
        if y >= top:
            glass[y, left:right + 1] = True
    glass = cv2.erode(glass.astype(np.uint8), np.ones((2 * border + 1,) * 2, np.uint8)).astype(bool)
    if conf.get("panes"):
        # the old figure lay over the border panes on the left side: the hole reaches to the glass's edge there and
        # the design draws a column of border panes again
        glass[top:, left + 2:left + 2 + conf["panes"]] |= glass[top:].any(1)[:, None]
        glass[box[3]:] = False
    glass[:top] = False
    seg = np.load(os.path.join(ROOT, "wip", "scene3d", f"{scene}_seg.npz"))
    # the flames are objects of their own, drawn from <scene>_flames.png: the glass goes on behind them, or the old
    # picture showed round each flame
    before = sam(pic, conf["before"]) | np.any([seg[k] for k in seg.files if k not in ("flames", "wheels") and not k.startswith("f")], 0)
    before = cv2.dilate(before.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
    return glass & ~before


def paint(scene, only=None, *seeds):
    import torch
    from diffusers import ZImageInpaintPipeline
    pipe = ZImageInpaintPipeline.from_pretrained("Tongyi-MAI/Z-Image-Turbo", torch_dtype=torch.bfloat16).to("cuda")
    out = os.path.join(ROOT, "wip", "gen", f"repaint-{scene}")
    os.makedirs(out, exist_ok=True)
    pic = plate(scene)
    for part, conf in PARTS[scene].items():
        if only and part != only:
            continue
        x0, y0, x1, y1 = conf["box"]
        s = conf["scale"]
        m = hole(scene, part)
        np.save(os.path.join(out, f"{part}-hole.npy"), m)
        # a thing that stands behind a moving one is painted on the clean plate, which does not show the moving one
        crop, mask = (plate(scene, f"{scene}_clean.png") if "thing" in conf else pic)[y0:y1, x0:x1], m[y0:y1, x0:x1]
        w, h = (x1 - x0) * s, (y1 - y0) * s
        big = cv2.resize(crop, (w, h), interpolation=cv2.INTER_CUBIC)
        bigm = cv2.resize(mask.astype(np.uint8) * 255, (w, h), interpolation=cv2.INTER_NEAREST)
        shown = [crop]
        if "design" in conf:
            import glassdesign
            big, exact = glassdesign.design(crop, mask, s, conf["design"], os.path.join(ROOT, conf.get("reference", "")),
                                            panes=conf.get("panes", 0))
        if "thing" in conf:
            px, py, thing, where = placed(conf["thing"], s)
            px, py = px - x0 * s, py - y0 * s
            big = big.astype(np.float32)
            sub = big[py:py + thing.shape[0], px:px + thing.shape[1]]
            fit = where[:sub.shape[0], :sub.shape[1]] & (bigm[py:py + sub.shape[0], px:px + sub.shape[1]] > 0)
            sub[fit] = thing[:sub.shape[0], :sub.shape[1]][fit]
            big = big.clip(0, 255).astype(np.uint8)
            exact = np.zeros(big.shape[:2], bool)
            conf = dict(conf, design="thing")
        for seed in [int(v) for v in seeds] or ([0, 25, 40, 55] if "design" in conf else [1, 2, 3]):
            if "design" in conf and seed == 0:
                gen = big
            else:
                gen = np.asarray(pipe(prompt=conf["prompt"], image=Image.fromarray(big), mask_image=Image.fromarray(bigm),
                                      strength=seed / 100 if "design" in conf else 1.0, height=h, width=w, num_inference_steps=9,
                                      guidance_scale=0.0, generator=torch.Generator("cuda").manual_seed(1 if "design" in conf else seed)).images[0])
                if "design" in conf:
                    gen = np.where(exact[..., None], big, gen)
            small = cv2.resize(gen, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
            a = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1)[..., None]
            new = (crop * (1 - a) + small * a).round().astype(np.uint8)
            Image.fromarray(new).save(os.path.join(out, f"{part}-{seed}.png"))
            shown.append(new)
            print(f"PAINTED {part} seed {seed}: {int(mask.sum())} px", flush=True)
        sheet = np.concatenate([np.pad(v, ((0, 0), (0, 6), (0, 0))) for v in shown], 1)
        if s > 2:
            sheet = cv2.resize(sheet, None, fx=3, fy=3, interpolation=cv2.INTER_LANCZOS4)
        Image.fromarray(sheet).save(os.path.join(ROOT, "wip", "preview", f"repaint-{scene}-{part}.png"))
    print("PAINT_DONE")


def apply(scene, *choices):
    """The chosen paint of each part (<part>=<seed>) into the plate files that show it."""
    keep = os.path.join(ROOT, "wip", "scene3d", "before-repaint")
    os.makedirs(keep, exist_ok=True)
    out = os.path.join(ROOT, "wip", "gen", f"repaint-{scene}")
    files = {}
    for choice in choices:
        part, seed = choice.split("=")
        conf = PARTS[scene][part]
        x0, y0, x1, y1 = conf["box"]
        new = np.asarray(Image.open(os.path.join(out, f"{part}-{seed}.png")).convert("RGB")).astype(np.float32)
        m = np.load(os.path.join(out, f"{part}-hole.npy"))[y0:y1, x0:x1]
        a = cv2.GaussianBlur(cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32), (0, 0), 1)[..., None]
        seg = np.load(os.path.join(ROOT, "wip", "scene3d", f"{scene}_seg.npz"))
        for name in conf["pictures"]:
            file = os.path.join(ROOT, "wip", "scene3d", name)
            if conf.get("under", {}).get(name):        # a moving thing before the part keeps its own pixels
                over = np.any([seg[k] for k in conf["under"][name]], 0)[y0:y1, x0:x1]
                a_name = a * ~over[..., None]
            else:
                a_name = a
            if not os.path.exists(os.path.join(keep, name)):
                shutil.copy2(file, os.path.join(keep, name))
            if name not in files:                    # as it is now, with what src/goldwork.py put elsewhere
                files[name] = np.asarray(Image.open(file).convert("RGB")).astype(np.float32)
            old, now = plate(scene, name)[y0:y1, x0:x1].astype(np.float32), files[name][y0:y1, x0:x1]
            files[name][y0:y1, x0:x1] = np.where(a_name > 0, old * (1 - a_name) + new * a_name, now)
    for name, pic in files.items():
        Image.fromarray(pic.round().astype(np.uint8)).save(os.path.join(ROOT, "wip", "scene3d", name))
        print("wrote", name)


if __name__ == "__main__":
    {"paint": paint, "apply": apply}[sys.argv[1]](*sys.argv[2:])
