"""After both suites: no test service process, no test container and no test named volume remain."""
import os
import socket

import support

CONTAINERS = (support.CONTAINER, support.NO_NETWORK_CONTAINER)
VOLUMES = (support.COLD_VOLUME, support.EMPTY_VOLUME)


def test_no_test_service_process():
    """The native service's PID is gone and its port accepts no connection."""
    pid = int((support.W / "functional/native.pid").read_text())
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        pass
    else:
        raise AssertionError(f"the test service process {pid} is still alive")
    port = int((support.W / "functional/native.port").read_text())
    with socket.socket() as sock:
        assert sock.connect_ex(("127.0.0.1", port)) != 0, f"port {port} still accepts connections"


def test_no_test_container():
    """Docker lists no container under either test name."""
    for name in CONTAINERS:
        found = support.docker("ps", "-a", "--filter", f"name=^{name}$",
                               "--format", "{{.Names}}").stdout.split()
        assert found == [], f"container {name} remains"


def test_no_test_volume():
    """Docker lists neither named volume the container tests created."""
    listed = support.docker("volume", "ls", "--format", "{{.Name}}").stdout.split()
    remaining = [name for name in VOLUMES if name in listed]
    assert remaining == [], f"volumes remain: {remaining}"
