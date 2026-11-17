"use strict";
// The Leftenant Voice portal: the login box, then Voice rendering, Transcription and Settings with four tabs, each at
// its own hash URL. Every button shows running, done or the service's reason beside it; any 401 returns to the login
// box with the service's message.

const $ = (id) => document.getElementById(id);
const SVG = "http://www.w3.org/2000/svg";
const PAGES = { render: "Voice rendering", transcribe: "Transcription", settings: "Settings" };
const TABS = { hf: "Hugging Face", api: "API tokens", voices: "Voices", models: "Models" };
// Display names of the service's engine and model keys; an unknown key shows as the service names it
const LABELS = { s2pro: "S2 Pro", "auk-flash": "AuK-Flash", nemotron: "Nemotron 3.5 Transcribe" };
const BARS = 48;
const MAX_TRANSCRIBE_ATTEMPTS = 5;

let voices = {};
let uploaded = [];
let freshVoice = null;
let defaultEngine = null;
let chosenEngine = null;
let health = null;
let healthTimer = null;
let asrWaiter = null;
let transcribePhase = null;
let sawDownload = false;
let sawWait = false;
let sent = false;
let recordingSeconds = null;
let transcriptUrl = null;
let current = null;
const renders = [];

const label = (key) => LABELS[key] || key;

function markCurrent(link, on) {
  if (on) link.setAttribute("aria-current", "page");
  else link.removeAttribute("aria-current");
}

/* Requests */

async function errorDetail(response) {
  let body = null;
  try {
    body = await response.json();
  } catch {
    // the body is not JSON; the status code is all there is
  }
  const detail = body && body.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => (item && item.msg
      ? (Array.isArray(item.loc) ? item.loc[item.loc.length - 1] + ": " : "") + item.msg
      : JSON.stringify(item))).join("; ");
  }
  return "the request failed with HTTP " + response.status;
}

/** Return `response` when it is ok; a refusal throws the service's `detail` with the status and Retry-After, and a
 * 401 outside /login returns to the login box. */
async function check(response, path) {
  if (response.ok) return response;
  const detail = await errorDetail(response);
  if (response.status === 401 && path !== "/login") {
    showLogin("Logged out: the service answered “" + detail + "”. Log in again.");
  }
  throw Object.assign(new Error(detail), { status: response.status, retryAfter: response.headers.get("Retry-After") });
}

async function api(path, options) {
  let response;
  try {
    response = await fetch(path, options);
  } catch {
    throw new Error("the service did not answer; check that it runs");
  }
  return check(response, path);
}

function postJson(path, body) {
  return api(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
}

/** POST a form like `api`, with XMLHttpRequest so `onSent` runs when the upload has finished. */
function upload(path, body, onSent) {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.open("POST", path);
    request.upload.addEventListener("load", onSent);
    request.addEventListener("load", () => {
      const headers = {};
      for (const name of ["Content-Type", "Retry-After"]) {
        if (request.getResponseHeader(name)) headers[name] = request.getResponseHeader(name);
      }
      resolve(check(new Response(request.responseText, { status: request.status, headers }), path));
    });
    request.addEventListener("error", () => reject(new Error("the service did not answer; check that it runs")));
    request.send(body);
  });
}

/* Outcomes, states and small builders */

function icon(name, className = "ic") {
  const svg = document.createElementNS(SVG, "svg");
  svg.setAttribute("class", className);
  svg.setAttribute("aria-hidden", "true");
  const use = document.createElementNS(SVG, "use");
  use.setAttribute("href", "#" + name);
  svg.append(use);
  return svg;
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

/** Show an outcome line: `kind` busy, ok or error with its text, or no kind for the line's idle text. */
function setOutcome(out, kind = "", text = out.dataset.idle || "") {
  if (!text) {
    out.replaceChildren();
    return;
  }
  const line = element("span");
  if (kind) line.dataset.kind = kind;
  if (kind === "busy") line.append(element("i", "p-spin"));
  else if (kind) line.append(icon(kind === "ok" ? "i-check" : "i-alert", "ic ic-sm"));
  line.append(text);
  out.replaceChildren(line);
}

/** Show the `[data-when]` parts of `card` that list `state`. */
function setState(card, state) {
  card.dataset.state = state;
  for (const part of card.querySelectorAll("[data-when]")) part.hidden = !part.dataset.when.split(" ").includes(state);
}

/** Bring a finished result into view and give its title the focus; on a phone it sits below the button. */
function reveal(card) {
  card.scrollIntoView({ block: "nearest", behavior: "smooth" });
  card.querySelector(".p-card-title").focus({ preventScroll: true });
}

/** Run `action` for `button`: disable it, say it runs, then show the text it returns or the reason it failed. */
async function run(button, outcome, busyText, action) {
  const caption = button.dataset.busy ? button.lastElementChild : null;
  const idleCaption = caption ? caption.textContent : "";
  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  if (caption) caption.textContent = button.dataset.busy;
  setOutcome(outcome, "busy", busyText);
  try {
    setOutcome(outcome, "ok", await action());
  } catch (error) {
    setOutcome(outcome, "error", error.message);
  } finally {
    button.removeAttribute("aria-busy");
    if (caption) caption.textContent = idleCaption;
    button.disabled = false;
    updateGates();
  }
}

/** A Delete button that arms on the first click and acts on a second, separate click within 5 s. */
function confirmFirst(button, name, action) {
  let armedAt = 0;
  let timer = null;
  const show = (armed) => {
    button.textContent = armed ? "Confirm" : "Delete";
    button.setAttribute("aria-label", (armed ? "Confirm delete of " : "Delete ") + name);
    if (armed) button.dataset.armed = "yes";
    else delete button.dataset.armed;
  };
  button.dataset.arm = "";
  show(false);
  button.addEventListener("click", (event) => {
    if (button.dataset.armed !== "yes") {
      armedAt = event.timeStamp;
      show(true);
      timer = setTimeout(() => show(false), 5000);
      return;
    }
    // the second click of the double-click that armed the button does not confirm
    if (event.detail > 1 && event.timeStamp - armedAt < 600) return;
    clearTimeout(timer);
    show(false);
    action();
  });
}

function deleteButton(name, action) {
  const button = element("button", "p-btn p-btn-sm");
  button.type = "button";
  confirmFirst(button, name, action);
  return button;
}

function badge(status, ...content) {
  const node = element("span", "p-badge");
  node.dataset.status = status;
  node.append(element("i"), ...content);
  return node;
}

function formatBytes(bytes) {
  const units = ["B", "KB", "MB", "GB", "TB"];
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return (unit === 0 ? String(value) : value.toFixed(1)) + " " + units[unit];
}

function clock(seconds) {
  const whole = Math.floor(seconds || 0);
  return Math.floor(whole / 60) + ":" + String(whole % 60).padStart(2, "0");
}

function elapsed(started) {
  const seconds = Math.round((performance.now() - started) / 1000);
  return seconds < 60 ? seconds + " s" : Math.floor(seconds / 60) + " min " + (seconds % 60) + " s";
}

/** The playing time of an audio file the browser can read, or null. */
function mediaSeconds(file) {
  return new Promise((resolve) => {
    const media = new Audio();
    const url = URL.createObjectURL(file);
    const done = (seconds) => {
      URL.revokeObjectURL(url);
      resolve(seconds);
    };
    media.addEventListener("loadedmetadata", () => done(Number.isFinite(media.duration) ? media.duration : null));
    media.addEventListener("error", () => done(null));
    media.src = url;
  });
}

const checked = (group) => {
  const input = document.querySelector(`input[name="${group}"]:checked`);
  return input ? input.value : null;
};

/* Login and the shell */

function showBanner(content, kind = "error") {
  const banner = $("login-banner");
  banner.dataset.kind = kind;
  $("login-banner-text").replaceChildren(...[content].flat());
  banner.hidden = !$("login-banner-text").textContent;
}

function showLogin(message, kind = "error") {
  clearInterval(healthTimer);
  healthTimer = null;
  if (asrWaiter) asrWaiter.reject(new Error("logged out while waiting for the transcription model"));
  asrWaiter = null;
  closeMenu();
  $("app-section").hidden = true;
  $("login-section").hidden = false;
  showBanner(message, kind);
  $("api-token-value").value = "";
  $("api-token-new").hidden = true;
  $("login-password").focus();
}

function showApp() {
  $("login-section").hidden = true;
  $("app-section").hidden = false;
  showBanner("");
  // an error written while the login box showed belongs to the old session
  for (const out of document.querySelectorAll("#app-section .p-out")) setOutcome(out);
  route();
  loadSettings();
  loadVoices();
  loadTokens();
  pollHealth();
  if (healthTimer === null) healthTimer = setInterval(pollHealth, 2000);
}

async function checkSession() {
  try {
    const response = await fetch("/session");
    if (response.ok && (await response.json()).authenticated) {
      showApp();
      return;
    }
  } catch {
    // the service is not reachable; the login box is the screen to show
  }
  showLogin("");
}

/** Show the page and Settings tab of the address: #/render, #/transcribe or #/settings/<tab>. */
function route() {
  const [name, tab] = location.hash.replace(/^#\/?/, "").split("/");
  const page = Object.hasOwn(PAGES, name) ? name : "render";
  const section = page === "settings" ? (Object.hasOwn(TABS, tab) ? tab : "hf") : "";
  for (const key of Object.keys(PAGES)) $("page-" + key).hidden = key !== page;
  for (const key of Object.keys(TABS)) $("set-" + key).hidden = key !== section;
  for (const link of document.querySelectorAll("[data-nav]")) markCurrent(link, link.dataset.nav === page);
  for (const link of document.querySelectorAll("[data-tab]")) markCurrent(link, link.dataset.tab === section);
  $("crumb-group").hidden = $("crumb-sep").hidden = page === "settings";
  $("crumb-title").textContent = PAGES[page];
  document.title = [PAGES[page], TABS[section], "Leftenant Voice"].filter(Boolean).join(" · ");
  closeMenu();
  // the loaded state of the models changes with use, so the Models tab reads it each time it opens
  if (section === "models" && !$("app-section").hidden) loadModels();
}

function closeMenu() {
  $("account-menu").hidden = true;
  $("account-button").setAttribute("aria-expanded", "false");
}

/* Model states from /health, polled every 2 s */

const LOADING = { downloading: ["live", "downloading"], loading: ["live", "loading"], error: ["error", "error"] };

function setBadge(kind, status, word, name, title) {
  for (const node of document.querySelectorAll(`[data-badge="${kind}"]`)) {
    node.dataset.status = status;
    node.querySelector("b").textContent = word;
    if (name) node.querySelector("span").textContent = name;
    node.title = title;
  }
}

function renderHealth(data) {
  health = data;
  const asr = data.asr || {};
  const facts = [data.engine ? label(data.engine) + " loaded" : "no engine loaded", data.busy ? "busy" : "not busy"];
  if (data.seconds_until_unload !== null && data.seconds_until_unload !== undefined) {
    facts.push("unloads in " + data.seconds_until_unload + " s");
  }
  if (data.error) facts.push(data.error);
  const speech = data.busy ? ["live", "speaking"] : LOADING[data.state] || (data.loaded ? ["ok", "ready"] : ["idle", "not loaded"]);
  setBadge("speech", ...speech, "Speech · " + label(data.engine || defaultEngine || "engine"), facts.join(" · "));
  const transcription = !asr.available ? ["idle", "not installed"] : asr.state === "ready" ? ["ok", "ready"]
    : LOADING[asr.state] || ["idle", "not loaded"];
  setBadge("asr", ...transcription, "", asr.error || "");
  if (asrWaiter && asr.state === "error") {
    asrWaiter.reject(new Error(asr.error || "the transcription model failed to load"));
    asrWaiter = null;
  } else if (asrWaiter && (asr.state === "ready" || asr.state === "down")) {
    asrWaiter.resolve();
    asrWaiter = null;
  }
  showEngineHint();
  showSteps();
  updateGates();
}

async function pollHealth() {
  try {
    const response = await fetch("/health", { cache: "no-store" });
    if (!response.ok) throw new Error("health request failed");
    renderHealth(await response.json());
  } catch {
    health = null;
    setBadge("speech", "error", "not reachable", "", "the service did not answer /health");
    setBadge("asr", "idle", "unknown", "", "");
    showEngineHint();
    updateGates();
  }
}

/** Enable Render with text, a voice and an idle service, and Transcribe with a recording; never while they run. */
function updateGates() {
  const speak = $("speak-button");
  if (!speak.hasAttribute("aria-busy")) {
    speak.disabled = Boolean(health && health.busy) || !$("speak-text").value.trim() || !checked("voice");
  }
  const transcribe = $("transcribe-button");
  if (!transcribe.hasAttribute("aria-busy")) transcribe.disabled = !$("transcribe-file").files.length;
}

/* Voice rendering */

function showEngineHint() {
  const hint = $("engine-hint");
  const chosen = checked("engine");
  let text = "";
  if (health && chosen) {
    if (health.state === "error") text = health.error || "the speech model failed to load";
    else if (LOADING[health.state]) text = "The speech model is " + health.state + "; a render waits for it.";
    else if (health.engine && chosen !== health.engine) {
      text = label(chosen) + " is not loaded; the first render loads it and unloads " + label(health.engine) + ".";
    } else if (!health.engine) text = label(chosen) + " is not loaded; the first render loads it.";
  }
  hint.textContent = text;
  hint.dataset.kind = health && health.state === "error" ? "error" : "";
  hint.hidden = !text;
}

function radio(group, value, text, isChecked) {
  const input = Object.assign(document.createElement("input"), { type: "radio", name: group, value, checked: isChecked });
  const choice = document.createElement("label");
  choice.append(input, text);
  return choice;
}

function fillEngines() {
  const names = Object.keys(voices);
  const pick = names.includes(chosenEngine) ? chosenEngine : names.includes(defaultEngine) ? defaultEngine : names[0];
  $("engine-seg").replaceChildren(...names.map((name) => radio("engine", name, label(name), name === pick)));
  fillVoiceCards();
}

function fillVoiceCards() {
  const names = voices[checked("engine")] || [];
  const previous = checked("voice");
  const pick = names.includes(previous) ? previous : names[0];
  $("voice-cards").replaceChildren(...names.map((name) => {
    const card = radio("voice", name, "", name === pick);
    card.className = "p-voice";
    const text = element("span", "p-voice-text");
    text.append(element("span", "p-voice-name", name),
      element("span", "p-voice-meta", uploaded.includes(name) ? "Cloned voice" : "Bundled voice"));
    card.append(element("span", "p-tile", name.charAt(0).toUpperCase()), text, element("span", "p-radio"));
    card.querySelector(".p-tile").setAttribute("aria-hidden", "true");
    card.querySelector(".p-radio").setAttribute("aria-hidden", "true");
    return card;
  }));
  showEngineHint();
  updateGates();
}

function updateCount() {
  const length = $("speak-text").value.length;
  const limit = $("speak-text").maxLength;
  $("speak-count").textContent = limit > 0 ? length + " / " + limit : length + " characters";
}

/* The player: a drawn waveform over an <audio> element */

const player = $("player");
const bars = Array.from({ length: BARS }, () => element("span"));
$("wave").replaceChildren(...bars);

function paintPlayer() {
  const total = Number.isFinite(player.duration) ? player.duration : 0;
  const lit = total ? Math.round((player.currentTime / total) * BARS) : 0;
  bars.forEach((bar, index) => bar.classList.toggle("on", index < lit));
  $("play-time").textContent = clock(player.currentTime) + " / " + clock(total);
  const playing = !player.paused && !player.ended;
  $("play-button").classList.toggle("is-playing", playing);
  $("play-button").setAttribute("aria-label", playing ? "Pause" : "Play");
}

/** The bar heights of a render: its peak level in each of BARS slices; flat when the browser cannot decode it. */
async function peaks(blob) {
  try {
    const audio = await new OfflineAudioContext(1, 1, 44100).decodeAudioData(await blob.arrayBuffer());
    const samples = audio.getChannelData(0);
    const step = Math.max(1, Math.floor(samples.length / BARS));
    const levels = bars.map((_, index) => {
      let peak = 0;
      for (let i = index * step; i < Math.min(samples.length, (index + 1) * step); i += 1) peak = Math.max(peak, Math.abs(samples[i]));
      return peak;
    });
    const top = Math.max(...levels) || 1;
    return levels.map((level) => level / top);
  } catch {
    return bars.map(() => 0);
  }
}

/** The download name of a render: its voice and the local clock time it finished, as `grimaldus-1259.mp3`. */
function mp3Name(render) {
  const clockTime = render.time.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
  return `${render.voice}-${clockTime.replace(":", "")}.mp3`;
}

async function showRender(render, autoplay) {
  current = render;
  player.src = render.url;
  Object.assign($("download"), { href: render.url, download: mp3Name(render) });
  $("result-facts").textContent = [render.voice, label(render.engine), render.text.length + " characters"].join(" · ");
  render.levels = render.levels || await peaks(render.blob);
  bars.forEach((bar, index) => { bar.style.height = Math.round(12 + 88 * render.levels[index]) + "%"; });
  setState($("render-result"), "done");
  paintPlayer();
  if (autoplay) player.play().catch(() => {});  // a refused autoplay leaves the play button to start it
  showSessionRenders();
}

function showSessionRenders() {
  $("recent-empty").hidden = renders.length > 0;
  $("recent-list").hidden = renders.length === 0;
  $("recent-count").hidden = renders.length === 0;
  $("recent-count").textContent = renders.length + (renders.length === 1 ? " render" : " renders");
  $("recent-list").replaceChildren(...renders.map((render) => {
    const item = element("li");
    const play = element("button", "p-icon-btn");
    play.type = "button";
    play.setAttribute("aria-label", "Play this render");
    play.append(icon("i-play"));
    play.addEventListener("click", () => showRender(render, true));
    const main = element("div", "p-li-main");
    const title = render.text.length > 60 ? render.text.slice(0, 60).trimEnd() + "…" : render.text;
    const time = render.time.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
    main.append(element("div", "p-li-title", title),
      element("div", "p-li-meta", [render.voice, render.seconds ? clock(render.seconds) : null, time].filter(Boolean).join(" · ")));
    const download = element("a", "p-icon-btn");
    Object.assign(download, { href: render.url, download: mp3Name(render) });
    download.setAttribute("aria-label", "Download MP3");
    download.append(icon("i-down"));
    item.append(play, main, download);
    return item;
  }));
}

/** Empty this session's renders and transcript, as a logout does. */
function forgetSession() {
  player.pause();
  player.removeAttribute("src");
  for (const render of renders.splice(0)) URL.revokeObjectURL(render.url);
  current = null;
  setState($("render-result"), "empty");
  showSessionRenders();
  setState($("transcript"), "empty");
}

/* Transcription */

function setStep(id, state, shown = true) {
  const step = $(id);
  step.hidden = !shown;
  if (state) step.dataset.step = state;
  else delete step.dataset.step;
}

/** Show the steps and the running line of a transcription from its phase and the model state in /health. */
function showSteps() {
  if (!transcribePhase) return;
  const state = health && health.asr ? health.asr.state : "";
  if (state === "downloading") sawDownload = true;
  const waiting = transcribePhase === "wait";
  const upload = transcribePhase === "upload" ? "active" : sent ? "done" : "";
  setStep("step-upload", upload);
  $("step-upload").querySelector("strong").textContent = { active: "Uploading", done: "Uploaded" }[upload] || "Upload";
  setStep("step-download", waiting && state === "downloading" ? "active" : "done", sawDownload);
  setStep("step-load", waiting && state === "downloading" ? "" : waiting ? "active" : "done", sawWait);
  setStep("step-transcribe", transcribePhase === "process" && state === "ready" ? "active" : "");
  const line = transcribePhase === "upload" ? "Uploading the recording…"
    : transcribePhase === "process" ? (state === "ready" ? "Transcribing… this can take minutes" : "Starting the transcription model…")
      : sawDownload ? "Waiting for the transcription model to download and load…"
        : "Waiting for the transcription model to load…";
  setOutcome($("transcribe-outcome"), "busy", line);
}

function phase(name) {
  transcribePhase = name;
  showSteps();
}

/** Wait until /health reports the transcription model ready, or down so a new request starts its load again. */
function waitForModel() {
  sawWait = true;
  phase("wait");
  const waiting = new Promise((resolve, reject) => {
    asrWaiter = { resolve, reject };
  });
  pollHealth();  // the 503 started the load; show its state now rather than at the next poll
  return waiting;
}

/** Send the recording when the model is ready: a 503 with Retry-After means the model loads, so the page waits for
 * /health to report it ready and sends the recording again. */
async function transcribeWhenReady(file) {
  for (let attempt = 0; attempt < MAX_TRANSCRIBE_ATTEMPTS; attempt += 1) {
    const state = health && health.asr ? health.asr.state : "";
    if (state === "downloading" || state === "loading") await waitForModel();
    const body = new FormData();
    body.append("file", file);
    body.append("language", $("transcribe-language").value);
    body.append("wording", checked("wording"));
    const context = $("transcribe-context").value.trim();
    if (context) body.append("context", context);
    phase("upload");
    try {
      return await (await upload("/transcribe", body, () => {
        sent = true;
        phase("process");
      })).json();
    } catch (error) {
      if (error.status !== 503 || !error.retryAfter) throw error;
      await waitForModel();
    }
  }
  throw new Error("the transcription model did not stay ready; press Transcribe again");
}

function showTranscript(result, file) {
  const text = result.text || "";
  $("transcribe-result").textContent = text;
  const words = (text.match(/\S+/g) || []).length;
  const chips = [result.language === "as spoken" ? "as spoken" : result.language, result.wording,
    recordingSeconds ? clock(recordingSeconds) : null, words.toLocaleString("en-GB") + (words === 1 ? " word" : " words")];
  $("transcript-chips").replaceChildren(...chips.filter(Boolean).map((chip) => element("span", "p-chip", chip)));
  if (transcriptUrl) URL.revokeObjectURL(transcriptUrl);
  transcriptUrl = URL.createObjectURL(new Blob([text], { type: "text/plain;charset=utf-8" }));
  Object.assign($("transcript-download"), { href: transcriptUrl, download: file.name.replace(/\.[^.]*$/, "") + ".txt" });
}

async function showRecording() {
  const file = $("transcribe-file").files[0];
  $("drop").hidden = Boolean(file);
  $("transcribe-chosen").hidden = !file;
  recordingSeconds = null;
  updateGates();
  if (!file) return;
  $("transcribe-file-name").textContent = file.name;
  $("transcribe-file-facts").textContent = formatBytes(file.size);
  const seconds = await mediaSeconds(file);
  if ($("transcribe-file").files[0] !== file) return;
  recordingSeconds = seconds;
  if (seconds !== null) $("transcribe-file-facts").textContent = formatBytes(file.size) + " · " + clock(seconds);
}

/** Copy `text`; a frame without the clipboard-write permission refuses the API, where a copy of the selection still
 * works. The button's caption says how it went. */
async function copyText(button, text, select) {
  const caption = button.lastElementChild;
  try {
    await navigator.clipboard.writeText(text);
    caption.textContent = "Copied";
  } catch {
    select();
    caption.textContent = document.execCommand("copy") ? "Copied" : "Press Ctrl+C";
  }
  setTimeout(() => { caption.textContent = "Copy"; }, 2500);
}

/* Settings */

function showTokenState(set, account) {
  const state = $("token-state");
  if (!set) state.replaceWith(Object.assign(badge("idle", "Not set"), { id: "token-state" }));
  else if (account) {
    state.replaceWith(Object.assign(badge("ok", "Saved · account ", element("b", "", account)), { id: "token-state" }));
  } else state.replaceWith(Object.assign(badge("info", "Set in the service environment"), { id: "token-state" }));
}

async function loadSettings() {
  try {
    const settings = await (await api("/settings")).json();
    defaultEngine = settings.default_engine || null;
    showTokenState(settings.hf_token_set, settings.hf_account);
    if (settings.max_text_chars) {
      $("speak-text").maxLength = settings.max_text_chars;
      $("speak-outcome").dataset.idle = "Up to " + settings.max_text_chars + " characters per render.";
      if (!$("speak-outcome").querySelector("[data-kind]")) setOutcome($("speak-outcome"));
    }
    updateCount();
    fillEngines();
  } catch (error) {
    setOutcome($("token-outcome"), "error", "The settings did not load: " + error.message);
  }
}

async function loadVoices() {
  try {
    const data = await (await api("/voices")).json();
    voices = data.voices || {};
    uploaded = data.uploaded || [];
    fillEngines();
    const names = [...new Set(Object.values(voices).flat())].sort();
    const rows = names.map((name) => {
      const row = element("li");
      const main = element("div", "p-li-main");
      const cloned = uploaded.includes(name);
      main.append(element("div", "p-li-title", name), element("div", "p-li-meta",
        !cloned ? "Bundled with the service" : name === freshVoice ? "Cloned just now" : "Cloned voice"));
      const tile = element("span", "p-tile", name.charAt(0).toUpperCase());
      tile.setAttribute("aria-hidden", "true");
      row.append(tile, main);
      if (!cloned) row.append(element("span", "p-chip", "bundled"));
      else {
        if (name === freshVoice) row.dataset.fresh = "";
        const button = deleteButton(name, () => run(button, $("voice-list-outcome"), "Deleting " + name + "…", async () => {
          await api("/voices/" + encodeURIComponent(name), { method: "DELETE" });
          await loadVoices();
          return "Deleted " + name;
        }));
        row.append(button);
      }
      return row;
    });
    if (uploaded.length === 0) rows.push(element("li", "p-muted", "No cloned voices yet."));
    $("voice-list").replaceChildren(...rows);
  } catch (error) {
    setOutcome($("speak-outcome"), "error", "The voices did not load: " + error.message);
    setOutcome($("voice-list-outcome"), "error", "The voices did not load: " + error.message);
  }
}

async function loadTokens() {
  try {
    const list = (await (await api("/tokens")).json()).tokens || [];
    $("api-token-empty").hidden = list.length > 0;
    $("api-token-table").hidden = list.length === 0;
    $("api-token-list").replaceChildren(...list.map((token) => {
      const row = element("div", "p-tr");
      row.setAttribute("role", "row");
      const created = new Date(token.created);
      const cells = [element("span", "p-strong", token.name), element("span", "p-mono", "vtts_" + token.prefix + "…"),
        element("span", "", Number.isNaN(created.getTime()) ? token.created
          : created.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })), element("span")];
      const button = deleteButton(token.name, () => run(button, $("api-token-list-outcome"), "Deleting " + token.name + "…",
        async () => {
          await api("/tokens/" + encodeURIComponent(token.name), { method: "DELETE" });
          await loadTokens();
          return "Deleted " + token.name + "; requests with it are refused from now on";
        }));
      cells[3].append(button);
      for (const cell of cells) cell.setAttribute("role", "cell");
      row.append(...cells);
      return row;
    }));
  } catch (error) {
    setOutcome($("api-token-list-outcome"), "error", "The tokens did not load: " + error.message);
  }
}

async function loadModels() {
  try {
    const list = (await (await api("/models")).json()).models || [];
    // a row keeps its outcome line across the refresh that follows its Delete
    const kept = {};
    for (const out of $("model-list").querySelectorAll(".p-out[data-model]")) kept[out.dataset.model] = out;
    $("model-list").replaceChildren(...list.map((model) => {
      const row = element("li", "p-model");
      const main = element("div", "p-li-main");
      const meta = element("div", "p-model-meta");
      meta.append(element("span", "p-strong", label(model.name)), model.loaded ? badge("ok", "Loaded")
        : model.cached ? badge("info", "Cached") : badge("idle", "Not downloaded"));
      const out = kept[model.name] || element("p", "p-out");
      out.dataset.model = model.name;
      out.setAttribute("role", "status");
      out.setAttribute("aria-live", "polite");
      main.append(meta, element("div", "p-li-meta p-mono", model.model), out);
      row.append(main, element("span", "p-size", formatBytes(model.bytes)));
      if (model.cached || model.loaded) {
        const button = deleteButton(model.name, () => run(button, out, "Deleting " + model.name + "…", async () => {
          const result = await (await api("/models/" + encodeURIComponent(model.name), { method: "DELETE" })).json();
          return "Deleted " + result.deleted + ": " + formatBytes(result.freed_bytes) +
            " freed. The next use downloads the model again.";
        }).then(() => {
          loadModels();
          pollHealth();
        }));
        row.append(button);
      }
      return row;
    }));
    const total = list.reduce((sum, model) => sum + model.bytes, 0);
    setOutcome($("models-total"), "", formatBytes(total) + " on disk.");
  } catch (error) {
    setOutcome($("model-list-outcome"), "error", "The models did not load: " + error.message);
  }
}

/* Buttons */

$("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = $("login-button");
  showBanner("");
  delete $("login-section").dataset.state;
  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  button.lastElementChild.textContent = "Logging in…";
  try {
    await postJson("/login", { password: $("login-password").value });
    $("login-password").value = "";
    if ((await (await api("/session")).json()).authenticated) {
      showApp();
      return;
    }
    // the login was accepted but the cookie was dropped, as a browser does in a frame of another site
    showBanner([element("b", "", "The password was accepted, but this browser did not keep the session cookie."),
      " This happens when a page of another site frames this one, so every request is refused. Open this page from" +
      " the same site as the page that frames it, or ",
      Object.assign(element("a", "", "open the service in its own tab"),
        { href: location.href.split("#")[0], target: "_blank", rel: "noopener" }), "."]);
  } catch (error) {
    $("login-section").dataset.state = "refused";
    const sentence = error.message.charAt(0).toUpperCase() + error.message.slice(1) + (/[.!?]$/.test(error.message) ? "" : ".");
    showBanner([element("b", "", sentence), error.status === 401 ? " Check it and try again." : ""]);
  } finally {
    button.disabled = false;
    button.removeAttribute("aria-busy");
    button.lastElementChild.textContent = "Log in";
  }
});

$("account-button").addEventListener("click", () => {
  const open = $("account-menu").hidden;
  $("account-menu").hidden = !open;
  $("account-button").setAttribute("aria-expanded", String(open));
  if (open) $("logout-button").focus();
});
document.addEventListener("click", (event) => {
  if (!event.target.closest(".p-account-wrap")) closeMenu();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !$("account-menu").hidden) {
    closeMenu();
    $("account-button").focus();
  }
});

$("logout-button").addEventListener("click", async () => {
  try {
    await fetch("/logout", { method: "POST" });
  } catch {
    // the service is gone and the session with it; the login box is the screen to show
  }
  forgetSession();
  showLogin("Logged out.", "info");
});

$("speak-text").addEventListener("input", () => {
  updateCount();
  updateGates();
});
$("engine-seg").addEventListener("change", () => {
  chosenEngine = checked("engine");
  fillVoiceCards();
});
$("voice-cards").addEventListener("change", updateGates);

$("speak-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const text = $("speak-text").value.trim();
  const voice = checked("voice");
  const engine = checked("engine");
  const card = $("render-result");
  const before = card.dataset.state;
  const started = performance.now();
  $("render-running-voice").textContent = "Rendering in " + voice;
  $("render-running-engine").textContent = label(engine);
  player.pause();
  setState(card, "running");
  run($("speak-button"), $("speak-outcome"), "Rendering… this takes about a minute", async () => {
    try {
      const blob = await (await postJson("/speak", { text, voice, engine })).blob();
      const render = { blob, url: URL.createObjectURL(blob), text, voice, engine, time: new Date() };
      renders.unshift(render);
      await showRender(render, true);
      reveal(card);
      return "Done in " + elapsed(started);
    } catch (error) {
      setState(card, before);
      throw error;
    }
  });
});

$("play-button").addEventListener("click", () => {
  if (player.paused) player.play().catch(() => {});
  else player.pause();
});
for (const name of ["timeupdate", "play", "pause", "ended"]) player.addEventListener(name, paintPlayer);
player.addEventListener("loadedmetadata", () => {
  if (current && Number.isFinite(player.duration)) {
    current.seconds = player.duration;
    showSessionRenders();
  }
  paintPlayer();
});

for (const button of document.querySelectorAll("[data-pick]")) {
  button.addEventListener("click", () => $(button.dataset.pick).click());
}
// a click on the box opens the picker; the inner button opens it on its own
$("drop").addEventListener("click", (event) => {
  if (!event.target.closest("[data-pick]")) $("transcribe-file").click();
});
$("transcribe-file").addEventListener("change", showRecording);
$("transcribe-unpick").addEventListener("click", () => {
  $("transcribe-file").value = "";
  showRecording();
});
/** Whether a drag carries files, as opposed to text or a link. */
const carriesFiles = (event) => event.dataTransfer && [...event.dataTransfer.types].includes("Files");

// a file dropped outside the drop box would be opened by the browser and replace the portal
for (const name of ["dragover", "drop"]) {
  document.addEventListener(name, (event) => { if (carriesFiles(event)) event.preventDefault(); });
}
$("page-transcribe").addEventListener("dragover", (event) => {
  if (!carriesFiles(event)) return;
  event.preventDefault();
  $("transcribe-form").dataset.over = "yes";
});
$("page-transcribe").addEventListener("dragleave", () => delete $("transcribe-form").dataset.over);
$("page-transcribe").addEventListener("drop", (event) => {
  if (!carriesFiles(event)) return;
  event.preventDefault();
  delete $("transcribe-form").dataset.over;
  if (event.dataTransfer.files.length) {
    $("transcribe-file").files = event.dataTransfer.files;
    showRecording();
  }
});

$("transcribe-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const file = $("transcribe-file").files[0];
  const card = $("transcript");
  const before = card.dataset.state;
  const started = performance.now();
  run($("transcribe-button"), $("transcribe-outcome"), "Uploading the recording…", async () => {
    if (!file) throw new Error("choose a recording first");
    $("step-upload-facts").textContent = file.name + " · " + formatBytes(file.size);
    sawDownload = false;
    sawWait = false;
    sent = false;
    setState(card, "running");
    try {
      const result = await transcribeWhenReady(file);
      showTranscript(result, file);
      setState(card, "done");
      reveal(card);
      return "Done in " + elapsed(started);
    } catch (error) {
      setState(card, before);
      throw error;
    } finally {
      transcribePhase = null;
    }
  });
});

$("transcript-copy").addEventListener("click", () => copyText($("transcript-copy"), $("transcribe-result").textContent,
  () => getSelection().selectAllChildren($("transcribe-result"))));

$("token-form").addEventListener("submit", (event) => {
  event.preventDefault();
  run($("token-save"), $("token-outcome"), "Checking the token with Hugging Face…", async () => {
    const token = $("token-input").value.trim();
    if (!token) throw new Error("enter a token first; Clear removes the saved one");
    const result = await (await postJson("/settings/hf-token", { token })).json();
    $("token-input").value = "";
    showTokenState(result.hf_token_set, result.hf_account);
    return "Saved: the token belongs to " + result.hf_account;
  });
});

$("token-clear").addEventListener("click", () => {
  run($("token-clear"), $("token-outcome"), "Clearing…", async () => {
    const result = await (await postJson("/settings/hf-token", { token: "" })).json();
    showTokenState(result.hf_token_set, result.hf_account);
    return "Cleared";
  });
});

$("api-token-form").addEventListener("submit", (event) => {
  event.preventDefault();
  run($("api-token-create"), $("api-token-outcome"), "Creating…", async () => {
    const created = await (await postJson("/tokens", { name: $("api-token-name").value.trim() })).json();
    $("api-token-value").value = created.token;
    $("api-token-new-name").textContent = "Token " + created.name + " created.";
    $("api-token-new").hidden = false;
    $("api-token-name").value = "";
    await loadTokens();
    return "Created " + created.name;
  });
});

$("api-token-copy").addEventListener("click", () => copyText($("api-token-copy"), $("api-token-value").value,
  () => $("api-token-value").select()));

$("upload-file").addEventListener("change", async () => {
  const file = $("upload-file").files[0];
  const name = $("upload-file-name");
  name.textContent = file ? file.name : "No file chosen";
  name.dataset.set = file ? "yes" : "";
  if (!file) return;
  const seconds = await mediaSeconds(file);
  if (seconds !== null && $("upload-file").files[0] === file) name.textContent = file.name + " · " + seconds.toFixed(1) + " s";
});

$("upload-form").addEventListener("submit", (event) => {
  event.preventDefault();
  run($("upload-button"), $("upload-outcome"), "Cloning…", async () => {
    const file = $("upload-file").files[0];
    if (!file) throw new Error("choose a reference WAV first");
    const body = new FormData();
    body.append("name", $("upload-name").value.trim());
    body.append("text", $("upload-text").value.trim());
    body.append("file", file);
    const result = await (await api("/voices", { method: "POST", body })).json();
    $("upload-form").reset();
    $("upload-file").dispatchEvent(new Event("change"));
    freshVoice = result.name;
    await loadVoices();
    return "Cloned " + result.name + "; choose it on Voice rendering";
  });
});

window.addEventListener("hashchange", route);

setState($("render-result"), "empty");
setState($("transcript"), "empty");
showSessionRenders();
updateGates();
checkSession();
