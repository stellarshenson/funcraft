"""A local stand-in for the page host and for the prayer counter, on port 8793, for src/sermon/test.py.

    python3 src/sermon/mock.py out/w40k-mechanicum-sermons

GET answers the files of the package under /user/konrad.jelen/, as the hub does: whole, without compression and with
the content type of the file name. /wrap answers a page that frames the sermon page without scripts, /hub a page that
frames it with the sandbox of the hub's welcome frame, which forbids downloads. Every package file carries the content
policy POLICY, the one the package needs from the hub, and nosniff, as the hub sends them. An address with ?noradio
gets the policy without the frame rule of the radio buttons. OPTIONS, POST and GET /api/report answer as the prayer
counter does: in the answer to a POST, count is the starts of the prayer by all readers and yours the starts of that
prayer by the reader; the report answers the reader's total over all prayers as count.
'Prayer to Omnissiah' answers 500, for the failed call. The real counter is never called.
"""
import json, mimetypes, pathlib, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
PACKAGE = pathlib.Path(sys.argv[1]).resolve()
WRAP = b'<!doctype html><body style="margin:0"><iframe sandbox="allow-same-origin" src="/user/konrad.jelen/index.html" style="width:100%;height:98vh;border:0"></iframe>'
HUB = WRAP.replace(b'sandbox="allow-same-origin"', b'sandbox="allow-same-origin allow-popups allow-popups-to-escape-sandbox allow-scripts"')
RADIO = "frame-src https://www.youtube-nocookie.com; "      # for the players of the radio buttons
POLICY = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; media-src 'self'; "
          "font-src 'self' data:; connect-src 'self' http://prayer-counter.example.test:8793; " + RADIO + "frame-ancestors 'self'")
counts = {"Chant to Omnissiah": 12340}                             # prayer: starts by all readers
yours = {"Chant to Omnissiah": 1, "Desecration of Flesh": 1}       # prayer: starts by the reader of the checks

class Handler(BaseHTTPRequestHandler):
    def answer(self, status, body=b"", kind="application/json", policy=None):
        self.send_response(status)
        if policy:
            self.send_header("Content-Security-Policy", policy)
            self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Access-Control-Allow-Origin", self.headers.get("Origin", "*"))
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        if self.path.startswith(("/wrap", "/hub")):
            return self.answer(200, WRAP if self.path.startswith("/wrap") else HUB, "text/html; charset=utf-8")
        if self.path.startswith("/api/report"):
            return self.answer(200, json.dumps({"count": sum(yours.values())}).encode())
        target = (PACKAGE / self.path.split("?")[0].removeprefix("/user/konrad.jelen/")).resolve()
        if not (target.is_relative_to(PACKAGE) and target.is_file()):
            return self.answer(404)
        policy = POLICY.replace(RADIO, "") if "noradio" in self.path else POLICY
        self.answer(200, target.read_bytes(), mimetypes.guess_type(target)[0] or "application/octet-stream", policy)
    def do_OPTIONS(self):
        self.answer(204)
    def do_POST(self):
        press = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        prayer = press["prayer"]
        if prayer == "Prayer to Omnissiah":
            return self.answer(500)
        if press["action"] == "start":
            counts[prayer], yours[prayer] = counts.get(prayer, 0) + 1, yours.get(prayer, 0) + 1
        self.answer(200, json.dumps({"prayer": prayer, "count": counts.get(prayer, 0), "yours": yours.get(prayer, 0)}).encode())
    def log_message(self, *args):
        pass

ThreadingHTTPServer(("127.0.0.1", 8793), Handler).serve_forever()
