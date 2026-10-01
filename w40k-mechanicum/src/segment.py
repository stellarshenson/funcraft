"""Masks of the plate elements that move (src/motion.py), cut by SAM 2.1
(facebook/sam2.1-hiera-large, Apache-2.0). Grounding DINO
(IDEA-Research/grounding-dino-base, Apache-2.0) proposes boxes from a text
prompt; the motion map holds the checked box and points of each element.
SAM runs on a crop around each element, so a small far figure is cut at
full plate resolution.

    .venv-moge/bin/python src/segment.py detect <name> "hooded priest" "candle"   # wip/preview/detect-<name>.png
    .venv-moge/bin/python src/segment.py cut <name>                                # wip/scene3d/<name>_seg.npz
"""
import os, sys
import numpy as np, torch, cv2
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import motion as M

ROOT = M.ROOT
DEV = "cuda"


def detect(name, prompts):
    from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection
    rid = "IDEA-Research/grounding-dino-base"
    proc = AutoProcessor.from_pretrained(rid)
    model = AutoModelForZeroShotObjectDetection.from_pretrained(rid).to(DEV).eval()
    img = Image.open(os.path.join(ROOT, "wip", "scene3d", name + ".png")).convert("RGB")
    W, H = img.size
    vis = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
    tiles = range(0, W - H + 1, (W - H) // 4)                 # five square tiles, overlapping
    for prompt in prompts:
        found = []
        for tx in tiles:
            tile = img.crop((tx, 0, tx + H, H))
            inputs = proc(images=tile, text=prompt + ".", return_tensors="pt").to(DEV)
            with torch.no_grad():
                out = model(**inputs)
            res = proc.post_process_grounded_object_detection(out, inputs.input_ids, threshold=0.2,
                                                              text_threshold=0.2, target_sizes=[(H, H)])[0]
            found += [([b[0] + tx, b[1], b[2] + tx, b[3]], s) for b, s in zip(res["boxes"].tolist(), res["scores"].tolist())]
        keep = cv2.dnn.NMSBoxes([[b[0], b[1], b[2] - b[0], b[3] - b[1]] for b, _ in found],
                                [s for _, s in found], 0.2, 0.5) if found else []
        for i in sorted(np.ravel(keep), key=lambda i: found[i][0][0]):
            box, score = found[i]
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
    np.savez_compressed(os.path.join(ROOT, "wip", "scene3d", f"{name}_seg.npz"), **{str(k): v for k, v in masks.items()})
    print("SEGMENT_DONE", name, len(masks))


def tidy(name, masks):
    """Close small gaps, drop specks (pieces under 5 % of the largest), take
    every carried piece out of its priest's mask, and give a pixel still
    claimed by two masks to the element whose median depth is nearest the
    pixel's own depth."""
    for k, m in masks.items():
        m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
        n, lab, st, _ = cv2.connectedComponentsWithStats(1 - m, connectivity=4)
        small = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] < 400]
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


if __name__ == "__main__":
    cmd, name = sys.argv[1], sys.argv[2]
    detect(name, sys.argv[3:]) if cmd == "detect" else cut(name)
