"""Réponses CIBLÉES d'AgriBot : si la question porte sur UN sol, UNE culture ou UNE structure,
on répond uniquement sur cet élément (et non sur toute la liste)."""
import re
from typing import Optional
from referentiel_ci import CULTURES, ZONES, normaliser

SOLS_INFO = {
    "argileux": {
        "nom": "Sol argileux",
        "def": "un sol à texture fine, riche en argile (plus d'un tiers de particules très fines).",
        "caract": ["retient très bien l'eau et les éléments nutritifs (fertilité chimique souvent bonne)",
                   "lourd et collant quand il est humide, dur et fissuré en saison sèche",
                   "draine lentement : risque d'asphyxie des racines et d'engorgement"],
        "cultures": "riz (bas-fonds), bananier, cacao sur sol argilo-limoneux profond, canne à sucre",
        "conseils": ["travaillez-le à bonne humidité (ni trop mouillé, ni trop sec)", "prévoyez un drainage ou des billons/buttes",
                     "apportez de la matière organique (compost, fumier) pour l'aérer"],
    },
    "sableux": {
        "nom": "Sol sableux",
        "def": "un sol à texture grossière, composé surtout de sable.",
        "caract": ["léger et facile à travailler", "laisse l'eau s'infiltrer très vite : il se dessèche rapidement",
                   "pauvre en éléments nutritifs et en matière organique, qui sont lessivés par la pluie"],
        "cultures": "arachide, manioc, anacarde, pastèque, mil",
        "conseils": ["fractionnez les apports d'engrais en plusieurs fois", "paillez le sol pour garder l'humidité",
                     "enrichissez-le en compost ou fumier"],
    },
    "limoneux": {
        "nom": "Sol limoneux",
        "def": "un sol équilibré, à particules moyennes, entre le sable et l'argile.",
        "caract": ["bonne rétention d'eau tout en drainant correctement", "généralement fertile et facile à travailler",
                   "sensible à la battance (croûte en surface après de fortes pluies) et à l'érosion"],
        "cultures": "maïs, igname, légumes, riz pluvial, cultures vivrières en général",
        "conseils": ["protégez-le par une couverture végétale ou un paillage", "évitez le tassement par les machines et le piétinement"],
    },
    "lateritique": {
        "nom": "Sol latéritique",
        "def": "un sol rouge ou brun-rouge, riche en fer et en aluminium, fréquent en savane et au centre du pays.",
        "caract": ["souvent acide et pauvre en phosphore", "peut contenir des graviers ou une couche durcie en profondeur",
                   "fragile : s'érode facilement une fois mis à nu"],
        "cultures": "anacarde, manioc, igname, mil, sorgho, arachide",
        "conseils": ["apportez des phosphates et de la matière organique", "corrigez l'acidité si nécessaire (chaulage, sur conseil ANADER)",
                     "limitez l'érosion avec des cordons pierreux ou un couvert végétal"],
    },
    "ferrallitique": {
        "nom": "Sol ferrallitique",
        "def": "un sol rouge ou jaune, profond et très ancien, typique des régions forestières humides du Sud et de l'Ouest.",
        "caract": ["profond et bien drainé", "acide et naturellement pauvre en éléments minéraux",
                   "sa fertilité repose surtout sur la litière de la forêt (matière organique)"],
        "cultures": "cacao, café, hévéa, palmier à huile, banane plantain",
        "conseils": ["conservez l'ombrage et la litière (paillage)", "apportez des engrais adaptés (NPK) selon le test de sol",
                     "protégez-le de l'érosion sur les pentes"],
    },
    "hydromorphe": {
        "nom": "Sol hydromorphe",
        "def": "un sol régulièrement gorgé d'eau, typique des bas-fonds et des plaines inondables.",
        "caract": ["engorgé une grande partie de l'année", "couleur grise avec des taches de rouille",
                   "pauvre en oxygène, mais souvent riche en matière organique"],
        "cultures": "riz de bas-fond, cultures maraîchères en saison sèche, canne à sucre",
        "conseils": ["aménagez le bas-fond (diguettes, drains) pour contrôler l'eau", "évitez les cultures qui craignent l'eau stagnante (manioc, igname)"],
    },
    "alluvionnaire": {
        "nom": "Sol alluvionnaire",
        "def": "un sol formé par les dépôts des rivières et fleuves dans les vallées.",
        "caract": ["très fertile (apports réguliers de limons)", "souvent limono-sableux et facile à travailler",
                   "peut être inondé pendant les crues"],
        "cultures": "maraîchage, maïs, riz, canne à sucre, banane",
        "conseils": ["profitez de la décrue pour les semis", "surveillez le calendrier des crues et le drainage"],
    },
}
_ALIAS_SOL = {"argileux": ["argileux", "argileuse", "argile", "argilo"], "sableux": ["sableux", "sableuse", "sable"],
              "limoneux": ["limoneux", "limoneuse", "limon"], "lateritique": ["lateritique", "laterite", "lateritiques"],
              "ferrallitique": ["ferrallitique", "ferralitique", "ferrallitiques"], "hydromorphe": ["hydromorphe", "hydromorphes"],
              "alluvionnaire": ["alluvionnaire", "alluvial", "alluviaux", "alluvion", "alluvions"]}

CULTURES_INFO = {
    "cacao": ("première culture de rente du pays (la Côte d'Ivoire est 1er producteur mondial)", "ferrallitique ou argilo-limoneux profond, bien drainé",
              "ombragez les jeunes plants, taillez et élaguez, récoltez les cabosses mûres, surveillez la pourriture brune et le swollen shoot"),
    "cafe": ("culture de rente, surtout le Robusta, cultivée au Centre et à l'Ouest", "ferrallitique profond et bien drainé",
             "taille d'entretien, ombrage léger, récolte des cerises bien mûres"),
    "hevea": ("arbre à caoutchouc naturel, en forte expansion", "profond et bien drainé (ferrallitique)",
              "saignée régulière une fois l'arbre mature, entretien de la plantation, lutte contre les maladies des feuilles"),
    "palmier": ("palmier à huile (huile de palme et palmiste), surtout dans le Sud", "profond, frais et riche en matière organique",
                "fertilisation (potasse notamment), récolte des régimes mûrs, entretien du pourtour des palmiers"),
    "anacarde": ("noix de cajou : la Côte d'Ivoire en est l'un des premiers producteurs mondiaux, surtout au Nord et au Centre", "léger, sableux ou latéritique, bien drainé",
                 "peu exigeant en eau, taille de formation, récolte des noix tombées à maturité"),
    "coton": ("culture de rente de la savane du Nord", "limoneux ou limono-sableux, profond",
              "semis en début de saison des pluies, sarclages, traitements contre les insectes selon les conseils de la filière"),
    "mais": ("céréale de base cultivée presque partout", "limoneux, fertile et bien drainé",
             "semis en début de saison des pluies, fumure NPK puis urée, sarclages précoces"),
    "riz": ("céréale de base, en pluvial, bas-fond ou irrigué", "argileux ou hydromorphe (bas-fonds) pour le riz inondé",
            "bonne maîtrise de l'eau, repiquage ou semis en ligne, désherbage régulier"),
    "manioc": ("tubercule vivrier très rustique", "léger, sableux ou latéritique ; il craint l'eau stagnante",
               "plantez des boutures saines, buttez, récoltez entre 8 et 12 mois selon la variété"),
    "igname": ("tubercule vivrier très apprécié, important au Centre et au Nord", "limoneux ou latéritique profond, meuble",
               "plantez sur buttes, tuteurez les lianes, paillez pendant la saison sèche"),
    "arachide": ("légumineuse vivrière et de rente", "léger et sableux, bien drainé",
                 "semis en début de saison des pluies, buttage, récolte à maturité pour éviter les moisissures"),
    "sorgho": ("céréale résistante à la sécheresse du Nord", "tous sols, même pauvres", "semis en début de pluies, démariage et sarclages"),
    "mil": ("céréale très résistante à la sécheresse, cultivée au Nord", "sableux à limono-sableux", "semis en début de pluies, démariage, sarclages"),
}

STRUCTURES = {
    "anader": "🏛️ **ANADER** (Agence Nationale d'Appui au Développement Rural) : elle fournit des conseils techniques aux agriculteurs, des formations et des tests de sol, dans toutes les régions.\n📞 +225 27 22 48 36 00",
    "firca": "🏛️ **FIRCA** (Fonds Interprofessionnel pour la Recherche et le Conseil Agricoles) : il finance la recherche et le conseil agricole pour les filières.",
    "ccc": "🏛️ **CCC** (Conseil du Coton et de l'Anacarde) : il régule et accompagne les filières coton et anacarde, surtout dans le Nord.",
    "cgfcc": "🏛️ **Conseil Café-Cacao** : il régule la filière café-cacao (prix, qualité, organisation des producteurs).",
    "coopagri": "🏛️ **COOPAGRI CI** : réseau de coopératives agricoles pour s'organiser, mutualiser les achats et vendre ensemble.",
}

_INFO = r"(c est quoi|qu est ce|qu est-ce|definition|definis|explique|parle|presente|dis moi|informations?|infos?|caracteris|decri|qu'est|que savoir|savoir sur|cultiver|conseils?|comment)"


def _sol(texte: str) -> Optional[str]:
    t = normaliser(texte).replace("-", " ")
    for code, alias in _ALIAS_SOL.items():
        if any(re.search(rf"\b{a}\b", t) for a in alias):
            return code
    return None


def fiche_sol(code: str) -> str:
    s = SOLS_INFO[code]
    return (f"🌍 **{s['nom']}** : c'est {s['def']}\n\n**Ses caractéristiques :**\n" + "\n".join(f"• {c}" for c in s["caract"]) +
            f"\n\n**Cultures qui s'y plaisent :** {s['cultures']}.\n\n**Nos conseils :**\n" + "\n".join(f"• {c}" for c in s["conseils"]) +
            "\n\n💡 Un test de sol à l'ANADER vous donnera des conseils précis pour votre parcelle.")


def fiche_culture(code: str) -> str:
    desc, sol, conseils = CULTURES_INFO[code]
    c = CULTURES[code]
    bonnes = [ZONES[z].split(" (")[0] for z, a in c["zones"].items() if a >= 0.9]
    return (f"{c['emoji']} **{c['label']}** : {desc}.\n\n"
            f"• **Zones les mieux adaptées :** {', '.join(bonnes) if bonnes else 'voir les zones moyennement adaptées'}\n"
            f"• **Climat idéal :** environ {c['pluv']} mm de pluie par an et {c['temp']} °C\n"
            f"• **Sol conseillé :** {sol}\n"
            f"• **Entretien :** {conseils}\n\n"
            f"🔮 Pour une estimation de rendement, demandez par exemple : « Quel rendement pour {c['label'].lower()} à Daloa ? »")


def reponse_ciblee(message: str, culture: Optional[str]) -> Optional[str]:
    """Répond uniquement sur l'élément demandé. None si la question n'est pas ciblée."""
    t = normaliser(message).replace("-", " ")
    for k, txt in STRUCTURES.items():
        if re.search(rf"\b{k}\b", t):
            return txt
    if culture and re.search(r"\bsols?\b", t) and re.search(r"(quel|quels|meilleur|convient|adapte|type de sol|pour)", t) and not _sol(message):
        desc, sol_c, _ = CULTURES_INFO[culture]
        c = CULTURES[culture]
        return (f"{c['emoji']} **Quel sol pour le {c['label'].lower()} ?**\n\n"
                f"Le sol conseillé est : **{sol_c}**.\n\n"
                f"💡 Pour comprendre un type de sol en détail, demandez par exemple : « C'est quoi un sol ferrallitique ? ». "
                "Un test de sol à l'ANADER confirmera ce qui convient à votre parcelle.")
    sol = _sol(message)
    if sol and not culture:
        return fiche_sol(sol)
    if sol and culture and re.search(r"(c est quoi|qu est ce|definition|caracteris)", t):
        return fiche_sol(sol)
    if culture and re.search(_INFO, t) and not re.search(r"(rendement|combien|predi|estim)", t):
        return fiche_culture(culture)
    return None


def focaliser(reponse: str, message: str) -> str:
    """Filet de sécurité : si une réponse liste plusieurs puces et que la question vise UNE d'entre elles,
    on ne garde que celle-ci (avec son titre et sa note finale)."""
    lignes = reponse.split("\n")
    debuts = [i for i, l in enumerate(lignes) if l.lstrip().startswith("• ")]
    if len(debuts) < 2:
        return reponse
    entete = lignes[:debuts[0]]
    blocs = []
    for k, d in enumerate(debuts):
        fin = debuts[k + 1] if k + 1 < len(debuts) else len(lignes)
        bloc = lignes[d:fin]
        pied = []
        if k + 1 == len(debuts):                       # dernier bloc : ce qui suit une ligne vide est la note finale
            for j, l in enumerate(bloc):
                if l.strip() == "":
                    bloc, pied = bloc[:j], bloc[j:]
                    break
        while bloc and bloc[-1].strip() == "":
            bloc = bloc[:-1]
        blocs.append((bloc, pied))
    pied_final = blocs[-1][1]
    t = " " + normaliser(message).replace("-", " ") + " "
    gardes = []
    for bloc, _ in blocs:
        m = re.search(r"\*\*(.+?)\*\*", bloc[0])
        if not m:
            continue
        mots = [w for w in normaliser(m.group(1)).replace("-", " ").replace("(", " ").replace(")", " ").split()
                if len(w) >= 3 and w not in ("zone", "sol", "sols", "culture", "cultures", "les", "des", "pour", "sec", "secs")]
        if any(f" {w} " in t for w in mots):
            gardes.append(bloc)
    if not gardes or len(gardes) == len(blocs):
        return reponse
    sortie = [l for l in entete if "Consultez la section" not in l] if False else entete
    for b in gardes:
        sortie += b
    return "\n".join(sortie + pied_final)


# ───────── Sols d'une ville (réponse locale, pas la liste générale) ─────────
SOLS_ZONE = {
    "sud": ("sols sableux côtiers et sols ferrallitiques sableux, avec des bas-fonds hydromorphes (lagunes)",
            "cocotier, palmier à huile, hévéa, ananas, banane, maraîchage",
            "sols légers qui retiennent mal l'eau et les engrais : fractionnez les apports et apportez de la matière organique"),
    "foret": ("sols ferrallitiques (profonds, acides, assez pauvres en éléments minéraux) et des bas-fonds hydromorphes",
              "cacao, café, hévéa, banane plantain, igname, manioc ; riz dans les bas-fonds",
              "corrigez l'acidité (chaulage), apportez de l'engrais et gardez un couvert végétal contre l'érosion"),
    "centre": ("sols ferrallitiques jaunes à gravillons et sols de transition forêt-savane, avec des bas-fonds humides",
               "igname, manioc, maïs, riz de bas-fonds, café, anacarde, coton",
               "sols assez vite épuisés : alternez les cultures, laissez des jachères et enrichissez en matière organique"),
    "nord": ("sols ferrugineux tropicaux, souvent gravillonnaires et peu profonds, avec des bas-fonds alluviaux fertiles",
             "coton, anacarde, maïs, sorgho, mil, igname ; riz dans les bas-fonds",
             "sols pauvres en matière organique : fumure organique, paillage et gestion de l'eau sont indispensables"),
}
NOTES_VILLE = {
    "man": "La région de Man est montagneuse (Dix-Huit Montagnes) : sur les pentes, le risque d'érosion est élevé, d'où l'intérêt des cultures en courbes de niveau et d'un couvert végétal ; les bas-fonds conviennent bien au riz et au maraîchage.",
}


def fiche_sols_ville(ville: str, zone: str) -> str:
    sols, cultures, conseil = SOLS_ZONE[zone]
    note = NOTES_VILLE.get(ville)
    return (f"📍 **Les sols de {ville.title()}** ({ZONES[zone].split(' (')[0]}) :\n\n"
            f"Oui, ils sont cultivables. On y trouve surtout des {sols}.\n\n"
            f"• **Cultures qui y réussissent :** {cultures}\n"
            f"• **Conseil :** {conseil}\n"
            + (f"• **À savoir :** {note}\n" if note else "")
            + "\n💡 Ces informations sont indicatives : un test de sol à l'ANADER vous donnera la réponse exacte pour votre parcelle.")
