"""Masks of the plate elements that move (src/motion.py), cut by SAM 2.1
(facebook/sam2.1-hiera-large, Apache-2.0). Grounding DINO
(IDEA-Research/grounding-dino-base, Apache-2.0) proposes boxes from a text
prompt; the motion map holds the checked box and points of each element.
SAM runs on a crop around each element, so a small far figure is cut at
full plate resolution.

    .venv-moge/bin/python src/segment.py detect <name> "hooded priest" "candle"   # wip/preview/detect-<name>.png
    .venv-moge/bin/python src/segment.py cut <name>                                # wip/scene3d/<name>_sam.npz, _seg.npz
    .venv-moge/bin/python src/segment.py flames <name>                             # flames again, SAM masks kept
"""
import os, sys, json
import numpy as np, torch, cv2
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import motion as M

ROOT = M.ROOT
DEV = "cuda"


def boxes(name, prompt, threshold=0.2):
    """Grounding DINO's boxes for `prompt` on five overlapping square tiles
    of the plate (it finds little on the whole 19:6 plate), merged."""
    from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection
    rid = "IDEA-Research/grounding-dino-base"
    proc = AutoProcessor.from_pretrained(rid)
    model = AutoModelForZeroShotObjectDetection.from_pretrained(rid).to(DEV).eval()
    img = Image.open(os.path.join(ROOT, "wip", "scene3d", name + ".png")).convert("RGB")
    W, H = img.size
    found = []
    for tx in range(0, W - H + 1, (W - H) // 4):
        inputs = proc(images=img.crop((tx, 0, tx + H, H)), text=prompt + ".", return_tensors="pt").to(DEV)
        with torch.no_grad():
            out = model(**inputs)
        res = proc.post_process_grounded_object_detection(out, inputs.input_ids, threshold=threshold,
                                                          text_threshold=0.2, target_sizes=[(H, H)])[0]
        found += [([b[0] + tx, b[1], b[2] + tx, b[3]], s) for b, s in zip(res["boxes"].tolist(), res["scores"].tolist())]
    keep = cv2.dnn.NMSBoxes([[b[0], b[1], b[2] - b[0], b[3] - b[1]] for b, _ in found],
                            [s for _, s in found], threshold, 0.5) if found else []
    return [found[i] for i in sorted(np.ravel(keep), key=lambda i: found[i][0][0])]


def detect(name, prompts):
    vis = cv2.imread(os.path.join(ROOT, "wip", "scene3d", name + ".png"))
    for prompt in prompts:
        for box, score in boxes(name, prompt):
            x0, y0, x1, y1 = (int(round(v)) for v in box)
            print(f"{prompt:20s} {score:.2f} ({x0}, {y0}, {x1}, {y1})")
            cv2.rectangle(vis, (x0, y0), (x1, y1), (0, 255, 255), 2)
            cv2.putText(vis, f"{prompt[:6]} {score:.2f}", (x0 + 3, y0 + 18), 0, 0.55, (0, 255, 255), 2)
    cv2.imwrite(os.path.join(ROOT, "wip", "preview", f"detect-{name}.png"), vis)


def cut(name):
    from transformers import Sam2Processor, Sam2Model
    rid = "facebook/sam2.1-hiera-large"
    proc = Sam2Processor.from_pretrained(rid)
    model = Sam2Model.from_pretrained(rid).to(DEV).eval()
    img = np.asarray(Image.open(os.path.join(ROOT, "wip", "scene3d", name + ".png")).convert("RGB"))
    H, W = img.shape[:2]
    masks = {}
    for el in M.MAPS[name]:
        if el["kind"] == "smoke":                         # a source point, no mask
            continue
        for k, part in enumerate(el.get("cuts", [el])):
            x0, y0, x1, y1 = part["box"]
            m = int(0.25 * max(x1 - x0, y1 - y0))           # context around the box
            cx0, cy0, cx1, cy1 = max(0, x0 - m), max(0, y0 - m), min(W, x1 + m), min(H, y1 + m)
            crop = Image.fromarray(img[cy0:cy1, cx0:cx1])
            pts = [[x - cx0, y - cy0] for x, y in part.get("pos", [])] + \
                  [[x - cx0, y - cy0] for x, y in part.get("neg", [])]
            lab = [1] * len(part.get("pos", [])) + [0] * len(part.get("neg", []))
            kw = dict(input_boxes=[[[x0 - cx0, y0 - cy0, x1 - cx0, y1 - cy0]]])
            if pts:
                kw.update(input_points=[[pts]], input_labels=[[lab]])
            inputs = proc(images=crop, return_tensors="pt", **kw).to(DEV)
            with torch.no_grad():
                out = model(**inputs, multimask_output=False)
            mk = proc.post_process_masks(out.pred_masks.cpu(), inputs["original_sizes"])[0][0, 0].numpy() > 0
            full = np.zeros((H, W), bool)
            full[cy0:cy1, cx0:cx1] = mk
            full[:y0], full[y1:], full[:, :x0], full[:, x1:] = False, False, False, False   # nothing outside the box
            masks[el["id"]] = masks.get(el["id"], np.zeros((H, W), bool)) | full
            print(f"{el['id']:>4} part {k}: {int(full.sum()):7d} px, iou {float(out.iou_scores.max()):.2f}")
    masks = tidy(name, masks)
    candles = np.array([b for b, s in boxes(name, "candle", 0.25)], np.float32).reshape(-1, 4)
    np.savez_compressed(os.path.join(ROOT, "wip", "scene3d", f"{name}_sam.npz"), candles=candles,
                        **{str(k): v for k, v in masks.items()})
    reflame(name)
    print("SEGMENT_DONE", name, len(masks))


def find_flames(name, masks, candles):
    """Candle flames of the plate: a white-hot core with an orange glow
    round it, not wider than tall, at least 0.3 of the size a 1.2 x 3 cm
    flame has at that depth, and at the top of a candle (`candles`:
    Grounding DINO's boxes; a highlight on brass has no candle under it);
    or any white-hot core inside a box of motion.FLAMES. The flame ends
    where the blob widens into the glowing top of the candle.
    A flame on a carried candle, and any other flame at least 6 px tall,
    gets a mask of its own, `f<n>`: the flame with a margin that holds its
    soft edge. The flame itself leaves every other mask. Every flame is
    listed with its wick and tip pixel, its world position and its owner
    (the carried candle it burns on)."""
    import actors as A
    img = np.asarray(Image.open(os.path.join(ROOT, "wip", "scene3d", name + ".png")).convert("RGB"), np.float32) / 255
    d = np.load(os.path.join(ROOT, "wip", "scene3d", name + ".npz"))
    depth, K = d["depth"], d["intrinsics"]
    depth = np.where(np.isfinite(depth) & (depth > 0), depth, 2 * np.nanmax(depth[np.isfinite(depth)]))
    H, W = depth.shape
    focal = float(K[0, 0]) * W
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    core = ((lum > 0.86) & (img.min(-1) > 0.6)).astype(np.uint8)       # the white-hot middle of a flame
    for x0, y0, x1, y1 in M.NOFLAME.get(name, []):
        core[y0:y1, x0:x1] = 0
    warm = (lum > 0.68) & (r > b + 0.12)                               # the flame's yellow body, not its glow on the air
    n, lab, st, _ = cv2.connectedComponentsWithStats(core, connectivity=8)
    carried = [el["id"] for el in M.MAPS[name] if el["kind"] == "carry" and not el.get("stands")]
    near = {k: cv2.dilate(masks[k].astype(np.uint8), np.ones((13, 13), np.uint8)) > 0 for k in carried}
    solid = np.zeros((H, W), bool)                                     # figures and things: a white blob on them is a highlight
    for el in M.MAPS[name]:
        if el["kind"] not in ("stream", "smoke", "carry"):
            solid |= masks[el["id"]]
    flames = []
    for i in range(1, n):
        x, y, w, h, area = st[i]
        if not 3 <= area <= 1500 or w > 40:
            continue
        m = lab == i
        ring = (cv2.dilate(m.astype(np.uint8), np.ones((19, 19), np.uint8)) > 0) & \
            ~(cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0)
        if (r - b)[ring].mean() < 0.18 or lum[ring].mean() > 0.75 * lum[m].mean():
            continue                                                   # no orange glow round it, or a bright surface
        forced = any(bx[0] <= x + w / 2 <= bx[2] and bx[1] <= y + h / 2 <= bx[3] for bx in M.FLAMES.get(name, []))
        zc = float(np.median(depth[m]))
        expect = (0.012 * focal / zc) * (0.03 * focal / zc)            # pixels of a 1.2 x 3 cm flame at that depth
        held = any((near[k] & m).any() for k in carried)
        glass = (b > r)[ring].mean() > 0.2                             # stained glass has blue beside it
        cx, cy = x + w / 2, y + h / 2
        on_candle = any(c[0] - 4 <= cx <= c[2] + 4 and c[1] - 0.4 * (c[3] - c[1]) <= cy <= c[1] + 0.5 * (c[3] - c[1])
                        for c in candles)
        if not forced and (area < max(3, 0.3 * expect) or h < 0.9 * w or glass or not (on_candle or held)
                           or (solid[m].mean() > 0.5 and not held)):
            continue                                                   # a highlight, or a window pane
        x0, x1 = max(x - w, 0), min(x + 2 * w, W)
        y1 = min(y + h + 2, H)
        body = np.zeros((H, W), bool)
        body[:y1, x0:x1] = warm[:y1, x0:x1] | core[:y1, x0:x1].astype(bool)
        nb, lb = cv2.connectedComponents(body.astype(np.uint8), connectivity=8)
        fl = np.isin(lb, np.unique(lb[m])) & body                       # the warm blob the core sits in
        ys, xs = np.nonzero(fl)
        widths = np.array([fl[row].sum() for row in range(ys.min(), ys.max() + 1)])
        top = float(np.median(widths[:max(2, int(0.4 * len(widths)))]))
        wide = np.nonzero(widths > max(1.8 * top, top + 6))[0]           # where the glowing top of the candle begins
        if len(wide):
            fl[ys.min() + int(wide[0]):] = False
        ys, xs = np.nonzero(fl)
        if len(ys) == 0 or ys.max() - ys.min() < 2 or ys.max() - ys.min() > 90:
            continue
        hf = int(ys.max() - ys.min() + 1)
        tip = (float(xs[ys == ys.min()].mean()), float(ys.min()))
        wick = (float(xs[ys == ys.max()].mean()), float(ys.max()))
        owner = next((k for k in carried if (near[k] & fl).any()), None)
        yy, xx = int(min(wick[1] + 6, H - 1)), int(wick[0])
        z = float(np.percentile(depth[max(yy - 3, 0):yy + 4, max(xx - 3, 0):xx + 4], 30))
        grow = lambda k: cv2.dilate(fl.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))) > 0
        f = dict(id=f"f{len(flames) + 1}", wick=wick, tip=tip, owner=owner, mesh=bool(hf >= 6 or owner is not None),
                 area=int(area), world=A.world(K, (W, H), wick[0], wick[1], z).tolist())
        if f["mesh"]:                                            # the flame is its own element
            cut = grow(9)
            cut[int(wick[1]) + 1:] = False                       # the candle below the wick stays the candle's
            for k in list(masks):
                if not k.startswith("f"):
                    masks[k] = masks[k] & ~cut
            masks[f["id"]] = grow(11)
        flames.append(f)
    return sorted(flames, key=lambda f: -f["area"])


def tidy(name, masks):
    """Close small gaps, drop specks (pieces under 5 % of the largest), take
    every carried piece out of its priest's mask, and give a pixel still
    claimed by two masks to the element whose median depth is nearest the
    pixel's own depth."""
    kind = {el["id"]: el["kind"] for el in M.MAPS[name]}
    H, W = next(iter(masks.values())).shape
    for k, m in masks.items():
        m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
        n, lab, st, _ = cv2.connectedComponentsWithStats(1 - m, connectivity=4)
        edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
        limit = H * W if kind[k] == "cloth" else 400      # a seal or tag pinned on cloth belongs to the cloth
        small = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] < limit and i not in edge]
        m[np.isin(lab, small)] = 1                                  # pin holes, not gaps between arm and body
        n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
        big = st[1:, cv2.CC_STAT_AREA].max() if n > 1 else 0
        masks[k] = np.isin(lab, [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] >= 0.05 * big])
    for el in M.MAPS[name]:                                         # a held thing and its hand are not the priest's
        if el["kind"] == "carry":
            masks[el["parent"]] = masks[el["parent"]] & ~masks[el["id"]]
    ld = np.log(np.load(os.path.join(ROOT, "wip", "scene3d", name + ".npz"))["depth"])
    keys = list(masks)
    stack = np.stack([masks[k] for k in keys])
    med = np.array([np.median(ld[masks[k]]) for k in keys])[:, None, None]
    best = np.where(stack, np.abs(ld[None] - med), np.inf).argmin(0)
    return {k: stack[i] & (best == i) for i, k in enumerate(keys)}


def reflame(name):
    """The masks SAM cut (<name>_sam.npz) plus the flames of the plate as it
    is now: <name>_seg.npz. Run again after the painted smoke is removed."""
    stem = os.path.join(ROOT, "wip", "scene3d", name)
    sam = np.load(stem + "_sam.npz")
    import actors as A
    masks = {k: sam[k] for k in sam.files if k != "candles"}
    d = np.load(stem + ".npz")
    depth, K = d["depth"], d["intrinsics"]
    depth = np.where(np.isfinite(depth) & (depth > 0), depth, 2 * np.nanmax(depth[np.isfinite(depth)]))
    fits = {}
    for el in M.MAPS[name]:                              # a fan is the disc inside its frame; the frame stays in the plate
        if el["kind"] == "spin":
            fits[el["id"]] = A.wheel_fit(el, masks[el["id"]], depth, K, depth.shape[::-1])
            if el["rim"] == "inner":
                masks[el["id"]] = A.wheel_disc(fits[el["id"]], K, depth.shape[::-1])
    flames = find_flames(name, masks, sam["candles"])
    np.savez_compressed(stem + "_seg.npz", flames=json.dumps(flames), wheels=json.dumps(fits), **masks)
    print(f"flames: {len(flames)}, with a mesh {sum(f['mesh'] for f in flames)}, "
          f"on carried candles {sum(f['owner'] is not None for f in flames)}")


if __name__ == "__main__":
    cmd, name = sys.argv[1], sys.argv[2]
    {"detect": lambda: detect(name, sys.argv[3:]), "cut": lambda: cut(name), "flames": lambda: reflame(name)}[cmd]()
