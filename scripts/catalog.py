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

# Royal decrees having the force of law or coordinating statutes: numbered (special-powers)
# decrees, decrees taken under special/extraordinary powers, and coordinations/codifications
# of laws. Matched on the title without its date prefix.
AR_RE = re.compile(
    r"^arr[êe]t[ée]\s+(royal\s+|du\s+r[ée]gent\s+)?(de\s+pouvoirs\s+sp[ée]ciaux\s+)?(n[°o]|num[ée]ro)\s*\d"
    r"|^arr[êe]t[ée]\s+de\s+pouvoirs\s+sp[ée]ciaux"
    r"|pouvoirs\s+(sp[ée]ciaux|extraordinaires)|habilitant\s+le\s+roi"
    r"|accordant\s+(des|certains)\s+pouvoirs\s+(sp[ée]ciaux\s+)?au\s+roi"
    r"|attribuant\s+(des|certains)\s+pouvoirs\s+(sp[ée]ciaux\s+)?au\s+roi"
    r"|^arr[êe]t[ée]\s+(royal|du\s+r[ée]gent)\s+(coordonnant|codifiant|portant\s+(la\s+)?(coordination|codification)"
    r"|relatif\s+[àa]\s+la\s+(coordination|codification)\s+(des|de\s+la)\s+lois?)",
    re.I,
)


def ar_has_legislative_force(title: str) -> bool:
    t = re.sub(r"^\s*\d{1,2}(er)?\s+\S+\s+\d{4}\.?\s*-\s*", "", title)
    return bool(AR_RE.search(t))

# Dutch directory names for the codes (keyed by the slug of the French Justel type).
NL_CODE_DIRS = {
    "code-belge-de-la-navigation": "belgisch-scheepvaartwetboek",
    "code-bruxellois-de-l-air-du-climat-et-de-la-maitrise-de-l-energie": "brussels-wetboek-van-lucht-klimaat-en-energiebeheersing",
    "code-bruxellois-de-l-amenagement-du-territoire": "brussels-wetboek-van-ruimtelijke-ordening",
    "code-bruxellois-du-logement": "brusselse-huisvestingscode",
    "code-civil": "burgerlijk-wetboek",
    "code-consulaire": "consulair-wetboek",
    "code-d-instruction-criminelle": "wetboek-van-strafvordering",
    "code-de-commerce": "wetboek-van-koophandel",
    "code-de-droit-economique": "wetboek-van-economisch-recht",
    "code-de-droit-international-prive": "wetboek-van-internationaal-privaatrecht",
    "code-de-l-enseignement-fondamental-et-secondaire": "wetboek-voor-het-basis-en-secundair-onderwijs",
    "code-de-l-enseignement-secondaire": "codex-secundair-onderwijs",
    "code-de-l-enseignement-superieur": "codex-hoger-onderwijs",
    "code-de-la-democratie-locale-et-de-la-decentralisation": "wetboek-van-de-plaatselijke-democratie-en-decentralisatie",
    "code-de-la-fonction-publique-wallonne": "waals-ambtenarenwetboek",
    "code-de-la-nationalite-belge": "wetboek-van-de-belgische-nationaliteit",
    "code-de-la-taxe-sur-la-valeur-ajoutee": "wetboek-van-de-belasting-over-de-toegevoegde-waarde",
    "code-de-procedure-penale-militaire": "wetboek-van-militaire-strafrechtspleging",
    "code-des-droits-d-enregistrement-d-hypotheque-et-de-greffe": "wetboek-der-registratie-hypotheek-en-griffierechten",
    "code-des-droits-de-succession": "wetboek-der-successierechten",
    "code-des-droits-de-timbre": "wetboek-der-zegelrechten",
    "code-des-droits-et-taxes-divers": "wetboek-diverse-rechten-en-taksen",
    "code-des-impots-sur-les-revenus": "wetboek-van-de-inkomstenbelastingen",
    "code-des-societes-et-des-associations": "wetboek-van-vennootschappen-en-verenigingen",
    "code-des-societes": "wetboek-van-vennootschappen",
    "code-des-taxes-assimilees-au-timbre": "wetboek-der-met-het-zegel-gelijkgestelde-taksen",
    "code-des-taxes-assimilees-aux-impots-sur-les-revenus": "wetboek-van-de-met-de-inkomstenbelastingen-gelijkgestelde-belastingen",
    "code-du-bien-etre-au-travail": "codex-over-het-welzijn-op-het-werk",
    "code-du-developpement-territorial": "wetboek-van-ruimtelijke-ontwikkeling",
    "code-du-logement": "huisvestingscode",
    "code-du-recouvrement-amiable-et-force-des-creances": "wetboek-van-de-minnelijke-en-gedwongen-invordering",
    "code-electoral-communal-bruxellois": "brussels-gemeentelijk-kieswetboek",
    "code-electoral": "kieswetboek",
    "code-ferroviaire": "spoorcodex",
    "code-flamand-de-l-amenagement-du-territoire": "vlaamse-codex-ruimtelijke-ordening",
    "code-flamand-de-l-enseignement-secondaire": "codex-secundair-onderwijs-vlaanderen",
    "code-flamand-de-la-fiscalite": "vlaamse-codex-fiscaliteit",
    "code-flamand-du-logement": "vlaamse-codex-wonen",
    "code-forestier": "boswetboek",
    "code-judiciaire": "gerechtelijk-wetboek",
    "code-penal-militaire": "militair-strafwetboek",
    "code-penal-social": "sociaal-strafwetboek",
    "code-penal": "strafwetboek",
    "code-procedure-armee-de-terre": "wetboek-van-rechtspleging-voor-de-landmacht",
    "code-rural": "veldwetboek",
    "code-wallon-de-l-action-sociale-et-de-la-sante": "waals-wetboek-van-sociale-actie-en-gezondheid",
    "code-wallon-de-l-agriculture": "waals-landbouwwetboek",
    "code-wallon-de-l-amenagement-du-territoire": "waals-wetboek-van-ruimtelijke-ordening",
    "code-wallon-de-l-environnement": "waals-milieuwetboek",
    "code-wallon-de-l-habitation-durable": "waals-wetboek-van-duurzaam-wonen",
    "code-wallon-du-bien-etre-des-animaux": "waals-dierenwelzijnwetboek",
    "code-wallon-du-developpement-territorial": "waals-wetboek-van-ruimtelijke-ontwikkeling",
    "code-wallon-du-tourisme": "waals-toerismewetboek",
}
