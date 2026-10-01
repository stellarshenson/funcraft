"""Scene plates generated with Z-Image-Turbo (Tongyi-MAI, Apache-2.0) in the
banner's 19:6 shape, after the Star Colonel's reference images. MoGe-2
(src/img2geometry.py) turns the chosen plate into depth, src/scenes.py into
an animated 3D scene. Drafts go to wip/gen/plate_<name>_<seed>.png
(skipped when present); `pick` copies the chosen one (PICKS) to
wip/scene3d/<name>.png and writes exact Latin on its parchments.

    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=2 \\
        .venv-moge/bin/python src/genplates.py gen all 1 2 3 4
    .venv-moge/bin/python src/genplates.py pick all
"""
import os, shutil, sys
import gentextures as G

PLATE = ("Grimdark gothic Warhammer 40,000 Adeptus Mechanicus concept art, cinematic ultra-wide matte painting, "
         "extremely detailed and ornate: every surface carved, riveted, embroidered or inscribed, blackened iron "
         "and tarnished gold, crimson velvet with dense gold embroidery of cog wheels and skulls, purity seals of "
         "red wax with long parchment strips of handwritten script, centuries of soot, grime, rust and dripping "
         "candle wax, low-key chiaroscuro, warm candlelight against cold light shafts through incense smoke, "
         "rich saturated colour, sharp focus throughout, no text overlay, no watermark")

PLATES = {
    "forge": "A cramped tech-priest's workshop at night high in a gothic hive city. Across the foreground a massive "
             "cluttered iron workbench: brass callipers, cog wheels, soldering irons, glass vials, data-slates, "
             "coils of cable, a magnifying lens on an articulated arm, candle stubs in pools of wax, and in the "
             "centre a sacred black graphics card with twin cooling fans resting on a crimson velvet cloth under "
             "a hanging iron lantern. Chains and crane hooks hang from the vaulted ceiling, cabinets of small "
             "drawers, a tall pointed arch window opens onto cathedral spires, walkways and smokestacks with "
             "orange windows in blue night fog. No people.",
    "vault": "A dark server vault made into a chapel: long rows of tall black server racks framed in gilded gothic "
             "arches with skull and cog ornaments, hundreds of tiny green status lights, thick black cables hanging "
             "like vines between them, one rack door open showing a sacred graphics card glowing green in its slot, "
             "a curved cogitator screen of green text, purity seals hanging from the rack doors, votive candles "
             "on the floor, incense smoke, a hooded adept in crimson robes kneeling in prayer before the open rack.",
    "street": "A deep canyon street between towering gothic cathedral spires of a hive city at dusk, seen from street "
              "level looking along it: colossal crimson banners with gold embroidered cog-and-skull emblems hang "
              "from the buttresses, iron lamp posts and braziers along the street, statues of hooded tech-priests "
              "in niches, flying buttresses and bridges crossing overhead, grey fog, a pale sky with shafts of light, "
              "small hooded pilgrims in crimson robes standing in prayer far down the street.",
    "saint": "A radiant golden shrine: a towering gilded statue of a hooded tech-priest saint with a mechanical skull "
             "face and one glowing green lens eye, arms spread, in a gilded gothic niche before a huge golden cog "
             "halo with sunburst rays, flanked by two tall stained glass windows of robed tech-priest saints in "
             "ruby, cobalt and amber glass, crimson banners with gold embroidery hanging either side, hundreds of "
             "dripping candles on tiered iron stands, golden light pouring down through incense smoke.",
    "hall": "A long vaulted gallery hung with dozens of enormous ancient crimson velvet banners on both sides, "
            "receding into the distance, each banner covered in dense gold goldwork embroidery: cog wheels "
            "enclosing half-machine skulls, scrollwork, heavy gold bullion fringes, torn and scorched edges, purity "
            "seals pinned to them; below them rows of candles and glass reliquary cases, a black and gold tiled "
            "floor, pale shafts of light from high clerestory windows through dust.",
    "reliquary": "A close-up still life of a sacred relic: a black graphics card with twin cooling fans enshrined "
                 "inside an ornate gilded gothic reliquary casket with glass panes, pinnacles, tiny statues of hooded "
                 "tech-priests at its corners, cog wheels and small skulls worked into the gold. The casket rests on a "
                 "crimson velvet altar cloth with dense gold embroidery; purity seals of red wax with parchment strips "
                 "hang from it; a brass censer smokes beside it; a half-machine skull with a red lens eye; dripping "
                 "candles on both sides; the dark cathedral behind softly out of focus.",
    "foundry": "A vast forge-temple manufactorum: a colossal crucible pours a stream of glowing molten metal into "
               "channels in the floor, showers of sparks, giant iron cog wheels and pistons in the walls, gothic arches "
               "of blackened iron, crimson banners with gold embroidered cog emblems hanging from chains, hooded "
               "tech-priests in crimson robes silhouetted against the glare, heat haze and smoke, the light orange "
               "and white-hot.",
    "scriptorium": "A candle-lit scriptorium of the Adeptus Mechanicus: towering shelves packed with scrolls, codices "
                   "and data-slates rising into dark vaults, long parchment scrolls hanging down covered in handwritten "
                   "script, lecterns draped in crimson velvet with gold embroidery, open illuminated books with red "
                   "initials, floating servo-skulls holding quills over the parchment, brass cogitators with small green "
                   "screens, piles of wax-sealed documents, hundreds of candles.",
    "choir": "A procession of hooded tech-priests in heavy crimson robes densely embroidered with gold cog wheels and "
             "skulls, walking in two rows down a candle-lit gothic nave towards the viewer, faces hidden in shadow "
             "with glowing green mechanical eyes, holding tall candles and smoking censers, mechanical arms and cables "
             "beneath the robes, purity seals on the robes, embroidered banners carried on poles, stained glass behind.",
    "voidshrine": "A shrine chamber aboard a void warship: a colossal round rose window of stained glass with a cog "
                  "and skull emblem at its centre, its outer panes clear and looking out onto deep space, the rust-red "
                  "forge world Mars, orbital rings and distant gothic battleships; beneath the window an altar of "
                  "crimson velvet with gold candlesticks and a brass skull, crimson banners hanging either side, cold "
                  "starlight against warm candlelight.",
}
for name, what in PLATES.items():
    G.JOBS[f"plate_{name}"] = (2432, 768, what + " " + PLATE)

# the drafts chosen by eye
PICKS = {"forge": 2, "vault": 2, "street": 4, "saint": 4, "hall": 1,
         "reliquary": 4, "foundry": 4, "scriptorium": 2, "choir": 4, "voidshrine": 4}

# the parchments each plate shows: box in plate pixels (x0, y0, x1, y1), the
# slant of their lines in degrees, and optionally the brightness (0-255) a
# sheet in shadow still has. The model writes illegible script;
# `inscribe` washes it out and writes exact Latin in its place.
PARCHMENTS = {
    "street": [(195, 385, 322, 515, 0), (1395, 392, 1505, 525, 0), (1020, 522, 1086, 602, 0),
               (465, 552, 528, 622, 0), (880, 605, 918, 658, 0)],
    "forge": [(1210, 612, 1440, 745, -4), (140, 675, 330, 768, -3, 90)],
    "vault": [(205, 405, 256, 500, 0), (442, 405, 488, 495, 0), (1120, 410, 1150, 488, 0), (1290, 405, 1326, 490, 0),
              (1493, 405, 1536, 490, 0), (1746, 395, 1794, 490, 0), (2028, 395, 2079, 490, 0)],
    "saint": [(196, 598, 256, 745, 0), (1285, 612, 1340, 750, 8)],
    "hall": [(130, 380, 170, 490, 0), (1655, 392, 1703, 525, 0), (1263, 410, 1292, 518, 0)],
    "reliquary": [(640, 555, 760, 690, 0), (815, 552, 928, 678, 0), (985, 538, 1090, 660, 0)],
    "foundry": [(1440, 470, 1478, 620, 0), (2001, 470, 2101, 650, 0)],
    "scriptorium": [(280, 55, 395, 280, 0), (527, 100, 635, 305, 0), (1276, 130, 1392, 335, 0),
                    (1568, 100, 1712, 350, 0), (1872, 55, 2012, 295, 0), (305, 415, 440, 510, 2),
                    (445, 405, 590, 500, 2), (812, 362, 985, 490, 10), (990, 355, 1120, 480, 10)],
    "voidshrine": [(1428, 440, 1490, 678, 0)],
}
PRAYER = G.SANCTA + ["Spiritus machinae, audi nos", "Ab errore numeri, libera nos", "Fiat computatio",
                     "Omnia per calculum", "Et in terra calculus", "Ave Omnissiah"]


def inscribe(name):
    """Exact Latin on the plate's parchments: the parchment is the pale part
    of each box; its old script is inpainted away; then lines of the prayer
    in brown ink with a red initial per phrase, written at three times the
    size and scaled down, slanted with the sheet, kept inside it."""
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    path = os.path.join(G.ROOT, "wip", "scene3d", f"{name}.png")
    im = np.asarray(Image.open(path).convert("RGB")).copy()
    for k, (x0, y0, x1, y1, slant, *floor) in enumerate(PARCHMENTS.get(name, [])):
        floor = floor[0] if floor else None
        box = im[y0:y1, x0:x1]
        hsv = cv2.cvtColor(box, cv2.COLOR_RGB2HSV).astype(float)
        pale = (hsv[..., 2] > (floor or 0.55 * np.percentile(hsv[..., 2], 90))) & (hsv[..., 1] < 205)
        sheet = cv2.morphologyEx(pale.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
        cs, _ = cv2.findContours(sheet, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        big = max(cv2.contourArea(c) for c in cs)
        sheet = cv2.drawContours(np.zeros_like(sheet), [c for c in cs if cv2.contourArea(c) > 0.08 * big], -1, 1, -1)   # stains included
        inner = cv2.erode(sheet, np.ones((5, 5), np.uint8))
        # a clean sheet: the parchment's own tone and stains, blurred past the
        # size of a letter over the sheet only, with a fine grain put back
        f = pale.astype(float) * inner
        clean = cv2.GaussianBlur(box * f[..., None], (0, 0), 5) / (cv2.GaussianBlur(f, (0, 0), 5)[..., None] + 1e-3)
        clean += np.random.default_rng(k).normal(0, 4, clean.shape[:2])[..., None]
        wash = cv2.GaussianBlur(inner.astype(float), (0, 0), 1.2)[..., None]
        box = (box * (1 - wash) + clean * wash).clip(0, 255).astype(np.uint8)
        light = box.astype(float).mean(-1) > 0.6 * np.percentile(box.astype(float).mean(-1)[inner > 0], 60)
        w, h = x1 - x0, y1 - y0
        S = 3
        size = max(8, min(w // 12, 16)) * S
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf", size)
        layer = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        words = " ".join(PRAYER[(k * 3 + j) % len(PRAYER)].capitalize() + "." for j in range(12)).split()
        cols = inner.any(0)
        left, right = np.argmax(cols), len(cols) - np.argmax(cols[::-1])
        y, i, prev = size * 0.4, 0, "."
        while y + size < h * S and i < len(words):
            row = inner[min(h - 1, int((y + size * 0.6) / S))]
            if row.any():                        # the sheet's own width at this line
                left, right = np.argmax(row), len(row) - np.argmax(row[::-1])
            band = slice(int(y / S), min(h, int((y + size) / S)))
            if (light[band, left:right].mean() if right > left else 0) < 0.6:
                y += size * 1.2                  # a seal or a tear across this line
                continue
            line = [words[i]]                    # a word too long for a narrow tag runs to the edge
            i += 1
            while i < len(words) and font.getlength(" ".join(line + [words[i]])) < (right - left) * S * 0.86:
                line.append(words[i])
                i += 1
            x = (left + (right - left) * 0.07) * S
            for wd in line:
                red = prev.endswith(".")             # a red initial opens each phrase
                d.text((x, y), wd[0], font=font, fill=(150, 20, 12, 235) if red else (58, 34, 18, 225))
                d.text((x + font.getlength(wd[0]), y), wd[1:], font=font, fill=(58, 34, 18, 225))
                x += font.getlength(wd + " ")
                prev = wd
            y += size * 1.2
        layer = layer.rotate(slant, resample=Image.BICUBIC).resize((w, h), Image.LANCZOS)
        a = np.asarray(layer).astype(float) / 255
        alpha = a[..., 3] * cv2.GaussianBlur(inner.astype(float), (0, 0), 1.0)
        out = box.astype(float) * (1 - alpha[..., None]) + a[..., :3] * 255 * alpha[..., None]
        im[y0:y1, x0:x1] = cv2.GaussianBlur(out, (0, 0), 0.4).clip(0, 255).astype(np.uint8)
    Image.fromarray(im).save(path)


if __name__ == "__main__":
    cmd, name = sys.argv[1], sys.argv[2]
    if cmd == "gen":
        seeds = tuple(int(a) for a in sys.argv[3:]) or (1, 2, 3, 4)
        for n in (PLATES if name == "all" else [name]):
            G.generate(f"plate_{n}", seeds)
    elif cmd == "pick":                           # copy the chosen draft and write its Latin
        os.makedirs(os.path.join(G.ROOT, "wip", "scene3d"), exist_ok=True)
        for n in (PICKS if name == "all" else [name]):
            shutil.copy(os.path.join(G.GEN, f"plate_{n}_{PICKS[n]}.png"), os.path.join(G.ROOT, "wip", "scene3d", f"{n}.png"))
            inscribe(n)
