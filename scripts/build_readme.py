#!/usr/bin/env python3
"""Regenerate README.md with per-directory counts (and skip statistics from the manifest)."""
from __future__ import annotations

import collections
import json
from datetime import date
from pathlib import Path

from catalog import DIRS
from common import RAW, REPO


def count(path: Path) -> int:
    return sum(1 for _ in path.rglob("*.md")) if path.exists() else 0


def fmt(n: int) -> str:
    return f"{n:,}"


ROWS = [
    ("constitution", "Constitution (coordinated text of 17 February 1994)"),
    ("code", "Codes (one file per code, or per part/book where Justel splits the code)"),
    ("loi", "Lois / wetten (incl. loi communale, loi provinciale…)"),
    ("arrete-loi", "Arrêtés-lois / besluitwetten"),
    ("arrete-regent", "Arrêtés du Régent / regentsbesluiten"),
    ("arrete-royal", "Arrêtés royaux with force of law or coordinating laws (filtered, see below)"),
    ("accord", "Accords de coopération / samenwerkingsakkoorden"),
]
REGIONS = [
    ("flandre", "decret", "Flemish Community/Region — decrees"),
    ("wallonie", "decret", "Walloon Region — decrees"),
    ("communaute-francaise", "decret", "French Community — decrees"),
    ("communaute-germanophone", "decret", "German-speaking Community — decrees"),
    ("bruxelles", "ordonnance", "Brussels-Capital Region — ordinances"),
    ("bruxelles", "decret", "Brussels (COCOF / French Community Commission) — decrees"),
]


def main():
    fr, nl = DIRS["fr"], DIRS["nl"]
    lines = []
    tot = collections.Counter()
    for key, label in ROWS:
        a, b = count(REPO / "fr" / fr[key]), count(REPO / "nl" / nl[key])
        tot["fr"] += a
        tot["nl"] += b
        lines.append(f"| {label} | `{fr[key]}/` | `{nl[key]}/` | {fmt(a)} | {fmt(b)} |")
    for reg, cat, label in REGIONS:
        pf = f"{fr['regions']}/{fr[reg]}/{fr[cat]}"
        pn = f"{nl['regions']}/{nl[reg]}/{nl[cat]}"
        a, b = count(REPO / "fr" / pf), count(REPO / "nl" / pn)
        tot["fr"] += a
        tot["nl"] += b
        lines.append(f"| {label} | `{pf}/` | `{pn}/` | {fmt(a)} | {fmt(b)} |")
    lines.append(f"| **Total** | | | **{fmt(tot['fr'])}** | **{fmt(tot['nl'])}** |")

    stats = collections.Counter()
    for mf in sorted((RAW / "manifest").glob("*.jsonl")):
        for x in mf.read_text(encoding="utf-8").splitlines():
            stats[json.loads(x)["result"]] += 1
    tpl = (REPO / "scripts" / "README.template.md").read_text(encoding="utf-8")
    out = tpl.replace("{{TABLE}}", "\n".join(lines))
    out = out.replace("{{DATE}}", date.today().isoformat())
    for k in ("written", "skipped-repealed", "skipped-german", "skipped-ar-filter", "no-text"):
        out = out.replace("{{" + k + "}}", fmt(stats[k]))
    (REPO / "README.md").write_text(out, encoding="utf-8")
    print(dict(stats), dict(tot))


if __name__ == "__main__":
    main()
