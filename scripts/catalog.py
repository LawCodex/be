"""Which Justel 'nature juridique' (dt) values are collected, and where they go."""
import re

# dt value -> (category key, region key or None)
TYPES = {
    "CONSTITUTION 1994": ("constitution", None),
    "LOI": ("loi", None),
    "LOI COMMUNALE": ("loi", None),
    "LOI PROVINCIALE": ("loi", None),
    "LOI DETENTION PREVENTIVE": ("loi", None),
    "ARRETE-LOI": ("arrete-loi", None),
    "ARRETE DU REGENT": ("arrete-regent", None),
    "ARRETE ROYAL": ("arrete-royal", None),  # filtered, see ar_has_legislative_force()
    "ACCORD DE COOPERATION (NATIONAL)": ("accord", None),
    "DECRET CONSEIL FLAMAND": ("decret", "flandre"),
    "DECRET REGION WALLONNE": ("decret", "wallonie"),
    "DECRET COMMUNAUTE FRANCAISE": ("decret", "communaute-francaise"),
    "DECRET COMMUNAUTE GERMANOPHONE": ("decret", "communaute-germanophone"),
    "ORDONNANCE (BRUXELLES)": ("ordonnance", "bruxelles"),
    "DECRET (BRUXELLES)": ("decret", "bruxelles"),
}
# every "CODE ..." dt value offered by the search form is added at runtime (category "code").

# Directory names per language
DIRS = {
    "fr": {
        "constitution": "constitution",
        "code": "codes",
        "loi": "lois",
        "arrete-loi": "arretes-lois",
        "arrete-regent": "arretes-du-regent",
        "arrete-royal": "arretes-royaux",
        "accord": "accords-de-cooperation",
        "regions": "regions",
        "decret": "decrets",
        "ordonnance": "ordonnances",
        "flandre": "flandre",
        "wallonie": "wallonie",
        "bruxelles": "bruxelles",
        "communaute-francaise": "communaute-francaise",
        "communaute-germanophone": "communaute-germanophone",
    },
    "nl": {
        "constitution": "grondwet",
        "code": "wetboeken",
        "loi": "wetten",
        "arrete-loi": "besluitwetten",
        "arrete-regent": "regentsbesluiten",
        "arrete-royal": "koninklijke-besluiten",
        "accord": "samenwerkingsakkoorden",
        "regions": "gewesten",
        "decret": "decreten",
        "ordonnance": "ordonnanties",
        "flandre": "vlaanderen",
        "wallonie": "wallonie",
        "bruxelles": "brussel",
        "communaute-francaise": "franse-gemeenschap",
        "communaute-germanophone": "duitstalige-gemeenschap",
    },
}

FM_TYPE = {
    "constitution": "constitution",
    "code": "code",
    "loi": "act",
    "arrete-loi": "decree-law",
    "arrete-regent": "decree-law",
    "arrete-royal": "royal-decree",
    "accord": "cooperation-agreement",
    "decret": "decree",
    "ordonnance": "ordinance",
}

# Royal decrees having the force of law (or coordinating statutes): numbered special-powers
# decrees, special/extraordinary-powers decrees and coordinations/codifications of laws.
AR_RE = re.compile(
    r"arr[êe]t[ée]\s+royal\s+(n[°o]|num[ée]ro)\s*\d"
    r"|pouvoirs\s+(sp[ée]ciaux|extraordinaires)"
    r"|habilitant\s+le\s+roi"
    r"|coordonn(ant|ée?s?)\b|portant\s+coordination|coordination\s+(des|de\s+la)\s+lois?"
    r"|codifi(ant|cation|ée?s?)\b",
    re.I,
)


def ar_has_legislative_force(title: str) -> bool:
    return bool(AR_RE.search(title))
