"""Checks the sermon page in the HTML viewer of the lab: before and after 'Trust HTML', one press of a prayer button,
one press of a radio button and one press of the holy download button.

    python3 src/sermon/lab.py

The lab token is read from the environment, sent to localhost:8888 only and never printed. The page opens in a
workspace of its own, sermon-preview, which the script deletes at the end.
"""
import os, urllib.request
from playwright.sync_api import sync_playwright
tok, user = os.environ["JUPYTERHUB_API_TOKEN"], os.environ["JUPYTERHUB_USER"]
LAB = f"http://localhost:8888/user/{user}/lab"
READ = """() => { const heard = document.getElementById("heard");
  return { title: document.getElementById("title").textContent, buttons: document.querySelectorAll(".prayers button").length,
           strip: heard.querySelector("strong").textContent + " | " + heard.querySelector("span").textContent, opacity: +getComputedStyle(heard).opacity,
           badge: [document.getElementById("badge").hidden, document.getElementById("badge").naturalWidth],
           sandbox: frameElement ? frameElement.sandbox.value : "frame not readable",
           reward: getComputedStyle(document.getElementById("reward")).visibility,
           row: Math.round(document.querySelector(".prayers").getBoundingClientRect().top + scrollY), height: document.documentElement.scrollHeight,
           overflow: document.documentElement.scrollWidth > innerWidth }; }"""

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
    ctx.route("http://localhost:8888/**", lambda route: route.continue_(headers={**route.request.headers, "Authorization": f"token {tok}"}))
    page = ctx.new_page()
    crashed = []
    page.on("crash", lambda: crashed.append(1))
    page.goto(LAB + "/workspaces/sermon-preview/tree/funcraft/w40k-mechanicum/out/w40k-mechanicum-sermons/index.html?reset", wait_until="domcontentloaded")
    page.wait_for_timeout(12000)
    print("before trust:", sermon_frame(page).evaluate(READ))
    page.locator("#jp-main-dock-panel .jp-Toolbar").locator("button:visible, jp-button:visible").filter(has_text="Trust HTML").first.click()
    page.wait_for_timeout(6000)
    frame = sermon_frame(page)
    before = frame.evaluate(READ)
    print("after trust: ", before)
    frame.locator(".prayers button").first.click()
    page.wait_for_timeout(1500)
    after = frame.evaluate(READ)
    print("after a press:", after)
    print("nothing moved:", (before["row"], before["height"]) == (after["row"], after["height"]), "| crashed:", bool(crashed))
    refused = []
    page.on("console", lambda m: refused.append(m.text[:160]) if "youtube" in m.text else None)
    frame.locator(".radios button").first.click()
    page.wait_for_timeout(2500)
    print("radio press:", frame.evaluate("""() => ({ buttons: [...document.querySelectorAll(".radios button")].map(b => b.textContent + " " + b.getAttribute("aria-pressed")),
        players: document.querySelectorAll("iframe").length, music: document.getElementById("music").paused })"""), "| console:", refused)
    got = {"downloads": [], "tabs": []}
    page.on("download", lambda d: got["downloads"].append(d.suggested_filename))
    ctx.on("page", lambda tab: got["tabs"].append(tab.url[:30]))
    frame.locator(".prayers .keep").click()
    page.wait_for_timeout(3000)
    print("holy download:", got)
    browser.close()
request = urllib.request.Request(f"{LAB}/api/workspaces/sermon-preview", method="DELETE", headers={"Authorization": "token " + tok})
print("workspace deleted:", urllib.request.urlopen(request).status)
