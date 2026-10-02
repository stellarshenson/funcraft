"""Builds out/15-sermon.html: a banner and the sermon of the day, one self-contained file.

    python3 src/sermon.py

The page holds two kinds of compressed stores, and its scripts unpack one store of each kind:

  sermons   the rows of references/calendar-plan.md, one store per month: JSON, deflated, in base64.
            The page inflates the store of the current month only
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


# months[m][d] = [title, fact] of day d + 1 of month m + 1
months = []
for line in (ROOT / "references/calendar-plan.md").read_text().split("\n"):
    if line.startswith("## "):
        assert line[3:] == MONTHS[len(months)], line
        months.append([])
    row = re.fullmatch(r"\| (\d+) \| (.+?) \| (.+) \|", line)
    if row:
        assert int(row[1]) == len(months[-1]) + 1, line
        months[-1].append([row[2], row[3]])
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
out = ROOT / "out/15-sermon.html"
out.write_text(page)
print("wrote", out, f"{out.stat().st_size / 1e6:.1f} MB, {sum(map(len, months))} sermons, {len(banners)} banners")
