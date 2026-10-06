"""Builds the sermon page as a package: the folder out/15-sermon/ with index.html and a resources folder, and the
same files as out/15-sermon.zip, with index.html at the root of the archive.

    python3 src/sermon.py

index.html holds the markup and the styles of src/sermon.template.html. Everything else is a file in resources/, and
the page asks for a file only when it needs it:

  <name>.js              the scripts: every script block of the template, named by its data-name. They hold the small
                         tables: the names of the banners, the prayers, the reward sermons of rewards.md and the
                         size of every badge
  sermons/<mm>.json.gz   the title and the Context of every entry of calendar/ for one month: JSON, gzipped. The
                         page gets the file of the current month and inflates it
  banners/<name>.avif    the scene GIFs of BANNERS, each reduced to WIDTH pixels and to every STEP-th frame, as an
                         animated AVIF, about a twentieth of the size of the same GIF. The page draws one with the
                         day of the year as the seed
  badges/<mm-dd>.avif    the service badge of every day, from resources/assets/badges/ (src/badges.py). The page
                         shows the badge of the day
  seals/<number>.avif    the seal of every reward sermon, from resources/assets/seal_<number>.png (src/seals.py).
                         The page shows one when the reader's total of prayers reaches its number
  music.mp3              the music file MUSIC as it is, on an audio element without controls
  prayers/<n>.mp3        the tunes of PRAYERS as they are: one button per tune

SERMON.md describes how to rebuild the page after a change of the sermons or of the animations.
"""
import gzip
import io
import json
import pathlib
import re
import shutil
import textwrap
import zipfile

from PIL import Image, ImageSequence

ROOT = pathlib.Path(__file__).parent.parent
OUT = ROOT / "out/15-sermon"              # the package as a folder; out/15-sermon.zip holds the same files
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
BANNERS = ["12-choir", "10-foundry", "09-reliquary", "08-hall", "06-street", "05-vault", "04-forge"]
WIDTH, STEP, QUALITY = 788, 2, 60         # banner width in pixels; every STEP-th frame is kept; AVIF quality
SEAL_QUALITY = 70                         # AVIF quality of the seals of the reward sermons
BADGE_QUALITY = 55                        # AVIF quality of the service badges of the days
MUSIC = "resources/assets/Children of the Omnissiah (Music Video) - Warhammer 40,000 Mechanicus Soundtrack.mp3"
PRAYERS = [                               # the prayer buttons: label, tune and gain (1 plays the tune as it is)
    ("Chant to Omnissiah", "resources/assets/Omnissiah Chant 40K.mp3", 1.4),
    ("Prayer to Omnissiah", "resources/assets/The Omnissiah's Pray.mp3", 1),
    ("Desecration of Flesh", "resources/assets/I made the PERFECT Tech Priest voice from scratch Warhammer 40k.mp3", 0.7),
]
sizes = {}                                # folder of the package: bytes written into it
written = []                              # the files of the package, as paths inside it


def write(name, data):
    """Writes one file of the package and returns its address in the page."""
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    folder = name.rpartition("/")[0]
    sizes[folder] = sizes.get(folder, 0) + len(data)
    written.append(name)
    return name


def avif(image, quality, **options):
    """An image, or the first frame of an animation with its other frames in options, as the bytes of an AVIF."""
    data = io.BytesIO()
    image.save(data, format="AVIF", quality=quality, speed=4, **options)
    return data.getvalue()


def banner(name):
    """Writes the GIF out/<name>.gif, reduced, as an animated AVIF and returns its size in pixels."""
    scene = Image.open(ROOT / f"out/{name}.gif")
    size = (WIDTH, round(scene.height * WIDTH / scene.width))
    frames = [f.convert("RGB") for f in ImageSequence.Iterator(scene)][::STEP]      # copies: the iterator reuses one image
    frames = [f.resize(size, Image.LANCZOS) for f in frames]
    data = avif(frames[0], QUALITY, save_all=True, append_images=frames[1:], duration=scene.info["duration"] * STEP)
    write(f"resources/banners/{name}.avif", data)
    print(f"{name}: {size[0]} x {size[1]}, {len(frames)} frames, {len(data) / 1e6:.2f} MB")
    return size


shutil.rmtree(OUT, ignore_errors=True)    # the package of the build before this one

# months[m][d] = [title, context] of day d + 1 of month m + 1, from the month files that src/liturgy.py checks
months = []
for m, month in enumerate(MONTHS, 1):
    text = (ROOT / f"calendar/{m:02d}-{month.lower()}.md").read_text()
    days = re.findall(rf"^## {month} (\d+) - (.+)\n\n\*\*Purpose\*\* - .+\n\n\*\*Context\*\* - (.+)$", text, flags=re.M)
    assert [int(day) for day, _, _ in days] == list(range(1, len(days) + 1)), month
    months.append([[title, context] for _, title, context in days])
    # mtime=0: the same sermons give the same bytes in every build
    write(f"resources/sermons/{m:02d}.json.gz", gzip.compress(json.dumps(months[-1], separators=(",", ":")).encode(), 9, mtime=0))
assert [len(m) for m in months] == [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31], [len(m) for m in months]

width, height = [banner(name) for name in BANNERS][0]
page = (ROOT / "src/sermon.template.html").read_text()
page = page.replace("{{WIDTH}}", str(width)).replace("{{HEIGHT}}", str(height))
page = page.replace("{{BANNER}}", BANNERS[0])                         # shown where scripts are switched off
page = page.replace("{{BANNERS}}", json.dumps(BANNERS))
write("resources/music.mp3", (ROOT / MUSIC).read_bytes())
prayers = [[label, write(f"resources/prayers/{n}.mp3", (ROOT / tune).read_bytes()), gain]
           for n, (label, tune, gain) in enumerate(PRAYERS, 1)]
page = page.replace("{{PRAYERS}}", json.dumps(prayers))

# rewards = [number, rank, title, sermon] of every entry of rewards.md
rewards = [[int(number), rank, title, sermon] for number, title, rank, sermon in
           re.findall(r"^## (\d+) - (.+)\n\n\*\*Rank\*\* - (.+)\n\n\*\*Sermon\*\* - (.+)$", (ROOT / "rewards.md").read_text(), flags=re.M)]
assert rewards and len({number for number, *_ in rewards}) == len(rewards), "rewards.md: no entry, or one number twice"
for number, *_ in rewards:
    write(f"resources/seals/{number}.avif", avif(Image.open(ROOT / f"resources/assets/seal_{number}.png"), SEAL_QUALITY))
page = page.replace("{{REWARDS}}", json.dumps(rewards))

# badges[m][d] = [width, height] of the badge of day d + 1 of month m + 1
badges = []
for m, days in enumerate(months, 1):
    badges.append([])
    for d in range(1, len(days) + 1):
        image = Image.open(ROOT / f"resources/assets/badges/{m:02d}-{d:02d}.png")
        write(f"resources/badges/{m:02d}-{d:02d}.avif", avif(image, BADGE_QUALITY))
        badges[-1].append(image.size)
page = page.replace("{{BADGES}}", json.dumps(badges, separators=(",", ":")))


def script(block):
    """Writes one script block of the template to its file and returns the tag that loads the file."""
    return f'<script src="{write(f"resources/{block[1]}.js", textwrap.dedent(block[2]).encode())}"></script>'


page = re.sub(r'<script data-name="(\w+)">\n(.*?)</script>', script, page, flags=re.S)
assert "{{" not in page and "<script>" not in page, "a placeholder or an inline script is left in the page"
write("index.html", page.encode())

# The archive takes the files this build wrote, not the files in the folder: JupyterLab puts checkpoint copies of new
# files into the folder while the build runs. An archive needs no entry for a folder.
with zipfile.ZipFile(OUT.with_suffix(".zip"), "w", zipfile.ZIP_DEFLATED) as archive:
    for name in sorted(written):
        archive.write(OUT / name, name)
print("package:", ", ".join(f"{folder or 'index.html'} {size / 1e6:.2f} MB" for folder, size in sorted(sizes.items())))
print(f"wrote {OUT} and {OUT.with_suffix('.zip').name}: {len(written)} files, {sum(sizes.values()) / 1e6:.1f} MB,",
      f"zip {OUT.with_suffix('.zip').stat().st_size / 1e6:.1f} MB, {sum(map(len, months))} sermons, {len(BANNERS)} banners,",
      len(prayers), "prayers,", len(rewards), "rewards,", sum(map(len, badges)), "badges")
