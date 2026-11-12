"""One synthesis at a time: two requests with a slow stub never overlap."""
import threading
import time

import app
from fastapi.testclient import TestClient


def test_one_synthesis_at_a_time(client, engines):
    engine = engines["alpha"]
    engine.delay = 0.3
    sid = client.cookies["sid"]
    responses = []

    def ask():
        own = TestClient(app.app)
        own.cookies.set("sid", sid)
        responses.append(own.post("/speak", json={"text": "hello", "voice": "grimaldus"}))

    threads = [threading.Thread(target=ask) for _ in range(2)]
    started = time.monotonic()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    elapsed = time.monotonic() - started
    assert [response.status_code for response in responses] == [200, 200]
    assert engine.max_active == 1
    assert elapsed >= 0.55  # the two 0.3 s syntheses ran one after the other
