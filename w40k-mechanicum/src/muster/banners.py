"""The right banner group of the muster plate in the order of its distances. The user's words: "please manage the size
of the banners vs distance". The banners of the right terrace stand in a row that comes towards the camera from left
to right, so each must be taller than its left neighbour. Measured on the plate, from the crossbar to the end of the
rags, by the column of the pole: 1720: 100 px, 1768: 120, 1897: 155, 2052: 270, 2163: 210, 2265: 170, 2375: 300. The
banner at 2052 is too tall for its place and the one at 2265 too short. This script lets the two change places.

    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 HF_HUB_OFFLINE=1 .venv-moge/bin/python src/muster/banners.py

- **Cut** - SAM 2.1 cuts each of the two banners with its pole, crossbar and finial
- **Behind** - the image model paints the air and the far city where the two banners were
- **Place** - each banner is laid at the pole of the other, reduced or enlarged about the foot of its pole, which
  lies on the line of the far heads: a thing that stands on that line keeps its foot there at every distance
- **Result** - heights by pole: 100, 120, 155, 170, 210, 248, 300

It reads wip/gen/plate_musterC_3.png and writes wip/gen/plate_muster_banners.png, on which src/muster/host.py sets the
crowd. A painted light in the sky, STRAY, is taken out as well.
"""
import os
import numpy as np, cv2, torch
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.path.join(ROOT, "wip", "gen")
FOOT = 446                                 # the row of the far heads on the right walk: the foot of every pole
# the two banners: box, points on it, points off it, the column of its pole, the column it goes to, its new size
MOVES = [dict(box=(2175, 190, 2282, FOOT), on=[(2230, 300), (2228, 232), (2265, 420), (2228, 205)], off=[], pole=2265, to=2052, size=1.0),
         dict(box=(1920, 85, 2080, FOOT), on=[(2000, 300), (2000, 160), (2052, 425), (1990, 110)], off=[(2015, 428)], pole=2052, to=2265, size=0.92)]
AIR = (1888, 60, 2336, 460)                # the part of the plate the image model sees when it paints behind the banners
STRAY = (2262, 163, 10)                    # a painted light in the sky: column, row, radius
EMPTY = ("Thick brown and orange dust haze and smoke over a forge city at dusk, faint grey silhouettes of distant gothic "
         "spires and smokestacks, empty air, no banner, no pole, no flag, a frame from a war film, muted colours, grain")


def main():
    from transformers import Sam2Processor, Sam2Model
    from diffusers import ZImageInpaintPipeline
    plate = np.asarray(Image.open(os.path.join(GEN, "plate_musterC_3.png")).convert("RGB")).copy()
    stray = np.zeros(plate.shape[:2], np.uint8)
    cv2.circle(stray, STRAY[:2], STRAY[2], 1, -1)
    plate = cv2.inpaint(plate, stray, 5, cv2.INPAINT_TELEA)
    rid = "facebook/sam2.1-hiera-large"
    proc, model = Sam2Processor.from_pretrained(rid), Sam2Model.from_pretrained(rid).to("cuda").eval()
    for move in MOVES:
        x0, y0, x1, y1 = move["box"]
        m = 40                                                        # room round the box
        cx0, cy0, cx1, cy1 = x0 - m, max(y0 - m, 0), min(x1 + m, plate.shape[1]), y1 + 4
        pts = [[x - cx0, y - cy0] for x, y in move["on"] + move["off"]]
        inputs = proc(images=Image.fromarray(plate[cy0:cy1, cx0:cx1]), input_boxes=[[[x0 - cx0, y0 - cy0, x1 - cx0, y1 - cy0]]],
                      input_points=[[pts]], input_labels=[[[1] * len(move["on"]) + [0] * len(move["off"])]], return_tensors="pt").to("cuda")
        with torch.no_grad():
            out = model(**inputs, multimask_output=False)
        cut = np.zeros(plate.shape[:2], bool)
        cut[cy0:cy1, cx0:cx1] = proc.post_process_masks(out.pred_masks.cpu(), inputs["original_sizes"])[0][0, 0].numpy() > 0
        cut[:y0], cut[y1:], cut[:, :x0], cut[:, x1:] = False, False, False, False
        move["mask"] = cut
        print(f"banner at pole {move['pole']}: {int(cut.sum())} px, iou {float(out.iou_scores.max()):.2f}", flush=True)
    del model
    torch.cuda.empty_cache()
    # behind the two banners
    hole = cv2.dilate((MOVES[0]["mask"] | MOVES[1]["mask"]).astype(np.uint8), np.ones((13, 13), np.uint8))
    ax0, ay0, ax1, ay1 = AIR
    crop, part = plate[ay0:ay1, ax0:ax1], hole[ay0:ay1, ax0:ax1]
    big = (2 * (ax1 - ax0), 2 * (ay1 - ay0))
    pipe = ZImageInpaintPipeline.from_pretrained("Tongyi-MAI/Z-Image-Turbo", torch_dtype=torch.bfloat16).to("cuda")
    gen = pipe(prompt=EMPTY, image=Image.fromarray(cv2.resize(crop, big, interpolation=cv2.INTER_CUBIC)),
               mask_image=Image.fromarray(cv2.resize(part, big, interpolation=cv2.INTER_NEAREST) * 255), strength=1.0,
               height=big[1], width=big[0], num_inference_steps=9, guidance_scale=0.0,
               generator=torch.Generator("cuda").manual_seed(2)).images[0]
    gen = cv2.resize(np.asarray(gen), (ax1 - ax0, ay1 - ay0), interpolation=cv2.INTER_AREA)
    a = cv2.GaussianBlur(part.astype(np.float32), (0, 0), 2)[..., None]
    empty = plate.copy()
    empty[ay0:ay1, ax0:ax1] = (crop * (1 - a) + gen * a).astype(np.uint8)
    Image.fromarray(empty).save(os.path.join(ROOT, "wip", "muster", "banners-empty.png"))
    # each banner at the pole of the other, the farther one first
    out = empty.astype(np.float32)
    H, W = plate.shape[:2]
    for move in MOVES:
        k = move["size"]
        warp = np.float32([[k, 0, move["to"] - k * move["pole"]], [0, k, FOOT - k * FOOT]])      # about the foot of the pole
        how = cv2.INTER_AREA if k < 1 else cv2.INTER_CUBIC
        colour = cv2.warpAffine(plate, warp, (W, H), flags=how).astype(np.float32)
        alpha = cv2.warpAffine(cv2.GaussianBlur(move["mask"].astype(np.float32), (0, 0), 0.7), warp, (W, H), flags=cv2.INTER_LINEAR)[..., None]
        out = out * (1 - alpha) + colour * alpha
        ys = np.where(move["mask"].any(1))[0]
        print(f"banner of pole {move['pole']} now at pole {move['to']}: {round(k * (ys.max() - ys.min()))} px tall", flush=True)
    done = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    path = os.path.join(GEN, "plate_muster_banners.png")
    done.save(path)
    print("wrote", path)


main()
