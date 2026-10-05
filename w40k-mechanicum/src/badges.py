"""The service badges of the daily sermons, drawn by the image model Z-Image-Turbo (Tongyi-MAI, Apache-2.0): one
embroidered duty patch per day of the calendar. badges.md says what the badge of each day shows, and the kind of day
in the calendar title gives the outline of the patch.

    python src/badges.py gen [day ...]     three drafts of each badge, wip/badges/<day>_<seed>.png; a draft that exists is kept
    python src/badges.py sheet <month>     the drafts of a month (01 to 12), eleven days per sheet, wip/badges/sheet_<month>_<part>.png
    python src/badges.py picks [month ...] the draft of every day that goes into the page, one sheet per month, wip/badges/picks_<month>.png
    python src/badges.py apply             those drafts without their black ground -> resources/assets/badges/<day>.png

gen needs the project's ML venv and one GPU, chosen by its nvidia-smi index:

    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 HF_HUB_OFFLINE=1 .venv-moge/bin/python src/badges.py gen

The draft of a day is the one named in CHOICES. A day without a choice gets the first of its drafts that shows one
whole patch inside the frame. src/sermon.py puts the badges into the sermon page.
"""
import pathlib
import re
import sys

from PIL import Image, ImageDraw

from seals import box, cut, fit

ROOT = pathlib.Path(__file__).parent.parent
WIP = ROOT / "wip" / "badges"
OUT = ROOT / "resources" / "assets" / "badges"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
SEEDS = (1, 2, 3)
SIZE = 240                                 # longer side of a stored badge in pixels: twice its size on the page

LOOK = ("One embroidered cloth patch seen from the front, lying flat, centred, isolated on a pure black background, "
        "the whole patch inside the frame with a black margin around it. A military duty patch of the Adeptus "
        "Mechanicus, Warhammer 40,000, grimdark gothic. Dense machine embroidery: raised satin stitch, visible thread "
        "texture, a thick merrowed edge of old gold thread, slightly worn and faded, soot in the recesses. Colours: "
        "dark crimson, black, old gold, bone white. No text, no letters, no numbers. Studio product photograph, "
        "evenly lit, sharp focus, nothing else in the frame")
# kind of day, the first word of its title: the outline of its patch
FORMS = {
    "Feast": "A round badge with a rim of short straight rays like a sunburst",
    "Rite": "A badge in the shape of a cog wheel with twelve square teeth",
    "Observance": "A badge in the shape of a heater shield",
    "Vigil": "A tall badge in the shape of a pointed gothic arch window",
    "Commemoration": "A badge in the shape of a vertical oval with a halo of fine gold rays around its edge",
    "Other": "A tall octagonal badge, a rectangle with cut corners",
}
# day: seed of the draft that goes into the page, where the first whole draft is not the best one
CHOICES = {"01-19": 2, "01-22": 2, "02-24": 3, "03-24": 3}


def calendar():
    """day "mm-dd": (kind of day, title, what the badge shows), from calendar/ and badges.md."""
    shows = dict(re.findall(r"^- \*\*(\d\d-\d\d)\*\* - (.+)$", (ROOT / "badges.md").read_text(), flags=re.M))
    days = {}
    for m, month in enumerate(MONTHS, 1):
        text = (ROOT / f"calendar/{m:02d}-{month.lower()}.md").read_text()
        for day, title in re.findall(rf"^## {month} (\d+) - (.+)$", text, flags=re.M):
            kind = title.split()[0]
            kind = kind if kind in FORMS else "Commemoration" if "Saint" in title else "Other"
            days[f"{m:02d}-{int(day):02d}"] = (kind, title)
    assert set(days) == set(shows), f"badges.md and calendar/ differ: {sorted(set(days) ^ set(shows))}"
    return {day: (*days[day], shows[day]) for day in days}


def prompt(kind, shows):
    return f"{FORMS[kind]}. It shows {shows}. {LOOK}"


def generate(days):
    import time
    import torch
    from diffusers import ZImagePipeline
    WIP.mkdir(parents=True, exist_ok=True)
    all_days, pipe, start, made = calendar(), None, time.time(), 0
    for day in days or all_days:
        kind, _, shows = all_days[day]
        for seed in SEEDS:
            draft = WIP / f"{day}_{seed}.png"
            if draft.exists():
                continue
            if pipe is None:
                pipe = ZImagePipeline.from_pretrained("Tongyi-MAI/Z-Image-Turbo", torch_dtype=torch.bfloat16).to("cuda")
            image = pipe(prompt=prompt(kind, shows), width=1024, height=1024, num_inference_steps=9,
                         guidance_scale=0.0, generator=torch.Generator("cuda").manual_seed(seed)).images[0]
            image.save(draft)
            made += 1
            print(f"wrote {draft.name}  {made} drafts in {time.time() - start:.0f} s", flush=True)
    print("generation complete", flush=True)


def whole(image):
    """True when a cut draft shows one patch that lies inside the frame."""
    import numpy as np
    from scipy import ndimage
    left, top, right, bottom = box(image)
    if min(left, top, image.width - right, image.height - bottom) < 6:
        return False
    objects, _ = ndimage.label(np.asarray(image.getchannel("A")) > 8)
    sizes = np.bincount(objects.ravel())[1:]
    return 0.15 < sizes.sum() / objects.size < 0.8 and sizes.max() > 0.97 * sizes.sum()


def pick(day):
    """The seed of the draft of a day that goes into the page, and whether that draft shows one whole patch."""
    seeds = [CHOICES[day]] if day in CHOICES else SEEDS
    for seed in seeds:
        if whole(cut(Image.open(WIP / f"{day}_{seed}.png").convert("RGB"))):
            return seed, True
    return seeds[0], False


def sheet(month):
    """All drafts of the days of a month beside each other, each with its seed, to choose from."""
    days = [day for day in calendar() if day.startswith(month)]
    for part in range(0, len(days), 11):
        rows = days[part:part + 11]
        out = Image.new("RGB", (250 * len(SEEDS) + 50, 250 * len(rows)), "black")
        draw = ImageDraw.Draw(out)
        for row, day in enumerate(rows):
            draw.text((4, 250 * row + 6), day, fill=(255, 90, 90))
            for column, seed in enumerate(SEEDS):
                draft = WIP / f"{day}_{seed}.png"
                if draft.exists():
                    out.paste(Image.open(draft).convert("RGB").resize((250, 250), Image.LANCZOS), (50 + 250 * column, 250 * row))
                draw.text((56 + 250 * column, 250 * row + 6), str(seed), fill=(255, 90, 90))
        name = f"sheet_{month}_{part // 11 + 1}.png"
        out.save(WIP / name)
        print("wrote", name, out.size)


def picks(months):
    """The draft that goes into the page for every day, one sheet per month, for the named months or for all. A red
    frame marks a day none of whose drafts shows one whole patch."""
    days, failed = list(calendar()), []
    for m in map(int, months or range(1, 13)):
        month = [day for day in days if day.startswith(f"{m:02d}")]
        out = Image.new("RGB", (8 * 170, 4 * 170), "black")
        draw = ImageDraw.Draw(out)
        for index, day in enumerate(month):
            seed, good = pick(day)
            x, y = 170 * (index % 8), 170 * (index // 8)
            out.paste(Image.open(WIP / f"{day}_{seed}.png").convert("RGB").resize((170, 170), Image.LANCZOS), (x, y))
            draw.text((x + 4, y + 4), f"{day[3:]} s{seed}", fill=(255, 90, 90))
            if not good:
                draw.rectangle((x, y, x + 169, y + 169), outline=(255, 0, 0), width=3)
                failed.append(day)
        out.save(WIP / f"picks_{m:02d}.png")
        print("wrote", f"picks_{m:02d}.png")
    print("no whole draft:", failed or "none")


def apply():
    """The chosen drafts without their black ground, as PNG files with transparency, SIZE pixels on the longer side."""
    OUT.mkdir(parents=True, exist_ok=True)
    total = 0
    for day in calendar():
        seed, _ = pick(day)
        badge = fit(cut(Image.open(WIP / f"{day}_{seed}.png").convert("RGB")), SIZE)
        badge.save(OUT / f"{day}.png", optimize=True)
        total += (OUT / f"{day}.png").stat().st_size
    print(f"wrote {len(list(OUT.glob('*.png')))} badges, {total / 1e6:.1f} MB, to {OUT}")


if __name__ == "__main__":
    command, arguments = (sys.argv[1] if len(sys.argv) > 1 else ""), sys.argv[2:]
    if command == "gen":
        generate(arguments)
    elif command == "sheet" and arguments:
        sheet(arguments[0])
    elif command == "picks":
        picks(arguments)
    elif command == "apply":
        apply()
    else:
        sys.exit(__doc__)
