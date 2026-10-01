# w40k-mechanicum

A looping 19:6 banner GIF of a machine cathedral in the style of the Warhammer 40k Adeptus Mechanicus: a gothic nave with stained glass, red banners, candles and incense, ending at a towering altar-machine that calculates, with the Sacred A5000 enshrined at its heart. It is rendered in Blender with Cycles on the GPU from downloaded models plus procedural geometry. `references/` holds the images the look follows.

## Output

| File | Contents |
|---|---|
| `out/01-mechanicum.gif` | the first version: nave, shrines, altar-machine, standing adepts |
| `out/02-mechanicum.gif` | a praying congregation, Mechanicus priests leading the rite, servitors, embroidered banners and drapes, Latin frieze and purity seals |

Both are 1140 × 360, 40 frames at 50 ms (2 s loop). The loop is exact: the render also produces the frame at phase 1.0 as `wip/frames/seam-check.png`, which must match `f000.png`. `src/mechanicum.py` builds the latest version; the first survives as its GIF only.

## Running it

```
make assets     # medallion render → resources/assets/emblem.png, then banner, plaque and screen textures
make banner     # render wip/frames, then assemble the GIF
make previews   # front, side and top views of every downloaded model → wip/preview/models/
```

Blender lives at `~/.local/opt/blender-4.5.9-linux-x64/blender`; the Makefile sets `CUDA_VISIBLE_DEVICES=1`. A frame takes about 13 s.

## Scene

- **Nave** - gothic sci-fi wall pieces in two storeys, stained glass behind their windows, sunlight shining through it as coloured shafts in the haze. Ribbed pillars carry gold priest statues and red banners with the cog-and-skull medallion and Latin mottos
- **Shrines** - four altars in the aisle, each holding an A5000 under a turning gear halo, with candelabra and candles
- **Altar-machine** - candle-lined steps, the "CALCULATING" screen, the Sacred A5000 in a gold tracery window lit by a beam, racks of cards with blinking green compute lights, the "OMNISSIAH COMPUTAT OMNIA" plaque, a skull in a turning sunburst, red drapes, cables and organ pipes rising out of frame
- **Figures** - everyone prays. A congregation of fourteen red-robed figures kneels in rows before the altar, a worshipper kneels beside each shrine, and hooded figures stand with hands pressed together. The Magus and a shock priest lead the rite from the top step with raised arms; the Dominus and a Magos bless the congregation; servitors bow at the steps and hang racked at the sides. Hooded praying priests stand as gold statues on the pillars
- **Decor** - servo-skulls with red lenses, cherubs carrying burning braziers, banner-bearing cherubs on the altar, guardian reliefs, reliquaries, swinging thuribles with rising incense
- **Embroidery and Latin** - banners embroidered in gold thread (lozenge borders, corner cogs, the medallion in a sunburst, a motto and a Latin verse), damask drapes, a carved frieze between the storeys (OMNISSIAH VULT, DEUS IN MACHINA, SPIRITUS MACHINAE LAUDETUR ...), purity seals with hand-lettered Latin prayers

## Layout

```
src/mechanicum.py      the scene and render loop
src/kit.py             bmesh primitives, shader-graph helper, animated materials
src/models.py          loads the downloads: joins, turns to face +Y, scales, origin at the base
src/emblem.py          renders the medallion for the banners
src/textures.py        banners, plaque and screen images
src/preview_models.py  model previews
src/assemble.py        frames → GIF
in/models/originals/   downloads exactly as received, each with SOURCE.txt
resources/assets/      generated textures in use
references/            the look to follow: reference images and links
wip/                   work in progress, not in git: drafts (gen/), plates and depth (scene3d/), frames, previews, logs
out/                   finished GIFs
```

## Loop

Everything that moves is a function of `phase` in [0, 1) and completes whole cycles per loop: fans one full turn, shrine halos one tooth, the sunburst two rays (its rings are cut into 5-degree segments so they repeat too), censers, banners and servo-skulls one swing. The compute lights and the screen change state every 4 frames, 10 states per loop. The incense is two copies of one rising noise, a loop apart, cross-faded by phase, so phase 1.0 equals phase 0.0.

## Model licences

| Model | Author | Licence | Used as |
|---|---|---|---|
| Gothic scifi ruin | Terrain4Print | **CC BY-NC-SA 4.0** | nave walls |
| Servo_Skull | Plasmastorm | **CC BY-NC-SA 4.0** | servo-skulls |
| Mechanicus Magus | Wholan | **CC BY-NC-SA 4.0** | the Magus |
| Machine Cult Shock Priest | DakkaDakkaStore | **CC BY-NC-SA 4.0** | the shock priest |
| dominus | Mangaratiba | CC BY 4.0, remix of NC parts | the Dominus |
| Martian Magos | BloodyLeech | CC BY 4.0, remix of NC parts | the Magos |
| Servitor | JohntheMaker2020 | CC BY-SA 4.0 | bowing servitors |
| Cyborg / Servitor - In Storage | BigMrTong | **CC BY-NC-SA 4.0** | racked servitors |
| the praying monk | TreeZii | CC0 | congregation |
| Kneeling Figure Religious Statue | José Pedro | **CC BY-NC-SA 4.0** | congregation |
| Praying Saint | the_white_jackal | **CC BY-NC-SA 4.0** | congregation |
| Space cult Body guard praying/kneeling | Bootlegfiledealer | CC BY 4.0 | congregation |
| Praying Cultist | Yasashii | **CC BY-NC 4.0** | standing worshippers |
| Praying Jesus Christ Statue | MAY3D | **CC BY-NC 4.0** | standing worshippers |
| Priest statue | Terrain4Print | **CC BY-NC-SA 4.0** | pillar statues |
| WH40K Cherub and brazier | Helforged_Miniatures | CC BY 4.0 | cherub braziers |
| Banner Cherub Buddies | Ellie_Valkyrie | **CC BY-NC-SA 4.0** | altar cherubs |
| Guardians of Omnissiah | Vontragg | **CC BY-NC-SA 4.0** | wall reliefs |
| Gothic monstrance/reliquary | AveSavaria | CC0 | reliquaries |
| Human skull | Peter from Belgium | CC0 | altar skull |
| Geforce RTX 3060/3070 (fan only) | printiks | CC BY 4.0 | A5000 fan |
| Thurible/Censer Prop | MickyBMan | CC BY-SA 4.0 | thuribles |
| Brass Candleholders | Tina (Poly Haven) | CC0 | candelabra |
| Gothic Window | skimbal | CC BY 4.0 | altar tracery window |
| Adeptus Mechanicus Symbol | con-f-use | CC BY-SA 4.0 | medallion, banner emblem |

> [!WARNING]
> Most of the figures carry non-commercial licences, and the priests, servitors, servo-skulls, cherubs and medallion are fan-made Games Workshop designs. The GIF is fine for personal use; check before using it anywhere commercial. The A5000 card is modelled here; "RTX A5000" is an NVIDIA product name.

The other downloads in `in/models/originals/` are not used yet; their `SOURCE.txt` files record author and licence.
