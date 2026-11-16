"""Offline acceptance check (docs/architecture.md section 7).

Runs every mode (search, explain, practice, progress, a review session) and starts the web page,
while listing the network sockets of Ollama and the AI TA every half second, and reports any
connection to another machine. The web step loads the page and every asset it links to; whether
the browser itself fetches anything else was checked in a browser (architecture.md section 7).
Practice answers go to a temporary learner folder, so the real practice history is untouched.

Run it from the repo root, once with the network on and once with Wi-Fi turned off:

    ../.venv/bin/python dev/tools/offline_check.py

The report is printed and also saved to data/logs/offline-check-<time>.txt (not in Git).
Exit status 0 means every mode worked and no outside connection was seen.
"""

from __future__ import annotations

import os
import re
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LOCAL = re.compile(r"^(127\.0\.0\.1|\[::1\]|localhost|\*)(:|$)")
STEPS = [
    ("search", ["search", "資訊增益怎麼算？"], None),
    ("explain", ["ask", "決策樹的資訊增益為什麼會偏好值很多的特徵？"], None),
    ("practice", ["quiz", "--topic", "決策樹 資訊增益", "--n", "1"],
     "資訊增益是分割前的熵減去分割後的加權熵，選增益最大的特徵。\n"),
    ("progress", ["progress"], None),
    ("review", ["review"], "我想練決策樹\n資訊增益是分割前的熵減去分割後的加權熵，選增益最大的特徵。\n進度\n結束\n"),
]
ASSET = re.compile(r'(?:src|href)="(/[^"]+)"')
OUTSIDE = re.compile(r'(?:src|href)="(https?://[^"]+)"')


def network_reachable() -> bool:
    """Whether this machine can reach the internet at all (the test condition, not the AI TA)."""
    try:
        socket.create_connection(("1.1.1.1", 443), timeout=2).close()
        return True
    except OSError:
        return False


def watched_pids() -> set[str]:
    out = subprocess.run(["pgrep", "-f", "Ollama.app|ollama serve|ai_ta"], capture_output=True, text=True).stdout
    return set(out.split())


class Watcher(threading.Thread):
    def __init__(self) -> None:
        super().__init__(daemon=True)
        self.found: dict[tuple[str, str], int] = {}
        self.samples = 0
        self.stop = threading.Event()

    def run(self) -> None:
        while not self.stop.is_set():
            pids = watched_pids()
            out = subprocess.run(["lsof", "-nP", "-i"], capture_output=True, text=True).stdout
            for line in out.splitlines()[1:]:
                cols = line.split()
                if len(cols) < 9 or cols[1] not in pids:
                    continue
                name = " ".join(cols[8:])
                if "->" in name:
                    remote = name.split("->", 1)[1].split()[0]
                    if not LOCAL.match(remote):
                        key = (cols[0], remote)
                        self.found[key] = self.found.get(key, 0) + 1
            self.samples += 1
            time.sleep(0.5)


def fetch(url: str) -> tuple[int, str]:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))   # never through a proxy
    try:
        with opener.open(url, timeout=10) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except (urllib.error.URLError, OSError) as exc:
        return getattr(exc, "code", 0) or 0, ""


def check_web(env: dict[str, str], report) -> bool:
    """Start the web page, load it and the assets it links to, and stop it."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    started = time.perf_counter()
    server = subprocess.Popen([sys.executable, "-m", "ai_ta", "web", "--port", str(port)], env=env, cwd=REPO,
                              stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    try:
        status, html = 0, ""
        while time.perf_counter() - started < 120 and status != 200:
            if server.poll() is not None:
                break
            time.sleep(1)
            status, html = fetch(base + "/")
        assets = sorted(set(ASSET.findall(html)))
        failed_assets = [a for a in assets if fetch(base + a)[0] != 200]
        outside = sorted(set(OUTSIDE.findall(html)))
        theme_status, theme = fetch(base + "/theme.css")
        google_fonts = "fonts.googleapis" in theme
        ok = status == 200 and theme_status == 200 and not failed_assets and not outside and not google_fonts
        report(f"== web: page {status}, {len(assets) - len(failed_assets)}/{len(assets)} assets, theme {theme_status}, "
               f"{time.perf_counter() - started:.1f} s")
        report(f"   outside links in the page: {', '.join(outside) or 'none'}; Google fonts in the theme: "
               f"{'yes' if google_fonts else 'no'}")
        if failed_assets:
            report("   failed assets: " + ", ".join(failed_assets[:5]))
        if status != 200 and server.poll() is not None:
            report("   stderr: " + (server.stderr.read() or "")[-400:])
        return ok
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()


def main() -> int:
    lines: list[str] = []

    def report(text: str = "") -> None:
        print(text)
        lines.append(text)

    report(f"offline check {datetime.now():%Y-%m-%d %H:%M}")
    report(f"internet reachable: {'yes' if network_reachable() else 'no (offline run)'}")
    env = {**os.environ, "PYTHONPATH": str(REPO / "dev" / "src"), "COLUMNS": "160",
           "AI_TA_LEARNER_DIR": tempfile.mkdtemp(prefix="ai-ta-offline-")}
    watcher = Watcher()
    watcher.start()
    failed = []
    for label, args, stdin in STEPS:
        started = time.perf_counter()
        result = subprocess.run([sys.executable, "-m", "ai_ta", *args], input=stdin, capture_output=True,
                                text=True, env=env, cwd=REPO)
        report(f"== {label}: exit {result.returncode}, {time.perf_counter() - started:.1f} s")
        for line in (result.stdout.strip().splitlines() or ["(no output)"])[-4:]:
            report("   " + line[:150])
        if result.returncode:
            failed.append(label)
            report("   stderr: " + result.stderr.strip()[-400:])
    if not check_web(env, report):
        failed.append("web")
    watcher.stop.set()
    watcher.join()
    report(f"network samples: {watcher.samples}")
    report("outside connections: " + ("none" if not watcher.found else ""))
    for (process, remote), count in sorted(watcher.found.items()):
        report(f"   {process} -> {remote} (seen in {count} samples)")
    report(f"result: {'PASS' if not failed and not watcher.found else 'FAIL'}"
           + (f" (failed: {', '.join(failed)})" if failed else ""))
    out = REPO / "data" / "logs" / f"offline-check-{datetime.now():%Y-%m-%d-%H%M}.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"saved {out.relative_to(REPO)}")
    return 0 if not failed and not watcher.found else 1


if __name__ == "__main__":
    raise SystemExit(main())
