#!/usr/bin/env python3
"""Fetch consolidated texts from Justel (FR + NL) and convert them to Markdown.

Usage: fetch_convert.py [--workers N] [DT ...]
Reads the lists produced by list_texts.py, writes <lang>/... Markdown files into the repo and
a manifest line per text to _raw/be/manifest/<dt-slug>.jsonl.
"""
from __future__ import annotations

import argparse
import collections
import html as htmlmod
import json
import re
import sys
import threading
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import date

import lxml.html

from catalog import DIRS, FM_TYPE, TYPES, ar_has_legislative_force
from common import BASE, LISTS, RAW, REPO, cached, http
from list_texts import slug as dtslug

TODAY = date.today()
RETRIEVED = TODAY.isoformat()
MANIFEST = RAW / "manifest"
GERMAN_RE = re.compile(r"traduction allemande|langue allemande|en langue allemande|version allemande", re.I)

MONTHS = {
    "janvier": 1, "fevrier": 2, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6, "juillet": 7,
    "aout": 8, "août": 8, "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12, "décembre": 12,
    "januari": 1, "februari": 2, "maart": 3, "april": 4, "mei": 5, "juni": 6, "juli": 7,
    "augustus": 8, "oktober": 10, "december": 12,
}

# ---------------------------------------------------------------- text helpers


def ascii_slug(s: str, maxlen: int = 80) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if len(s) > maxlen:
        s = s[:maxlen].rsplit("-", 1)[0]
    return s or "texte"


def parse_date(s: str | None):
    if not s:
        return None
    s = htmlmod.unescape(s).strip().lower()
    m = re.search(r"(\d{1,2})(?:er)?\s+([a-zéûè]+)\s+(\d{4})", s)
    if m and m.group(2) in MONTHS:
        try:
            return date(int(m.group(3)), MONTHS[m.group(2)], int(m.group(1)))
        except ValueError:
            return None
    m = re.search(r"(\d{2})-(\d{2})-(\d{4})", s)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            return None
    return None


def strip_tags(s: str) -> str:
    return re.sub(r"\s+", " ", htmlmod.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


SUP_O, SUP_C = "\x01", "\x02"


def frag_text(frag: str) -> list[str]:
    """Convert a Justel HTML fragment to a list of Markdown blocks (paragraphs / tables)."""
    if not frag.strip():
        return []
    try:
        root = lxml.html.fragment_fromstring(frag, create_parent="div")
    except Exception:  # noqa: BLE001
        return [md_escape_line(x) for x in strip_tags(frag.replace("<BR>", "\n")).split("\n") if x.strip()]
    blocks: list[str] = []
    buf: list[str] = []

    def walk(el):
        tag = el.tag if isinstance(el.tag, str) else ""
        tag = tag.lower()
        if tag == "br":
            buf.append("\n")
        elif tag == "table":
            flush()
            for a in list(el.iter()):
                if isinstance(a.tag, str):
                    for k in list(a.attrib):
                        if k.lower() not in ("colspan", "rowspan"):
                            del a.attrib[k]
            t = lxml.html.tostring(el, encoding="unicode")
            t = re.sub(r"\s*\n\s*", " ", t)
            blocks.append(t.strip())
        elif tag == "img":
            src = el.get("src", "")
            if src:
                if src.startswith("/"):
                    src = "https://www.ejustice.just.fgov.be" + src
                buf.append(f"![]({src})")
        elif tag == "sup":
            buf.append(SUP_O + el.text_content().strip() + SUP_C)
        elif tag in ("script", "style"):
            pass
        else:
            if el.text:
                buf.append(el.text)
            for c in el:
                walk(c)
                if c.tail:
                    buf.append(c.tail)
        return

    def flush():
        if buf:
            txt = "".join(buf)
            buf.clear()
            for line in txt.split("\n"):
                line = re.sub(r"[ \t\xa0]+", " ", line).strip()
                if line:
                    blocks.append(md_escape_line(line))

    if root.text:
        buf.append(root.text)
    for c in root:
        walk(c)
        if c.tail:
            buf.append(c.tail)
    flush()
    return blocks


def md_escape_line(line: str) -> str:
    if line.startswith("<table") or line.startswith("!["):
        return line
    line = line.replace("&", "&amp;") if re.search(r"&[#a-zA-Z0-9]+;", line) else line
    line = line.replace("<", "&lt;").replace(">", "&gt;")
    line = line.replace("*", r"\*").replace("_", r"\_")
    line = line.replace(SUP_O, "<sup>").replace(SUP_C, "</sup>")
    if re.match(r"^(\d+)([.)])(\s|$)", line):
        line = re.sub(r"^(\d+)([.)])", r"\1\\\2", line)
    elif re.match(r"^([#+\-=|]|~~~|```)", line) and not re.match(r"^-{3,}$", line):
        line = "\\" + line
    return line


# ---------------------------------------------------------------- heading hierarchy

KINDS = [
    ("PARTIE", "DEEL", "TEIL"),
    ("LIVRE", "BOEK", "BUCH"),
    ("TITRE", "TITEL"),
    ("SOUS-TITRE", "ONDERTITEL", "UNTERTITEL"),
    ("CHAPITRE", "HOOFDSTUK", "KAPITEL"),
    ("SOUS-CHAPITRE", "ONDERHOOFDSTUK"),
    ("SECTION", "AFDELING", "ABSCHNITT"),
    ("SOUS-SECTION", "ONDERAFDELING", "UNTERABSCHNITT"),
    ("PARAGRAPHE", "§", "PARAGRAAF"),
    ("SOUS-PARAGRAPHE", "SUBPARAGRAAF", "ONDERPARAGRAAF"),
]
KIND_OF = {w: i for i, ws in enumerate(KINDS) for w in ws}


def heading_kind(text: str):
    t = re.sub(r"<sup>.*?</sup>|\\", "", text)
    words = re.findall(r"§|[A-Za-zÀ-ÿ\-]+", t)[:3]
    for w in words:
        u = unicodedata.normalize("NFKD", w).encode("ascii", "ignore").decode().upper() if w != "§" else w
        if u in KIND_OF:
            return KIND_OF[u]
    return None


# ---------------------------------------------------------------- page parsing

SEG_RE = re.compile(r"<A NAME='(LNK\d+|Art[^']*)'[^>]*>", re.I)


def section(page: str, ident: str) -> str:
    m = re.search(r'<div id="list-title-%s"[^>]*>(.*?)(?=<div id="list-title-|<div class="links)' % re.escape(ident),
                  page, re.S)
    return m.group(1) if m else ""


def parse_page(page: str) -> dict:
    head = section(page, "1")
    d: dict = {}
    m = re.search(r'<p class="list-item--title">(.*?)</p>', head, re.S)
    full_title = strip_tags(m.group(1)) if m else ""
    notes = re.findall(r"\((?:NOTE|NOTA)\s*:\s*(.*?)\)(?=\s*(?:\(|$))", full_title)
    title = re.sub(r"\s*\((?:NOTE|NOTA)\s*:.*$", "", full_title).strip()
    d["full_title"], d["title"], d["notes"] = full_title, title, notes
    fields = {}
    for k, v in re.findall(r"<strong>\s*(.*?)\s*</strong>(.*?)</p>", head, re.S):
        fields[strip_tags(k).rstrip(" :").lower()] = strip_tags(v)
    d["fields"] = fields
    m = re.search(r'id="link-text"[^>]*href="([^"]+)"', page)
    d["eli"] = m.group(1) if m else None
    txt = section(page, "3")
    txt = re.sub(r'^\s*<h2[^>]*>.*?</h2>', "", txt, flags=re.S)
    txt = re.sub(r"</div>\s*$", "", txt.strip())
    d["text_html"] = txt
    d["preamble"] = re.sub(r'^\s*<h2[^>]*>.*?</h2>', "", section(page, "sw_prev"), flags=re.S)
    d["signatures"] = re.sub(r'^\s*<h2[^>]*>.*?</h2>', "", section(page, "sw_sign"), flags=re.S)
    return d


def text_to_md(txt: str) -> tuple[list[str], int]:
    """Return markdown lines of the body and the number of articles."""
    parts = SEG_RE.split(txt)
    pre, segs = parts[0], list(zip(parts[1::2], parts[2::2]))
    items = []  # (kind, label/heading, blocks)
    for name, body in segs:
        if name.upper().startswith("LNK"):
            blocks = frag_text(body)
            head = blocks[0] if blocks else ""
            items.append(("h", head, blocks[1:]))
        else:
            num = name[4:] if name.lower().startswith("art.") else name[3:]
            num = num.strip()
            blocks = frag_text(body)
            if blocks:
                pat = r"^(Article|Artikel|Art\.)\s*" + re.escape(md_escape_line(num)) + r"\s*\.?\s*"
                first = re.sub(pat, "", blocks[0], count=1, flags=re.I)
                if first != blocks[0]:
                    blocks = ([first] if first.strip() else []) + blocks[1:]
            items.append(("a", num, blocks))
    kinds_present = sorted({heading_kind(h) for t, h, _ in items if t == "h"} - {None})
    level_of = {k: 2 + i for i, k in enumerate(kinds_present)}
    art_level = 2 + len(kinds_present)
    out: list[str] = []
    out += [b for b in frag_text(pre)]
    cur = 2
    nart = 0
    for t, h, blocks in items:
        if t == "h":
            k = heading_kind(h)
            lvl = level_of.get(k, cur) if k is not None else cur
            cur = lvl
            out.append("#" * min(lvl, 6) + " " + (h or "…"))
        else:
            nart += 1
            label = f"Art. {h}"
            out.append("#" * art_level + " " + label if art_level <= 6 else f"**{label}**")
        out += blocks
    return out, nart


# ---------------------------------------------------------------- output


def yaml_str(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def year_of(d):
    return d.year if d else None


def promulgation(parsed, item):
    dossier = parsed["fields"].get("dossier numéro") or parsed["fields"].get("dossiernummer") or ""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", dossier)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    return parse_date(item["title"].split(" - ")[0])


def status_of(parsed):
    f = parsed["fields"]
    fin = parse_date(f.get("fin de validité") or f.get("fin de validit&eacute") or f.get("opheffing"))
    for k, v in f.items():
        if k.startswith("fin de validit"):
            fin = parse_date(v)
    abrog = any(re.match(r"\s*(abrog|opgeheven|annul|vernietigd)", n, re.I) for n in parsed["notes"])
    if fin and fin <= TODAY:
        return "repealed", fin
    if abrog and not (fin and fin > TODAY):
        return "repealed", fin
    return "in_force", fin


def last_amended(parsed):
    for n in parsed["notes"]:
        m = re.search(r"(?:mise à jour au|tekstbijwerking tot|bijgewerkt tot)\s*(\d{2}-\d{2}-\d{4})", n)
        if m:
            return parse_date(m.group(1))
    return None


def strip_date_prefix(title: str) -> str:
    return re.sub(r"^\s*\d{1,2}(er)?\s+\S+\s+\d{4}\.?\s*-\s*", "", title).strip() or title


def rel_path(lang, item, parsed, prom, code_dirs):
    cat, region = cat_of(item["dt"])
    D = DIRS[lang]
    name = f"{item['numac'].lower()}-{ascii_slug(strip_date_prefix(parsed['title']), 80)}.md"
    year = str(prom.year if prom else item["numac"][:4])
    if cat == "constitution":
        return f"{lang}/{D['constitution']}/{name}"
    if cat == "code":
        return f"{lang}/{D['code']}/{code_dirs[lang]}/{name}"
    if region:
        return f"{lang}/{D['regions']}/{D[region]}/{D[cat]}/{year}/{name}"
    return f"{lang}/{D[cat]}/{year}/{name}"


def cat_of(dt):
    return TYPES.get(dt, ("code", None))


def render(lang, item, parsed, prom, rel):
    status, fin = status_of(parsed)
    body, nart = text_to_md(parsed["text_html"])
    cat, region = cat_of(item["dt"])
    la = last_amended(parsed)
    f = parsed["fields"]
    inforce = None
    for k, v in f.items():
        if k.startswith("entrée en vigueur") or k.startswith("entr&eacute;e en vigueur") or k.startswith("inwerkingtreding"):
            inforce = parse_date(v)
    fm = ["---", f"title: {yaml_str(strip_date_prefix(parsed['title']))}",
          f"identifier: {yaml_str(item['numac'])}"]
    if parsed["eli"]:
        fm.append(f"eli: {yaml_str(parsed['eli'])}")
    fm += [f"type: {FM_TYPE[cat]}", f"justel_type: {yaml_str(item['dt'])}", "jurisdiction: be"]
    if region:
        fm.append(f"region: {region}")
    fm.append(f"language: {lang}")
    if prom:
        fm.append(f"date: {prom.isoformat()}")
    pub = parse_date(f.get("publication") or f.get("publicatie"))
    if pub:
        fm.append(f"published: {pub.isoformat()}")
    if inforce:
        fm.append(f"entry_into_force: {inforce.isoformat()}")
    if la:
        fm.append(f"last_amended: {la.isoformat()}")
    if fin:
        fm.append(f"end_of_validity: {fin.isoformat()}")
    fm.append(f"status: {status}")
    src_lang = "fr" if lang == "fr" else "nl"
    fm.append(f"source: {yaml_str(parsed['eli'] or BASE + 'article.pl?language=' + src_lang + '&numac_search=' + item['numac'])}")
    dept = f.get("source") or f.get("bron")
    if dept:
        fm.append(f"department: {yaml_str(dept)}")
    if len(parsed["notes"]) == 1:
        fm.append(f"justel_note: {yaml_str(parsed['notes'][0])}")
    elif parsed["notes"]:
        fm.append("justel_notes:")
        fm += [f"  - {yaml_str(n)}" for n in parsed["notes"]]
    fm += [f"retrieved: {RETRIEVED}", "---", ""]
    out = fm + [f"# {md_escape_line(parsed['title'])}", ""]
    pre = frag_text(parsed["preamble"])
    for b in pre:
        out += [b, ""]
    for line in body:
        out += [line, ""]
    sig = frag_text(parsed["signatures"])
    if sig:
        out += ["---", ""]
        for b in sig:
            out += [b, ""]
    return "\n".join(out).rstrip() + "\n", nart


# ---------------------------------------------------------------- driver


def fetch(lang, numac):
    lt = "F" if lang == "fr" else "N"
    return cached(f"{lang}/{numac[:4]}/{numac}", lambda: http(
        "GET", BASE + "article.pl", params={"language": lang, "numac_search": numac, "lg_txt": lt},
        check='id="list-title-1"'))


def nl_code_dir(titles: list[str], fallback: str) -> str:
    votes = collections.Counter()
    for t in titles:
        t = strip_date_prefix(t)
        t = re.sub(r"^\[[^\]]*\]\s*", "", t)
        m = re.match(r"([^,:.(\-]+)", t)
        if m and "wetboek" in m.group(1).lower() or (m and "code" in m.group(1).lower()):
            votes[ascii_slug(m.group(1), 60)] += 1
    return votes.most_common(1)[0][0] if votes else fallback


def process(item, code_dirs, nl_titles, lock):
    numac = item["numac"]
    rec = {"numac": numac, "dt": item["dt"], "title": item["title"]}
    if GERMAN_RE.search(item["title"]):
        rec["result"] = "skipped-german"
        return rec
    if TYPES.get(item["dt"], ("code",))[0] in ("arrete-royal", "arrete-regent") and not ar_has_legislative_force(item["title"]):
        rec["result"] = "skipped-ar-filter"
        return rec
    pfr = parse_page(fetch("fr", numac))
    status, _ = status_of(pfr)
    rec["status"] = status
    if status == "repealed":
        rec["result"] = "skipped-repealed"
        return rec
    prom = promulgation(pfr, item)
    rec["date"] = prom.isoformat() if prom else None
    written = {}
    for lang in ("fr", "nl"):
        p = pfr if lang == "fr" else parse_page(fetch("nl", numac))
        if not p["title"] or not re.search(r"\S", strip_tags(p["text_html"])):
            continue
        if lang == "nl" and nl_titles is not None:
            with lock:
                nl_titles.append(p["title"])
        rel = rel_path(lang, item, p, prom, code_dirs)
        md, nart = render(lang, item, p, prom, rel)
        path = REPO / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(md, encoding="utf-8")
        written[lang] = rel
        rec[f"{lang}_articles"] = nart
    rec.update({f"{k}_path": v for k, v in written.items()})
    rec["result"] = "written" if written else "no-text"
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("dts", nargs="*")
    a = ap.parse_args()
    MANIFEST.mkdir(parents=True, exist_ok=True)
    files = sorted(LISTS.glob("*.jsonl"))
    # default order: constitution, codes, laws, regional texts, the rest
    prio = {"constitution": 0, "code": 1, "loi": 2, "decret": 3, "ordonnance": 3}

    def first_dt(f):
        with open(f, encoding="utf-8") as fh:
            line = fh.readline()
        return json.loads(line)["dt"] if line.strip() else ""
    order = {f: first_dt(f) for f in files}
    if a.dts:
        files = [f for d in a.dts for f in files if order[f] == d]
    else:
        files.sort(key=lambda f: (prio.get(cat_of(order[f])[0], 9), f.name))
    lock = threading.Lock()
    for lf in files:
        items = [json.loads(x) for x in lf.read_text(encoding="utf-8").splitlines() if x.strip()]
        if not items:
            continue
        dt = items[0]["dt"]
        if a.dts and dt not in a.dts:
            continue
        mf = MANIFEST / lf.name
        done = {}
        if mf.exists():
            for x in mf.read_text(encoding="utf-8").splitlines():
                r = json.loads(x)
                done[r["numac"]] = r
        cat = cat_of(dt)[0]
        code_dirs = None
        nl_titles = None
        if cat == "code":
            fr_dir = dtslug(dt)
            # NL directory: majority vote over NL titles; requires a first pass over NL pages
            titles = []
            for it in items:
                if GERMAN_RE.search(it["title"]):
                    continue
                try:
                    titles.append(parse_page(fetch("nl", it["numac"]))["title"])
                except Exception as e:  # noqa: BLE001
                    print("WARN", it["numac"], e, file=sys.stderr)
            code_dirs = {"fr": ascii_slug(fr_dir, 60), "nl": nl_code_dir(titles, ascii_slug(fr_dir, 60))}
        todo = [it for it in items if it["numac"] not in done]
        print(f"{dt}: {len(items)} listed, {len(todo)} to do", flush=True)
        n = 0
        with open(mf, "a", encoding="utf-8") as mfh, ThreadPoolExecutor(a.workers) as ex:
            def job(it):
                try:
                    return process(it, code_dirs, nl_titles, lock)
                except Exception as e:  # noqa: BLE001
                    print("ERROR", it["numac"], repr(e), file=sys.stderr, flush=True)
                    return None
            for rec in ex.map(job, todo):
                if rec is None:
                    continue
                mfh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                mfh.flush()
                n += 1
                if n % 200 == 0:
                    print(f"  {dt}: {n}/{len(todo)}", flush=True)
        print(f"{dt}: done", flush=True)


if __name__ == "__main__":
    main()
