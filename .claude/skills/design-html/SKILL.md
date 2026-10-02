---
name: design-html
description: Builds small self-contained HTML pages for GalaxaLab - welcome pages, message-of-the-day pages, pages that show data by date - as one file with embedded animated images, packed data and inline scripts, and keeps them small enough to load. Use when asked to build, shrink, repackage or fix such a page ("mini webpage", "welcome page", "sermon page", "embed the gif", "page crashes the browser", "page is too big", "reduce the gifs", "encode the data in the html", "choose by date", "works without scripts"), or when a GIF or a data table has to go inside one HTML file.
---

# Self-contained HTML pages

One HTML file with everything inside: styles, images, data, scripts. A build script makes it from a template; nobody edits the built file. Paths are relative to `~/workspace/funcraft/`. Looping GIF sources: `design-gif`. The W40k look: `design-w40k`.

Working examples to copy from:

| Page | Build | Template | Has scripts |
|---|---|---|---|
| `w40k-mechanicum/out/15-sermon.html`, 2.0 MB | `src/sermon.py`, `make sermon` | `src/sermon.template.html` | yes: data by date, one of seven banners |
| `mech-design/out/06-behemoth-welcome.html`, 0.47 MB | `src/welcome.py`, `make welcome` | `src/welcome.template.html` | no: animated banner, embedded font |

## Build
- Template with `{{NAME}}` placeholders, a Python script that fills them, a Make target. `out/` is not in git
- The build prints the size of every embedded part and of the page - the size is checked on every build
- A page that others rebuild gets a how-to file beside the README: what to edit, the command, the checks (`w40k-mechanicum/SERMON.md`)
- Review comments of the lab's HTML viewer are stored in the built file. Fix the template and rebuild; the rebuild removes the comments

## Size
- Seven GIFs of 7 MB each made a 64.4 MB page. It crashed the Star Colonel's browser and headless Chrome in the lab viewer. The same page is 2.0 MB now
- Keep a page under 5 MB. Base64 adds a third to every embedded file

## Animated images
- Store an animation as animated AVIF, not GIF or WebP. Measured on one 788 × 249 banner of 40 frames: GIF about 7 MB, WebP quality 55 1.28 MB, AVIF quality 60 0.27 MB. A 1140 × 360 banner of 30 frames: GIF 6.66 MB, AVIF quality 70 0.33 MB
- Pillow 11.3 or newer: `frames[0].save(buf, format="AVIF", save_all=True, append_images=frames[1:], duration=ms, quality=60, speed=4)`. The result loops without end
- `speed=4` gave the smallest file. `speed=2` and `speed=0` were larger and took 34 s and 471 s against 6 s
- `ImageSequence.Iterator` reuses one image object. Convert inside the loop: `[f.convert("RGB") for f in ImageSequence.Iterator(gif)]`. A plain `list(...)` gives 40 copies of one frame
- To halve the frames keep every second one and double `duration`
- Deflate on top of AVIF or WebP saves nothing
- Choose the quality by eye: paste the same crop of the source and of each quality side by side. AVIF also removes the dither of the GIF
- Give the image box its ratio in CSS (`aspect-ratio: W / H`) and let the image fill it at `width: 100%`. The page then does not jump when the image arrives. All images of one box need the same ratio

## Fonts
- A font goes in the page as a data address and needs no script: `@font-face { font-family: "Name"; src: url("data:font/woff2;base64,...") format("woff2"); font-weight: 400 900; }`
- Reduce it first with fontTools: `subset.Subsetter()`, `populate(unicodes=range(0x20, 0x7F))`, `subset(font)`, `font.flavor = "woff2"`. Orbitron with its weight axis: 51 kB as TTF, 12 kB in the page (`mech-design/src/welcome.py`)
- The source file goes in `resources/fonts/`. Embed a font only when its licence allows it (Orbitron: SIL Open Font License 1.1)
- A wider font changes every box that holds it: measure the columns again

## Several images, one shown
- Keep each image as a base64 string in a script array. Give the browser only the chosen one: `img.src = "data:image/avif;base64," + STORE[i]`. An image the browser never receives costs no decoding
- Seven `<img>` elements, or a `src` that is replaced after load, make the browser decode images nobody sees
- The image for readers without scripts goes in `<noscript><img ...></noscript>`. It shows in a frame that forbids scripts and stays undecoded where scripts run
- A choice that must be the same for every reader on one day: draw with a seeded generator (mulberry32) and the day of the year as the seed. A seeded draw repeats: 57 of 365 pairs of following days got the same of seven images. `day % count` never repeats on following days

## Dynamic data
- Split the data by the key the page looks up first (the month), so the page unpacks one part
- Build: `base64.b64encode(zlib.compress(json.dumps(part, separators=(",", ":")).encode(), 9))`, one string per part
- Page: `new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream("deflate"))).json()` with `bytes = Uint8Array.from(atob(store), c => c.charCodeAt(0))`. It is asynchronous
- Measured: 366 rows, 89 kB of JSON, 53 kB in the page as 12 stores
- Raw JSON inside a `<script>` needs `.replace("</", "<\\/")`; base64 does not
- Write data to the page with `textContent`
- A date override in the address (`#MM-DD`) makes every day testable. The script runs once, so reload after a change of the address

## Scripts
- The Welcome tab of GalaxaLab runs no scripts: its frame has no `allow-scripts` and the hub serves `script-src 'none'`. A page for that tab moves with CSS animations only
- The lab's HTML viewer runs scripts only after `Trust HTML`
- A page with scripts carries its fallback in the markup: a sentence that says scripts are switched off, and the `noscript` image
- One `<script>` block per independent job. An error in one block does not stop the next. A top-level `const` of one block is visible in the next

## Text
- Readers are not native English speakers. Short literal sentences; no metaphor, idiom, slang or list of three for rhythm. A page that "sounds like AI" gets the `humanizer` skill

## Check before reporting
Run every check, then report. The 64 MB page was reported as done before the lab viewer test.

- Serve `out/`: `(setsid python3 -m http.server 8791 >/dev/null 2>&1 &)`. Stop it in a separate command: `pkill -f 'http\.server 879[1]'`. A pattern that matches the command line of its own shell ends that shell with exit 144
- Playwright for Python: `p.chromium.launch(channel="chrome", headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])`
- At 1440 px and 390 px: the expected text is on the page, no console or page errors, `document.documentElement.scrollWidth > innerWidth` is false, `naturalWidth` of the image is the stored width
- Animation: screenshots of the image at several times differ, also after one full loop
- Without scripts: a wrapper page with `<iframe sandbox="allow-same-origin" src="...">` shows the fallback
- In the lab viewer: `http://localhost:8888/user/$JUPYTERHUB_USER/lab/tree/<path from ~/workspace>` with the header `Authorization: token` read from `JUPYTERHUB_API_TOKEN` inside the script and never printed. Listen for the `crash` event, read the page inside the frame, press `Trust HTML`, read again
- Look at the screenshots
- Publishing is the Star Colonel's step. `/galaxalab/var/welcome.html` and the GalaxaHub configuration stay untouched unless asked

<!-- improved 2026-10-02 | body 0→1087w / 0→59L | benchmark n/a (not run) | via improve-skill -->
