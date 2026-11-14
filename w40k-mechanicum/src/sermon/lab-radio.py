"""Asks whether a radio of the sermon page would play in the HTML viewer of the lab if the content policy of the lab
allowed the YouTube player. The lab is not changed: the test browser alone gets the policy header with one more rule.

    python3 src/sermon/lab-radio.py

The lab token is read from the environment, sent to localhost:8888 only and never printed. An error of route.fetch
lists the request headers with the token in its text: the handler catches every such error and prints nothing, and
only pages go through route.fetch, because a stream of the lab never ends and route.fetch would wait for it. Run the
script through a filter that replaces the token, and write no log before that filter:

    python3 src/sermon/lab-radio.py 2>&1 | python3 -c "import os, sys; [sys.stdout.write(line.replace(os.environ['JUPYTERHUB_API_TOKEN'], '<token>')) for line in sys.stdin]"
 The page opens in a
workspace of its own, sermon-preview, which the script deletes at the end.
"""
import os, urllib.request
from playwright.sync_api import sync_playwright
tok, user = os.environ["JUPYTERHUB_API_TOKEN"], os.environ["JUPYTERHUB_USER"]
LAB = f"http://localhost:8888/user/{user}/lab"
RULE = "frame-src 'self' data: blob: https://www.youtube-nocookie.com; "
VIDEO = """() => { const v = document.querySelector("video"); const e = document.querySelector(".ytp-error");
  return { video: v && { time: Math.round(v.currentTime), paused: v.paused, muted: v.muted }, error: e && e.innerText.slice(0, 200), referrer: document.referrer }; }"""

def allow(route):
    sent = {**route.request.headers, "Authorization": f"token {tok}"}
    if route.request.resource_type != "document":
        return route.continue_(headers=sent)
    try:
        answer = route.fetch(headers=sent)
    except Exception:                                       # its text holds the token
        return route.abort()
    headers = dict(answer.headers)
    if "content-security-policy" in headers:
        headers["content-security-policy"] = RULE + headers["content-security-policy"]
    route.fulfill(response=answer, headers=headers)

def sermon_frame(page):
    for frame in page.frames:
        try:
            if frame != page.main_frame and frame.evaluate("!!document.getElementById('title')"):
                return frame
        except Exception:
            pass

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    ctx.route("http://localhost:8888/**", allow)
    page = ctx.new_page()
    notes = []
    page.on("console", lambda m: notes.append(m.text[:200]) if "youtube" in m.text.lower() or "Content Security" in m.text else None)
    page.goto(LAB + "/workspaces/sermon-preview/tree/funcraft/w40k-mechanicum/out/w40k-mechanicum-sermons/index.html?reset", wait_until="domcontentloaded")
    page.wait_for_timeout(15000)
    page.locator("#jp-main-dock-panel .jp-Toolbar").locator("button:visible, jp-button:visible").filter(has_text="Trust HTML").first.click()
    page.wait_for_timeout(6000)
    frame = sermon_frame(page)
    print("page address:", frame.url[:30], "| sandbox:", frame.evaluate("frameElement.sandbox.value"))
    frame.locator(".radios button").first.click()
    second = 0
    for wait in (3, 5, 8):
        page.wait_for_timeout(wait * 1000)
        second += wait
        lit = frame.evaluate("""() => [...document.querySelectorAll('.radios [aria-pressed="true"]')].map(b => b.textContent)""")
        players = [f for f in page.frames if "youtube" in f.url]
        state = None
        for player in players:
            try:
                state = player.evaluate(VIDEO)
            except Exception as error:
                state = str(error)[:100]
        print(f"after {second} s: lit {lit} | YouTube frames {len(players)} | player {state}")
    print("console:", notes)
    browser.close()
request = urllib.request.Request(f"{LAB}/api/workspaces/sermon-preview", method="DELETE", headers={"Authorization": "token " + tok})
print("workspace deleted:", urllib.request.urlopen(request).status)
