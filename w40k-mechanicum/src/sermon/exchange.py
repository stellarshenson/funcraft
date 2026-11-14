"""Checks the sermons exchanged on 12 October 2026 in the built sermon page, in headless Chrome against
src/sermon/mock.py: each of the days opened by its date shows the Context of calendar/ and its badge from the package.

    (setsid python3 src/sermon/mock.py out/w40k-mechanicum-sermons >/dev/null 2>&1 &)
    python3 src/sermon/exchange.py
    pkill -f 'sermon/mock\\.py'          # in a command of its own
"""
import hashlib, pathlib, re, sys
from playwright.sync_api import sync_playwright
ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "src" / "calendar"))
from exchange import NEW, MONTHS
PAGE = "http://workbench.example.test:8793/user/konrad.jelen/index.html"
SHOWN = """async () => { const b = document.querySelector("#badge");
  const bytes = new Uint8Array(await (await fetch(b.src)).arrayBuffer());
  return { title: document.querySelector("#title").textContent, text: document.querySelector("#sermon").textContent,
           badge: b.src.split("/").pop(), width: b.naturalWidth, hidden: b.hidden, bytes: Array.from(bytes) }; }"""
flat = lambda s: re.sub(r"\s+", " ", s).strip()

faults = 0
with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True, args=["--no-sandbox", "--disable-dev-shm-usage",
        "--host-resolver-rules=MAP *.example.test 127.0.0.1", "--autoplay-policy=no-user-gesture-required"])
    for day, (_, context, _, _) in NEW.items():
        m, d = int(day[:2]), int(day[3:])
        title = re.search(rf"^## {MONTHS[m - 1]} {d} - (.+)$", (ROOT / f"calendar/{m:02d}-{MONTHS[m - 1].lower()}.md").read_text(), flags=re.M)[1]
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(f"{PAGE}#{day}", wait_until="load")
        page.wait_for_function("() => !document.querySelector('#badge').hidden && document.querySelector('#badge').naturalWidth > 0", timeout=15000)
        got = page.evaluate(SHOWN)
        built = (ROOT / f"out/w40k-mechanicum-sermons/resources/badges/{day}.avif").read_bytes()
        ok = (flat(got["title"]) == title and flat(got["text"]) == flat(context) and got["badge"] == f"{day}.avif"
              and got["width"] > 0 and hashlib.md5(bytes(got["bytes"])).digest() == hashlib.md5(built).digest())
        print(("ok   " if ok else "FAIL ") + f"{day} {title}", "" if ok else (got["title"], got["text"][:80], got["badge"], got["width"]))
        faults += not ok
        page.close()
    browser.close()
print(len(NEW), "days,", faults, "FAIL")
