# Belgium — LawCodex

Belgian legislation **in force**, as plain Markdown: one file per text, in the current
consolidated version (*législation consolidée* / *geconsolideerde wetgeving*) published by the
**Justel** database of the Belgian Official Gazette (*Moniteur belge* / *Belgisch Staatsblad*,
FPS Justice), in both **French** (`fr/`) and **Dutch** (`nl/`).

Part of [LawCodex](https://github.com/LawCodex) — the laws of every country as Markdown in git.

Retrieved: 2026-10-11.

## Contents

| Category | French | Dutch | FR files | NL files |
|---|---|---|---:|---:|
| Constitution (coordinated text of 17 February 1994) | `constitution/` | `grondwet/` | 1 | 1 |
| Codes (one file per code, or per part/book where Justel splits the code) | `codes/` | `wetboeken/` | 0 | 0 |
| Lois / wetten (incl. loi communale, loi provinciale…) | `lois/` | `wetten/` | 0 | 0 |
| Arrêtés-lois / besluitwetten | `arretes-lois/` | `besluitwetten/` | 0 | 0 |
| Arrêtés du Régent / regentsbesluiten | `arretes-du-regent/` | `regentsbesluiten/` | 0 | 0 |
| Arrêtés royaux with force of law or coordinating laws (filtered, see below) | `arretes-royaux/` | `koninklijke-besluiten/` | 0 | 0 |
| Accords de coopération / samenwerkingsakkoorden | `accords-de-cooperation/` | `samenwerkingsakkoorden/` | 0 | 0 |
| Flemish Community/Region — decrees | `regions/flandre/decrets/` | `gewesten/vlaanderen/decreten/` | 0 | 0 |
| Walloon Region — decrees | `regions/wallonie/decrets/` | `gewesten/wallonie/decreten/` | 0 | 0 |
| French Community — decrees | `regions/communaute-francaise/decrets/` | `gewesten/franse-gemeenschap/decreten/` | 0 | 0 |
| German-speaking Community — decrees | `regions/communaute-germanophone/decrets/` | `gewesten/duitstalige-gemeenschap/decreten/` | 0 | 0 |
| Brussels-Capital Region — ordinances | `regions/bruxelles/ordonnances/` | `gewesten/brussel/ordonnanties/` | 0 | 0 |
| Brussels (COCOF / French Community Commission) — decrees | `regions/bruxelles/decrets/` | `gewesten/brussel/decreten/` | 0 | 0 |
| **Total** | | | **1** | **1** |

Federated entities (regions and communities) are grouped under `fr/regions/` / `nl/gewesten/`.
Year directories (`<year>/`) use the year of promulgation / signature of the text.

Key texts, for orientation:

| Text | French | Dutch |
|---|---|---|
| Constitution / Grondwet | [`fr/constitution/`](fr/constitution/) | [`nl/grondwet/`](nl/grondwet/) |
| Code civil / Burgerlijk Wetboek (new books 1–9 and remaining parts of the old Code) | [`fr/codes/code-civil/`](fr/codes/code-civil/) | [`nl/wetboeken/`](nl/wetboeken/) |
| Code pénal / Strafwetboek | [`fr/codes/code-penal/`](fr/codes/code-penal/) | [`nl/wetboeken/`](nl/wetboeken/) |
| Code judiciaire / Gerechtelijk Wetboek (one file per part) | [`fr/codes/code-judiciaire/`](fr/codes/code-judiciaire/) | [`nl/wetboeken/`](nl/wetboeken/) |
| Code des sociétés et des associations / Wetboek van vennootschappen en verenigingen | [`fr/codes/code-des-societes-et-des-associations/`](fr/codes/code-des-societes-et-des-associations/) | [`nl/wetboeken/`](nl/wetboeken/) |
| Code de droit économique / Wetboek van economisch recht | [`fr/codes/code-de-droit-economique/`](fr/codes/code-de-droit-economique/) | [`nl/wetboeken/`](nl/wetboeken/) |

## Structure

```
fr/                                   nl/
  constitution/                         grondwet/
  codes/<code>/                         wetboeken/<wetboek>/
  lois/<year>/                          wetten/<year>/
  arretes-lois/<year>/                  besluitwetten/<year>/
  arretes-du-regent/<year>/             regentsbesluiten/<year>/
  arretes-royaux/<year>/                koninklijke-besluiten/<year>/
  accords-de-cooperation/<year>/        samenwerkingsakkoorden/<year>/
  regions/                              gewesten/
    flandre/decrets/<year>/               vlaanderen/decreten/<year>/
    wallonie/decrets/<year>/              wallonie/decreten/<year>/
    communaute-francaise/decrets/<year>/  franse-gemeenschap/decreten/<year>/
    communaute-germanophone/decrets/…     duitstalige-gemeenschap/decreten/…
    bruxelles/ordonnances/<year>/         brussel/ordonnanties/<year>/
    bruxelles/decrets/<year>/             brussel/decreten/<year>/
```

Files are named `<numac>-<slug-of-title>.md`. The **NUMAC** is the official identifier of the
publication in the Moniteur belge; the same text exists under the same NUMAC in both languages
(in `fr/` and in `nl/`), so the two language versions can be paired by filename prefix.
Large codes are split by Justel itself into several texts (e.g. the *Code judiciaire* into its
eight parts, the *Code civil* into its books); each becomes one file inside the code's directory.

## File format

```yaml
---
title: "La Constitution coordonnée."
identifier: "1994021048"              # NUMAC
eli: "https://www.ejustice.just.fgov.be/eli/constitution/1994/02/17/1994021048/justel"
type: constitution                    # constitution | code | act | decree-law | royal-decree | cooperation-agreement | decree | ordinance
justel_type: "CONSTITUTION 1994"      # Justel "nature juridique"
jurisdiction: be
region: flandre                       # only for texts of regions/communities
language: fr
date: 1994-02-17                      # promulgation / signature date
published: 1994-02-17                 # publication in the Moniteur belge
entry_into_force: 1994-02-27
last_amended: 2026-07-24              # Justel "mise à jour au" / "tekstbijwerking tot"
end_of_validity: …                    # only when Justel announces a future end of validity
status: in_force
source: "https://www.ejustice.just.fgov.be/eli/constitution/1994/02/17/1994021048/justel"
department: "Intérieur - Fonction publique"
justel_note: "…"                      # Justel's own note(s) on the title
retrieved: 2026-10-11
---
```

The H1 is the full official title (with its date). It is followed by the preamble (if any), the
text with its structure (Partie/Livre/Titre/Chapitre/Section… mapped to Markdown headings, the
deepest level being the articles: `Art. 5`; when the hierarchy is deeper than six levels the
article labels are in **bold**), and, after a horizontal rule, the signatures.
The consolidation markers of Justel are kept verbatim: `[<sup>1</sup> … ]<sup>1</sup>` brackets
around inserted/replaced text and the footnotes after `----------` such as
`(1)<L 2014-01-06/36, art. 1, 061; En vigueur : 31-01-2014>` identifying the amending act.

## What is included / not included

Included Justel *natures juridiques*: `CONSTITUTION 1994`, every `CODE …` type, `LOI`,
`LOI COMMUNALE`, `LOI PROVINCIALE`, `LOI DETENTION PREVENTIVE`, `ARRETE-LOI`, `ARRETE DU REGENT`,
`ACCORD DE COOPERATION (NATIONAL)`, `DECRET CONSEIL FLAMAND`, `DECRET REGION WALLONNE`,
`DECRET COMMUNAUTE FRANCAISE`, `DECRET COMMUNAUTE GERMANOPHONE`, `ORDONNANCE (BRUXELLES)`,
`DECRET (BRUXELLES)`, and a filtered subset of `ARRETE ROYAL`.

Statistics of the last run (texts, not files):

- written (in at least one language): 0
- skipped because Justel marks them as repealed / no longer valid (*Abrogé*, *Fin de validité* in
  the past): 0
- skipped German-translation entries (Justel only links the PDF image for these, there is no
  text): 0
- royal decrees skipped by the filter (ordinary regulatory royal decrees): 0
- no consolidated text available in Justel (only the scanned Moniteur image): 0

**Royal decrees.** Justel holds about 100,000 *arrêtés royaux*, overwhelmingly ordinary
executive regulations. Only those whose title identifies them as having the force of law or as
coordinating statutes are included: numbered royal decrees (*arrêté royal n° …*,
special-powers decrees), decrees taken under special/extraordinary powers (*pouvoirs spéciaux*,
*habilitant le Roi*) and coordinations/codifications of laws (*lois coordonnées*, *portant
coordination*, *codification*). The regex is in [`scripts/catalog.py`](scripts/catalog.py).

**Not included:**

- German (`de/`): Justel offers no consolidated German text; German translations
  (*Zentrale Dienststelle für Deutsche Übersetzungen*) are only available as Moniteur PDF images.
- Repealed and expired texts, and historical constitution (1831).
- Ordinary royal decrees, ministerial decrees (*arrêtés ministériels*, ~40,000), executive orders
  of the regional and community governments (*arrêtés du Gouvernement flamand/wallon/…*,
  Brussels *arrêtés* and *règlements*), circulars, collective labour agreements, treaties (the
  laws approving them are included as `LOI`), EU acts, Constitutional Court judgments.
- Texts for which Justel only has the scanned image of the Moniteur belge.
- Language: a text appears in a language directory only when Justel has the consolidated text in
  that language (some regional texts exist in only one of FR/NL).

## Sources

- Justel — Législation consolidée / Geconsolideerde wetgeving, SPF Justice / FOD Justitie,
  Moniteur belge / Belgisch Staatsblad:
  <https://www.ejustice.just.fgov.be/cgi_loi/rech.pl?language=fr>
- ELI permalinks, e.g. `https://www.ejustice.just.fgov.be/eli/loi/<yyyy>/<mm>/<dd>/<numac>/justel`
  (Dutch: `/eli/wet/…`).

No open-data dump or bulk API of Justel exists; the corpus is obtained by querying the public
search form (per *nature juridique*, split by promulgation-date range because Justel caps result
lists at 10,000) and fetching each text page in French and Dutch, politely (descriptive
User-Agent, at most 4 concurrent requests, rate limit, retries with backoff, local cache).

**Status of the texts.** The Justel consolidations are produced by the Official Gazette for
information only; only the texts published in the Moniteur belge are authentic. Justel updates
consolidations with a delay (typically a few months); the `last_amended` field gives the date up
to which Justel has integrated amendments.

## Licence

Official acts of public authorities are excluded from copyright protection in Belgium
(Code de droit économique, art. XI.172, § 2: *« Les actes officiels de l'autorité ne donnent pas
lieu au droit d'auteur »*). The texts here are reproduced without alteration other than the
conversion to Markdown. The scripts are provided as-is.

## Regenerating

```sh
python -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt
cd scripts
../.venv/bin/python list_texts.py          # enumerate texts per nature juridique -> _raw/be/lists/
../.venv/bin/python fetch_convert.py       # fetch FR+NL pages (cached in _raw/be/cache/) and write fr/ nl/
../.venv/bin/python build_readme.py        # refresh counts in this README
```

The raw cache lives outside the repository (`../_raw/be/`, override with `LAWCODEX_RAW`).
