"""Builds out/06-behemoth-welcome.html: src/welcome.template.html with the banner embedded, one self-contained file.

    python3 src/welcome.py

The banner is out/05-banner-offset.gif stored as an animated AVIF in base64, about a twentieth of the size of the GIF.
The font of the title is resources/fonts/Orbitron-VF.ttf reduced to the Latin characters and stored as WOFF2 in base64.
The page holds no script: the Welcome tab of GalaxaLab runs none.
"""
import base64
import io
import pathlib

from fontTools import subset
from fontTools.ttLib import TTFont
from PIL import Image, ImageSequence

ROOT = pathlib.Path(__file__).parent.parent
QUALITY = 70                              # AVIF quality, 0 to 100

scene = Image.open(ROOT / "out/05-banner-offset.gif")
frames = [f.convert("RGB") for f in ImageSequence.Iterator(scene)]          # copies: the iterator reuses one image
avif = io.BytesIO()
frames[0].save(avif, format="AVIF", save_all=True, append_images=frames[1:], duration=scene.info["duration"],
               quality=QUALITY, speed=4)
print(f"banner: {scene.width} x {scene.height}, {len(frames)} frames, {len(avif.getvalue()) / 1e6:.2f} MB")

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
page = page.replace("{{BANNER}}", "data:image/avif;base64," + base64.b64encode(avif.getvalue()).decode())
out = ROOT / "out/06-behemoth-welcome.html"
out.write_text(page)
print("wrote", out, f"{out.stat().st_size / 1e6:.2f} MB")
