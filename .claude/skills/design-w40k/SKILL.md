---
name: design-w40k
description: Art direction and asset recipes for Warhammer 40,000 Adeptus Mechanicus scenes in the funcraft banners (w40k-mechanicum, mech-design) - the grimdark gothic grade, distressed materials, shiny gold against absorbent crimson velvet, embroidered banners and altar cloths, the Cog Mechanicum, purity seals and Latin, figurative stained glass, candlelit shadowplay, figures painted by part, BattleMechs in household livery with ornament on every armour plate, holy cloth banners with tassels and enamel sigils, textures generated with Z-Image-Turbo and reference images turned into 3D with MoGe-2. Use when building, dressing, texturing, lighting or reviewing any W40k, Mechanicus or techno-gothic scene, when a render looks clean, flat, pale, washed out, plastic, waxy or "not W40k", or when asked for embroidery, drapes, banners, seals, sigils, heraldry, livery, holy cloth, Latin, stained glass, skulls, cogs, servitors, tech-priests or "more detail".
---

# Design W40k

Rules for the Adeptus Mechanicus look, each learned from a render the Star Colonel rejected. Paths are relative to `~/workspace/funcraft/w40k-mechanicum/`. Blender mechanics (running, rigs, volumes, API traps): `design-blender`. Loops and GIFs: `design-gif`.

## References
- `references/*.png` - the Star Colonel's target images: altar shrine, priests offering the Sacred A5000, crimson drapery, banners, stained glass. Crop and compare against them before sending anything
- `references/rogue-trader/` - Steam screenshots of Warhammer 40,000: Rogue Trader (Owlcat) and its DLC; `SOURCE.txt` lists URLs. Visual reference only
- What they share: low key, rust-umber-black mass with one or two accents; blackened iron and pewter structure with gold trims; crimson velvet everywhere; every surface carved, embroidered or written on; hundreds of dripping candles; smoke; light shafts against candle warmth

## Grade
- Measure, do not guess: luminance percentiles, saturation, share and value of red-hued pixels, on the reference and on the render. Reference 11:10 - L p25 0.05, p50 0.12, p75 0.27, p95 0.50; crimson 43 % of pixels at value 0.18
- Sweep before settling: save the scene (`-- shot=altar blend`), render a grid of haze density × exposure × look at half size, measure each
- Close-ups: AgX Punchy, exposure -0.15 (the Star Colonel asked brighter than the reference numbers), haze 0.005. Denser haze under a strong shaft turns into a pale veil; AgX turns bright saturated red pink - keep reds dark and lit by candles, not floods
- The nave (`SHOT = None`) keeps its v2 grade; close-up changes live under `if SHOT:` in `materials()`, `lights()`, `atmosphere()`, `render_setup()`

## Materials
- **Gold must gleam**: base (0.95, 0.66, 0.24), `distressed_gold(..., polish=1.0)`, grime only in crevices, `weather(amount=0.3, rough_gain=0.08)`. It needs something bright to reflect: a soft warm area light out of frame (`glint`)
- **Cloth absorbs**: velvet and robes roughness 1.0, Specular IOR Level 0, crimson sheen tint; embroidered thread alone is metallic and glossy (`embroidered(..., matte=True)`)
- **Structure is blackened pewter** (`MAT["pewter"]`), not brass; gold is for trims, halos, cogs, frames
- **Everything is old**: `weather()` wraps any material with grime blotches, soot streaks down, dust on upward faces. Only light on gold
- **Skin** is warm and mottled (`skin_mat`: bruise and jaundice noise, subsurface), never grey

## Textures
Hand-drawn PIL textures read flat, pale and "unembroidered". Generate them: `src/gentextures.py` with Z-Image-Turbo (Tongyi-MAI, Apache-2.0, 9 steps, ~4 s per image on the RTX PRO 6000).

- Prompts end with `STYLE` (fabric), `METAL` (iron) or `GLASS`: centuries-old wear spelled out (threadbare pile, moth holes, soot, wax, tarnished thread), "flat frontal orthographic, evenly lit, fills the frame"
- Draft 3+ seeds per texture, look at every one, pick in `CHOICES`. **Check every Latin word letter by letter** - it wrote CALCILUM for CALCULUM nine times, LAUDETTUR, SALVATO, COMBUTAT, FIES. Change the motto to words it spells (AVE OMNISSIAH, DEUS IN MACHINA, OMNISSIAH VULT, MACHINA VULT) rather than accept a misspelling
- `apply all`: cuts the studio backdrop to alpha (fringes and tabs hang free), writes `<stem>.png` + `<stem>_gold.png` (gold-hue mask → metallic, glossy, raised in `embroidered()`)
- Exact Latin that must be long (parchment prayers, plaques' fallback) stays in PIL (`src/textures.py`) - fill the whole surface, no blank areas. On plates it is draped, see Text on surfaces
- Relief panels (`relief_*`: niches with statues, quatrefoils with cogs, skull friezes) go on any flat iron via `relief_mat()` - box projection in object coordinates, brightness as bump

## Iconography
- **No blank slates**: every flat surface carries relief, embroidery, Latin, binary or seals. A bare parchment strip or plain cloth was the first thing noticed
- **Cog Mechanicum**: the `medallion` model (con-f-use, CC BY-SA) - loaded half a turn about Y, it arrives upside down. `cog_mechanicum()` paints its 155 loose pieces: brass cog, red field behind the machine half, black behind the bone half, bone and gunmetal skull halves, dark hoses, glowing red eye. `emblem.png` renders it upright in gold for embroidery. A skull in a plain gear is "not W40k"
- **Purity seals**: domed dark wax stamped with a cog, parchment strip written top to bottom with red rubrics, foxed and torn (`seal()`, `parchment()`); pin them in rows over cloths and hems
- **Skulls** are aged, grimy, set in cogs, niches or reliefs - never a row of clean white skulls
- Latin in use: OMNISSIAH VULT, AVE OMNISSIAH, DEUS IN MACHINA, IN CALCULO SALVATIO, SCIENTIA AD ASTRA, LABOR FIDES MACHINA AETERNA, SPIRITUS MACHINAE, MACHINA VULT, MEMORIA AETERNA, PRO OMNISSIAH; litany lines in `LITANY`

## Text on surfaces
Text placed in image space reads as pasted: the Star Colonel rejected a straight block, lines traced along the generated script, and a plane chart on warped street parchments. Accepted: the text written as a flat texture and draped on the object's shape, the shape taken from surface and outline together (`src/inscribe.py`, `DESIGN.md` 2.5).

- Shape evidence, both together: the measured surface and the outline. MoGe-2 on an enlarged crop round the object (on the whole plate a sheet is one flat plane), depth solved from the normals. A sheet is cut straight, so a wavy edge on the flat chart is warp the measurement missed - carry it into the chart (`waves()`)
- Chart = the surface laid flat (least squares conformal map); write on the chart, map back per pixel; ink multiplies the surface so its shading lies on the text
- Plane text only where bend and edge waves are both near zero
- Cut the sheet with SAM 2.1 from points, not from the text box: the box clips the sheet and hides its edges
- Remove the old script per stroke (local 75th-percentile tone). Closing blurs the sheet, inpainting leaves blotches, and text on a flattened sheet reads as an overlay
- Check `wip/preview/sheets-<name>.png` for every sheet before building: grid lines straight on a sheet drawn warped = failed drape. One accepted sheet proves nothing about the others - the book pages passed (bend 16-35°) while the street parchments were still plane (bend 4-8°)

## Drapery and glass
- Crimson must fill a large share of the frame (the reference: 43 %): curtains tied back beside the relic (`curtain()`), hangings over the table ends, banners lowered into shot to frame it, fringed
- Stained glass is figurative - a tech-priest saint with a skull face under a cog sunburst, the Machine God, a Magos holding a card - lead-lined jewel colours, one window per bay and storey (`window_mat`). Random Voronoi cells in rainbow or amber are "very not w40k"

## Light and shadowplay
- Low key: candles (clusters with wax pools and drips, one point light each), the relic, cyan coolant as the one cold accent. No front fill
- Shadowplay: spots shining through a leaded window pattern made in the light's own node tree (`window_light`: pointed arch, mullion, transom, diamond cames). Window geometry in front of a spot ends up in frame - do not build it
- Rim-light figures from behind; backlight the relic so it stands dark against a glowing lancet
- Name lights distinctly: `bpy.data.objects["shaft"]` returned a pillar cylinder called `shaft`

## Figures
- One material on a sculpt reads as wax or plastic. Paint by part per `design-blender`: loose pieces when the STL has them, region rules otherwise
- Region rules live in `src/paintfig.py`: measure on orthographic clay views with a height grid, write predicates on face centre and normal, render the views coloured by class, fix overreach (belt bands across arms, cloak rules catching heels), repeat
- Classes: skin, cloth, machine, leather; machine = worn gunmetal with brass fittings; cloth = absorbent crimson or oxblood
- A servo-skull is the model (`servo_skull` in `src/models.py`), painted by piece and lit (`src/servoskull.py`), never a skull painted into the plate by the image model: that gave a plain skull with a red eye, "not a proper servo-skull"
- A statue stays still: no head turn on the saint. A calm place (the forge) keeps its fans and drapes still

## Mechs in livery
BattleMechs as war engines of a knightly household of the Cult Mechanicus: `../mech-design/`, its `PROCESSION.md` section 6. Walk, rig and joints: `design-mech`.

- **Household** - three enamels: Mars red (0.20, 0.012, 0.009 linear), black, bone (0.44, 0.38, 0.27); each chassis is led by another one, gold trims on all. "Think of imperial knights insignia"
- **Ornament by plate size** (radius of the largest circle in the plate): under 7 cm a dark seam line; from 7 cm a steel band with rivets; from 18 cm a raised gold trim and an engraved field; from 24 cm a gold emblem (60 %), a halved field (16 %) or warning stripes (8 %); from 36 cm a cog-tooth border, an emblem and a scroll with a motto
- Trim, band and seam follow the plate's real outline at a constant distance, so they read as part of the model
- **Engraving** - a damask of quatrefoils with skulls, a filigree of vines: tone on tone on red and bone, gold inlay on black
- **Emblems** - cog with skull (on every centre-line plate), skull in laurels, winged skull, cog-axe and staff, chalice with flames, winged hourglass, fleur-de-lys, wax seal. A generated eagle had one head, the Imperial eagle has two - not used
- **Holy cloth** between the legs - crimson velvet about 1 m wide, forked end, golden tassels (kutasy) at the lower corners. Draw the layout exactly: a cog wheel that holds the house mark on a disc parted as the Machina Opus (left half bone on red, right half red on bone), mottos in type (PER CALCULUM AD ASTRA), the name in binary cant, the cog with the skull, a border of cog teeth and beads. A plain two-colour cloth "has nothing on it"
- The image model paints the velvet alone (tone-on-tone cog damask); use only its brightness on the household red, so the cloth keeps one red. Asked to repaint the whole layout it wrote FER for PER at strength 0.30 and painted a skull over the mark at 0.55
- Thread: ridges that follow each outline, a darker cord at the edges; bone thread is not metal (`../mech-design/src/procession/clothart.py`)
- **Sigil badge** (`../mech-design/src/sigil.py`) - the glyph's two inks as enamel, steel wire along every edge, a steel rim so a dark enamel shows on a dark page. Red with bone was chosen over black with red. The house mark in the cog wheel is the house's own Mechanicum sigil
- **Joints** - a steel hub, bolted flanges, ribs. A toy's snap-on ball is not W40k
- **Forge deck** - riveted black iron with brass inlays, grates that glow orange and light the legs from below; a skyline of forge towers, cog wheels and chimneys, "very mechanicum-like or holy-terra like"; chimney smoke simulated, dense and slow because it is far; embers; ground fog behind the mechs
- No smoke leaves the mechs, no halos

## Reference image to 3D
- MoGe-2 (`src/img2geometry.py`, venv `.venv-moge`, GPU 1): metric point map, normals, mask, intrinsics, plus a fill layer (depth pushed out from breaks, inpainted colour) for what a moving camera uncovers
- `src/backdrop.py` builds the textured mesh and a matching camera; from its own viewpoint it reproduces the image, moves up to ~8 cm show clean parallax, 25 cm and more smear
- Scene-level alternatives: Mira-Scene (VAST-AI, MIT, per-object meshes; eight separate environments, SAM 3D weights gated), WorldCrafter (TencentARC, image to camera-controlled video), GAE (TencentARC, research)

## Motion
The Star Colonel asked for less and subtler movement: fans a ninth of a turn per loop (the fan model has nine identical blades), lights and screen change every 8 frames, coolant rings one spacing per loop, banners sway 0.6°, the near servitor rises 1 cm once per loop. Loop rules: `design-gif`.

## Before sending
- Render `-- shot=<name> preview` (24 samples, ~40 s); looking at GIF size and 2× crops per `design-blender`
- Compare side by side with the reference crop the Star Colonel sent; measure the grade
- Previews before any animation render

<!-- improved 2026-10-07 | body 1510→2000w / 77→93L | trigger n/a (unrun) | via improve-skill -->
