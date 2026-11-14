"""Checks the answer strip, the rewards, the service badge, the download buttons and the row of radio buttons of the sermon page in headless Chrome against
src/sermon/mock.py, and takes screenshots into wip/sermon/. No radio button is pressed here: src/sermon/radio.py checks the radios, which play from YouTube.
Start the stand-in first, with a fresh process for every run:

    (setsid python3 src/sermon/mock.py out/w40k-mechanicum-sermons >/dev/null 2>&1 &)
    python3 src/sermon/test.py
    pkill -f 'sermon/mock\\.py'          # in a command of its own
"""
import datetime, pathlib, re
from PIL import Image
from playwright.sync_api import sync_playwright
OUT = pathlib.Path(__file__).parent.parent.parent / "wip" / "sermon"
PAGE = "http://workbench.example.test:8793/user/konrad.jelen/index.html"
REWARDS = [int(n) for n in re.findall(r"^## (\d+) - ", (OUT.parent.parent / "rewards.md").read_text(), flags=re.M)]
METRICS = """() => { const box = s => { const b = document.querySelector(s).getBoundingClientRect(); return [Math.round(b.top + scrollY), Math.round(b.height)]; };
  return { doc: [document.documentElement.scrollWidth, document.documentElement.scrollHeight], inner: innerWidth,
           cloth: box(".cloth"), prayers: box(".prayers"), radios: box(".radios"), main: box("main") }; }"""
RADIOS = """() => { const row = s => [...document.querySelectorAll(s + " button:not(.keep)")].map(b => b.getBoundingClientRect());
  const prayers = row(".prayers"), radios = row(".radios");
  return { labels: [...document.querySelectorAll(".radios button")].map(b => b.textContent), lit: document.querySelectorAll('.radios [aria-pressed="true"]').length,
           below: Math.min(...radios.map(b => b.top)) - Math.max(...prayers.map(b => b.bottom)), inside: radios.every(b => b.left >= 0 && b.right <= innerWidth),
           heights: [...new Set([...prayers, ...radios].map(b => Math.round(b.height)))], rows: new Set(radios.map(b => Math.round(b.top))).size,
           frames: document.querySelectorAll("iframe").length }; }"""
STATE = """() => { const heard = document.getElementById("heard"), seal = document.getElementById("reward");
  return { title: heard.querySelector("strong").textContent, line: heard.querySelector("span").textContent, failed: heard.classList.contains("failed"),
           heardOpacity: +getComputedStyle(heard).opacity, shown: seal.classList.contains("shown"), sealOpacity: +getComputedStyle(seal).opacity,
           sealVisibility: getComputedStyle(seal).visibility, rank: seal.querySelector(".rank").textContent, sermon: seal.querySelector("h2").textContent,
           whom: seal.querySelector(".for").textContent, lesson: seal.querySelector(".lesson").textContent, image: seal.querySelector("img").naturalWidth }; }"""
STRIP = """() => { const b = document.getElementById("heard").getBoundingClientRect();
  return { left: b.left, right: b.right, top: b.top, height: Math.round(b.height), w: innerWidth, cogs: [...document.querySelectorAll("#heard svg")].filter(x => x.getBoundingClientRect().width > 0).length }; }"""
BADGE = """() => { const b = document.getElementById("badge"), box = b.getBoundingClientRect(), cloth = document.querySelector(".cloth").getBoundingClientRect(),
  text = document.getElementById("sermon").getBoundingClientRect();
  return { hidden: b.hidden, natural: [b.naturalWidth, b.naturalHeight], height: Math.round(box.height), width: Math.round(box.width),
           inside: box.left > cloth.left && box.right < cloth.right && box.top > cloth.top && box.bottom < cloth.bottom, right: box.left > text.left + text.width / 2 }; }"""
TODAY = datetime.date.today().strftime("%m-%d")
MUSIC = '''document.getElementById("music").paused'''

def keepsake(download, name):
    """Saves a downloaded keepsake and returns whether it has the file name and the size of one."""
    path = OUT / ("keepsake-" + name)
    download.save_as(path)
    image = Image.open(path)
    return download.suggested_filename == name and image.format == "PNG" and image.width == 1000 and 600 < image.height < 1500, (download.suggested_filename, image.size)

faults = []
def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name, "" if ok else detail)
    if not ok: faults.append(name)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True, args=["--no-sandbox", "--disable-dev-shm-usage",
        "--host-resolver-rules=MAP *.example.test 127.0.0.1", "--autoplay-policy=no-user-gesture-required"])
    for width, height in ((1440, 900), (720, 900), (390, 844)):
        page = browser.new_page(viewport={"width": width, "height": height})
        errors, asked = [], []
        page.on("request", lambda r: asked.append(r.url.split("/user/konrad.jelen/")[-1]) if "/user/konrad.jelen/" in r.url else None)
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        page.goto(PAGE, wait_until="load")
        page.wait_for_function("document.getElementById('title').textContent !== 'The cogitator sleeps' && document.querySelectorAll('.prayers button').length === 4 && document.querySelectorAll('.radios button').length === 4")
        page.wait_for_timeout(800)
        before = page.evaluate(METRICS)
        loaded = sorted(re.sub(r"banners/[\w-]+", "banners/*", name) for name in asked)
        check(f"{width}: the page asks for the files of the day only", loaded == sorted(["index.html", "resources/music.mp3", "resources/banners/*.avif",
              f"resources/badges/{TODAY}.avif", f"resources/sermons/{TODAY[:2]}.json.gz"] + [f"resources/{n}.js" for n in ("badge", "banner", "music", "prayers", "radio", "sermon")]), loaded)
        radios = page.evaluate(RADIOS)
        check(f"{width}: four radio buttons in a row of their own below the prayer row, none lit, no player", radios["labels"] == ["Holy Mars Radio", "Holy Terra Radio", "Forge Radio", "Cogitator Radio"]
              and radios["lit"] == 0 and radios["frames"] == 0 and radios["below"] == 8 and radios["inside"] and len(radios["heights"]) == 1
              and radios["rows"] == (2 if width <= 520 else 1), radios)
        badge = page.evaluate(BADGE)
        check(f"{width}: badge of the day shown beside the sermon text", not badge["hidden"] and max(badge["natural"]) == 240 and badge["inside"] and badge["right"]
              and badge["height"] == (72 if width <= 520 else 88), badge)
        with page.expect_download() as got:
            page.get_by_role("button", name="Holy Download").click()
        ok, detail = keepsake(got.value, f"sermon-{TODAY}.png")
        check(f"{width}: the download button gives the sermon as an image", ok, detail)
        check(f"{width}: nothing moved by the download", before == page.evaluate(METRICS))
        check(f"{width}: no horizontal overflow", before["doc"][0] <= before["inner"], before)
        if width == 1440:                                                  # the Tab key gives a button the focus: no frame of the browser
            page.keyboard.press("Tab"); page.wait_for_timeout(300)
            focus = page.evaluate("""() => { const b = document.activeElement, s = getComputedStyle(b);
                return { label: b.textContent, shown: b.matches(":focus-visible"), outline: s.outlineStyle, border: s.borderTopColor }; }""")
            # the focus was on the download button, which the checks above pressed: the Tab key moves it to the first radio button
            check("focus by the Tab key: no frame of the browser, the gold border of the hover state", focus == {"label": "Holy Mars Radio", "shown": True,
                  "outline": "none", "border": "rgb(194, 146, 58)"}, focus)
            page.locator("main").screenshot(path=str(OUT / "focus-tab.png"))
            page.evaluate("document.activeElement.blur()")
        if width == 1440:                                                  # the banner stops the music and plays it on
            states = [page.evaluate(MUSIC)]
            for _ in range(2):
                page.locator(".banner").click(); page.wait_for_timeout(400)
                states.append(page.evaluate(MUSIC))
            check("banner: one click stops the music, the next click plays it on", states == [False, True, False], states)
            check("banner: nothing moved", before == page.evaluate(METRICS))
        name = "Chant to Omnissiah"
        page.get_by_role("button", name=name).click(); page.wait_for_timeout(1000)
        state, after, strip = page.evaluate(STATE), page.evaluate(METRICS), page.evaluate(STRIP)
        check(f"{width}: strip texts", state["title"] == "Prayer recorded" and bool(re.fullmatch(r"This prayer: \d+ by the congregation · Your prayers: \d+", state["line"])), state)
        check(f"{width}: strip visible", state["heardOpacity"] > .95 and not state["failed"], state["heardOpacity"])
        check(f"{width}: nothing moved", before == after, (before, after))
        check(f"{width}: strip at the top edge, as wide as the window", abs(strip["top"]) < 1 and strip["left"] == 0 and strip["right"] == strip["w"]
              and strip["cogs"] == (1 if width <= 520 else 2), strip)
        page.screenshot(path=str(OUT / f"answer-{width}.png"))
        if width == 1440:
            chant = page.get_by_role("button", name=name)
            page.wait_for_timeout(1000)                                    # a reward would start 1.2 s after the answer
            state = page.evaluate(STATE)
            check("total 3: the strip shows the reader's total over all prayers, not the 2 of this prayer", state["line"].endswith("· Your prayers: 3"), state["line"])
            check("total 3: no reward", not state["shown"] and state["sealVisibility"] == "hidden", state)
            chant.click(); page.wait_for_timeout(400)                      # stop
            chant.click(); page.wait_for_timeout(700)                      # start: total 4
            state = page.evaluate(STATE)
            check("total 4: the strip comes first, the reward later", state["heardOpacity"] > .95 and not state["shown"], state)
            page.wait_for_timeout(2300)
            state = page.evaluate(STATE)
            check("total 4: the strip stays while the reward shows", state["heardOpacity"] > .95, state["heardOpacity"])
            page.screenshot(path=str(OUT / "answer-with-reward.png"))
            check("total 4: reward shown", state["shown"] and state["sealOpacity"] > .95 and state["sealVisibility"] == "visible", state)
            check("total 4: reward texts", state["image"] > 200 and state["rank"] == "Seal of the Supplicant · 4 · 100" and state["sermon"] == "Sermon of the Pareto Rule"
                  and state["whom"] == "For konrad.jelen, who has said 4 prayers." and state["lesson"].startswith("Hear this, Supplicant."), state)
            check("total 4: nothing moved", before == page.evaluate(METRICS))
            with page.expect_download() as got:
                page.locator("#reward .keep").click()
            ok, detail = keepsake(got.value, "reward-4.png")
            check("total 4: the download button on the reward gives the reward sermon as an image", ok, detail)
            page.wait_for_timeout(600)
            check("total 4: the reward stays open after the download", page.evaluate(STATE)["shown"])
            page.mouse.click(700, 30); page.wait_for_timeout(1600)        # a click anywhere closes the reward
            state = page.evaluate(STATE)
            check("click: reward closed", not state["shown"] and state["sealOpacity"] < .05 and state["sealVisibility"] == "hidden", state)
            check("click: the click on the banner that closed the reward did not stop the music", page.evaluate(MUSIC) is False)
            page.get_by_role("button", name="Prayer to Omnissiah").click(); page.wait_for_timeout(1200)
            state = page.evaluate(STATE)
            check("failed call: strip texts", state["title"] == "Prayer not recorded" and state["line"] == "The noosphere did not answer." and state["failed"] and state["heardOpacity"] > .95, state)
            check("failed call: nothing moved", before == page.evaluate(METRICS))
            page.screenshot(path=str(OUT / "answer-failed.png"))
            page.wait_for_timeout(3600)
            check("strip gone after 4.5 s", page.evaluate(STATE)["heardOpacity"] < .05, page.evaluate(STATE)["heardOpacity"])
            if chant.get_attribute("aria-pressed") == "true":              # the tune of the start before still plays
                chant.click(); page.wait_for_timeout(400)
            chant.click(); page.wait_for_timeout(2600)                     # start: total 5, and 4 of this prayer
            state = page.evaluate(STATE)
            check("total 5 with 4 of one prayer: the strip shows 5, and no reward comes", state["line"].endswith("· Your prayers: 5") and not state["shown"]
                  and state["sealVisibility"] == "hidden", state)
            errors = [e for e in errors if "500" not in e]                 # the stand-in answers 500 for the failed call
        check(f"{width}: no console or page errors", not errors, errors)
        page.close()
    page = browser.new_page(viewport={"width": 1440, "height": 900})       # the report of the counter fails: a counted prayer without a total
    page.route("**/api/report*", lambda route: route.abort())
    page.goto(PAGE, wait_until="load")
    page.wait_for_function("document.querySelectorAll('.prayers button').length === 4")
    page.get_by_role("button", name="Desecration of Flesh").click(); page.wait_for_timeout(2600)
    state = page.evaluate(STATE)
    check("report fails: the strip shows the counted prayer without a total, and no reward comes", state["title"] == "Prayer recorded"
          and bool(re.fullmatch(r"This prayer: \d+ by the congregation", state["line"])) and not state["failed"] and not state["shown"], state)
    page.close()
    for width, height in ((1440, 900), (390, 844)):                        # every reward by its address
        for number in REWARDS:
            page = browser.new_page(viewport={"width": width, "height": height})
            page.goto(f"{PAGE}#reward-{number}", wait_until="load")
            page.wait_for_function("document.getElementById('title').textContent !== 'The cogitator sleeps'")
            page.wait_for_timeout(1700)
            fit = page.evaluate("""() => { const d = document.querySelector("#reward > div"), b = d.getBoundingClientRect(), i = document.querySelector("#reward img");
                return { shown: document.getElementById("reward").classList.contains("shown"), left: b.left, right: b.right, top: b.top, bottom: b.bottom,
                         scroll: d.scrollHeight - d.clientHeight, image: i.naturalWidth, overflow: document.documentElement.scrollWidth > innerWidth, w: innerWidth, h: innerHeight }; }""")
            check(f"{width}: reward {number} fits", fit["shown"] and fit["left"] >= 7 and fit["right"] <= fit["w"] - 7 and fit["top"] >= 7 and fit["bottom"] <= fit["h"] - 7
                  and fit["scroll"] <= 0 and fit["image"] > 200 and not fit["overflow"], fit)
            if width == 1440 or number in (42, 40000):
                page.screenshot(path=str(OUT / f"reward-{number}{'' if width == 1440 else '-narrow'}.png"))
            page.close()
    page = browser.new_page(viewport={"width": 1440, "height": 900})       # in a frame that forbids downloads: the image opens in a new tab
    downloads = []
    page.on("download", lambda d: downloads.append(d))
    page.goto("http://workbench.example.test:8793/hub", wait_until="load")
    frame = page.frames[1]
    frame.wait_for_function("document.querySelectorAll('.prayers button').length === 4")
    # Safari opens a tab only while the page handles the click: note whether open() is called inside the click
    frame.evaluate("""() => { addEventListener("click", () => { window.inClick = true; setTimeout(() => window.inClick = false); }, true);
        const real = window.open; window.open = (...a) => { window.openedInClick = window.inClick; return real.apply(window, a); }; }""")
    with page.expect_popup() as got:
        frame.get_by_role("button", name="Holy Download").click()
    tab = got.value
    check("frame without downloads: the tab is opened while the click is handled, as Safari requires", frame.evaluate("window.openedInClick") is True)
    tab.wait_for_url(lambda url: url.startswith("blob:"))      # the tab opens empty at the click and gets the image when it is drawn
    tab.wait_for_load_state()
    shown = tab.evaluate("() => document.images.length === 1 && document.images[0].naturalWidth")
    check("frame without downloads: the image opens in a new tab", tab.url.startswith("blob:") and shown == 1000 and not downloads, (tab.url[:40], shown, len(downloads)))
    tab.screenshot(path=str(OUT / "keepsake-tab.png"))
    page.close()
    page = browser.new_page(viewport={"width": 1440, "height": 900})       # without scripts: the fallback text, no buttons, no badge, no reward
    page.goto("http://workbench.example.test:8793/wrap", wait_until="load"); page.wait_for_timeout(1500)
    check("no scripts: fallback", page.frames[1].evaluate("""() => document.getElementById("title").textContent === "The cogitator sleeps" && document.querySelectorAll(".prayers button, .radios button").length === 0
          && document.getElementById("badge").hidden && getComputedStyle(document.getElementById("reward")).visibility === "hidden" """))
    browser.close()
print("checks:", "all passed" if not faults else f"{len(faults)} FAILED {faults}")
