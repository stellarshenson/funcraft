"""Checks the banner of every day of the sermon page in headless Chrome against src/sermon/mock.py: the page's own
choice for each of the 366 day numbers, the file of every banner, and one day per banner opened by its date.
Start the stand-in first, with a fresh process for every run:

    (setsid python3 src/sermon/mock.py out/w40k-mechanicum-sermons >/dev/null 2>&1 &)
    python3 src/sermon/banners.py
    pkill -f 'sermon/mock\\.py'          # in a command of its own
"""
import collections, datetime, itertools, pathlib
from playwright.sync_api import sync_playwright
ROOT = pathlib.Path(__file__).parent.parent.parent
PAGE = "http://workbench.example.test:8793/user/konrad.jelen/index.html"
CHOICE = "() => ({ names: BANNERS, days: Array.from({ length: 366 }, (_, k) => BANNERS[Math.floor(draw(k + 1) * BANNERS.length)]) })"
SHOWN = """() => { const i = document.querySelector(".banner img"); return { src: i.src.split("/").pop(), size: [i.naturalWidth, i.naturalHeight], number }; }"""

faults = []
def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name, "" if ok else detail)
    if not ok: faults.append(name)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True, args=["--no-sandbox", "--disable-dev-shm-usage",
        "--host-resolver-rules=MAP *.example.test 127.0.0.1", "--autoplay-policy=no-user-gesture-required"])
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto(PAGE, wait_until="load")
    got = page.evaluate(CHOICE)
    names, days = got["names"], got["days"]
    built = sorted(f.stem for f in (ROOT / "out/w40k-mechanicum-sermons/resources/banners").glob("*.avif"))
    check(f"the page lists the {len(built)} banners of the package", sorted(names) == built, (names, built))
    check("the list holds the muster", "16-muster" in names, names)
    count = collections.Counter(days)
    check("every banner is the banner of some day", set(count) == set(names), dict(count))
    check("every one of the 366 days has a banner of the list", len(days) == 366 and all(d in names for d in days))
    for name in names:
        status, size = page.evaluate("async name => { const r = await fetch(`resources/banners/${name}.avif`); return [r.status, (await r.arrayBuffer()).byteLength]; }", name)
        check(f"{name}: the file is served", status == 200 and size > 50000, (status, size))
    year = datetime.date.today().year
    for name in names:                                                # the first day of this year with each banner, opened by its date
        number = days.index(name) + 1
        date = datetime.date(year, 1, 1) + datetime.timedelta(number - 1)
        page.goto(PAGE + date.strftime("#%m-%d"))
        page.reload(wait_until="load")
        page.wait_for_function("document.querySelector('.banner img')?.naturalWidth > 0")
        shown = page.evaluate(SHOWN)
        check(f"{date:%m-%d}, day {number}: the page shows {name}", shown == {"src": name + ".avif", "size": [788, 249], "number": number}, shown)
        box = page.locator(".banner img")
        first = box.screenshot(); page.wait_for_timeout(500); second = box.screenshot()
        check(f"{date:%m-%d}: the banner moves", first != second)
    browser.close()

same = sum(a == b for a, b in zip(days, days[1:]))
run = max(sum(1 for _ in g) for _, g in itertools.groupby(days))
print("days per banner:", ", ".join(f"{n} {count[n]}" for n in names))
print(f"the same banner on the next day: {same} times in the year; longest run {run} days")
print("\n" + (f"{len(faults)} FAULTS: {faults}" if faults else "all checks passed"))
