import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

REF = ROOT / "tests" / "refserver" / "mtprotoproxy.py"
REF_SECRET = "0123456789abcdef0123456789abcdef"


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def _telegram_reachable() -> bool:
    try:
        socket.create_connection(("149.154.167.51", 443), timeout=5).close()
        return True
    except OSError:
        return False


def _start(tmp_path: Path, mask: bool):
    port = _free_port()
    cfg = tmp_path / f"config_{port}.py"
    cfg.write_text(
        f"PORT = {port}\n"
        f"USERS = {{'u': '{REF_SECRET}'}}\n"
        "MODES = {'classic': True, 'secure': True, 'tls': True}\n"
        "TLS_DOMAIN = 'www.google.com'\n"
        "USE_MIDDLE_PROXY = False\n"
        f"MASK = {mask}\n"
        "LISTEN_ADDR_IPV6 = None\n"
        "PREFER_IPV6 = False\n"  # upstream to Telegram over IPv4: v6 on CI/sandbox hosts was flaky

    )
    proc = subprocess.Popen([sys.executable, str(REF), str(cfg)], cwd=tmp_path,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            socket.create_connection(("127.0.0.1", port), timeout=1).close()
            return proc, port
        except OSError:
            if proc.poll() is not None:
                raise RuntimeError("reference server exited early")
            time.sleep(0.2)
    proc.kill()
    raise RuntimeError("reference server did not start")


@pytest.fixture(scope="session")
def telegram_online():
    if os.environ.get("TGPROXY_OFFLINE") == "1" or not _telegram_reachable():
        pytest.skip("Telegram DCs unreachable from this host")
    return True


@pytest.fixture(scope="session")
def refserver(tmp_path_factory, telegram_online):
    proc, port = _start(tmp_path_factory.mktemp("ref"), mask=False)
    yield port
    proc.terminate()
    proc.wait(10)


@pytest.fixture(scope="session")
def refserver_masked(tmp_path_factory, telegram_online):
    proc, port = _start(tmp_path_factory.mktemp("refm"), mask=True)
    yield port
    proc.terminate()
    proc.wait(10)
