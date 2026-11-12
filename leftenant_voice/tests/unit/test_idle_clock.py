"""A finished load restarts the idle countdown: a cold start's download must not unload the model at once."""
import time

import app


def test_a_finished_load_restarts_the_idle_countdown(engines):
    """After a load that outlasted IDLE_UNLOAD_SECONDS, /health reports a full idle window, not an expired one."""
    before = time.monotonic()
    app.last_request = before - 10_000
    app._switch_to(engines["alpha"])
    assert app.loaded_engine == "alpha"
    assert app.last_request >= before
