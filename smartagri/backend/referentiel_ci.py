"""
Référentiel agro-climatique de la Côte d'Ivoire.
Source unique utilisée par l'API de prédiction (et exposée à /api/prediction/referentiel
pour que le web et le mobile affichent les mêmes listes).
"""
import unicodedata

# ─── Zones agro-écologiques ───────────────────────────────────────
ZONES = {
    "sud":    "Sud littoral",
    "foret":  "Zone forestière (Ouest, Centre-Ouest, Est)",
    "centre": "Centre (transition forêt-savane)",
    "nord":   "Nord (savane)",
}

# ─── Villes → zone ────────────────────────────────────────────────
_VILLES_ZONE = {
    "sud":    ["abidjan", "san-pedro", "tabou", "grand-lahou", "sassandra", "aboisso", "dabou", "jacqueville", "grand-bassam"],
    "foret":  ["daloa", "gagnoa", "soubre", "issia", "divo", "lakota", "man", "touba", "danane", "guiglo",
               "duekoue", "abengourou", "agboville", "adzope", "oume", "seguela"],
    "centre": ["yamoussoukro", "bouake", "dimbokro", "toumodi", "bongouanou", "mankono", "bondoukou", "daoukro",
               "katiola", "beoumi", "sakassou"],
    "nord":   ["korhogo", "odienne", "tingrela", "ferkessedougou", "boundiali", "dabakala", "kong", "ouangolodougou"],
}
VILLES_ZONE = {v: z for z, villes in _VILLES_ZONE.items() for v in villes}


def normaliser(texte: str) -> str:
    t = unicodedata.normalize("NFD", (texte or "").lower().strip())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return t.replace(" ", "-").replace("_", "-")


def zone_depuis_ville(ville: str | None, latitude: float | None = None) -> str | None:
    """Retourne la zone ('sud', 'foret', 'centre', 'nord') ou None si inconnue."""
    if ville:
        z = VILLES_ZONE.get(normaliser(ville))
        if z:
            return z
    if latitude is not None and 4.0 <= latitude <= 10.8:      # latitudes de la Côte d'Ivoire
        if latitude >= 8.8: return "nord"
        if latitude >= 7.0: return "centre"
        if latitude >= 5.6: return "foret"
        return "sud"
    return None


# ─── Cultures ─────────────────────────────────────────────────────
# rendement de base (t/ha), pluviométrie optimale (mm), température optimale (°C),
# aptitude par zone (1.0 = idéale, 0.2 = très peu adaptée)
CULTURES = {
    "cacao":    {"label": "Cacao",           "emoji": "🍫", "base": 0.8,  "pluv": 1600, "temp": 26,
                 "zones": {"sud": 0.95, "foret": 1.00, "centre": 0.60, "nord": 0.25}},
    "cafe":     {"label": "Café",            "emoji": "☕", "base": 0.6,  "pluv": 1500, "temp": 24,
                 "zones": {"sud": 0.85, "foret": 1.00, "centre": 0.60, "nord": 0.25}},
    "hevea":    {"label": "Hévéa",           "emoji": "🌳", "base": 1.5,  "pluv": 1500, "temp": 27,
                 "zones": {"sud": 1.00, "foret": 1.00, "centre": 0.70, "nord": 0.40}},
    "palmier":  {"label": "Palmier à huile", "emoji": "🌴", "base": 15.0, "pluv": 1800, "temp": 27,
                 "zones": {"sud": 1.00, "foret": 0.90, "centre": 0.50, "nord": 0.20}},
    "anacarde": {"label": "Anacarde",        "emoji": "🥜", "base": 0.9,  "pluv": 1000, "temp": 29,
                 "zones": {"sud": 0.50, "foret": 0.70, "centre": 1.00, "nord": 1.00}},
    "coton":    {"label": "Coton",           "emoji": "☁️", "base": 1.5,  "pluv": 850,  "temp": 30,
                 "zones": {"sud": 0.20, "foret": 0.40, "centre": 0.90, "nord": 1.00}},
    "mais":     {"label": "Maïs",            "emoji": "🌽", "base": 3.0,  "pluv": 650,  "temp": 26,
                 "zones": {"sud": 0.90, "foret": 1.00, "centre": 1.00, "nord": 0.90}},
    "riz":      {"label": "Riz",             "emoji": "🌾", "base": 3.5,  "pluv": 1000, "temp": 28,
                 "zones": {"sud": 1.00, "foret": 1.00, "centre": 1.00, "nord": 0.90}},
    "manioc":   {"label": "Manioc",          "emoji": "🥔", "base": 11.0, "pluv": 875,  "temp": 27,
                 "zones": {"sud": 1.00, "foret": 1.00, "centre": 1.00, "nord": 0.80}},
    "igname":   {"label": "Igname",          "emoji": "🍠", "base": 8.0,  "pluv": 1250, "temp": 28,
                 "zones": {"sud": 0.80, "foret": 0.90, "centre": 1.00, "nord": 1.00}},
    # Cultures du Nord ivoirien (savane)
    "arachide": {"label": "Arachide",        "emoji": "🥜", "base": 1.5,  "pluv": 700,  "temp": 30,
                 "zones": {"sud": 0.50, "foret": 0.70, "centre": 0.90, "nord": 1.00}},
    "sorgho":   {"label": "Sorgho",          "emoji": "🌿", "base": 1.8,  "pluv": 700,  "temp": 30,
                 "zones": {"sud": 0.30, "foret": 0.50, "centre": 0.80, "nord": 1.00}},
    "mil":      {"label": "Mil",             "emoji": "🌿", "base": 1.2,  "pluv": 650,  "temp": 30,
                 "zones": {"sud": 0.20, "foret": 0.40, "centre": 0.70, "nord": 1.00}},
}

# ─── Sols ─────────────────────────────────────────────────────────
SOLS = {
    "ferrallitique": {"label": "Ferrallitique (dominant en CI)", "coeff": 1.00},
    "argileux":      {"label": "Argileux",                       "coeff": 1.10},
    "limoneux":      {"label": "Limoneux",                       "coeff": 1.05},
    "hydromorphe":   {"label": "Hydromorphe (bas-fonds)",        "coeff": 1.08},
    "alluvionnaire": {"label": "Alluvionnaire",                  "coeff": 1.12},
    "lateritique":   {"label": "Latéritique",                    "coeff": 0.90},
    "sableux":       {"label": "Sableux",                        "coeff": 0.85},
}

# Plages réalistes pour la Côte d'Ivoire (curseurs de l'interface)
PLAGES_UI = {
    "pluviometrie": {"min": 300, "max": 2500, "defaut": 1200, "unite": "mm"},
    "temperature":  {"min": 18,  "max": 38,   "defaut": 27,   "unite": "°C"},
    "engrais_kg":   {"min": 0,   "max": 300,  "defaut": 50,   "unite": "kg/ha"},
}
# Plages acceptées par l'API (un peu plus larges pour rester compatible avec l'application mobile)
PLUV_API = (200, 3000)
TEMP_API = (15, 40)
