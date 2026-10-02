# w40k-mechanicum - Sermon page v1

Status: DRAFT for internal review, 2026-10-02.

## Contents

- [1. Overview](#1.-Overview)
- [2. Rebuild](#2.-Rebuild)
  - [2.1 Sermons changed](#2.1-Sermons-changed)
  - [2.2 Animations changed](#2.2-Animations-changed)
  - [2.3 Music changed](#2.3-Music-changed)
  - [2.4 Prayer buttons changed](#2.4-Prayer-buttons-changed)
  - [2.5 Size and quality](#2.5-Size-and-quality)
- [3. Check](#3.-Check)
- [4. Publish](#4.-Publish)

## 1. Overview

This document describes how to rebuild the sermon page after the sermons, the animations, the music or the prayer buttons change. The page is `out/15-sermon.html`, one self-contained file of 7.1 MB: a banner animation above the sermon of today's date, one music file that plays once, and three prayer buttons that each play a tune. One command builds it in about 40 s:

```
make sermon
```

The build packs two kinds of stores into the page. The scripts of the page unpack one store of each kind.

| Part | Source | Stored in the page as | Unpacked by the page |
|---|---|---|---|
| Sermons | `calendar/`, 12 month files with 366 entries | 12 stores, one per month: JSON, deflated, base64 | the store of the current month |
| Banners | 7 scene GIFs of `out/`, listed in `src/sermon.py` | 7 stores: animated AVIF, base64 | one store, chosen by the day of the year |
| Music | one mp3 file of `resources/assets/`, named in `src/sermon.py` | the file as it is, base64, on an audio element without controls | - |
| Prayers | 3 mp3 files of `resources/assets/`, listed in `src/sermon.py` | 3 stores: the file as it is, base64 | the store of a button, when the button is pressed |
| Layout | `src/sermon.template.html` | HTML, CSS and four scripts | - |

`out/` is not in git. The page is rebuilt from the sources, never edited by hand.

## 2. Rebuild

This section lists the steps for each kind of change. Every change ends with `make sermon`.

### 2.1 Sermons changed

The page shows the title and the Context of one entry of `calendar/`, the month files `calendar/MM-<month>.md`. It does not show the Purpose line, and it does not read `references/calendar-plan.md`.

- **Edit** - change the title in the heading or the text of the `**Context**` line of the entry
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

The page plays one music file once, without controls. The build puts the file into the page as it is.

- **File** - the constant `MUSIC` in `src/sermon.py` names the file, as a path below the project folder. `resources/` is not in git
- **Change** - put the new file in `resources/assets/`, set `MUSIC`, then `make sermon`
- **Format** - mp3. For another format change the type `audio/mpeg` in `src/sermon.template.html`
- **Size** - the file grows by a third in the page: 1.69 MB of mp3 are 2.26 MB of the page. The workstation has no mp3 encoder, so the build cannot reduce the file
- **Start** - a browser allows sound only after the first action of the reader on the page. The music starts on load where the browser allows it, and on the first click or key press elsewhere
- **Once** - the audio element has no `loop` attribute. Add `loop` in `src/sermon.template.html` to repeat the music without end
- **Again** - a click on the sermon, the red cloth with the title and the text, starts the music from the beginning when it has ended. While the music plays, the click changes nothing
- **Licence** - the built page contains the whole music file. Use a file whose licence allows the copy

### 2.4 Prayer buttons changed

The page shows one thin button per prayer below the sermon. A button plays its tune over the music and over the other tunes.

- **List** - `PRAYERS` in `src/sermon.py` holds one pair per button: the label and the path of the tune below the project folder
- **Change** - edit, add or remove a pair, then `make sermon`. The buttons share one row and wrap on a narrow page
- **Second press** - a press on a button whose tune plays stops the tune. The next press starts it from the beginning
- **State** - a button is lit while its tune plays
- **Size** - the three tunes are 2.10 MB of mp3 and 2.8 MB of the page. The browser decodes a tune only after the first press of its button
- **Scripts** - a script makes the buttons. Where scripts are switched off the page has no buttons
- **Licence** - as for the music: the built page contains the whole files

### 2.5 Size and quality

Three constants in `src/sermon.py` set the size of the banners. The build prints the size of every banner and of the page.

| Constant | Value | Effect |
|---|---|---|
| `WIDTH` | 788 | width of the stored banner in pixels. The page scales the banner to its own width |
| `STEP` | 2 | every second frame of the GIF is kept: 40 frames of 100 ms from 80 frames of 50 ms |
| `QUALITY` | 60 | AVIF quality, 0 to 100. At 50 the choir banner is 0.18 MB, at 60 it is 0.26 MB |

With these values a banner is 0.13 MB to 0.26 MB. The same banner is 1.28 MB as animated WebP and about 7 MB as GIF.

## 3. Check

This section lists the checks after a build.

- **Build output** - the last line reads `wrote .../out/15-sermon.html 7.1 MB, 366 sermons, 7 banners, 3 prayers`
- **Today** - open the page in a browser. It shows the date, the day number, the title and the sermon of today
- **Any date** - add `#MM-DD` to the address, for example `15-sermon.html#02-29`. Reload the page after a change of the address
- **Banner** - the banner moves. It is the same on every load of one day and differs between days, for example `#10-02` and `#10-03`
- **Music** - the music starts after the first click or key press on the page, plays to its end and does not start again by itself. After its end a click on the sermon starts it again; a click on the sermon while it plays does not stop it
- **Prayer buttons** - three buttons stand below the sermon. A press starts the tune and lights the button; a second press stops it; the light goes out at the end of the tune
- **Lab viewer** - in the HTML viewer of the lab press `Trust HTML`. Before that the viewer runs no scripts. After it the sermon shows and the music starts on load

> [!WARNING]
> The page needs scripts. Where scripts are switched off it shows the first banner and the text `The cogitator sleeps`, with no sermon. There the music starts only if the browser allows sound without an action of the reader. The Welcome tab of GalaxaLab runs no scripts.

The page needs a browser that shows animated AVIF and has `DecompressionStream`. It was checked in Chrome 154.

## 4. Publish

The page has no other files. To publish, copy `out/15-sermon.html` over the published copy. The page contains the music file and the prayer tunes: publish it only where their licences allow that.
