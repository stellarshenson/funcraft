"""The page in a headless browser against the service with stub engines (`stub_service.py`): the login, a 401 that
returns to the login box, the address of each page and Settings tab, API token create, and the drop, drag and download
name behaviour of the Transcription and Voice rendering pages. No GPU and no model; the
interpreter needs playwright, and google-chrome must be installed.
"""
import os
import re
import shutil
import signal
import subprocess
from pathlib import Path

import httpx
import pytest
import support
from playwright.sync_api import expect, sync_playwright

HERE = Path(__file__).resolve().parent
ROUTES = {"render": "#page-render", "transcribe": "#page-transcribe", "settings/hf": "#set-hf",
          "settings/api": "#set-api", "settings/voices": "#set-voices", "settings/models": "#set-models"}


@pytest.fixture(scope="module")
def base(tmp_path_factory):
    """The stub service on a free port with the test password, stopped after the module."""
    folder = tmp_path_factory.mktemp("browser")
    port = support.free_port()
    env = dict(os.environ, S2PRO_PASSWORD=support.PASSWORD)
    if support.FFMPEG_DIR:
        env["PATH"] = f"{support.FFMPEG_DIR}:{env['PATH']}"
    log = (folder / "stub-service.log").open("w")
    process = subprocess.Popen([str(support.PYTHON), str(HERE / "stub_service.py"), str(port), str(folder / "data")],
                               env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    url = f"http://127.0.0.1:{port}"
    try:
        support.wait_for(lambda: support.get_json(f"{url}/health")["status"] == "ok", 60, "the stub service")
        yield url
    finally:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=30)
        log.close()


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as playwright:
        chrome = playwright.chromium.launch(executable_path=shutil.which("google-chrome"))
        yield chrome
        chrome.close()


@pytest.fixture
def page(browser):
    """A page in a fresh browser context, so each test starts without a session cookie."""
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    yield context.new_page()
    context.close()


def log_in(page, base: str, route: str = "render") -> None:
    page.goto(f"{base}/#/{route}")
    page.fill("#login-password", support.PASSWORD)
    page.click("#login-button")
    expect(page.locator("#app-section")).to_be_visible()


def test_a_wrong_password_is_refused_and_the_right_one_opens_the_portal(page, base):
    """Logged out only the login box shows; a wrong password shows the service's reason, the right one the portal."""
    page.goto(base + "/")
    expect(page.locator("#login-section")).to_be_visible()
    expect(page.locator("#app-section")).to_be_hidden()
    page.fill("#login-password", "wrong")
    page.click("#login-button")
    expect(page.locator("#login-banner")).to_contain_text("Wrong password.")
    expect(page.locator("#app-section")).to_be_hidden()
    log_in(page, base)
    expect(page.locator("#login-section")).to_be_hidden()
    expect(page.locator("#page-render")).to_be_visible()
    expect(page.locator("#engine-badge")).to_contain_text("ready")


def test_a_401_returns_to_the_login_box_and_a_new_login_shows_no_old_error(page, base):
    """With the session cookie gone, the next request is refused: the login box shows the service's message; after a
    new login no outcome line still carries the refusal."""
    log_in(page, base, "settings/api")
    page.context.clear_cookies()
    page.fill("#api-token-name", "after-logout")
    page.click("#api-token-create")
    expect(page.locator("#login-section")).to_be_visible()
    expect(page.locator("#login-banner")).to_contain_text("log in first")
    log_in(page, base, "settings/api")
    expect(page.locator("#set-api")).to_be_visible()
    expect(page.locator("#api-token-outcome")).not_to_contain_text("log in first")
    assert page.locator("#app-section [data-kind='error']").count() == 0


def test_each_page_and_settings_tab_has_its_own_address(page, base):
    """Every address shows its page or tab and marks it current; a reload stays on it."""
    log_in(page, base)
    for route, section in ROUTES.items():
        page.goto(f"{base}/#/{route}")
        expect(page.locator(section)).to_be_visible()
        page.reload()
        expect(page.locator(section)).to_be_visible()
        visible = [selector for selector in ROUTES.values() if page.locator(selector).is_visible()]
        assert visible == [section], (route, visible)
        name = route.split("/")[0]
        assert page.locator(f".p-side [data-nav='{name}']").get_attribute("aria-current") == "page"
    page.click(".p-side [data-nav='transcribe']")
    expect(page).to_have_url(f"{base}/#/transcribe")
    expect(page.locator("#page-transcribe")).to_be_visible()


def test_create_token_shows_it_once_and_the_token_works(page, base):
    """Create token shows the new token once with Copy and lists it; the token opens /voices as Bearer; Delete
    revokes it."""
    log_in(page, base, "settings/api")
    page.fill("#api-token-name", "browser-test")
    page.click("#api-token-create")
    expect(page.locator("#api-token-outcome")).to_contain_text("Created browser-test")
    expect(page.locator("#api-token-new")).to_be_visible()
    expect(page.locator("#api-token-copy")).to_be_visible()
    token = page.input_value("#api-token-value")
    assert token.startswith("vtts_")
    expect(page.locator("#api-token-list")).to_contain_text("browser-test")
    assert httpx.get(f"{base}/voices", headers={"Authorization": f"Bearer {token}"}).status_code == 200
    page.reload()
    expect(page.locator("#api-token-list")).to_contain_text("browser-test")
    expect(page.locator("#api-token-new")).to_be_hidden()
    delete = page.locator("#api-token-list button", has_text="Delete")
    delete.click()
    page.locator("#api-token-list button", has_text="Confirm").click()
    expect(page.locator("#api-token-list-outcome")).to_contain_text("Deleted browser-test")
    assert httpx.get(f"{base}/voices", headers={"Authorization": f"Bearer {token}"}).status_code == 401


FILE_DRAG = """(selector) => {
    const files = new DataTransfer();
    files.items.add(new File(["x"], "recording.mp3", {type: "audio/mpeg"}));
    window.portalStillLoaded = true;
    const target = document.querySelector(selector);
    const cancelled = {};
    for (const type of ["dragover", "drop"]) {
        cancelled[type] = !target.dispatchEvent(new DragEvent(type, {dataTransfer: files, bubbles: true, cancelable: true}));
    }
    return cancelled;
}"""


@pytest.mark.parametrize("route, target", [("render", "#page-render"), ("transcribe", "#page-transcribe")])
def test_a_file_dragged_over_the_portal_is_never_opened_by_the_browser(page, base, route, target):
    """A file over the Voice rendering page or a Transcription gutter has its drag and drop cancelled, so the portal
    stays loaded."""
    log_in(page, base, route)
    assert page.evaluate(FILE_DRAG, target) == {"dragover": True, "drop": True}
    assert page.evaluate("window.portalStillLoaded") is True
    expect(page.locator("#app-section")).to_be_visible()


def test_a_click_on_the_drop_box_opens_the_file_picker_once(page, base):
    """A click on the box, away from its button, clicks the file input once; a click on the button also once."""
    log_in(page, base, "transcribe")
    page.evaluate("""() => {
        window.pickerClicks = 0;
        document.getElementById("transcribe-file").addEventListener("click", (event) => {
            event.preventDefault();
            window.pickerClicks += 1;
        });
    }""")
    page.click("#drop strong")
    assert page.evaluate("window.pickerClicks") == 1
    page.click("#drop [data-pick]")
    assert page.evaluate("window.pickerClicks") == 2


def test_text_dragged_into_names_and_terms_is_inserted(page, base):
    """A text drag keeps the browser's behaviour: the field receives the text."""
    log_in(page, base, "transcribe")
    source = page.locator("#page-transcribe header p")
    source.click(click_count=3)
    source.drag_to(page.locator("#transcribe-context"))
    assert "Turn a recording into text" in page.input_value("#transcribe-context")


def test_the_drag_highlight_is_on_the_form_card_with_and_without_a_recording(page, base, tmp_path):
    """Dragging files over the page sets the highlight attribute on the form card, before and after a recording is
    chosen; leaving clears it."""
    log_in(page, base, "transcribe")
    form = page.locator("#transcribe-form")
    page.evaluate(FILE_DRAG.replace('["dragover", "drop"]', '["dragover"]'), "#page-transcribe")
    expect(form).to_have_attribute("data-over", "yes")
    page.dispatch_event("#page-transcribe", "dragleave")
    expect(form).not_to_have_attribute("data-over", "yes")
    recording = tmp_path / "recording.wav"
    recording.write_bytes(b"RIFF")
    page.set_input_files("#transcribe-file", str(recording))
    expect(page.locator("#drop")).to_be_hidden()
    page.evaluate(FILE_DRAG.replace('["dragover", "drop"]', '["dragover"]'), "#page-transcribe")
    expect(form).to_have_attribute("data-over", "yes")


def test_a_downloaded_render_is_named_voice_and_clock_time(page, base):
    """The result card and this session's list name the download `<voice>-<HHMM>.mp3`."""
    log_in(page, base, "render")
    page.fill("#speak-text", "Brothers, we stand upon the wall.")
    page.click("#speak-button")
    expect(page.locator("#render-result")).to_have_attribute("data-state", "done", timeout=60000)
    pattern = r"[a-z0-9-]+-\d{4}\.mp3"
    assert re.fullmatch(pattern, page.get_attribute("#download", "download"))
    assert re.fullmatch(pattern, page.get_attribute("#recent-list a[download]", "download"))
