#!/usr/bin/env python3
"""Enumerate Justel consolidated texts per 'nature juridique' via the public search.

Writes one JSON line per text to _raw/be/lists/<dt-slug>.jsonl:
  {"numac", "dt", "title", "pub_date", "source"}
Justel refuses result sets over 10,000 texts, so large types are split recursively by
promulgation-date range.
"""
from __future__ import annotations

import html
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

from common import BASE, LISTS, http
from catalog import TYPES

ITEM_RE = re.compile(
    r'<p class="list-item--subtitle">\s*(.*?)\s*</p>\s*'
    r'<a href="article\.pl\?[^"]*?numac_search=([0-9A-Z]+)[^"]*" class="list-item--title">\s*(.*?)\s*</a>\s*'
    r'<p class="list-item--date">\s*(.*?)\s*</p>',
    re.S,
)
LAST_RE = re.compile(r'page=(\d+)[^"]*" class="pagination-button pagination-last')


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def code_types() -> list[str]:
    page = http("GET", BASE + "rech.pl", params={"language": "fr"})
    sel = re.search(r'name="dt">(.*?)</select>', page, re.S).group(1)
    opts = [html.unescape(o).strip() for o in re.findall(r"<option[^>]*>(.*?)</option>", sel)]
    return [o for o in opts if o.startswith("CODE ")]


def params(dt, d1=None, d2=None, page=1):
    p = {"language": "fr", "sum_date": "", "page": str(page), "trier": "promulgation",
         "dt": dt, "fr": "f", "choix1": "et", "choix2": "et"}
    if d1:
        p["ddd"], p["ddf"] = d1.isoformat(), d2.isoformat()
    return p


def parse(page):
    return [
        {"numac": m.group(2), "title": html.unescape(re.sub(r"\s+", " ", m.group(3))).strip(),
         "pub_date": m.group(4).strip(), "source": html.unescape(m.group(1)).strip()}
        for m in ITEM_RE.finditer(page)
    ]


def list_range(dt, d1=None, d2=None):
    first = http("GET", BASE + "list.pl", params=params(dt, d1, d2))
    if "plus de 10.000" in first:
        assert d1 and d2 and d1 < d2, (dt, d1, d2)
        mid = d1 + (d2 - d1) / 2
        return list_range(dt, d1, mid) + list_range(dt, mid + timedelta(days=1), d2)
    m = LAST_RE.search(first)
    last = int(m.group(1)) if m else 1
    items = parse(first)
    with ThreadPoolExecutor(4) as ex:
        for pg in ex.map(lambda n: http("GET", BASE + "list.pl", params=params(dt, d1, d2, n)),
                         range(2, last + 1)):
            items += parse(pg)
    print(f"  {dt} {d1}..{d2}: {last} pages, {len(items)} items", file=sys.stderr, flush=True)
    return items


def main():
    LISTS.mkdir(parents=True, exist_ok=True)
    dts = list(TYPES) + code_types()
    only = set(sys.argv[1:])
    for dt in dts:
        if only and dt not in only:
            continue
        out = LISTS / f"{slug(dt)}.jsonl"
        if out.exists() and not only:
            continue
        probe = http("GET", BASE + "list.pl", params=params(dt))
        if "plus de 10.000" in probe:
            items = list_range(dt, date(1700, 1, 1), date.today())
        else:
            items = list_range(dt)
        seen, uniq = set(), []
        for it in items:
            if it["numac"] not in seen:
                seen.add(it["numac"])
                it["dt"] = dt
                uniq.append(it)
        tmp = out.with_suffix(".tmp")
        tmp.write_text("".join(json.dumps(i, ensure_ascii=False) + "\n" for i in uniq), encoding="utf-8")
        tmp.replace(out)
        print(f"{dt}: {len(uniq)}", flush=True)


if __name__ == "__main__":
    main()
