# w40k-mechanicum - Sermon package design v1

Status: DRAFT for internal review, 2026-10-05.

## Contents

- [1. Overview](#1.-Overview)
- [2. Design rules](#2.-Design-rules)
- [3. Package layout](#3.-Package-layout)
- [4. Page file](#4.-Page-file)
- [5. Scripts](#5.-Scripts)
- [6. Data files](#6.-Data-files)
  - [6.1 Sermons](#6.1-Sermons)
  - [6.2 Banners](#6.2-Banners)
  - [6.3 Service badges](#6.3-Service-badges)
  - [6.4 Seals](#6.4-Seals)
  - [6.5 Sound](#6.5-Sound)
- [7. Behaviour](#7.-Behaviour)
  - [7.1 Day and sermon](#7.1-Day-and-sermon)
  - [7.2 Prayers and the prayer counter](#7.2-Prayers-and-the-prayer-counter)
  - [7.3 Rewards](#7.3-Rewards)
  - [7.4 Holy download](#7.4-Holy-download)
- [8. Host requirements](#8.-Host-requirements)
- [9. Build](#9.-Build)
- [10. Checks](#10.-Checks)
- [11. Open points](#11.-Open-points)

## 1. Overview

This document describes how the sermon package is designed: its files, the rule that decides what a browser transfers, its scripts, its data formats and what it needs from the host that serves it. `SERMON.md` describes the steps to rebuild the package after a change of its sources.

The package is the page "Sermon of the Day". It shows a banner animation, the sermon of today's date with the service badge of that day, three prayer buttons and a download button, and it plays one piece of music. `make sermon` builds the package in two forms with the same files:

- **Folder** - `out/15-sermon/`, with `index.html` and the folder `resources/`
- **Archive** - `out/15-sermon.zip`, with `index.html` at the root of the archive

The package has 408 files of 9.9 MB together. A visit transfers 10 of them, about 2.1 MB, of which 1.7 MB is the music.

## 2. Design rules

This section lists the six rules that every part of the package follows.

- **One page file without script** - `index.html` holds the markup and the styles. It holds no script, so a host policy that forbids inline scripts does not stop the page
- **Every other part is a file** - scripts, data, images and sound are files in `resources/`. No file is stored inside another file as base64, which adds one third to its size
- **A file is requested when it is needed** - a visit requests the files of one day. A prayer tune is requested when its button is pressed, and a seal when its reward is shown
- **Files are stored compressed** - the hub sends a package file as it is, without compression in transit. So the build gzips the sermons, and images and sound use formats that are compressed already: AVIF and mp3
- **Scripts are independent** - each of the five scripts does one job. An error in one does not stop the others: the sermon shows where the banner fails
- **Nothing moves after the first layout** - the answer strip and the reward lie above the page and take no room in it, and the badge gets its width and height before its image arrives

## 3. Package layout

This section lists the files of the package, their size and when the page requests them.

```
index.html
resources/
    sermon.js  banner.js  music.js  prayers.js  badge.js
    music.mp3
    sermons/   01.json.gz ... 12.json.gz
    banners/   04-forge.avif ... 12-choir.avif
    badges/    01-01.avif ... 12-31.avif
    seals/     4.avif ... 40000.avif
    prayers/   1.mp3  2.mp3  3.mp3
```

| Path | Files | Size | Content | Requested |
|---|---:|---:|---|---|
| `index.html` | 1 | 13 kB | markup, styles, drawn ornaments | on every visit |
| `resources/<name>.js` | 5 | 27 kB | the scripts and their small tables | on every visit |
| `resources/sermons/<mm>.json.gz` | 12 | 45 kB | title and text of the days of one month | the file of the current month |
| `resources/banners/<name>.avif` | 7 | 1.20 MB | scene animations | one file, chosen by the day |
| `resources/badges/<mm-dd>.avif` | 366 | 4.06 MB | service badges | the badge of the day |
| `resources/seals/<number>.avif` | 13 | 0.29 MB | seals of the reward sermons | when a reward is shown |
| `resources/music.mp3` | 1 | 1.69 MB | the music | on every visit |
| `resources/prayers/<n>.mp3` | 3 | 2.55 MB | prayer tunes | when its button is pressed |
| **Total** | **408** | **9.9 MB** | | |

A visit requests `index.html`, the five scripts, one month of sermons, one banner, one badge and the music. Without the music these are 0.2 MB to 0.3 MB.

## 4. Page file

This section describes `index.html`, the only file outside `resources/`. The build makes it from `src/sermon.template.html`.

- **Banner area** - a box with the aspect ratio of the banners, 788 to 249, so the place is kept before the banner arrives. A `noscript` element holds the first banner for a browser that runs no scripts
- **Cloth** - the patch with the sermon: the day line, the title, the invocation, the service badge, the sermon text and the blessing. Seam, corner cogs and bands are drawn with CSS and inline SVG
- **Prayer row** - an empty row. The scripts put the three prayer buttons and the download button into it
- **Answer strip** - a strip at the top edge of the window for the answer of the prayer counter
- **Reward** - a patch in the middle of the window, above the dimmed page, for a reward sermon with its seal
- **Audio element** - the music, without controls
- **Script tags** - five tags that load the scripts in a fixed order

The styles are one `style` block. The cloth textures and the page icon are SVG images written as `data:` addresses inside the page file, so they need no file of their own.

| Page width | Badge | Prayer row |
|---|---|---|
| 1100 px and wider | 112 px high, raised beside the title, so a short sermon does not make the cloth higher | one row |
| 521 px to 1099 px | 112 px high, at the right of the sermon text, which flows around it | one row |
| 520 px and narrower | 92 px high, at the right of the sermon text | two rows |

Where scripts do not run, the page shows the first banner and the text `The cogitator sleeps`, with no sermon, no badge and no buttons.

## 5. Scripts

This section lists the five scripts. They are the script blocks of `src/sermon.template.html`; the build writes each block, named by its `data-name`, to one file.

| File | Size | Job | Table it holds | Files it requests |
|---|---:|---|---|---|
| `sermon.js` | 2.3 kB | finds the day, gets the month of sermons, writes day line, title, invocation, sermon and blessing | 7 invocations, 7 blessings, the month names | `sermons/<mm>.json.gz` |
| `banner.js` | 0.9 kB | chooses one banner with the day of the year as the seed | the 7 banner names | one banner |
| `music.js` | 0.7 kB | starts the music at the first click or key press where the browser blocked it at load | none | none |
| `prayers.js` | 12.9 kB | prayer buttons, tunes, the call to the prayer counter, the answer strip, the reward | the 3 prayers, the 13 reward sermons | a tune, a seal |
| `badge.js` | 9.8 kB | shows the badge of the day, draws the downloaded image, the download buttons | width and height of the 366 badges | the badge of the day |

- **Order** - the page loads the scripts in the order of the table. `sermon.js` defines the values of the day - `month`, `date`, `year` and `number`, the day of the year - and the other scripts read them
- **Same banner for all** - the banner seed is the day of the year, so every reader sees the same banner on the same day
- **Text tables stay in the scripts** - the reward sermons are 7 kB of text and the badge sizes 4 kB. A file of their own would cost one more request on every visit

## 6. Data files

This section describes the format of every kind of data file and the source it is built from.

### 6.1 Sermons

The sermons are one file per month, so a visit transfers one twelfth of them.

- **Content** - a JSON list with one row `[title, context]` per day of the month, in the order of the days, from the entries of `calendar/`
- **Compression** - gzip, level 9. The 12 files are 45 kB together; the same JSON is 104 kB uncompressed
- **Reading** - `sermon.js` fetches `resources/sermons/<mm>.json.gz` and inflates it with `DecompressionStream("gzip")`
- **Same bytes in every build** - the gzip header carries no time, so unchanged sermons give unchanged files

### 6.2 Banners

The banners are the scene animations of the project, reduced for the page.

- **Format** - animated AVIF, 788 px wide, 40 frames of 100 ms: every second frame of the scene GIF, quality 60
- **Size** - 0.13 MB to 0.26 MB each. The same banner is about 7 MB as GIF
- **Source** - the scene GIFs `out/<name>.gif`, listed in `BANNERS` of `src/sermon.py`

### 6.3 Service badges

Every day of the calendar has its own service badge: an embroidered duty patch that shows the subject of the sermon of that day.

- **Format** - AVIF with transparency, 240 px on the longer side, quality 55, about 11 kB each. The page shows a badge 112 px high, so the file has about twice the pixels of the screen
- **Design line** - `badges.md` holds one line per day that says what the badge shows. A line names objects only: no text and no exact count above four, because the image model keeps neither
- **Drawing** - `src/badges.py` gives the line, the outline and the look to the image model Z-Image-Turbo, makes three drafts per day, takes the first draft that shows one whole patch inside the frame, and removes the black ground
- **Sizes** - `badge.js` holds the width and the height of every badge, because the outlines differ

The kind of day, the first word of its title, sets the outline of the patch.

| Kind of day | Days | Outline |
|---|---:|---|
| Feast | 103 | round, with a rim of short rays |
| Rite | 82 | cog wheel with square teeth |
| Observance | 72 | heater shield |
| Vigil | 56 | pointed gothic arch |
| Commemoration, and other days of a saint | 49 | vertical oval with a halo of rays |
| Other | 4 | tall octagon |

### 6.4 Seals

Every reward sermon has its own seal, which is also its badge on the downloaded image.

- **Format** - AVIF with transparency, 360 px on the longer side, quality 70, 22 kB on average
- **Source** - `rewards.md` holds the 13 reward sermons, `src/seals.py` the design of each seal

### 6.5 Sound

The sound files go into the package as they are.

- **Music** - `resources/music.mp3`, 1.69 MB, played once
- **Prayer tunes** - `resources/prayers/1.mp3` to `3.mp3`, 0.46 MB to 1.45 MB. `prayers.js` holds the label and the gain of each: 1.4, 1 and 0.7

## 7. Behaviour

This section describes what the page does with the files.

### 7.1 Day and sermon

The page shows the sermon of today's date by the clock of the reader's browser.

- **Any date** - the address `index.html#02-29` shows the sermon, the badge and the banner of that date
- **Day line** - the date, the day number of the year and that number in binary
- **Invocation and blessing** - one of seven lines each, chosen by the day number
- **Music** - starts at load where the browser allows sound, else at the first click or key press. A click on the sermon starts it again after its end

### 7.2 Prayers and the prayer counter

A press of a prayer button starts its tune and reports the press to the prayer counter; a second press stops the tune.

- **Address** - the host of the page with `prayer-counter` as its first label, path `/api/prayers`
- **Call** - `POST` with `{prayer, action, user, time, day, sermon}`, no cookie, and no header but `Content-Type`. `action` is `start` or `stop`; the counter counts a `start`
- **Reader** - the user name from the lab address `/user/<name>/` of the page or of a page that frames it; without such an address the call carries no name
- **Answer** - `{prayer, count, yours}`. The answer strip shows `Prayer recorded` with the counts for 4.5 s
- **Failed call** - a dark strip with `Prayer not recorded`. The tune plays in both cases

### 7.3 Rewards

When the reader's count of prayers reaches the number of a reward sermon, the page shows that sermon with its seal 1.2 s after the answer strip.

- **Numbers** - 4, 42, 64, 137, 256, 314, 666, 1024, 1729, 6174, 8128, 27182 and 40000
- **Leaving** - the next click or key press outside the download button closes the reward
- **Look at one reward** - the address `index.html#reward-42` shows the reward of 42 without any prayer

### 7.4 Holy download

The download button gives the reader one PNG image to keep: the sermon with its badge.

- **Buttons** - a small button with an arrow at the end of the prayer row, for the sermon of the day, and the same button on a reward, for the reward sermon
- **Image** - 1000 px wide, drawn on a canvas in the colours of the cloth: the badge or the seal, a head line, the title, a line in italics, the sermon and the closing lines
- **Sermon of the day** - the head line is the date with the year and the day number; the closing line is the blessing
- **Reward sermon** - the head line is the rank with the number; the line in italics names the reader and the count; the closing line is the date of the grant
- **File name** - `sermon-<mm-dd>.png` or `reward-<number>.png`
- **Frame without downloads** - where the frame of the page has a sandbox without `allow-downloads`, the image opens in a new tab, and the reader saves it there

## 8. Host requirements

This section lists what the package needs from the host that serves it and from the browser.

- **Archive** - `index.html` at the root, entries for files only, 9.4 MiB unpacked. The welcome page store of GalaxaHub accepts a package up to 16 MiB unpacked
- **Files as they are** - the host sends `sermons/<mm>.json.gz` without a `Content-Encoding` header. With that header the browser inflates the file first, and the inflate of the page then fails
- **Frame** - a frame that shows the page needs `allow-scripts` and `allow-same-origin` in its sandbox, and `allow-downloads` for a download or `allow-popups` for the new tab
- **Browser** - animated AVIF and `DecompressionStream`. Checked in Chrome 154

The content policy of the host must allow the following.

| Directive | Needed value | For |
|---|---|---|
| `script-src` | `'self'` | the five scripts |
| `style-src` | `'self' 'unsafe-inline'` | the `style` block and two `style` attributes |
| `img-src` | `'self' data:` | banner, badge and seals; the page icon and the cloth textures are `data:` addresses |
| `media-src` | `'self'` | the music and the prayer tunes |
| `connect-src` | `'self' https://prayer-counter.<host>` | the month of sermons; the prayer counter |

> [!WARNING]
> The source of the GalaxaHub welcome handler, read on 2026-10-05, sends packages with `script-src 'none'`. Under that policy the page shows only its fallback text.

## 9. Build

This section describes how `make sermon`, which runs `src/sermon.py`, makes the package.

| Source | Step | Output |
|---|---|---|
| `calendar/*.md`, 366 entries | title and Context of every entry, per month, as JSON, gzipped | `resources/sermons/<mm>.json.gz` |
| `out/<name>.gif`, 7 scenes | reduced to 788 px and every second frame, as animated AVIF | `resources/banners/<name>.avif` |
| `resources/assets/badges/<mm-dd>.png`, from `src/badges.py` | as AVIF; the sizes go into the page | `resources/badges/<mm-dd>.avif` |
| `rewards.md` and `resources/assets/seal_<number>.png` | sermons into the page, seals as AVIF | `resources/seals/<number>.avif` |
| mp3 files of `resources/assets/` | copied | `resources/music.mp3`, `resources/prayers/<n>.mp3` |
| `src/sermon.template.html` | placeholders filled; every script block written to a file | `index.html`, `resources/<name>.js` |
| the folder `out/15-sermon/` | all files, sorted, deflated | `out/15-sermon.zip` |

- **Clean start** - the build removes the folder of the build before it, so no file of an old build stays in the package
- **Complete or nothing** - the build stops when a month has a missing day, when `rewards.md` has one number twice, or when a placeholder or an inline script is left in the page
- **Not in git** - `out/` and `resources/` are not in git. The package holds music and prayer tunes: publish it only where their licences allow that

## 10. Checks

This section lists the checks that run after a build. Their scripts are in `wip/sermon/`, which is not in git.

- **Stand-in host** - `mock.py` serves the package folder on port 8793 as the hub does: whole files, no compression, content type by file name. It also answers as the prayer counter, so the real counter is never called
- **Page checks** - `test.py` runs 70 checks in headless Chrome at 1440, 720 and 390 px width: the 10 requested files, the badge, both download buttons, the answer strip, every reward, a frame without downloads and a frame without scripts
- **Lab viewer** - `lab.py` opens `out/15-sermon/index.html` in the HTML viewer of the lab and checks the sermon, the badge and one download
- **Calendar** - `python3 src/liturgy.py` checks the form of the 366 entries

## 11. Open points

This section lists what is not settled.

- **Reader's total** - the page takes `yours` of the prayer counter as the reader's total over all prayers. The counter answers the count of the pressed prayer, measured on 2026-10-05. Until one of them changes, a reward appears when one prayer alone reaches the number. The counter gives the total as `count` of `GET /api/report?user=<name>`
- **Hub policy** - the page needs `script-src 'self'` and the prayer counter in `connect-src` from the hub, as section 8 lists
