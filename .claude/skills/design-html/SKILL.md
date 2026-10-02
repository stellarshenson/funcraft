---
name: design-html
description: Builds small self-contained HTML pages for GalaxaLab - welcome pages, message-of-the-day pages, pages that show data by date - as one file with embedded animated images, packed data and inline scripts, and keeps them small enough to load. Use when asked to build, shrink, repackage or fix such a page ("mini webpage", "welcome page", "sermon page", "embed the gif", "page crashes the browser", "page is too big", "reduce the gifs", "encode the data in the html", "choose by date", "works without scripts", "scale the fonts with the screen size", "number is mispositioned", "play music in the background", "embed the mp3"), or when a GIF or a data table has to go inside one HTML file.
---

# Self-contained HTML pages

One HTML file with everything inside: styles, images, data, scripts. A build script makes it from a template; nobody edits the built file. Paths are relative to `~/workspace/funcraft/`. Looping GIF sources: `design-gif`. The W40k look: `design-w40k`.

Working examples to copy from:

| Page | Build | Template | Has scripts |
|---|---|---|---|
| `w40k-mechanicum/out/15-sermon.html`, 7.1 MB | `src/sermon.py`, `make sermon` | `src/sermon.template.html` | yes: data by date, one of seven banners, music, tunes on buttons |
| `mech-design/out/06-behemoth-welcome.html`, 0.47 MB | `src/welcome.py`, `make welcome` | `src/welcome.template.html` | no: animated banner, embedded font, type sizes that follow the page width |

## Build
- Template with `{{NAME}}` placeholders, a Python script that fills them, a Make target. `out/` is not in git
- The build prints the size of every embedded part and of the page - the size is checked on every build
- A page that others rebuild gets a how-to file beside the README: what to edit, the command, the checks (`w40k-mechanicum/SERMON.md`)
- Review comments of the lab's HTML viewer are stored in the built file. Fix the template and rebuild; the rebuild removes the comments

## Size
- Seven GIFs of 7 MB each made a 64.4 MB page. It crashed the Star Colonel's browser and headless Chrome in the lab viewer. The same page is 2.0 MB now, and 7.1 MB with four audio files that the Star Colonel ordered
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

## Layout and type sizes
Working example: `mech-design/src/welcome.template.html`.

- Type sizes follow the page width through the root size; every other size is in `rem`: `html { font-size: clamp(11px, 9.44px + 0.4vw, 14px); }` gives 14 px from 1140 px up and 11 px at 390 px. Slope in `vw` = 100 × (max − min) / (wide − narrow); offset = min − slope × narrow / 100
- Large fonts fall faster through an added length: `--extra: clamp(0px, 0.8vw - 3.12px, 6px)` on `html`, then `font-size: calc(1.17rem + var(--extra))` (22.4 px at 1140 px, 12.9 px at 390 px). A root that fell from 14 px to 12 px alone was sent back as too weak
- Labels of 0.8 rem fall below 10 px under 720 px: read them in the screenshot
- Centre large digits on the digits: put the font on the block and add `text-box: trim-both cap alphabetic`. The trim uses the font of the block, not of a child element. Chrome 154 supports it; a browser without it centres by the metrics of the font
- A value in a tile whose rows stack goes beside the rows at half the height of the tile: `grid-area: 1 / 2 / 4 / 3` on the value, `align-content: center` on the tile. In the top right corner it was sent back as too close to the border. Under 480 px there is no room beside the name and the value goes in the first line
- A report about a position belongs to one layout. The lab viewer panel was 720 px wide, below the 980 px breakpoint, and the first correction went to the wide layout. Ask for a screenshot when the report does not name the width
- Headless Chrome here has no Bahnschrift and no Segoe UI and draws both as DejaVu Sans. Say in the report that a position that depends on the font was not checked in the reader's font

## Music
Working example: `w40k-mechanicum/src/sermon.template.html`; how to change the file: `w40k-mechanicum/SERMON.md`.

- Embed the audio file as it is, as a data address on an audio element: `<audio id="music" autoplay src="data:audio/mpeg;base64,...">`. An mp3 of 1.69 MB is 2.26 MB in the page. Without `controls` the element is invisible; `loop` repeats it without end
- A browser blocks sound before the first action of the reader on the page, so `autoplay` alone leaves a fresh page silent. Start it on that action, in a script block of its own: `music.play().catch(() => { ... })`, and in the catch add one handler for `pointerdown` and `keydown` that removes itself from both and calls `music.play()`. With `{ once: true }` on each, the second event starts a track that has ended again
- Lab HTML viewer: after `Trust HTML` the music starts on load. Before it no script runs: an element without `controls` cannot be started there, with `controls` the play control works
- The lab policy allows audio from the lab itself, from `data:` and from `blob:`. The viewer sets the base address to the folder of the page (`/user/<name>/files/<folder>/`), so a file beside the page loads by its relative path. `/files/` sends a file only as a whole: the reader cannot jump inside a long file
- The YouTube player does not work in the lab: the policy in `/galaxalab/etc/jupyter/jupyter_lab_config.py` has no `frame-src`, so every frame from another host is blocked. A page opened as a file gets YouTube error 153 (no referrer). A window opened from the viewer inherits its sandbox and YouTube refuses it. A frame to `/user/<name>/proxy/<port>/` worked, with a web server running on that port
- A tune on a button: keep the mp3 as a base64 string in a script array and make the element on the first press, `new Audio("data:audio/mpeg;base64," + store)`. A tune that is never pressed costs no decoding. Several elements play at once, over the music. Light the button from the `play` and `pause` events (`aria-pressed`); `pause` also fires at the end of the tune
- Make such buttons in the script. A button in the markup does nothing where scripts are switched off
- No mp3 encoder is installed (sox writes Ogg, there is no ffmpeg): an mp3 goes in unchanged
- The built page holds the whole file. Embed music only when its licence allows the copy; a page with a commercial track stays out of the public repository and is not published
- Test: read `paused`, `currentTime`, `ended` and `error` of the element on load, after one click, after `currentTime = duration - 2`, and after a later key press

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
- At 1440 px, 720 px (a lab panel) and 390 px: the expected text is on the page, no console or page errors, `document.documentElement.scrollWidth > innerWidth` is false, `naturalWidth` of the image is the stored width
- Animation: screenshots of the image at several times differ, also after one full loop
- Without scripts: a wrapper page with `<iframe sandbox="allow-same-origin" src="...">` shows the fallback
- In the lab viewer: `http://localhost:8888/user/$JUPYTERHUB_USER/lab/tree/<path from ~/workspace>` with the header `Authorization: token` read from `JUPYTERHUB_API_TOKEN` inside the script and never printed. Listen for the `crash` event, read the page inside the frame, press `Trust HTML`, read again
- Look at the screenshots
- Publishing is the Star Colonel's step. `/galaxalab/var/welcome.html` and the GalaxaHub configuration stay untouched unless asked

<!-- improved 2026-10-02 | body 1793→1887w / 78→80L | benchmark n/a (not run) | via improve-skill -->
