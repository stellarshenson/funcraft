"""Scene plates generated with Z-Image-Turbo (Tongyi-MAI, Apache-2.0) in the
banner's 19:6 shape, after the Star Colonel's reference images. MoGe-2
(src/img2geometry.py) turns the chosen plate into depth, src/scenes.py into
an animated 3D scene. Drafts go to wip/gen/plate_<name>_<seed>.png
(skipped when present); `pick` copies the chosen one (PICKS) to
wip/scene3d/<name>.png. src/inscribe.py then writes exact Latin on the
parchments and book pages listed here.

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

# the parchments each plate shows: box in plate pixels (x0, y0, x1, y1).
# The model writes illegible script; src/inscribe.py takes it out and
# drapes exact Latin on the sheet in its place.
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
                    (1568, 100, 1712, 350, 0), (1872, 55, 2012, 295, 0)],
    "voidshrine": [(1428, 440, 1490, 678, 0)],
}
# the pages of open books: the four corners of each page's text block in
# plate pixels (top left, top right, bottom right, bottom left).
PAGES = {
    "scriptorium": [((334, 426), (407, 420), (457, 490), (388, 498)), ((423, 422), (498, 418), (550, 483), (480, 497)),
                    ((902, 376), (982, 372), (923, 461), (843, 452)), ((1009, 372), (1077, 375), (1023, 462), (944, 454))],
}
PRAYER = G.SANCTA + ["Spiritus machinae, audi nos", "Ab errore numeri, libera nos", "Fiat computatio",
                     "Omnia per calculum", "Et in terra calculus", "Ave Omnissiah"]


INK, RED = (58, 34, 18), (150, 20, 12)
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"


def pick(n):
    """Copy the chosen draft of plate n to wip/scene3d/<n>.png."""
    os.makedirs(os.path.join(G.ROOT, "wip", "scene3d"), exist_ok=True)
    shutil.copy(os.path.join(G.GEN, f"plate_{n}_{PICKS[n]}.png"), os.path.join(G.ROOT, "wip", "scene3d", f"{n}.png"))
    smoky = os.path.join(G.GEN, f"plate_{n}_smoky.png")              # the copy src/cleanplate.py keeps of the old plate
    if os.path.exists(smoky):
        os.remove(smoky)


if __name__ == "__main__":
    cmd, name = sys.argv[1], sys.argv[2]
    if cmd == "gen":
        seeds = tuple(int(a) for a in sys.argv[3:]) or (1, 2, 3, 4)
        for n in (PLATES if name == "all" else [name]):
            G.generate(f"plate_{n}", seeds)
    elif cmd == "pick":
        for n in (PICKS if name == "all" else [name]):
            pick(n)
