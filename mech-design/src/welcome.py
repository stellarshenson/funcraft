"""Builds out/behemoth-welcome.html: src/welcome.template.html with the banner embedded, one self-contained file.

    python3 src/welcome.py                          # out/behemoth-welcome.html
    python3 src/welcome.py <crest.png> <page.html>  # the page with another crest, to compare two

The banner is out/10-banner-procession-marauder.avif, an animated AVIF, stored in base64 as it is.
The crest on the hazard strip is resources/assets/cog-stellars.png, the wheel of src/sigil.py; the seal over the closing
litany is resources/assets/cog-mechanicum.png, its sigil. Both are reduced to twice their size on the page.
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
CREST, SEAL = 108, 112                    # pixels: twice the size the page shows the crest and the seal at

avif = (ROOT / "out/10-banner-procession-marauder.avif").read_bytes()
print(f"banner: {len(avif) / 1e6:.2f} MB")



def png(path, side):
    """The picture `path` at `side` pixels, as the text of a data URI."""
    b = io.BytesIO()
    Image.open(path).resize((side, side), Image.LANCZOS).save(b, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


crest = png(sys.argv[1] if len(sys.argv) > 2 else ROOT / "resources/assets/cog-stellars.png", CREST)
seal = png(ROOT / "resources/assets/cog-mechanicum.png", SEAL)
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
