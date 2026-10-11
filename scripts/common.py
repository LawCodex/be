"""Shared helpers for the LawCodex Belgium (Justel) scraper."""
from __future__ import annotations

import gzip
import os
import threading
import time
from pathlib import Path

import requests

BASE = "https://www.ejustice.just.fgov.be/cgi_loi/"
UA = "LawCodex/1.0 (+https://github.com/LawCodex)"
REPO = Path(__file__).resolve().parent.parent
RAW = Path(os.environ.get("LAWCODEX_RAW", REPO.parent / "_raw" / "be"))
CACHE = RAW / "cache"
LISTS = RAW / "lists"

_local = threading.local()
_lock = threading.Lock()
_last = [0.0]
MIN_INTERVAL = 0.25  # global minimum spacing between request starts (seconds)


def session() -> requests.Session:
    s = getattr(_local, "s", None)
    if s is None:
        s = requests.Session()
        s.headers["User-Agent"] = UA
        _local.s = s
    return s


def _throttle():
    with _lock:
        now = time.monotonic()
        wait = _last[0] + MIN_INTERVAL - now
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.monotonic()


def http(method: str, url: str, data=None, params=None, tries: int = 6) -> str:
    """GET/POST with retries + backoff; returns text decoded as cp1252 (Justel is Latin-1/cp1252)."""
    delay = 5
    for attempt in range(tries):
        _throttle()
        try:
            r = session().request(method, url, data=data, params=params, timeout=180)
            if r.status_code == 200 and r.content:
                return r.content.decode("cp1252", errors="replace")
            err = f"HTTP {r.status_code}"
        except requests.RequestException as e:  # noqa: PERF203
            err = repr(e)
        if attempt == tries - 1:
            raise RuntimeError(f"{url} {params or data}: {err}")
        time.sleep(delay)
        delay = min(delay * 2, 300)
    raise AssertionError


def cached(key: str, fetch) -> str:
    """Return cached text for key (relative path under CACHE), fetching it if missing."""
    p = CACHE / (key + ".html.gz")
    if p.exists():
        with gzip.open(p, "rt", encoding="utf-8") as f:
            return f.read()
    txt = fetch()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        f.write(txt)
    tmp.replace(p)
    return txt
