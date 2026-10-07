# w40k-mechanicum - Sermon page v2

Status: DRAFT for internal review, 2026-10-07.

## Contents

- [1. Overview](#1.-Overview)
- [2. Rebuild](#2.-Rebuild)
  - [2.1 Sermons changed](#2.1-Sermons-changed)
  - [2.2 Animations changed](#2.2-Animations-changed)
  - [2.3 Music changed](#2.3-Music-changed)
  - [2.4 Prayer buttons changed](#2.4-Prayer-buttons-changed)
  - [2.5 Prayer counter](#2.5-Prayer-counter)
  - [2.6 Reward sermons changed](#2.6-Reward-sermons-changed)
  - [2.7 Service badges changed](#2.7-Service-badges-changed)
  - [2.8 Size and quality](#2.8-Size-and-quality)
  - [2.9 Radio buttons changed](#2.9-Radio-buttons-changed)
- [3. Check](#3.-Check)
- [4. Publish](#4.-Publish)

## 1. Overview

This document describes how to rebuild the sermon page after the sermons, the animations, the music, the prayer buttons, the radio buttons, the reward sermons or the service badges change. The page is a package: the folder `out/w40k-mechanicum-sermons/` with `index.html` and a `resources` folder, and the same files as `out/w40k-mechanicum-sermons.zip`, 9.9 MB together. It shows a banner animation above the sermon of today's date with the service badge of the day, plays one music file once, and has three prayer buttons that each play a tune, four radio buttons that each play the sound of a YouTube video, and one download button. `design-sermons-html.md` describes the design of the package. One command builds it in about 40 s:

```
make sermon
```

The build writes every part as files into `resources/`. The page requests a file only when it needs it.

| Part | Source | Files in the package | Requested by the page |
|---|---|---|---|
| Sermons | `calendar/`, 12 month files with 366 entries | `resources/sermons/<mm>.json.gz`, 12 files: JSON, gzipped | the file of the current month |
| Banners | 7 scene GIFs of `out/`, listed in `src/sermon.py` | `resources/banners/<name>.avif`, 7 animated AVIF files | one file, chosen by the day of the year |
| Music | one mp3 file of `resources/assets/`, named in `src/sermon.py` | `resources/music.mp3`, the file as it is | on every visit |
| Prayers | 3 mp3 files of `resources/assets/`, listed in `src/sermon.py` | `resources/prayers/<n>.mp3`, the files as they are | the tune of a button, when the button is pressed |
| Rewards | `rewards.md`, 13 entries, and 13 seals of `resources/assets/` | the sermons in `resources/prayers.js`; `resources/seals/<number>.avif`, 0.29 MB together | a seal, when its reward is shown |
| Service badges | `badges.md`, 366 lines, and 366 badges of `resources/assets/badges/` | `resources/badges/<mm-dd>.avif`, 4.06 MB together | the badge of the day |
| Radios | `RADIOS` in `src/sermon.template.html`, 4 rows | none: `resources/radio.js` holds the names of the videos | nothing of the package: the player and its sound come from YouTube when a radio button is pressed |
| Layout | `src/sermon.template.html` | `index.html` and six scripts `resources/<name>.js` | on every visit |

`out/` is not in git. The package is rebuilt from the sources, never edited by hand.

## 2. Rebuild

This section lists the steps for each kind of change. Every change ends with `make sermon`.

### 2.1 Sermons changed

The page shows the title and the Context of one entry of `calendar/`, the month files `calendar/MM-<month>.md`. It does not show the Purpose line, and it does not read `references/calendar-plan.md`.

- **Edit** - change the title in the heading or the text of the `**Context**` line of the entry. The rules are in `references/calendar-brief.md`; its section 5 demands that every statement of an entry follows from the one before it
- **Check** - `python3 src/liturgy.py`. It must end with 0 faults; it also writes `out/14-calendar.md`
- **Build** - `make sermon`
- **Entry format** - `## <Month> <day> - <title>`, an empty line, `**Purpose** - <text>`, an empty line, `**Context** - <text>`. The build takes only entries of this form
- **Completeness** - the build stops with an assertion when a month has a missing day, a day out of order or a wrong number of days

The invocation above the sermon and the blessing below it are two lists of seven lines in `src/sermon.template.html`, `INVOCATIONS` and `BLESSINGS`. The day number of the year selects the line.

### 2.2 Animations changed

The build reads the scene GIFs each time, so a new render reaches the page on the next build.

- **Scene rendered again** - `out/<name>.gif` is replaced by the render pipeline (`DESIGN.md`). Run `make sermon`
- **Banner added or removed** - edit the list `BANNERS` in `src/sermon.py`, then `make sermon`. A name is the GIF file name without `.gif`
- **First banner** - the first name of `BANNERS` is the banner shown where scripts are switched off
- **Banner of the day** - the page draws the banner with a generator whose seed is the day number of the year. Every reader sees the same banner on the same day. A change of the number or of the order of `BANNERS` changes the banner of every day
- **Aspect ratio** - every GIF of the list must have the same width and height. The page reserves one box, with the ratio of the first banner

### 2.3 Music changed

The page plays one music file once, without controls. The build copies the file into the package as it is.

- **File** - the constant `MUSIC` in `src/sermon.py` names the file, as a path below the project folder. `resources/` is not in git
- **Change** - put the new file in `resources/assets/`, set `MUSIC`, then `make sermon`
- **Format** - mp3. For another format change the file name `resources/music.mp3` in `src/sermon.py` and in `src/sermon.template.html`
- **Size** - 1.69 MB. The workstation has no mp3 encoder, so the build cannot reduce the file
- **Start** - a browser allows sound only after the first action of the reader on the page. The music starts on load where the browser allows it, and on the first click or key press elsewhere
- **Once** - the audio element has no `loop` attribute. Add `loop` in `src/sermon.template.html` to repeat the music without end
- **Stop and play** - a click on the banner animation stops the music while it plays. The next click on the banner plays it on from the place where it stopped. While a radio plays, the click stops the radio and the music plays on
- **Again** - a click on the sermon, the red cloth with the title and the text, starts the music from the beginning when it has ended, and plays it on after a click on the banner or a radio has stopped it. While the music or a radio plays, a click on the sermon changes nothing
- **Licence** - the package contains the whole music file. Use a file whose licence allows the copy

### 2.4 Prayer buttons changed

The page shows one thin button per prayer below the sermon. A button plays its tune over the music, over a radio and over the other tunes.

- **List** - `PRAYERS` in `src/sermon.py` holds one row per button: the label, the path of the tune below the project folder and the gain
- **Change** - edit, add or remove a row, then `make sermon`. The buttons share one row and wrap on a narrow page
- **Second press** - a press on a button whose tune plays stops the tune. The next press starts it from the beginning
- **State** - a button is lit while its tune plays
- **Gain** - the loudness of a tune as a factor: 1 plays the file as it is, 1.4 is 3 dB louder, 0.7 is 3 dB quieter. The chant has 1.4 and the third tune 0.7. The peak of the chant is 3.4 dB below full scale, so a gain above 1.48 clips it. Measure the peak of a file before a gain above 1
- **Size** - the three tunes are 2.55 MB. The browser requests a tune only at the first press of its button
- **Scripts** - a script makes the buttons. Where scripts are switched off the page has no buttons
- **Licence** - as for the music: the package contains the whole files

### 2.5 Prayer counter

The page reports every press of a prayer button to the prayer counter, a service on a host of its own. The browser console shows each call and its answer.

- **Host** - the host of the page with `prayer-counter` as its first label: a page on `workbench.lab.example.org` calls `prayer-counter.lab.example.org`, with the protocol and the port of the page. The script takes the host from the base address of the page, because in the lab HTML viewer the page address is a blob without a host
- **Call** - `POST /api/prayers` with the header `Content-Type: application/json`, no cookie and no other header
- **Body** - JSON with `prayer` (the label of the button), `action` (`start` or `stop`), `user`, `time` (UTC), `day` (`MM-DD`) and `sermon` (the title the page shows). The service counts only `start`
- **User** - the page reads the name from the lab address `/user/<name>/` of the page itself or of a page that frames it. Opened from another address, `user` is `null`. The service has no other knowledge of the reader, so anybody can send any name
- **Answer** - `200` with `{"prayer", "count", "yours"}`: `count` is the number of presses of this prayer by all readers, `yours` the number of presses by this reader, which the page reads as the reader's total over all prayers. On 2026-10-05 the counter answered the count of the pressed prayer only (`design-sermons-html.md`, section 11); `400` for an invalid field, `413` for a body over 4096 bytes
- **No waiting** - the tune starts or stops at once. The page does not wait for the answer
- **Answer strip** - after the answer to a `start` the page shows a strip at the top edge of the window, as wide as the window: the headline `Prayer recorded` and the line `This prayer: 42 by the congregation · Your prayers: 3`, with `count` and `yours` of the answer. The strip is bright crimson with a gold edge and a gold glow. It slides in, stays and slides out in 4.5 s
- **Failed call** - when the call fails or the answer is not `200`, the strip is dark, without the glow, and reads `Prayer not recorded` and `The noosphere did not answer.`
- **Room** - the strip lies over the page and takes no room, so nothing moves when it appears
- **With a reward** - at a holy number the strip comes first and the reward follows 1.2 s later. The strip lies above the dimmed page of the reward, so both are readable
- **Console** - one line per press, `[prayer counter] <user> pressed "<prayer>" (<action>): POST ...`, then `[prayer counter] counted: ...` or `[prayer counter] not counted: <reason>`
- **Policy** - the call goes to another host, so the server that sends the page must allow it in its Content-Security-Policy (`connect-src`). The lab allows only its own host: in the lab HTML viewer the browser blocks the call and the console reads `not counted: Failed to fetch`
- **Not used by the page** - `GET /api/prayers` answers the counts per prayer, `GET /api/report` answers the counts by sermon, prayer, user and date as JSON, with the filter `?user=<name>`, and `POST /api/reset` deletes the counts
- **Report** - `python3 src/counter.py` reads `GET /api/report` and prints the totals, the prayers of every reader and the prayers of every day as Markdown tables. The command `/prayer-counter` runs it

### 2.6 Reward sermons changed

The page rewards a reader whose total of prayers reaches a holy number: it shows the seal of that number and a sermon for this reader. The sermons are the entries of `rewards.md`, and every entry has a seal of its own design.

- **When** - the answer of the prayer counter to a `start` has `yours` equal to the number of an entry. `yours` is the reader's total over all prayers, so a reader receives each reward once
- **What** - a patch in the middle of the window, above the page, which is dimmed while the patch shows: the seal, the rank with the number and its binary form, the title, the line `For <user>, who has said <n> prayers.` and the sermon. It takes no room in the page, so nothing moves
- **Closing** - the patch fades in and stays. The next click or key press of the reader outside the download button fades it out
- **Download** - the small button with the arrow on the patch gives the reward sermon with its seal as one PNG image (2.7)
- **Edit** - change, add or remove an entry of `rewards.md`, then `make sermon`
- **Logic** - a reward sermon is one chain: what the number is, what the number teaches, what the forge grants, and a blessing that uses the lesson. A fact that the lesson does not use is removed
- **Entry format** - `## <number> - <title>`, an empty line, `**Rank** - <rank>`, an empty line, `**Sermon** - <text>`. The build takes only entries of this form and stops when a number occurs twice
- **Seal** - `resources/assets/seal_<number>.png`, an image with a transparent ground. The build writes it to `resources/seals/<number>.avif` and stops when the file of an entry is missing
- **New seal** - `src/seals.py` designs the seals with the image model Z-Image-Turbo. Add the design of the new number to `SEALS`, run `gen`, then `sheet`, look at the six drafts in `wip/seals/sheet_<number>.png`, put the seed of the best draft into `CHOICES` and run `apply`. The head of the script has the commands
- **Look** - add `#reward-<number>` to the address of the page, for example `index.html#reward-42`. The page then shows that reward on load

| Number | Rank | Title | The number | Seal |
|---:|---|---|---|---|
| 4 | Supplicant | Sermon of the Pareto Rule | 80 divided by 20, the Pareto rule | red wax purity seal with a cog, brass studs and parchment strips |
| 42 | Initiate | Sermon of the Alternating Word | 101010 in binary | bronze cog medallion with a skull, half bone and half machine |
| 64 | Acolyte | Sermon of the Whole Word | 2 to the power 6, one machine word | plane of core memory in a brass ring, on a chain |
| 137 | Lexmechanic | Sermon of the Constant | the inverse of the fine-structure constant | gold medallion with a crystal lens and rays |
| 256 | Enginseer | Sermon of the Full Byte | 2 to the power 8, the values of one byte | cog with a crossed axe and wrench, a skull and two mechadendrites |
| 314 | Tech-Priest | Sermon of the Circle | the first three digits of pi | golden armillary sphere around a red Mars |
| 666 | Logis | Sermon of the Wheel of Chance | the sum of 1 to 36, the numbers on a roulette wheel | wheel of chance in a cog rim, its gold ball on a chain |
| 1024 | Magos | Sermon of the Kibi | 2 to the power 10, one kibi | gold order star with the cog, the skull and a laurel wreath |
| 1729 | Archmagos | Sermon of the Two Ways | the smallest sum of two cubes in two ways | jewelled cube of gold and steel, in two halves |
| 6174 | Archmagos Dominus | Sermon of the Fixed Point | Kaprekar's constant | cog with a gold spiral that ends in one red gem, over crossed spears |
| 8128 | Archmagos Veneratus | Sermon of the Perfect Number | the fourth perfect number | gold medal with one diamond and six skulls at equal distances |
| 27182 | Fabricator Locum | Sermon of the Natural Base | the first five digits of e | golden nautilus spiral around the skull, under a red Mars |
| 40000 | Fabricator-General | Sermon of the Forty Millennia | one prayer for every year of forty millennia | winged cog with a crowned skull over a red Mars, with hanging wax seals |

### 2.7 Service badges changed

Every day has a service badge: an embroidered duty patch at the right of the sermon text. The image model draws each badge from one design line, and the download button puts the badge on the image the reader keeps.

- **Design line** - `badges.md` holds one line per day, `- **MM-DD** - <what the badge shows>`. A line names objects only: no text and no exact count above four, because the image model keeps neither
- **Outline** - the kind of day, the first word of its title, sets the outline of the patch: `FORMS` in `src/badges.py`. `design-sermons-html.md`, section 6.3, lists the six outlines
- **Drafts** - `src/badges.py gen [day ...]` draws three drafts of each named day, or of every day, into `wip/badges/`. A draft that exists is kept: delete the drafts of a day to draw it again after a change of its line. The head of the script has the command with the GPU
- **Choice** - the badge of a day is its first draft that shows one whole patch inside the frame. `picks` writes one sheet per month with the chosen draft of every day and frames in red a day without such a draft. `sheet <month>` shows all drafts of a month. Put the seed of a better draft into `CHOICES`
- **Apply** - `apply` removes the black ground and writes `resources/assets/badges/<mm-dd>.png`, 240 px on the longer side. Then `make sermon`. The build stops when the badge of a day is missing
- **Download button** - the small button with the arrow at the end of the prayer row gives the sermon of the day as one PNG image, 1000 px wide: the badge, the date with the year and the day number, the title, the invocation, the sermon and the blessing. The file name is `sermon-<mm-dd>.png`. The same button on a reward gives `reward-<number>.png`
- **Frame without downloads** - in a frame whose sandbox has no `allow-downloads` the image opens in a new tab, and the reader saves it there. The tab opens empty at the click and gets the image a moment later, because Safari lets a page open a tab only while it handles the click

### 2.8 Size and quality

Constants in `src/sermon.py` set the size of the images. The build prints the size of every banner and of every folder of the package.

| Constant | Value | Effect |
|---|---|---|
| `WIDTH` | 788 | width of the stored banner in pixels. The page scales the banner to its own width |
| `STEP` | 2 | every second frame of the GIF is kept: 40 frames of 100 ms from 80 frames of 50 ms |
| `QUALITY` | 60 | AVIF quality of the banners, 0 to 100. At 50 the choir banner is 0.18 MB, at 60 it is 0.26 MB |
| `SEAL_QUALITY` | 70 | AVIF quality of the seals: 22 kB per seal on average |
| `BADGE_QUALITY` | 55 | AVIF quality of the service badges: about 11 kB per badge |

With these values a banner is 0.13 MB to 0.26 MB. The same banner is 1.28 MB as animated WebP and about 7 MB as GIF.

### 2.9 Radio buttons changed

The page shows one thin button per radio in a row below the prayer buttons. A radio is the sound of a YouTube video: the package holds no file of it.

| Button | Video | Earliest start | Title on YouTube | Channel | Length |
|---|---|---:|---|---|---:|
| Holy Mars Radio | [`VMs_p5EWri4`](https://www.youtube.com/watch?v=VMs_p5EWri4) | 34 s | Holy Mars, ambient choir and organ music | Domains of Ambience | 10825 s |
| Holy Terra Radio | [`k5xDyG72wHE`](https://www.youtube.com/watch?v=k5xDyG72wHE) | 0 s | Holy Terra, choir and piano music | Domains of Ambience | 10839 s |
| Forge Radio | [`M3D9TYNRXwY`](https://www.youtube.com/watch?v=M3D9TYNRXwY) | 0 s | The Binaric Shroudpsalm - Adeptus Mechanicus, 22 tracks | OmniVox40k | 4633 s |
| Cogitator Radio | [`M3D9TYNRXwY`](https://www.youtube.com/watch?v=M3D9TYNRXwY&t=319s) | 319 s | the same video as Forge Radio | OmniVox40k | 4633 s |

- **List** - `RADIOS` in the script block `radio` of `src/sermon.template.html` holds one row per button: the label, the name of the video, the earliest second of a start and the length of the video in seconds. The name is the part after `v=` in the address of the video
- **Start** - at every press the radio starts at a second drawn at random between its earliest start and the end of its video
- **Repeat** - at the end of its video the same radio starts again, from second 0, and its button stays lit
- **Change** - edit, add or remove a row, then `make sermon`
- **Source** - the music stays on YouTube, and the table links the video of each radio. `resources/assets/music/` holds mp3 copies of such videos, 293 MiB together. They are not in git, which ignores `resources/` and every sound file, and the package does not use them
- **Press** - a press starts the radio and lights the button, and the music of the page stops. A press of another radio button replaces the first radio. A second press of the lit button stops the radio. A click on the banner stops it too, and the music of the page then plays on
- **After a second press** - the music of the page stays silent. A click on the banner or on the sermon plays it on
- **Same video twice** - Forge Radio and Cogitator Radio play one video. They differ only in the earliest start, second 0 and second 319
- **Player** - the player of YouTube, in a frame that the reader does not see. `design-sermons-html.md`, section 7.5, describes it
- **Host** - the host that sends the page must allow the frame in its Content-Security-Policy: `frame-src https://www.youtube-nocookie.com`. Where it does not, as in the lab HTML viewer, the button goes out at once and the music plays on
- **Lab viewer** - no radio plays in the HTML viewer of the lab, with any policy: the viewer shows the page from a `blob:` address, which sends no referrer, and YouTube refuses such a player. The radios need the page at an `http` or `https` address, as on the hub
- **New video** - the owner of a video can forbid its use in a player on another page. Such a video leaves the button lit without sound. `wip/sermon/radio.py` checks that every radio plays and that the length in its row is the length of the video; add the new row to its list `RADIOS`
- **Terms** - the rules of YouTube for embedded players ask for a visible player of at least 200 px width and height, and YouTube can play advertisements in the player

## 3. Check

This section lists the checks after a build.

- **Build output** - the last line reads `wrote .../out/w40k-mechanicum-sermons and w40k-mechanicum-sermons.zip: 409 files, 9.9 MB, zip 9.8 MB, 366 sermons, 7 banners, 3 prayers, 13 rewards, 366 badges`
- **Scripted checks** - `wip/sermon/test.py` runs 78 checks in headless Chrome against `wip/sermon/mock.py`, which serves the package and answers as the prayer counter. `wip/sermon/radio.py` runs 35 checks of the radio buttons against the same stand-in; it needs the network, because the radios play from YouTube. The head of each script has its commands. `wip/` is not in git
- **Today** - open `out/w40k-mechanicum-sermons/index.html` in the HTML viewer of the lab or through a web server. It shows the date, the day number, the title, the sermon and the badge of today. Opened as a local file, the browser blocks the request for the sermons
- **Any date** - add `#MM-DD` to the address, for example `index.html#02-29`. Reload the page after a change of the address
- **Banner** - the banner moves. It is the same on every load of one day and differs between days, for example `#10-02` and `#10-03`
- **Badge** - the badge of the day stands at the right of the sermon text, and nothing moves when it arrives
- **Music** - the music starts after the first click or key press on the page, plays to its end and does not start again by itself. After its end a click on the sermon starts it again; a click on the sermon while it plays does not stop it. A click on the banner stops it, and the next click on the banner plays it on
- **Prayer counter** - open the browser console and press a prayer button. Two lines that start with `[prayer counter]` appear; the second reads `counted` with the count where the page may reach the service, and `not counted` with the reason elsewhere
- **Answer strip** - after a press that starts a tune, a strip slides in at the top edge of the window and slides out after 4.5 s. Nothing on the page moves when it appears
- **Reward** - open the page with `#reward-42` at the end of the address. The patch with the seal and the sermon fades in; a click or a key press fades it out
- **Prayer buttons** - three buttons stand below the sermon, and the small download button at the end of their row. A press starts the tune and lights the button; a second press stops it; the light goes out at the end of the tune
- **Radio buttons** - four buttons stand in a row below the prayer buttons. A press lights the button, stops the music and starts the sound of the radio within a few seconds; a second press stops the radio, and a click on the banner stops the radio and plays the music
- **Download** - a press of the download button saves `sermon-<mm-dd>.png`. On a reward it saves `reward-<number>.png`, and the reward stays open
- **Lab viewer** - in the HTML viewer of the lab press `Trust HTML`. Before that the viewer runs no scripts. After it the sermon shows and the music starts on load. A press of a prayer button shows the failed-call strip there, because the lab blocks the call. A press of a radio button lights nothing there, because the lab blocks the player of YouTube

> [!WARNING]
> The page needs scripts. Where scripts are switched off it shows the first banner and the text `The cogitator sleeps`, with no sermon, no badge and no buttons. There the music starts only if the browser allows sound without an action of the reader. The Welcome tab of GalaxaLab runs no scripts.

The page needs a browser that shows animated AVIF and has `DecompressionStream`. It was checked in Chrome 154.

## 4. Publish

The package is complete in both forms. To publish, upload `out/w40k-mechanicum-sermons.zip` where a package is accepted, or copy the folder `out/w40k-mechanicum-sermons/` with its `resources` folder over the published copy. JupyterLab can add `.ipynb_checkpoints` folders to the folder; the zip holds only the files of the build. `design-sermons-html.md`, section 8, lists what the host must allow. The package contains the music file and the prayer tunes: publish it only where their licences allow that.
