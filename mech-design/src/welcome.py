"""Builds out/behemoth-welcome.html: src/welcome.template.html with the banner embedded, one self-contained file.

    python3 src/welcome.py                          # out/behemoth-welcome.html
    python3 src/welcome.py <crest.png> <page.html>  # the page with another crest, to compare two

The banner is out/10-banner-procession-marauder.avif, an animated AVIF, stored in base64 as it is.
The crest on the hazard strip is resources/assets/cog-stellars.png, the wheel of src/sigil.py; the seal over the closing
litany is resources/assets/cog-mechanicum.png, its sigil. Each is cut to the square round its visible part, with the same
room on every side, and reduced to twice its size on the page. The page shows both at one size, so the two look equally large.
The font of the title is resources/fonts/Orbitron-VF.ttf reduced to the Latin characters and stored as WOFF2 in base64.
The page holds no script: the Welcome tab of GalaxaLab runs none.
"""
import base64
import io
import pathlib
import sys

from fontTools import subset
from fontTools.ttLib import TTFont
from PIL import Image

ROOT = pathlib.Path(__file__).parent.parent
BADGE = 108                               # pixels: twice the largest size the page shows the crest and the seal at
ROOM = 0.046                              # the share of a badge's side that stays free on each side of its visible part, as round the wheel

avif = (ROOT / "out/10-banner-procession-marauder.avif").read_bytes()
print(f"banner: {len(avif) / 1e6:.2f} MB")



def png(path, side):
    """The badge `path` at `side` pixels, as the text of a data URI: the longer side of its visible part fills the
    same share of the square in every badge."""
    im = Image.open(path).convert("RGBA")
    left, top, right, bottom = im.getchannel("A").getbbox()
    whole = round(max(right - left, bottom - top) / (1 - 2 * ROOM))
    square = Image.new("RGBA", (whole, whole), (0, 0, 0, 0))
    square.paste(im.crop((left, top, right, bottom)), ((whole - (right - left)) // 2, (whole - (bottom - top)) // 2))
    b = io.BytesIO()
    square.resize((side, side), Image.LANCZOS).save(b, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


crest = png(sys.argv[1] if len(sys.argv) > 2 else ROOT / "resources/assets/cog-stellars.png", BADGE)
seal = png(ROOT / "resources/assets/cog-mechanicum.png", BADGE)
print(f"crest: {len(crest) / 1e3:.0f} kB, seal: {len(seal) / 1e3:.0f} kB")

# the font keeps its weight axis; only the characters U+0020 to U+007E stay
font = TTFont(ROOT / "resources/fonts/Orbitron-VF.ttf")
subsetter = subset.Subsetter()
subsetter.populate(unicodes=range(0x20, 0x7F))
subsetter.subset(font)
font.flavor = "woff2"
woff2 = io.BytesIO()
font.save(woff2)
print(f"font: {len(woff2.getvalue()) / 1e3:.0f} kB")

page = (ROOT / "src/welcome.template.html").read_text()
page = page.replace("{{FONT}}", base64.b64encode(woff2.getvalue()).decode())
page = page.replace("{{BANNER}}", "data:image/avif;base64," + base64.b64encode(avif).decode())
page = page.replace("{{CREST}}", crest).replace("{{SEAL}}", seal)
out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "out/behemoth-welcome.html"
out.write_text(page)
print("wrote", out, f"{out.stat().st_size / 1e6:.2f} MB")
