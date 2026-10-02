# w40k-mechanicum - Sermon page v1

Status: DRAFT for internal review, 2026-10-02.

## Contents

- [1. Overview](#1.-Overview)
- [2. Rebuild](#2.-Rebuild)
  - [2.1 Sermons changed](#2.1-Sermons-changed)
  - [2.2 Animations changed](#2.2-Animations-changed)
  - [2.3 Size and quality](#2.3-Size-and-quality)
- [3. Check](#3.-Check)
- [4. Publish](#4.-Publish)

## 1. Overview

This document describes how to rebuild the sermon page after the sermons or the animations change. The page is `out/15-sermon.html`, one self-contained file of 2.0 MB: a banner animation above the sermon of today's date. One command builds it in about 40 s:

```
make sermon
```

The build packs two kinds of stores into the page. The scripts of the page unpack one store of each kind.

| Part | Source | Stored in the page as | Unpacked by the page |
|---|---|---|---|
| Sermons | `references/calendar-plan.md`, 366 rows | 12 stores, one per month: JSON, deflated, base64 | the store of the current month |
| Banners | 7 scene GIFs of `out/`, listed in `src/sermon.py` | 7 stores: animated AVIF, base64 | one store, chosen by the day of the year |
| Layout | `src/sermon.template.html` | HTML, CSS and two scripts | - |

`out/` is not in git. The page is rebuilt from the sources, never edited by hand.

## 2. Rebuild

This section lists the steps for each kind of change. Every change ends with `make sermon`.

### 2.1 Sermons changed

The page shows the title and the fact of one row of `references/calendar-plan.md`. It does not read the entries in `calendar/`.

- **Edit** - change the `Title` or the `Fact` cell of the row under its `## <Month>` heading
- **Build** - `make sermon`
- **Row format** - `| <day> | <title> | <fact> |`. A `|` inside the title or the fact breaks the row
- **Completeness** - the build stops with an assertion when a month has a missing day, a day out of order or a wrong number of days
- **Calendar entry** - the entry of the same day in `calendar/` carries the same title. After a title change, change the entry too and run `python3 src/liturgy.py`

The invocation above the sermon and the blessing below it are two lists of seven lines in `src/sermon.template.html`, `INVOCATIONS` and `BLESSINGS`. The day number of the year selects the line.

### 2.2 Animations changed

The build reads the scene GIFs each time, so a new render reaches the page on the next build.

- **Scene rendered again** - `out/<name>.gif` is replaced by the render pipeline (`DESIGN.md`). Run `make sermon`
- **Banner added or removed** - edit the list `BANNERS` in `src/sermon.py`, then `make sermon`. A name is the GIF file name without `.gif`
- **First banner** - the first name of `BANNERS` is the banner shown where scripts are switched off
- **Banner of the day** - the page draws the banner with a generator whose seed is the day number of the year. Every reader sees the same banner on the same day. A change of the number or of the order of `BANNERS` changes the banner of every day
- **Aspect ratio** - every GIF of the list must have the same width and height. The page reserves one box, with the ratio of the first banner

### 2.3 Size and quality

Three constants in `src/sermon.py` set the size of the banners. The build prints the size of every banner and of the page.

| Constant | Value | Effect |
|---|---|---|
| `WIDTH` | 788 | width of the stored banner in pixels. The page scales the banner to its own width |
| `STEP` | 2 | every second frame of the GIF is kept: 40 frames of 100 ms from 80 frames of 50 ms |
| `QUALITY` | 60 | AVIF quality, 0 to 100. At 50 the choir banner is 0.18 MB, at 60 it is 0.27 MB |

With these values a banner is 0.12 MB to 0.27 MB. The same banner is 1.28 MB as animated WebP and about 7 MB as GIF.

## 3. Check

This section lists the checks after a build.

- **Build output** - the last line reads `wrote .../out/15-sermon.html 2.0 MB, 366 sermons, 7 banners`
- **Today** - open the page in a browser. It shows the date, the day number, the title and the sermon of today
- **Any date** - add `#MM-DD` to the address, for example `15-sermon.html#02-29`. Reload the page after a change of the address
- **Banner** - the banner moves. It is the same on every load of one day and differs between days, for example `#10-02` and `#10-03`
- **Lab viewer** - in the HTML viewer of the lab press `Trust HTML`. Before that the viewer runs no scripts

> [!WARNING]
> The page needs scripts. Where scripts are switched off it shows the first banner and the text `The cogitator sleeps`, with no sermon. The Welcome tab of GalaxaLab runs no scripts.

The page needs a browser that shows animated AVIF and has `DecompressionStream`. It was checked in Chrome 154.

## 4. Publish

The page has no other files. To publish, copy `out/15-sermon.html` over the published copy.
