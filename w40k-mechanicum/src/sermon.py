"""Builds out/15-sermon.html: a banner, the sermon of the day and music, one self-contained file.

    python3 src/sermon.py

The page holds the music file MUSIC as it is, in base64, on an audio element without controls, and the tunes of
PRAYERS as stores in base64: one button per tune, and the browser gets a tune only when its button is pressed.

The page holds two kinds of compressed stores, and its scripts unpack one store of each kind:

  sermons   the title and the Context of every entry of calendar/, one store per month: JSON, deflated, in
            base64. The page inflates the store of the current month only
  banners   the scene GIFs of BANNERS, each reduced to WIDTH pixels and to every STEP-th frame and stored as an
            animated AVIF in base64, about a twentieth of the size of the same GIF. The page draws one with the
            day of the year as the seed and gives only that one to the browser to decode

SERMON.md describes how to rebuild the page after a change of the sermons or of the animations.
"""
import base64
import io
import json
import pathlib
import re
import zlib

from PIL import Image, ImageSequence

ROOT = pathlib.Path(__file__).parent.parent
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
BANNERS = ["12-choir", "10-foundry", "09-reliquary", "08-hall", "06-street", "05-vault", "04-forge"]
WIDTH, STEP, QUALITY = 788, 2, 60         # banner width in pixels; every STEP-th frame is kept; AVIF quality
MUSIC = "resources/assets/Children of the Omnissiah (Music Video) - Warhammer 40,000 Mechanicus Soundtrack.mp3"
PRAYERS = [                               # the prayer buttons: label and tune
    ("Chant to Omnissiah", "resources/assets/Omnissiah Chant 40K.mp3"),
    ("Prayer to Omnissiah", "resources/assets/The Omnissiah's Pray.mp3"),
    ("Desecration of Flesh", "resources/assets/From the moment I understood the weakness of my flesh, it disgusted me.mp3"),
]


def banner(name):
    """The GIF out/<name>.gif, reduced, as an animated AVIF in base64, with its size in pixels."""
    scene = Image.open(ROOT / f"out/{name}.gif")
    size = (WIDTH, round(scene.height * WIDTH / scene.width))
    frames = [f.convert("RGB") for f in ImageSequence.Iterator(scene)][::STEP]      # copies: the iterator reuses one image
    frames = [f.resize(size, Image.LANCZOS) for f in frames]
    avif = io.BytesIO()
    frames[0].save(avif, format="AVIF", save_all=True, append_images=frames[1:],
                   duration=scene.info["duration"] * STEP, quality=QUALITY, speed=4)
    print(f"{name}: {size[0]} x {size[1]}, {len(frames)} frames, {len(avif.getvalue()) / 1e6:.2f} MB")
    return size, base64.b64encode(avif.getvalue()).decode()


# months[m][d] = [title, context] of day d + 1 of month m + 1, from the month files that src/liturgy.py checks
months = []
for m, month in enumerate(MONTHS, 1):
    text = (ROOT / f"calendar/{m:02d}-{month.lower()}.md").read_text()
    days = re.findall(rf"^## {month} (\d+) - (.+)\n\n\*\*Purpose\*\* - .+\n\n\*\*Context\*\* - (.+)$", text, flags=re.M)
    assert [int(day) for day, _, _ in days] == list(range(1, len(days) + 1)), month
    months.append([[title, context] for _, title, context in days])
assert [len(m) for m in months] == [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31], [len(m) for m in months]
plain = [json.dumps(m, separators=(",", ":")).encode() for m in months]
sermons = [base64.b64encode(zlib.compress(p, 9)).decode() for p in plain]
print(f"sermons: {sum(map(len, plain)) / 1e3:.0f} kB of JSON, {sum(map(len, sermons)) / 1e3:.0f} kB in the page")

banners = [banner(name) for name in BANNERS]
(width, height), banners = banners[0][0], [store for _, store in banners]
page = (ROOT / "src/sermon.template.html").read_text()
page = page.replace("{{WIDTH}}", str(width)).replace("{{HEIGHT}}", str(height))
page = page.replace("{{BANNER}}", banners[0])                         # shown where scripts are switched off
page = page.replace("{{BANNERS}}", json.dumps(banners))
page = page.replace("{{SERMONS}}", json.dumps(sermons))
music = (ROOT / MUSIC).read_bytes()
print(f"music: {len(music) / 1e6:.2f} MB")
page = page.replace("{{MUSIC}}", base64.b64encode(music).decode())
prayers = [(label, (ROOT / tune).read_bytes()) for label, tune in PRAYERS]
print("prayers:", ", ".join(f"{label} {len(tune) / 1e6:.2f} MB" for label, tune in prayers))
page = page.replace("{{PRAYERS}}", json.dumps([[label, base64.b64encode(tune).decode()] for label, tune in prayers]))
out = ROOT / "out/15-sermon.html"
out.write_text(page)
print("wrote", out, f"{out.stat().st_size / 1e6:.1f} MB, {sum(map(len, months))} sermons, {len(banners)} banners,",
      len(prayers), "prayers")
