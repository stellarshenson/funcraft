"""The packed crowd of the muster plate. The user's words: variant C3 of draft B4 "is good prototype, but there must be
different types of mechanicum personnel, with battered dirty robes, and they need to be tightly packed crowd almost
flowing through the image", "the crowd must be really tight, images of individual smaller", "look at the reference
image". Asked to paint a crowd into the plate, the image model paints large bright figures. So the crowd is drawn as a
picture of its own, where the model packs it tightly, and laid small on the walks of the plate; the model then paints
the whole plate again lightly, so that crowd and plate become one picture.

    GPU=(CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 HF_HUB_OFFLINE=1)
    env "${GPU[@]}" .venv-moge/bin/python src/muster/pack.py throng [seeds]   # wip/gen/throngtall_<seed>.png, 2048 x 2048
    env "${GPU[@]}" .venv-moge/bin/python src/muster/pack.py parapet          # wip/muster/parapet.png: what stands before the crowd
    python3 src/muster/pack.py lay [base]                                     # wip/gen/plate_musterP.png, wip/preview/muster-plate.png
    env "${GPU[@]}" .venv-moge/bin/python src/muster/pack.py paint            # wip/gen/plate_musterH_<k>.png: rejected, see below

- **Walks** - WALKS gives, for each walk of the plate, the line of the far heads and the line of the parapet's top.
  The crowd fills the strip between them
- **Size of a figure** - the crowd picture, TOP rows cut off, is as tall as the strip at every column, so a figure is
  about an eighth of the strip's height: about 23 pixels where the strip is 184 pixels high, 3 % of the plate's height,
  as in the reference picture
- **Along the walk** - the crowd picture is as much narrower as it is lower, so nobody is stretched. The strip gets
  lower with distance, so it takes ever more of the crowd picture per pixel; the pictures of THRONGS and their mirror
  images follow each other
- **Light** - the crowd pictures are lit brighter than the plate. Each is first brought to the mean colour of all, and
  on the plate the crowd is made darker than the air behind it, as figures against haze are
- **Haze** - with distance the crowd takes the colour of the air behind it
- **Parapet** - SAM 2.1 cuts the rampart with its parapet out of the plate (`parapet`); the crowd stands behind it
- **No second painting** - `paint` lets the image model paint the plate with the crowd again. At 35 % it turned the
  crowd into dark haze, at 45 % and 55 % into fewer and larger figures, and it set machines on the parapet. A figure
  of 23 pixels is too small for the model at the size of the plate, so the laid crowd stays as it is
"""
import os, sys
import numpy as np, cv2
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.path.join(ROOT, "wip", "gen")
sys.path.insert(0, os.path.join(ROOT, "src"))
SIZE = (2432, 768)
LUM = np.array([0.2126, 0.7152, 0.0722], np.float32)
THRONGS, TOP = (1, 2, 3), 300              # the seeds of the crowd pictures; their rows above TOP show the place behind the crowd
STEM = "throngside"                        # the crowd pictures in use: wip/gen/<STEM>_<seed>.png
# The first crowd pictures, "throngtall" from THRONG, show the crowd from behind. Laid on a walk, such a crowd faces
# across the walk. The user: "the crowd must be facing the longitudal direction, they are facing left". The pictures
# in use, "throngside" from MARCH, show the crowd from the side: everyone faces right, which is along both walks, the
# way a crowd goes that flows through the picture from left to right. They are not mirrored on the ribbon
MARCH = ("An immense crowd of Adeptus Mechanicus personnel stands pressed together in a dense column that faces the right "
         "edge of the frame, seen from behind their right shoulders, a three-quarter rear view, and a little from above "
         "through a long telephoto lens. Every figure faces right and slightly away from the camera, so the backs of the "
         "hoods and the right shoulders are visible; all look in the same direction. The crowd is packed shoulder to "
         "shoulder without any gap, it fills the whole frame from edge to edge and no ground is visible: thousands of "
         "small figures in many rows that recede upwards, hooded tech-priest adepts in battered, torn, patched and "
         "soot-stained crimson robes, a few in clean bright red robes, enginseers with mechanical arms and cables on "
         "their backs, forge workers and menials in grey and brown rags and leather aprons, servitors with metal "
         "limbs, skitarii in helmets with long lances held upright; staffs, lances and small pennants stand above the "
         "heads. Backlit by fire through orange dust and smoke, soot, ash and grime, a frame from a war film, a muted "
         "palette of dirty crimson, grey, brown and dull amber, no text overlay, no watermark")
THRONG = ("An immense crowd of Adeptus Mechanicus personnel, seen from behind and from above through a long telephoto "
          "lens, packed shoulder to shoulder and filling the whole frame from edge to edge, no ground visible between "
          "them, thousands of small figures in many rows that recede upwards: hooded tech-priest adepts in battered, "
          "torn, patched and soot-stained crimson robes, a few in clean bright red robes, enginseers with mechanical "
          "arms and cables on their backs, forge workers and menials in grey and brown rags and leather aprons, "
          "servitors with metal limbs, skitarii in helmets with long lances; staffs, lances and small pennants stand "
          "above the heads. Backlit by fire through orange dust and smoke, dark silhouettes with warm rim light, soot, "
          "ash and grime, a frame from a war film, a muted palette of dirty crimson, grey, brown and dull amber, no "
          "text overlay, no watermark")
# the walks of variant C3, in plate pixels: the line of the far heads, and the line of the parapet's top
WALKS = {
    "left": dict(top=[(0, 468), (300, 463), (600, 457), (900, 451), (1135, 446)],
                 bottom=[(0, 652), (150, 612), (300, 572), (520, 532), (700, 506), (900, 480), (1050, 463), (1135, 454)]),
    "right": dict(top=[(1830, 446), (2432, 440)], bottom=[(1830, 498), (2000, 514), (2200, 530), (2432, 546)]),
}
REACH = 0.28                               # the crowd reaches this share of the strip's height below the parapet line, behind the parapet
# what SAM 2.1 cuts the two ramparts from: a box, points on the rampart, points on the figures behind its parapet
RAMPARTS = [((0, 440, 1200, 768), [(120, 700), (400, 625), (650, 565), (900, 515), (1060, 480), (500, 720), (800, 640), (250, 600)],
             [(60, 560), (160, 535), (300, 515), (450, 500), (700, 478), (40, 480)]),
            ((1800, 470, 2432, 768), [(1900, 545), (2100, 565), (2300, 585), (2000, 660), (2350, 640)],
             [(2000, 480), (2200, 488), (2380, 495), (1900, 470)])]
PACKED = ("A vast host of the Adeptus Mechanicus flows along the top of a colossal fortress rampart on a forge world, "
          "seen from far away through a long telephoto lens: a tightly packed crowd of thousands of tiny figures, "
          "shoulder to shoulder, fills the whole rampart walk from the left foreground to a vanishing point right of "
          "centre, crosses a colossal arched bridge and fills a second terrace on the right, like a river of people. "
          "They are Mechanicum personnel of many kinds: hooded tech-priest adepts in battered, torn and soot-stained "
          "crimson robes, enginseers with mechanical arms, forge workers and menials in grey and brown rags, servitors "
          "with metal limbs, skitarii with lances. Every figure is very small beside the banners. Above the host a long "
          "row of colossal tattered crimson war banners hangs from tall iron poles and recedes into the distance, each "
          "banner with black bands and a white cog wheel enclosing a skull on a black field, scorched, its lower edge "
          "torn into long rags. Bonfires burn dirty orange among the host. Enormous billowing masses of black and brown "
          "smoke roll across the sky and between the banners; no sun is visible, only a dull orange glow. Gothic hive "
          "spires stand in shadow on the left. The rampart drops into a deep chasm that glows orange with fire; dense "
          "dirty brown and orange dust haze swallows the distance. Ash and embers drift in the air; everything is "
          "blackened with soot.")
GRIME = ("Grimdark Warhammer 40,000 Adeptus Mechanicus, a frame from a war film, long telephoto lens, shot through "
         "thick smoke and dust, low contrast in the distance, crushed dark foreground, heavy atmospheric haze, film "
         "grain, soot, ash and grime on every surface, a muted palette of dirty crimson, black, brown and dull amber, "
         "underexposed, no clean surface, no bright colour, no blue sky, no text overlay, no watermark")
PAINTS = ((0.35, 4), (0.45, 4), (0.55, 4))  # H1 to H3: the share of the guide that is painted again, and the seed


def throng(*seeds):
    import gentextures as G
    G.JOBS["throngtall"], G.JOBS["throngside"] = (2048, 2048, THRONG), (2048, 2048, MARCH)
    G.generate(STEM, tuple(map(int, seeds)) or THRONGS)


def parapet():
    """What stands before the crowd: the two ramparts with their parapets, cut out of the plate by SAM 2.1."""
    import torch
    from transformers import Sam2Processor, Sam2Model
    rid = "facebook/sam2.1-hiera-large"
    proc, model = Sam2Processor.from_pretrained(rid), Sam2Model.from_pretrained(rid).to("cuda").eval()
    img = np.asarray(Image.open(os.path.join(GEN, "plate_musterC_3.png")).convert("RGB"))
    mask = np.zeros(img.shape[:2], bool)
    for (x0, y0, x1, y1), on, off in RAMPARTS:
        pts = [[x - x0, y - y0] for x, y in on + off]
        inputs = proc(images=Image.fromarray(img[y0:y1, x0:x1]), input_points=[[pts]], input_labels=[[[1] * len(on) + [0] * len(off)]],
                      return_tensors="pt").to("cuda")
        with torch.no_grad():
            out = model(**inputs, multimask_output=False)
        cut = proc.post_process_masks(out.pred_masks.cpu(), inputs["original_sizes"])[0][0, 0].numpy() > 0
        mask[y0:y1, x0:x1] |= cut
        print(f"rampart in {(x0, y0, x1, y1)}: {int(cut.sum())} px, iou {float(out.iou_scores.max()):.2f}", flush=True)
    Image.fromarray(mask.astype(np.uint8) * 255).save(os.path.join(ROOT, "wip", "muster", "parapet.png"))


def ribbon(slice_=640, lap=192):
    """The crowd pictures, without the rows above TOP, each brought to the mean colour and the
    contrast of all, cut into slices of `slice_` columns that follow each other in turn, picture after picture, each
    faded into the next over `lap` columns and the last into the first; and smaller copies of that ribbon, each half
    the size of the one before. In turn, because one picture alone over a long stretch of the walk shows its own
    mix of people, and the change to the next picture was visible as a line."""
    tiles = [np.asarray(Image.open(os.path.join(GEN, f"{STEM}_{s}.png")).convert("RGB"))[TOP:].astype(np.float32) for s in THRONGS]
    mean, spread = np.mean([t.mean((0, 1)) for t in tiles], 0), np.mean([t.std((0, 1)) for t in tiles], 0)
    tiles = [(t - t.mean((0, 1))) * (spread / t.std((0, 1))) + mean for t in tiles]
    if STEM == "throngtall":                                          # a crowd seen from behind may be mirrored; a crowd that faces right may not
        tiles = tiles + [t[:, ::-1] for t in tiles]
    step = slice_ - lap
    cuts = [tiles[k % len(tiles)][:, c:c + slice_] for c in range(0, tiles[0].shape[1] - slice_ + 1, step) for k in range(len(tiles))]
    cuts = [cuts[k] for k in np.random.default_rng(11).permutation(len(cuts))]
    fade = np.linspace(0, 1, lap, dtype=np.float32)[None, :, None]
    parts = [np.concatenate([cuts[k - 1][:, -lap:] * (1 - fade) + c[:, :lap] * fade, c[:, lap:-lap]], 1) for k, c in enumerate(cuts)]
    levels = [np.clip(np.concatenate(parts, 1), 0, 255).astype(np.uint8)]
    while levels[-1].shape[0] > 24:
        h, w = levels[-1].shape[:2]
        levels.append(cv2.resize(levels[-1], (w // 2, h // 2), interpolation=cv2.INTER_AREA))
    return levels


def lay(base=os.path.join(GEN, "plate_musterC_3.png")):
    plate = np.asarray(Image.open(base).convert("RGB")).astype(np.float32)
    levels = ribbon()
    rows, wide = levels[0].shape[:2]
    air = cv2.GaussianBlur(plate, (0, 0), 25)                         # the colour of the air at every place
    front = np.asarray(Image.open(os.path.join(ROOT, "wip", "muster", "parapet.png")), np.float32) / 255
    front = cv2.GaussianBlur(front, (0, 0), 0.8)
    for name, walk in WALKS.items():
        (xa, _), (xb, _) = walk["top"][0], walk["top"][-1]
        xs = np.arange(xa, xb)
        top, bottom = (np.interp(xs, *zip(*walk[k])) for k in ("top", "bottom"))
        high = (bottom - top) * (1 + REACH)                           # the strip reaches behind the parapet
        size = high / rows                                            # plate pixels per pixel of the crowd picture
        u = np.cumsum(1.0 / size) % wide                              # where along the ribbon each column reads
        y0, y1 = int(top.min()) - 8, int((top + high).max()) + 2
        ys = np.arange(y0, y1, dtype=np.float32)[:, None]
        v = (ys - top[None]) / high[None] * rows                      # below 0: above the far heads
        crowd = np.zeros((y1 - y0, len(xs), 3), np.float32)
        level = np.clip(np.floor(np.log2(1.0 / size)).astype(int), 0, len(levels) - 1)
        for k in np.unique(level):
            cols = np.where(level == k)[0]
            mx = np.repeat((u[cols] / 2 ** k)[None], y1 - y0, 0).astype(np.float32)
            my = (v[:, cols] / 2 ** k).astype(np.float32)
            crowd[:, cols] = cv2.remap(levels[k], mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        far = np.clip(1.0 - high / high.max(), 0, 1)[None, :, None]   # 0 at the nearest column of the walk, towards 1 far away
        here = air[y0:y1, xa:xb]
        behind = air[np.clip(top.astype(int) - 12, 0, SIZE[1] - 1), xs]         # the air just over the far heads, per column
        dark = 0.62 * (behind @ LUM) / (crowd.mean((0, 1)) @ LUM)     # figures stand darker than the air behind them
        crowd = (crowd - crowd.mean((0, 1))) * 1.12 + crowd.mean((0, 1))
        crowd = crowd * np.clip(dark, 0.35, 1.0)[None, :, None] * np.array([1.0, 0.93, 0.85], np.float32)
        crowd = crowd * (1 - 0.6 * far) + here * 0.6 * far            # haze
        inside = ((v >= 0) & (v <= rows)).astype(np.float32)
        rise = np.clip(v / (0.10 * rows), 0, 1)                       # the far heads come out of the air behind them
        a = (inside * rise * (1 - front[y0:y1, xa:xb]))[..., None]
        plate[y0:y1, xa:xb] = plate[y0:y1, xa:xb] * (1 - a) + crowd * a
        print(f"walk {name}: columns {xa} to {xb}, a figure about {high.max() / 8:.0f} px at the near end, {high.min() / 8:.0f} px at the far end")
    done = Image.fromarray(np.clip(plate, 0, 255).astype(np.uint8))
    for out in (os.path.join(GEN, "plate_musterP.png"), os.path.join(ROOT, "wip", "preview", "muster-plate.png")):
        done.save(out)
        print("wrote", out)


def paint():
    import torch
    from diffusers import ZImageImg2ImgPipeline
    guide = Image.open(os.path.join(GEN, "plate_musterP.png")).convert("RGB")
    pipe = ZImageImg2ImgPipeline.from_pretrained("Tongyi-MAI/Z-Image-Turbo", torch_dtype=torch.bfloat16).to("cuda")
    print("prompt tokens:", len(pipe.tokenizer(PACKED + " " + GRIME)["input_ids"]), flush=True)
    for k, (strength, seed) in enumerate(PAINTS, 1):
        pipe(prompt=PACKED + " " + GRIME, image=guide, strength=strength, height=SIZE[1], width=SIZE[0], num_inference_steps=14,
             guidance_scale=0.0, generator=torch.Generator("cuda").manual_seed(seed)).images[0].save(os.path.join(GEN, f"plate_musterH_{k}.png"))
        print("wrote plate_musterH", k, "strength", strength, "seed", seed, flush=True)


if __name__ == "__main__":
    {"throng": throng, "parapet": parapet, "lay": lay, "paint": paint}[sys.argv[1]](*sys.argv[2:])
