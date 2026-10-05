"""The seals of the reward sermons, designed with the image model Z-Image-Turbo (Tongyi-MAI, Apache-2.0): one seal per
entry of rewards.md, each with a design of its own.

    python src/seals.py gen [number ...]    six drafts of each seal, wip/seals/<number>_<seed>.png; a draft that exists is kept
    python src/seals.py sheet               all drafts of every seal on one sheet per seal, wip/seals/sheet_<number>.png
    python src/seals.py apply               the drafts named in CHOICES, without their black ground -> resources/assets/seal_<number>.png

gen needs the project's ML venv and one GPU, chosen by its nvidia-smi index:

    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 HF_HUB_OFFLINE=1 .venv-moge/bin/python src/seals.py gen

src/sermon.py puts the seals into the sermon page. A new entry of rewards.md needs a prompt in SEALS and a seed in CHOICES.
"""
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFilter

ROOT = pathlib.Path(__file__).parent.parent
WIP = ROOT / "wip" / "seals"
OUT = ROOT / "resources" / "assets"
SEEDS = (1, 2, 3, 4, 5, 6)
SIZE = 360                                 # longer side of a stored seal in pixels: twice its size on the page
GROUND = 26                                # a pixel whose brightest channel is below this value can be ground
GROUNDS = {27182: 60}                      # a draft with a lighter ground: its own value in place of GROUND
HOLES = (64, 256)                          # seals whose openings are cut out too: dark areas of 3000 pixels or more inside the object

LOOK = ("One object seen from the front, centred, isolated on a pure black background, the whole object inside the "
        "frame with a black margin around it. Warhammer 40,000 Adeptus Mechanicus relic, grimdark gothic: worn edges, "
        "fine scratches, soot in the recesses, polished highlights. No text, no letters, no numbers. Studio product "
        "photograph, evenly lit, sharp focus, nothing else in the frame")
SKULL = ("a skull that is half pale bone and half dark steel machine, the machine half with one round glowing red "
         "lens as its eye")
SEALS = {
    # number of the reward: what the seal shows
    4: "A purity seal: a thick round disc of dark red sealing wax with a pressed scalloped edge, stamped in its centre "
       "with a small cog wheel around four round brass studs set in a square, and two strips of old yellowed "
       "parchment hanging below the wax, covered in tiny lines of faded ink",
    42: "A round bronze medallion on a short crimson ribbon: its rim is a cog wheel with square teeth, its face has a "
        "ring of square marks all the way around, one raised and polished, the next sunken and dark, in turn, and "
        "in the centre is " + SKULL,
    64: "A square plane of magnetic core memory set in a round cog wheel of brass: inside a frame of blackened iron a "
        "dense fine grid of many tiny gold rings threaded on thin crossing copper wires, a rivet at each corner of "
        "the frame, hanging from a short chain of iron links",
    137: "A round medallion of polished gold and dark steel on a crimson ribbon: in its centre a large faceted clear "
         "crystal lens that glows with white and pale blue light, thin gold rays that spread from the lens to a rim "
         "of cog teeth, fine engraved rings between the rays",
    256: "A heavy badge of gunmetal steel and brass: a large cog wheel with square teeth, across it a crossed axe "
         "with a cog-shaped blade and a large wrench, a small skull where they cross, two coiled segmented metal "
         "tentacle arms with claws that curl around the sides, copper cables",
    314: "A round golden reliquary medal on a wide crimson silk ribbon with gold edges: inside a rim of gold cog "
         "teeth an armillary sphere of nested golden rings and orbits, in its centre a small red sphere, the planet "
         "Mars, tiny gears between the rings",
    666: "A round wheel of chance of black iron and gold inside a rim of cog teeth: a ring of many small pockets of "
         "red enamel and black enamel in turn, like a roulette wheel, one small gold ball held fast in a pocket by a "
         "tiny iron clamp and a chain, and in the centre of the wheel a red wax purity seal with a parchment strip",
    1024: "An ornate order star of gold and crimson enamel on a wide crimson ribbon: a star of ten gold rays with a "
          "small red gem on every point, on it a cog wheel of black iron and polished steel that encloses " + SKULL +
          ", and a laurel wreath of gold around the cog",
    1729: "A grand jewelled relic badge on a crimson and black ribbon: two interlocked cubes of polished gold and "
          "dark steel, every face engraved with fine circuit lines, in the centre of a golden sunburst of long sharp "
          "rays inside a rim of cog teeth, large red gems, gold filigree",
    6174: "A commander's badge of gold and black iron on a crimson sash: a cog wheel with square teeth, on its face a "
          "spiral of thick gold wire that winds inwards to one large round red gem in the exact centre, and behind the "
          "cog two crossed gothic halberds with cog-shaped blades",
    8128: "A venerable reliquary medal of pale gold and polished steel on a white and crimson ribbon: a ring of even "
          "cog teeth around one large flawless round diamond, six identical small golden skulls set at equal distances "
          "around the diamond, a halo of fine straight gold rays, thin gold filigree, perfectly symmetrical",
    27182: "A great seal of office of gold and crimson enamel on a heavy gold chain of office: a golden spiral like a "
           "nautilus shell whose chambers are cog teeth that grow from tiny to large, in the centre of the spiral " +
           SKULL + ", a small red enamel disc, the planet Mars, above it, rubies and filigree",
    40000: "The grand seal of the Fabricator-General of Mars: a very large and richly ornate golden cog wheel with "
           "square teeth that encloses " + SKULL + ", with a golden crown on the skull, behind the cog the red planet "
           "Mars as a large disc of red enamel, mechanical wings of gold feathers and steel cables spread to both "
           "sides, rubies and filigree, and two purity seals of red wax with parchment strips hanging below",
}
# number of the reward: seed of the draft that goes into the page
CHOICES = {4: 4, 42: 2, 64: 1, 137: 3, 256: 5, 314: 3, 666: 6, 1024: 5, 1729: 3, 6174: 1, 8128: 1, 27182: 4, 40000: 2}


def generate(numbers):
    import torch
    from diffusers import ZImagePipeline
    WIP.mkdir(parents=True, exist_ok=True)
    pipe = None
    for number in numbers:
        for seed in SEEDS:
            draft = WIP / f"{number}_{seed}.png"
            if draft.exists():
                continue
            if pipe is None:
                pipe = ZImagePipeline.from_pretrained("Tongyi-MAI/Z-Image-Turbo", torch_dtype=torch.bfloat16).to("cuda")
            image = pipe(prompt=SEALS[number] + ". " + LOOK, width=1024, height=1024, num_inference_steps=9,
                         guidance_scale=0.0, generator=torch.Generator("cuda").manual_seed(seed)).images[0]
            image.save(draft)
            print("wrote", draft.name, flush=True)
    print("generation complete", flush=True)


def sheet():
    """The drafts of a seal beside each other, each with its seed, to choose from."""
    for number in SEALS:
        drafts = [(seed, WIP / f"{number}_{seed}.png") for seed in SEEDS if (WIP / f"{number}_{seed}.png").exists()]
        if not drafts:
            continue
        out = Image.new("RGB", (400 * len(drafts), 400), "black")
        for column, (seed, path) in enumerate(drafts):
            out.paste(Image.open(path).convert("RGB").resize((400, 400), Image.LANCZOS), (400 * column, 0))
            ImageDraw.Draw(out).text((400 * column + 8, 6), str(seed), fill=(255, 60, 60))
        out.save(WIP / f"sheet_{number}.png")
        print("wrote", f"sheet_{number}.png", out.size)


def cut(image, ground=GROUND, holes=False):
    """The image without its black ground, with transparency, in its frame. The ground is the dark area that touches
    the border. The dark inside the object stays, except with holes: then dark areas of 3000 pixels or more inside
    the object are cut out too."""
    import numpy as np
    from scipy import ndimage
    regions, _ = ndimage.label(np.asarray(image).max(axis=2) < ground)
    border = np.concatenate([regions[0], regions[-1], regions[:, 0], regions[:, -1]])
    large = np.flatnonzero(np.bincount(regions.ravel()) >= 3000) if holes else []
    ground = np.isin(regions, [region for region in {*border.tolist(), *large} if region])
    objects, _ = ndimage.label(~ground)
    ground |= np.isin(objects, np.flatnonzero(np.bincount(objects.ravel()) < 500))      # specks of dust on the ground
    alpha = Image.fromarray(np.where(ground, 0, 255).astype("uint8"))
    out = image.copy()
    out.putalpha(alpha.filter(ImageFilter.GaussianBlur(1.2)))          # a soft edge instead of a stair
    return out


def box(image):
    """The bounding box of the visible part of a cut image."""
    return image.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()


def fit(image, size):
    """A cut image, cropped to its visible part and reduced to size pixels on the longer side."""
    image = image.crop(box(image))
    scale = size / max(image.size)
    return image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)


def apply():
    """The chosen drafts without their black ground, as PNG files with transparency, SIZE pixels on the longer side."""
    for number, seed in CHOICES.items():
        image = Image.open(WIP / f"{number}_{seed}.png").convert("RGB")
        seal = fit(cut(image, GROUNDS.get(number, GROUND), number in HOLES), SIZE)
        seal.save(OUT / f"seal_{number}.png", optimize=True)
        print(f"seal_{number}.png", seal.size, (OUT / f"seal_{number}.png").stat().st_size // 1024, "kB")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "gen":
        generate([int(number) for number in sys.argv[2:]] or list(SEALS))
    elif command == "sheet":
        sheet()
    elif command == "apply":
        apply()
    else:
        sys.exit(__doc__)
