"""Drafts of the muster plate, to choose from: the scene of resources/assets/scenes/mechanicum.png designed anew by
Z-Image-Turbo, in two looks, and the picture itself cut to the banner's 19:6 shape.

    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 HF_HUB_OFFLINE=1 .venv-moge/bin/python src/muster/drafts.py gen
    python3 src/muster/drafts.py sheet        # wip/preview/plates-muster.png
    ... src/muster/drafts.py smoked           # draft B4 with more smoke and dirt: wip/gen/plate_musterC_<k>.png

    ... src/muster/drafts.py scale            # the scale of the picture: plate_musterD_<seed>.png, plate_musterE_<k>.png

    python3 src/muster/drafts.py guide        # wip/muster/guide.png: the layout the F drafts are painted from
    ... src/muster/drafts.py wide             # plate_musterF_<k>.png: the guide painted again after WIDE

    ... src/muster/drafts.py crowd [seeds]    # F1 with a denser crowd on the left terrace: plate_musterG_<seed>.png

    ... src/muster/drafts.py throng [seeds]   # a dense crowd as a picture of its own: wip/gen/throng_<seed>.png

The user chose draft B4 and ordered it "more smoked, dirty like in the original image". C1 is the scene SMOKED drawn
from nothing with the seed of B4; C2 to C4 are B4 painted again by the image model after SMOKED, changed by the shares
in STRENGTHS. The user then ordered the scale of the picture ("sheer scale is amazing"), more pilgrims on the left, and
a crowd mixed from adepts and workers with battered and clean robes: D<seed> is the scene VAST drawn from nothing, E1
and E2 are the picture itself painted again after VAST, so that its scale stays. The model draws large figures when it
draws from nothing (D), and the picture alone has no chasm and no arched bridge, which the user likes in B4. So the F
drafts start from a layout, `guide`: the whole picture on the left, the same picture mirrored on the right, so that
two banner rows of one perspective recede to one point, and between them the chasm with the arched bridge of B4.
The user chose F1 as the base. `crowd` paints the crowd of its left terrace again at twice the size of the plate, so
that the figures come out half as tall and four times as many.

Drafts: wip/gen/plate_musterA_<seed>.png (the look of the other plates, genplates.PLATE), plate_musterB_<seed>.png
(the look of the picture, DUSK) and plate_muster_0.png (the picture itself, rows TOP to TOP + 624, enlarged).
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
PICTURE = os.path.join(ROOT, "resources", "assets", "scenes", "mechanicum.png")
TOP = 104                                  # first row of the picture that stays in the 19:6 cut
SIZE = (2432, 768)
SEEDS = (1, 2, 3, 4)

SCENE = ("A vast host of the Adeptus Mechanicus massed along the top of a colossal fortress rampart on a forge world, "
         "seen from the rampart looking along it into the distance: thousands of small hooded tech-priests and "
         "skitarii soldiers in crimson robes with staffs and lances stand shoulder to shoulder behind an ornate "
         "carved iron parapet that runs from the left foreground to a vanishing point right of centre. Above the "
         "host a long row of colossal tattered crimson war banners hangs from tall iron poles and recedes into the "
         "distance, each banner with black bands and a white cog wheel enclosing a skull on a black field, its "
         "lower edge torn into long rags. Bonfires and braziers burn among the host, thick columns of black smoke "
         "rise behind the banners, towering gothic hive spires stand in shadow on the left. On the right the "
         "rampart drops into a deep chasm that glows orange with molten light; beyond it a second bridge crowded "
         "with tiny figures and the dim silhouettes of forge cathedrals, cranes and smokestacks dissolve in thick "
         "orange and pink dust haze under a pale hidden sun.")
DUSK = ("Grimdark gothic Warhammer 40,000 Adeptus Mechanicus, cinematic ultra-wide film still, long telephoto lens, "
        "extremely detailed, blackened iron and soot, ragged crimson cloth, glowing embers and sparks, backlit by a "
        "low sun through dense orange dust and smoke, strong atmospheric perspective, dark silhouettes against "
        "bright haze, a palette of crimson, black and amber, sharp focus, no text overlay, no watermark")

HOST = SCENE[:SCENE.index("Bonfires and braziers")]
SMOKED = (HOST + "Bonfires and braziers burn dirty orange among the host. The air is choked: enormous billowing masses "
          "of black and brown smoke roll low across the whole sky and between the banners and hide the sky; no sun "
          "and no clear sky are visible, only a dull orange glow behind the smoke. Towering gothic hive spires stand "
          "in shadow on the left. On the right the rampart drops into a deep chasm that glows orange with molten "
          "light; dense dirty brown and orange dust haze swallows the distance, so the second bridge, the cranes and "
          "the forge cathedrals beyond it are only faint grey silhouettes. Ash and embers drift in the air. "
          "Everything is filthy: the banners are scorched, soot-stained and torn into rags with holes, the iron "
          "parapet is blackened and caked with soot and ash, the robes are dusty and dark.")
GRIME = ("Grimdark Warhammer 40,000 Adeptus Mechanicus, a frame from a war film, long telephoto lens, shot through "
         "thick smoke and dust, low contrast in the distance, crushed dark foreground, heavy atmospheric haze, film "
         "grain, soot, ash and grime on every surface, a muted palette of dirty crimson, black, brown and dull amber, "
         "underexposed, no clean surface, no bright colour, no blue sky, no text overlay, no watermark")
STRENGTHS = (0.5, 0.65, 0.8)               # C2, C3, C4: the share of B4 that the image model paints again

VAST = ("An immense host of the Adeptus Mechanicus on the top of a colossal fortress rampart on a forge world, seen from "
        "far away through a long telephoto lens, looking along the rampart into the distance. The scale is vast: the "
        "terrace on the rampart is hundreds of metres wide and packed from edge to edge with a crowd of many thousands "
        "of tiny figures, each only a speck: hooded adepts in crimson robes, some robes clean and bright, most "
        "battered, torn and soot-stained, mixed with bare-headed forge workers and menials in grey and brown rags, "
        "servitors and skitarii with lances; thousands of heads and staffs recede into the haze. Out of the crowd rise "
        "colossal war banners on iron masts as tall as cathedral towers, fifty times the height of a man: a long row "
        "on the left that recedes to a vanishing point, and a second group on the right. Every banner is a huge "
        "tattered crimson cloth with black bands and a black field with a white cog wheel emblem, scorched, full of "
        "holes, its lower edge torn into long rags. Great bonfires burn among the crowd, small beside the banners. In "
        "the middle the rampart drops into a deep chasm that glows orange with fire, spanned far away by a colossal "
        "bridge crowded with more tiny figures. Gothic hive spires tower in shadow on the far left. Enormous masses "
        "of black and brown smoke roll across the sky and between the banners and hide the sky; no sun is visible, "
        "only a dull orange glow. Dense dirty brown and orange dust haze swallows the distance. Ash and embers drift "
        "in the air; everything is blackened with soot.")
VAST_SEEDS = (1, 2, 3, 4, 5, 6)
REPAINT = (0.6, 0.75)                      # E1, E2: the share of the picture that the image model paints again


def scale():
    import torch
    from PIL import Image
    from diffusers import ZImageImg2ImgPipeline
    import gentextures as G
    G.JOBS["plate_musterD"] = (*SIZE, VAST + " " + GRIME)
    G.generate("plate_musterD", VAST_SEEDS)
    if G.PIPE is not None:
        print("prompt tokens:", len(G.PIPE.tokenizer(VAST + " " + GRIME)["input_ids"]), flush=True)
    picture = Image.open(os.path.join(G.GEN, "plate_muster_0.png")).convert("RGB")
    pipe = ZImageImg2ImgPipeline.from_pipe(G.PIPE) if G.PIPE is not None else \
        ZImageImg2ImgPipeline.from_pretrained("Tongyi-MAI/Z-Image-Turbo", torch_dtype=torch.bfloat16).to("cuda")
    for k, strength in enumerate(REPAINT, 1):
        out = os.path.join(G.GEN, f"plate_musterE_{k}.png")
        if os.path.exists(out):
            continue
        pipe(prompt=VAST + " " + GRIME, image=picture, strength=strength, height=SIZE[1], width=SIZE[0],
             num_inference_steps=14, guidance_scale=0.0, generator=torch.Generator("cuda").manual_seed(4)).images[0].save(out)
        print("wrote plate_musterE", k, "strength", strength, flush=True)

WIDE = ("An immense host of the Adeptus Mechanicus on the top of a colossal fortress rampart on a forge world, seen from "
        "far away through a long telephoto lens. The scale is vast: two rows of colossal tattered crimson war banners "
        "on iron masts as tall as cathedral towers, fifty times the height of a man, stand on the left and on the "
        "right and recede towards the centre, each banner smaller with distance in strict perspective. Every banner "
        "is a huge crimson cloth with black bands and a black field with a white cog wheel emblem, scorched, full of "
        "holes, its lower edge torn into long rags. Under the banners both terraces are packed from edge to edge with "
        "a crowd of many thousands of tiny figures, each only a speck: hooded adepts in crimson robes, some robes "
        "clean and bright, most battered, torn and soot-stained, mixed with bare-headed forge workers and menials in "
        "grey and brown rags, servitors and skitarii with lances. Great bonfires burn among the crowd, small beside "
        "the banners. Between the two terraces, in the centre, the rampart drops into a deep chasm that glows orange "
        "with fire, spanned in the middle distance by a colossal arched stone bridge crowded with more tiny figures. "
        "Gothic hive spires tower in shadow at the edges. Enormous masses of black and brown smoke roll across the "
        "sky and between the banners and hide the sky; no sun is visible, only a dull orange glow. Dense dirty brown "
        "and orange dust haze swallows the distance. Ash and embers drift in the air; everything is blackened with soot.")
VANISH = 1420                              # column of the picture at which its banner row ends
WIDE_DRAFTS = ((0.6, 4), (0.7, 4), (0.8, 4), (0.7, 1), (0.5, 1), (0.6, 1))      # F1 to F6: the share painted again, and the seed


def guide():
    """The layout of the F drafts, 2432 x 768: the whole picture reduced to the plate's height on the left, the same
    mirrored on the right, the two joined at the point where their banner rows end, and the chasm with the arched
    bridge of draft B4 between them."""
    import numpy as np
    from PIL import Image
    picture = Image.open(PICTURE).convert("RGB")
    k = SIZE[1] / picture.height
    left = np.asarray(picture.resize((round(picture.width * k), SIZE[1]), Image.LANCZOS), np.float32)
    end = round(VANISH * k)                                           # the column where the two rows meet
    wide = SIZE[0] - (2 * end - left.shape[1])                        # the mirrored picture reaches the right edge
    right = np.asarray(Image.fromarray(left[:, ::-1].astype(np.uint8)).resize((wide, SIZE[1]), Image.LANCZOS), np.float32)
    out = np.zeros((SIZE[1], SIZE[0], 3), np.float32)
    out[:, :left.shape[1]] = left
    xs = np.arange(SIZE[0], dtype=np.float32)
    t = np.clip((xs - (end - 80)) / 160, 0, 1)
    w = (t * t * (3 - 2 * t))[None, :, None]
    mirrored = np.zeros_like(out)
    mirrored[:, SIZE[0] - wide:] = right
    out = out * (1 - w) + mirrored * w
    b4 = np.asarray(Image.open(os.path.join(ROOT, "wip", "gen", "plate_musterB_4.png")).convert("RGB"), np.float32)
    patch = b4[360:768, 1000:1800]                                    # the chasm, its fire and the arched bridge
    y0, x0 = 360, end - 400
    yy, xx = np.mgrid[:patch.shape[0], :patch.shape[1]].astype(np.float32)
    d = np.hypot((xx - 400) / 400, (yy - 250) / 300)                  # 1 at the rim of an ellipse low in the patch
    a = np.clip((1.0 - d) / 0.35, 0, 1)[..., None]
    out[y0:y0 + patch.shape[0], x0:x0 + patch.shape[1]] = out[y0:y0 + patch.shape[0], x0:x0 + patch.shape[1]] * (1 - a) + patch * a
    Image.fromarray(out.astype(np.uint8)).save(os.path.join(ROOT, "wip", "muster", "guide.png"))
    print("wrote wip/muster/guide.png; the rows meet at column", end)


def wide():
    import torch
    from PIL import Image
    from diffusers import ZImageImg2ImgPipeline
    layout = Image.open(os.path.join(ROOT, "wip", "muster", "guide.png")).convert("RGB")
    pipe = ZImageImg2ImgPipeline.from_pretrained("Tongyi-MAI/Z-Image-Turbo", torch_dtype=torch.bfloat16).to("cuda")
    print("prompt tokens:", len(pipe.tokenizer(WIDE + " " + GRIME)["input_ids"]), flush=True)
    for k, (strength, seed) in enumerate(WIDE_DRAFTS, 1):
        out = os.path.join(ROOT, "wip", "gen", f"plate_musterF_{k}.png")
        if os.path.exists(out):
            continue
        pipe(prompt=WIDE + " " + GRIME, image=layout, strength=strength, height=SIZE[1], width=SIZE[0],
             num_inference_steps=14, guidance_scale=0.0, generator=torch.Generator("cuda").manual_seed(seed)).images[0].save(out)
        print("wrote plate_musterF", k, "strength", strength, "seed", seed, flush=True)

PEOPLE = ("A dense crowd of pilgrims packed shoulder to shoulder on the terrace of a colossal fortress rampart, seen from "
          "far away through a long telephoto lens: many hundreds of small figures fill the whole terrace from the "
          "foreground to its far end. Hooded adepts of the Adeptus Mechanicus in crimson robes, a few robes clean and "
          "bright red, most battered, torn, patched and soot-stained, stand mixed with bare-headed forge workers and "
          "menials in grey and brown rags and leather aprons, servitors with metal limbs, and a few skitarii with "
          "lances. Row behind row of heads and shoulders recedes into smoke and dust haze; bonfires burn behind the "
          "crowd. Soot, ash and grime on everything, a frame from a war film, a muted palette of dirty crimson, grey, "
          "brown and dull amber, no text overlay, no watermark")
TERRACE = (0, 440, 1024, 288)              # x, y, width, height of the part of F1 that is painted at twice its size
# where the crowd stands, in plate pixels, and the masts and their bases inside it, which stay as they are
STAND = [(0, 500), (300, 505), (600, 510), (960, 528), (960, 572), (850, 598), (600, 645), (330, 700), (200, 728), (0, 728)]
MASTS = [(95, 500, 180, 700), (495, 500, 585, 655), (790, 500, 812, 600)]


def crowd(*seeds):
    import numpy as np, cv2, torch
    from PIL import Image
    from diffusers import ZImageInpaintPipeline
    base = np.asarray(Image.open(os.path.join(ROOT, "wip", "gen", "plate_musterF_1.png")).convert("RGB"))
    x0, y0, w, h = TERRACE
    hole = np.zeros(base.shape[:2], np.uint8)
    cv2.fillPoly(hole, [np.array(STAND, np.int32)], 1)
    for a, b, c, d in MASTS:
        hole[b:d, a:c] = 0
    part, mask = base[y0:y0 + h, x0:x0 + w], hole[y0:y0 + h, x0:x0 + w]
    big = lambda a, how: cv2.resize(a, (2 * w, 2 * h), interpolation=how)
    pipe = ZImageInpaintPipeline.from_pretrained("Tongyi-MAI/Z-Image-Turbo", torch_dtype=torch.bfloat16).to("cuda")
    for seed in map(int, seeds or (1, 2, 3)):
        gen = pipe(prompt=PEOPLE, image=Image.fromarray(big(part, cv2.INTER_CUBIC)), mask_image=Image.fromarray(big(mask, cv2.INTER_NEAREST) * 255),
                   strength=1.0, height=2 * h, width=2 * w, num_inference_steps=9, guidance_scale=0.0,
                   generator=torch.Generator("cuda").manual_seed(seed)).images[0]
        small = cv2.resize(np.asarray(gen), (w, h), interpolation=cv2.INTER_AREA)
        a = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 2.5)[..., None]
        out = base.copy()
        out[y0:y0 + h, x0:x0 + w] = (part * (1 - a) + small * a).astype(np.uint8)
        Image.fromarray(out).save(os.path.join(ROOT, "wip", "gen", f"plate_musterG_{seed}.png"))
        print("wrote plate_musterG", seed, flush=True)

THRONG = ("An immense crowd of Adeptus Mechanicus personnel, seen from behind and from above through a long telephoto "
          "lens, packed shoulder to shoulder and filling the whole frame from edge to edge, no ground visible between "
          "them, thousands of small figures in rows that recede upwards: hooded tech-priest adepts in battered, torn, "
          "patched and soot-stained crimson robes, a few in clean bright red robes, enginseers with mechanical arms "
          "and cables on their backs, forge workers and menials in grey and brown rags and leather aprons, servitors "
          "with metal limbs, skitarii in helmets with long lances; staffs, lances and small pennants stand above the "
          "heads. Backlit by fire through orange dust and smoke, dark silhouettes with warm rim light, soot, ash and "
          "grime, a frame from a war film, a muted palette of dirty crimson, grey, brown and dull amber, no text "
          "overlay, no watermark")


def throng(*seeds):
    import gentextures as G
    G.JOBS["throng"] = (2432, 1024, THRONG)
    G.generate("throng", tuple(map(int, seeds)) or (1, 2, 3))


def smoked():
    import torch
    from PIL import Image
    from diffusers import ZImageImg2ImgPipeline
    import gentextures as G
    G.JOBS["plate_musterC"] = (*SIZE, SMOKED + " " + GRIME)
    if not os.path.exists(os.path.join(G.GEN, "plate_musterC_1.png")):
        G.generate("plate_musterC", (4,))                                # the seed of B4
        os.rename(os.path.join(G.GEN, "plate_musterC_4.png"), os.path.join(G.GEN, "plate_musterC_1.png"))
    b4 = Image.open(os.path.join(G.GEN, "plate_musterB_4.png")).convert("RGB")
    pipe = ZImageImg2ImgPipeline.from_pipe(G.PIPE) if G.PIPE is not None else \
        ZImageImg2ImgPipeline.from_pretrained("Tongyi-MAI/Z-Image-Turbo", torch_dtype=torch.bfloat16).to("cuda")
    for k, strength in enumerate(STRENGTHS, 2):
        out = os.path.join(G.GEN, f"plate_musterC_{k}.png")
        if os.path.exists(out):
            continue
        pipe(prompt=SMOKED + " " + GRIME, image=b4, strength=strength, height=SIZE[1], width=SIZE[0],
             num_inference_steps=14, guidance_scale=0.0, generator=torch.Generator("cuda").manual_seed(4)).images[0].save(out)
        print("wrote plate_musterC", k, "strength", strength, flush=True)


def gen():
    import gentextures as G, genplates as P
    G.JOBS["plate_musterA"] = (*SIZE, SCENE + " " + P.PLATE)
    G.JOBS["plate_musterB"] = (*SIZE, SCENE + " " + DUSK)
    for stem in ("plate_musterA", "plate_musterB"):
        G.generate(stem, SEEDS)


def cut():
    from PIL import Image
    im = Image.open(PICTURE).convert("RGB")
    rows = round(im.width * SIZE[1] / SIZE[0])
    out = im.crop((0, TOP, im.width, TOP + rows)).resize(SIZE, Image.LANCZOS)
    out.save(os.path.join(ROOT, "wip", "gen", "plate_muster_0.png"))
    print("cut rows", TOP, "to", TOP + rows, "of", im.height, "->", out.size)


def sheet(which="drafts"):
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 30)
    names = [("0  the picture itself, cut to 19:6", "plate_muster_0")]
    if which == "smoked":
        names += [("B4  the chosen draft", "plate_musterB_4"), ("C1  smoked scene drawn from nothing, seed of B4", "plate_musterC_1")]
        names += [(f"C{k}  B4 painted again, {round(100 * s)} % changed", f"plate_musterC_{k}") for k, s in enumerate(STRENGTHS, 2)]
    elif which == "scale":
        names += [("C3  B4 painted again, 65 % changed", "plate_musterC_3")]
        names += [(f"D{s}  the scale of the picture, drawn from nothing", f"plate_musterD_{s}") for s in VAST_SEEDS]
        names += [(f"E{k}  the picture painted again, {round(100 * s)} % changed", f"plate_musterE_{k}") for k, s in enumerate(REPAINT, 1)]
    elif which == "wide":
        names = [("0  the picture itself, cut to 19:6", "plate_muster_0"), ("B4  the draft chosen first", "plate_musterB_4")]
        names += [(f"F{k}  two banner rows of the picture and the arched bridge, {round(100 * s)} % painted again, seed {seed}", f"plate_musterF_{k}")
                  for k, (s, seed) in enumerate(WIDE_DRAFTS, 1)]
    else:
        names += [(f"A{s}  new design, look of the other plates", f"plate_musterA_{s}") for s in SEEDS]
        names += [(f"B{s}  new design, look of the picture", f"plate_musterB_{s}") for s in SEEDS]
    tiles = [(label, os.path.join(ROOT, "wip", "gen", stem + ".png")) for label, stem in names]
    tiles = [(label, path) for label, path in tiles if os.path.exists(path)]
    w, h = 1216, 384
    page = Image.new("RGB", (w, (h + 44) * len(tiles)), (12, 12, 14))
    draw = ImageDraw.Draw(page)
    for k, (label, path) in enumerate(tiles):
        page.paste(Image.open(path).convert("RGB").resize((w, h), Image.LANCZOS), (0, k * (h + 44) + 44))
        draw.text((8, k * (h + 44) + 6), label, fill=(255, 210, 120), font=font)
    out = os.path.join(ROOT, "wip", "preview", "plates-muster.png" if which == "drafts" else f"plates-muster-{which}.png")
    page.save(out)
    print("wrote", out, page.size)


if __name__ == "__main__":
    {"gen": gen, "cut": cut, "sheet": sheet, "smoked": smoked, "scale": scale, "guide": guide, "wide": wide, "crowd": crowd, "throng": throng}[sys.argv[1]](*sys.argv[2:])
