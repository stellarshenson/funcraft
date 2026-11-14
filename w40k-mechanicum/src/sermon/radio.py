"""Checks the radio buttons of the sermon page in headless Chrome against src/sermon/mock.py. A radio plays a YouTube
video, so these checks need the network and reach youtube-nocookie.com; src/sermon/test.py needs neither. The browser
runs with its default rule for sound: a page may start sound only after an action of the reader.

    (setsid python3 src/sermon/mock.py out/w40k-mechanicum-sermons >/dev/null 2>&1 &)
    python3 src/sermon/radio.py
    pkill -f 'sermon/mock\\.py'          # in a command of its own
"""
import pathlib, re
from playwright.sync_api import sync_playwright
OUT = pathlib.Path(__file__).parent.parent.parent / "wip" / "sermon"
HOST = "http://workbench.example.test:8793"
PAGE = HOST + "/user/konrad.jelen/index.html"
# button: video, earliest second of a start, length of the video in seconds - as RADIOS of src/sermon.template.html
RADIOS = {"Holy Mars Radio": ("VMs_p5EWri4", 34, 10825), "Holy Terra Radio": ("k5xDyG72wHE", 0, 10839),
          "Forge Radio": ("M3D9TYNRXwY", 0, 4633), "Cogitator Radio": ("M3D9TYNRXwY", 319, 4633)}
STATE = """() => ({ lit: [...document.querySelectorAll(".radios button")].filter(b => b.getAttribute("aria-pressed") === "true").map(b => b.textContent),
  frames: [...document.querySelectorAll("iframe")].map(f => f.src), music: [document.getElementById("music").paused, Math.round(document.getElementById("music").currentTime)],
  box: [document.documentElement.scrollWidth, document.documentElement.scrollHeight, innerWidth] })"""
VIDEO = """() => { const v = document.querySelector("video"); const e = document.querySelector(".ytp-error");
  return { video: v && { time: v.currentTime, paused: v.paused, muted: v.muted, volume: v.volume, length: v.duration }, error: e && e.innerText }; }"""

faults, starts = [], {}
def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name, "" if ok else detail)
    if not ok: faults.append(name)

def player(page):
    """The reading of the one YouTube player of the page, or the reason why there is none."""
    players = [f for f in page.frames if "youtube-nocookie.com/embed/" in f.url]
    if len(players) != 1:
        return f"{len(players)} players"
    try:
        return players[0].evaluate(VIDEO)
    except Exception as error:                          # the frame was still loading
        return str(error)[:120]

def sound(page, start, wait=25):
    """Whether the YouTube player of the page plays with sound at or after a second, read twice, 2 s apart."""
    last = None
    for _ in range(wait):
        page.wait_for_timeout(1000)
        first = player(page)
        page.wait_for_timeout(2000)
        last = player(page)
        if isinstance(first, str) or isinstance(last, str):
            continue
        a, b = first["video"], last["video"]
        if a and b and not b["paused"] and not b["muted"] and b["volume"] > 0 and b["time"] > a["time"] and b["time"] >= start:
            return True, last
    return False, last

def held(state, name):
    """Whether the page holds the one player of a radio at a start inside its video; notes the start."""
    video, earliest, length = RADIOS[name]
    hit = len(state["frames"]) == 1 and re.fullmatch(rf"https://www\.youtube-nocookie\.com/embed/{video}\?autoplay=1&loop=1&playlist={video}&start=(\d+)", state["frames"][0])
    if not hit:
        return False
    starts.setdefault(name, []).append(int(hit[1]))
    return state["lit"] == [name] and earliest <= int(hit[1]) < length

def long(detail, name):
    """Whether the player reports the length that RADIOS holds for a radio."""
    return isinstance(detail, dict) and bool(detail["video"]) and abs(detail["video"]["length"] - RADIOS[name][2]) < 2

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True, args=["--no-sandbox", "--disable-dev-shm-usage",
        "--host-resolver-rules=MAP *.example.test 127.0.0.1"])
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
    page.goto(PAGE, wait_until="load")
    page.wait_for_function("document.querySelectorAll('.radios button').length === 4 && document.querySelectorAll('.prayers button').length === 4")
    page.wait_for_timeout(1500)
    before = page.evaluate(STATE)
    check("load: four radio buttons, none lit, no player", [b.inner_text() for b in page.locator(".radios button").all()] == list(RADIOS)
          and not before["lit"] and not before["frames"], before)
    check("load: the browser holds the music back until the first action", before["music"][0], before)
    page.screenshot(path=str(OUT / "radio-1440.png"))

    name = "Holy Mars Radio"                                              # the first action of the reader is a press of a radio button
    page.get_by_role("button", name=name).click(); page.wait_for_timeout(500)
    state = page.evaluate(STATE)
    check("Mars: the button is lit and one player holds its video at a start inside the video", held(state, name), state)
    check("Mars: the press did not start the music", state["music"] == [True, 0], state)
    check("Mars: nothing moved", state["box"] == before["box"], (before["box"], state["box"]))
    ok, detail = sound(page, starts[name][-1])
    check("Mars: the player plays with sound from its start", ok, detail)
    check("Mars: the length in RADIOS is the length of the video", long(detail, name), detail)
    page.locator("#sermon").click(); page.wait_for_timeout(700)
    state = page.evaluate(STATE)
    check("Mars: a click on the sermon does not start the music and does not stop the radio", state["music"] == [True, 0] and state["lit"] == [name], state)
    page.screenshot(path=str(OUT / "radio-playing.png"))
    page.locator(".banner").click(); page.wait_for_timeout(1500)
    state = page.evaluate(STATE)
    check("Mars: a click on the banner stops the radio and plays the music", not state["lit"] and not state["frames"] and not state["music"][0]
          and not [f for f in page.frames if "youtube" in f.url], (state, [f.url for f in page.frames]))

    for name in ("Holy Terra Radio", "Forge Radio", "Cogitator Radio"):   # another radio takes the place of the one before
        page.get_by_role("button", name=name).click(); page.wait_for_timeout(500)
        state = page.evaluate(STATE)
        check(f"{name}: it alone is lit, with one player at a start inside the video", held(state, name), state)
        check(f"{name}: the music is silent", state["music"][0], state)
        ok, detail = sound(page, starts[name][-1])
        check(f"{name}: the player plays with sound from its start", ok, detail)
        check(f"{name}: the length in RADIOS is the length of the video", long(detail, name), detail)

    page.get_by_role("button", name="Cogitator Radio").click(); page.wait_for_timeout(1500)      # the second press
    state = page.evaluate(STATE)
    check("second press: no button lit, no player, no YouTube frame left", not state["lit"] and not state["frames"]
          and not [f for f in page.frames if "youtube" in f.url], (state, [f.url for f in page.frames]))
    check("second press: the music stays silent", state["music"][0], state)
    page.locator(".banner").click(); page.wait_for_timeout(1500)
    state = page.evaluate(STATE)
    check("after the radio: a click on the banner starts the music", not state["music"][0], state)
    page.locator(".banner").click(); page.wait_for_timeout(700)
    state = page.evaluate(STATE)
    check("the next click on the banner stops the music", state["music"][0] and state["music"][1] >= 1, state)
    page.locator("#sermon").click(); page.wait_for_timeout(1500)
    state = page.evaluate(STATE)
    check("a click on the sermon plays the music on", not state["music"][0] and state["music"][1] >= 1, state)
    check("no console or page errors", not errors, errors)
    page.close()

    page = browser.new_page(viewport={"width": 1440, "height": 900})       # in the frame of the hub's Welcome page, with its sandbox
    page.goto(HOST + "/hub", wait_until="load")
    frame = page.frames[1]
    frame.wait_for_function("document.querySelectorAll('.radios button').length === 4")
    frame.get_by_role("button", name="Holy Mars Radio").click(); page.wait_for_timeout(500)
    state = frame.evaluate(STATE)
    check("hub frame: the player holds the video at a start inside the video", held(state, "Holy Mars Radio"), state)
    ok, detail = sound(page, starts["Holy Mars Radio"][-1])
    check("hub frame: the player plays with sound", ok, detail)
    check("a second press of one radio starts at another second", len(set(starts["Holy Mars Radio"])) == 2, starts)
    page.close()

    page = browser.new_page(viewport={"width": 1440, "height": 900})       # the end of a video: the same radio starts again
    page.goto(PAGE, wait_until="load")
    page.wait_for_function("document.querySelectorAll('.radios button').length === 4")
    video, earliest, length = RADIOS["Forge Radio"]
    page.evaluate(f"Math.random = () => {(length - 12 - earliest + 0.5) / (length - earliest)}")      # the draw that starts 12 s before the end
    page.get_by_role("button", name="Forge Radio").click(); page.wait_for_timeout(500)
    state = page.evaluate(STATE)
    check("end of a video: the radio starts 12 s before the end", held(state, "Forge Radio") and starts["Forge Radio"][-1] == length - 12, (state, starts))
    readings, again = [], False
    for _ in range(30):                                                    # up to 60 s
        page.wait_for_timeout(2000)
        reading = player(page)
        readings.append(reading if isinstance(reading, str) else (round(reading["video"]["time"]), reading["video"]["paused"]) if reading["video"] else str(reading["error"]))
        seen = [r for r in readings if isinstance(r, tuple)]
        late = [k for k, (time, _) in enumerate(seen) if time >= length - 12]
        early = [k for k, (time, paused) in enumerate(seen) if late and k > late[0] and time < length - 60 and not paused]
        if len(early) >= 2 and seen[early[-1]][0] > seen[early[0]][0]:      # after the end: two readings near the start, the second later
            again = True
            break
    state = page.evaluate(STATE)
    check("end of a video: the same radio plays again, and its button stays lit", again and state["lit"] == ["Forge Radio"] and len(state["frames"]) == 1, (readings, state))
    print("     readings of the player as (second, paused):", readings)
    page.close()

    page = browser.new_page(viewport={"width": 1440, "height": 900})       # a host policy without the frame rule
    refused = []
    page.on("console", lambda m: refused.append(m.text) if m.type == "error" else None)
    page.goto(PAGE + "?noradio", wait_until="load")
    page.wait_for_function("document.querySelectorAll('.radios button').length === 4")
    page.locator(".banner").click(); page.wait_for_timeout(1500)          # the first action, a click on the banner, starts the music
    playing = not page.evaluate(STATE)["music"][0]
    check("first action on the banner: the music plays", playing, page.evaluate(STATE))
    page.get_by_role("button", name="Holy Mars Radio").click(); page.wait_for_timeout(1500)
    state = page.evaluate(STATE)
    check("policy without the frame rule: the button goes out and no player stays", not state["lit"] and not state["frames"]
          and any("youtube-nocookie.com" in line for line in refused), (state, refused))
    check("policy without the frame rule: the music plays on", playing and not state["music"][0], (playing, state))
    browser.close()
print("checks:", "all passed" if not faults else f"{len(faults)} FAILED {faults}")
