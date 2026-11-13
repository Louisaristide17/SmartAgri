"""
Outils de l'agent AgriBot : l'agent comprend la demande, choisit un outil, l'exécute
(base de données, modèle ML) puis formule la réponse. Contrairement à un simple chatbot,
il agit sur les données de l'utilisateur.

Outils : mes_parcelles · mes_predictions · predire_rendement · cultures_de_la_zone
Garde-fous : refus des produits non homologués, hors-sujet, demandes médicales/juridiques.
"""
import re
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session

from models import Parcelle, Prediction, Conversation, User
from referentiel_ci import CULTURES, ZONES, VILLES_ZONE, SOLS, normaliser, zone_depuis_ville

CLIMAT_DEFAUT = {"sud": (1900, 27), "foret": (1500, 26.5), "centre": (1150, 27.5), "nord": (1000, 28.5)}

REFUS = [
    (r"paraquat|glyphosate pur|ddt|endosulfan|lindane|pesticide interdit|non homologu",
     "⚠️ Je vous prie de m'excuser, mais je ne peux pas vous conseiller de produits non homologués en Côte d'Ivoire : ils sont dangereux pour votre santé et vos cultures. Je vous invite aimablement à vous adresser à l'ANADER ou à un revendeur agréé, qui vous orienteront vers une solution autorisée."),
    (r"m[ée]dicament|maladie humaine|diagnostic|ordonnance|avocat|proc[èe]s|imp[ôo]t",
     "Je vous remercie de votre confiance, mais cette question sort de mon domaine (l'agriculture). Pour un avis médical ou juridique, je vous recommande respectueusement de consulter un professionnel qualifié. Je reste volontiers à votre service pour tout ce qui concerne vos cultures."),
]


def _culture_dans(texte: str) -> Optional[str]:
    t = normaliser(texte).replace("-", " ")
    alias = {"cafe": ["cafe", "caféier"], "hevea": ["hevea", "caoutchouc"], "palmier": ["palmier", "huile de palme"],
             "anacarde": ["anacarde", "cajou", "noix de cajou"], "mais": ["mais"], "cacao": ["cacao", "cacaoyer"]}
    for code in CULTURES:
        for a in alias.get(code, [code]):
            if re.search(rf"\b{a}\b", t):
                return code
    return None


def _ville_dans(texte: str) -> Optional[str]:
    t = " " + normaliser(texte) + " "
    for v in sorted(VILLES_ZONE, key=len, reverse=True):
        if f"-{v}-" in "-" + t.replace(" ", "-") + "-" or re.search(rf"\b{re.escape(v)}\b", t.replace("-", " ")):
            return v
    # tolérance aux fautes de frappe (ex. « Korogho » -> korhogo)
    from difflib import SequenceMatcher
    mots = [w for w in re.findall(r"[a-z]{4,}", t) if w not in _MOTS_COURANTS]
    meilleur, score = None, 0.0
    for w in mots:
        for v in VILLES_ZONE:
            r = SequenceMatcher(None, w, v).ratio()
            if r > score:
                meilleur, score = v, r
    return meilleur if score >= 0.82 else None


_MOTS_COURANTS = {"sols", "sol", "terre", "terres", "cacao", "mais", "riz", "cafe", "fiable", "adapte", "adaptee", "pour", "dans",
                  "quel", "quelle", "culture", "cultures", "rendement", "mes", "parcelles", "bonjour", "merci", "engrais", "pluie"}


def adequation_culture_ville(culture: str, ville: str) -> str:
    """Le sol/le climat de la ville conviennent-ils à la culture ? Verdict + estimation du modèle ML."""
    from savoir import SOLS_ZONE
    zone = zone_depuis_ville(ville)
    c = CULTURES[culture]
    apt = c["zones"].get(zone, 1.0)
    verdict = ("très bien adaptée" if apt >= 0.9 else "bien adaptée" if apt >= 0.7 else
               "moyennement adaptée" if apt >= 0.5 else "peu adaptée")
    pluie, temp = CLIMAT_DEFAUT.get(zone, (1300, 27))
    sols = SOLS_ZONE[zone][0]
    rep = (f"📍 **{c['label']} à {ville.title()}** ({ZONES[zone].split(' (')[0]}) : la zone est **{verdict}** à cette culture.\n\n"
           f"• **Sols de la zone :** {sols}\n"
           f"• **Climat typique :** environ {pluie} mm de pluie par an, {temp} °C ; le {c['label'].lower()} préfère environ {c['pluv']} mm et {c['temp']} °C.\n")
    try:
        rep += "• **Estimation du modèle :** " + predire_rendement(culture, ville).split("\n")[1].replace("**", "").strip() + "\n"
    except Exception:
        pass
    if apt < 0.7:
        meilleures = sorted(((a, v["label"]) for k, v in CULTURES.items() for z, a in [(zone, v["zones"].get(zone, 0))]), reverse=True)[:3]
        rep += "\n💡 Dans cette zone, mieux vaut privilégier : " + ", ".join(l for _, l in meilleures) + "."
    return rep + "\n\n⚠️ Indication générale : un test de sol à l'ANADER confirmera la réponse pour votre parcelle."


# ───────── Outils ─────────
def mes_parcelles(db: Session, user: User) -> str:
    ps = db.query(Parcelle).filter(Parcelle.user_id == user.id).all()
    if not ps:
        return "Vous n'avez pas encore de parcelle enregistrée."
    lignes = [f"• {p.nom} — {CULTURES.get(p.culture, {}).get('label', p.culture)}, {p.superficie} ha, sol {p.type_sol}, {p.ville or 'ville inconnue'}" for p in ps]
    total = sum(p.superficie for p in ps)
    return f"🌱 Vous avez {len(ps)} parcelle(s), {total:.1f} ha au total :\n" + "\n".join(lignes)


def mes_predictions(db: Session, user: User) -> str:
    pr = (db.query(Prediction).filter(Prediction.user_id == user.id).order_by(Prediction.created_at.desc()).limit(5).all())
    if not pr:
        return "Aucune prédiction pour l'instant. Lancez-en une depuis l'onglet Prédiction."
    lignes = [f"• {CULTURES.get(p.culture, {}).get('label', p.culture)} : {p.rendement_predit} t/ha (fiabilité {p.confiance:.0f} %)" for p in pr]
    moy = sum(p.rendement_predit for p in pr) / len(pr)
    return f"📊 Vos {len(pr)} dernières prédictions (moyenne {moy:.2f} t/ha) :\n" + "\n".join(lignes)


def predire_rendement(culture: str, ville: Optional[str], sol: str = "ferrallitique", engrais: float = 80) -> str:
    from routers.prediction_router import predict_yield
    from schemas import PredictionInput
    zone = zone_depuis_ville(ville) if ville else None
    pluie, temp = CLIMAT_DEFAUT.get(zone, (1300, 27))
    pluie = max(300, min(2500, pluie)); 
    data = PredictionInput(culture=culture, pluviometrie=pluie, temperature=temp, engrais_kg=engrais, superficie=1, type_sol=sol, ville=ville)
    rend, conf, avert = predict_yield(data, zone)
    lieu = f"{ville.title()} ({ZONES[zone]})" if zone else "conditions moyennes de Côte d'Ivoire"
    rep = (f"🔮 {CULTURES[culture]['label']} à {lieu}, sol {sol}, climat typique ({pluie:.0f} mm, {temp} °C), {engrais:.0f} kg/ha d'engrais :\n"
           f"**{rend} t/ha** estimées, fiabilité {conf:.0f} %.")
    if avert:
        rep += f"\n⚠️ {avert}"
    return rep + "\n\nAffinez avec l'onglet Prédiction (vos vraies valeurs de pluie, température, engrais)."


def cultures_de_la_zone(zone: str) -> str:
    bonnes = sorted(((c["zones"].get(zone, 0), c["label"]) for c in CULTURES.values()), reverse=True)
    top = [f"{lab}" for apt, lab in bonnes if apt >= 0.9][:6]
    return f"🌍 Zone « {ZONES[zone]} » — cultures les mieux adaptées : " + ", ".join(top) + "."


# ───────── Agent ─────────
def garde_fou(message: str) -> Optional[str]:
    """Garde-fous appliqués AVANT tout appel au LLM (produits interdits, hors-domaine)."""
    m = message.lower()
    for pattern, reponse in REFUS:
        if re.search(pattern, m):
            return reponse
    return None


def run_agent(message: str, db: Session, user: User, history: List[dict]) -> Tuple[Optional[str], List[str]]:
    """Retourne (réponse, outils utilisés). Réponse None -> laisser le LLM / la base de règles répondre."""
    m = message.lower()
    cc = conversation_courante(message, user)
    if cc:
        return cc, ["conversation"]
    for pattern, reponse in REFUS:                       # garde-fous
        if re.search(pattern, m):
            return reponse, ["garde-fou"]

    # mémoire : si la culture/ville n'est pas dans le message, reprendre celle de la conversation
    culture, ville = _culture_dans(message), _ville_dans(message)
    for h in reversed(history[-10:]):
        if h["role"] == "user" and h["content"] != message:
            culture = culture or _culture_dans(h["content"]); ville = ville or _ville_dans(h["content"])

    # « le sol de <ville> convient-il à <culture> ? » : verdict d'adéquation (culture ET ville dans le message)
    c_msg, v_msg = _culture_dans(message), _ville_dans(message)
    if c_msg and v_msg and zone_depuis_ville(v_msg) and re.search(
            r"\bsols?\b|\bterres?\b|terrain|fiable|adapt|convient|favorable|pratiqu|bon pour|bien pour|possible", m):
        return adequation_culture_ville(c_msg, v_msg), ["adequation_culture_ville (modèle ML)"]

    # sols d'une VILLE citée dans le message (et non héritée de la conversation) -> réponse locale
    ville_msg = _ville_dans(message)
    if ville_msg and zone_depuis_ville(ville_msg) and re.search(r"\bsols?\b|\bterres?\b|terrains?|pratiqu|cultivable|fertile", m):
        from savoir import fiche_sols_ville
        return fiche_sols_ville(ville_msg, zone_depuis_ville(ville_msg)), ["sols_de_la_ville"]

    if re.search(r"mes parcelles|mes champs|mes plantations|parcelles? (ai|possède|enregistr)|combien.{0,15}parcelles|liste.{0,15}parcelles", m):
        return mes_parcelles(db, user), ["mes_parcelles"]
    if re.search(r"mes pr[ée]dictions|mon historique|derni[èe]res? pr[ée]diction", m):
        return mes_predictions(db, user), ["mes_predictions"]
    if re.search(r"(combien|quel).*(rend|produ|r[ée]colt)|pr[ée]di|estim|rendement|^\s*et (pour|avec|si|le|la|l')", m) and culture:
        return predire_rendement(culture, ville), ["predire_rendement (modèle ML)"]
    if re.search(r"que (planter|cultiver)|quelle culture|quoi (planter|cultiver)|adapt", m) and ville:
        z = zone_depuis_ville(ville)
        if z:
            return cultures_de_la_zone(z), ["cultures_de_la_zone"]
    # question ciblée sur UN sol, UNE culture, UNE structure : on répond uniquement sur cet élément
    from savoir import reponse_ciblee
    cible = reponse_ciblee(message, _culture_dans(message))
    if cible:
        return cible, ["fiche ciblée"]
    return None, []



# ───────── Politesse et conversation courante ─────────
import hashlib

def _prenom(user) -> str:
    return (getattr(user, "firstname", "") or "").strip().title()

def _choix(options: List[str], graine: str) -> str:
    """Choix stable (pas de répétition mécanique d'une même formule)."""
    return options[int(hashlib.md5(graine.encode()).hexdigest(), 16) % len(options)]

def conversation_courante(message: str, user) -> Optional[str]:
    """Salutations, remerciements, au revoir, 'comment ça va', présentation : réponse chaleureuse immédiate."""
    m = normaliser(message).replace("-", " ").strip()
    p = _prenom(user)
    nom = f" {p}" if p else ""
    if re.fullmatch(r"(bonjour|bonsoir|salut|coucou|hello|bjr|bsr|allo)( agribot| a tous| tout le monde)?", m):
        return (f"Bonjour{nom} ! 🌱 Je suis ravi de vous accueillir. Je suis AgriBot, votre assistant agricole pour la Côte d'Ivoire.\n\n"
                "Je peux, avec plaisir :\n"
                "• vous parler de vos parcelles et de vos prédictions ;\n"
                "• estimer le rendement d'une culture (par exemple : « Quel rendement pour le cacao à Daloa ? ») ;\n"
                "• vous conseiller sur les engrais, les maladies, les semis ou l'irrigation.\n\n"
                "Comment puis-je vous aider aujourd'hui ?")
    if re.search(r"\b(merci|remercie|thanks|c est gentil|je te remercie)\b", m):
        return _choix([f"Avec grand plaisir{nom} ! 😊 C'est un honneur de vous accompagner. N'hésitez surtout pas si vous avez d'autres questions.",
                       f"Je vous en prie{nom}, tout le plaisir est pour moi ! 🌿 Je reste à votre entière disposition.",
                       f"Merci à vous{nom} pour votre confiance ! Je suis là chaque fois que vous avez besoin d'un conseil."], m)
    if re.search(r"\b(au revoir|a bientot|a plus|bonne journee|bonne soiree|bye|a demain)\b", m):
        return f"Au revoir{nom} et bonne continuation ! 🌾 Je vous souhaite de belles récoltes. À très bientôt !"
    if re.search(r"(comment (vas|allez|va) (tu|vous)|ca va|comment ca va|tu vas bien)", m):
        return f"Je vous remercie de prendre de mes nouvelles, je vais très bien{nom} ! 😊 Et vous, j'espère que vos cultures se portent bien ? Dites-moi comment je peux vous aider."
    if re.search(r"(qui es tu|qui etes vous|tu es qui|presente toi|que sais tu faire|que peux tu faire|tu peux faire quoi|aide|help)", m):
        return ("Je suis AgriBot 🤖🌱, l'assistant agricole de SmartAgri, dédié à la Côte d'Ivoire. Avec plaisir, voici ce que je sais faire :\n"
                "• consulter vos parcelles et vos dernières prédictions ;\n"
                "• estimer le rendement d'une culture grâce au modèle d'intelligence artificielle ;\n"
                "• indiquer les cultures adaptées à votre zone ;\n"
                "• répondre à vos questions sur les engrais, maladies, semis et irrigation.\n\n"
                "Que souhaitez-vous savoir ?")
    if re.search(r"\b(api|intelligence artificielle|\bia\b|machine learning|modele|chatgpt|claude|deepseek|groq|technologie|comment tu fonctionnes|comment fonctionnes)\b", m):
        return ("Avec plaisir ! 🤖 Je fonctionne grâce à l'**API SmartAgri** (développée avec FastAPI) : "
                "elle me donne accès à vos parcelles et à vos prédictions, et au **modèle de machine learning** entraîné sur les cultures de la Côte d'Ivoire "
                "pour estimer les rendements.\n\n"
                "Pour comprendre et rédiger les réponses, je peux aussi m'appuyer sur un modèle de langage via une API externe (Claude, DeepSeek ou Groq), "
                "quand l'administrateur de l'application l'a activé ; sinon, je réponds avec mes règles et ma base de connaissances agricoles.\n\n"
                "Si vous le souhaitez, je peux vous aider sur vos cultures : rendement, sols, engrais, maladies, semis. Que souhaitez-vous savoir ?")
    return None


def politesse(texte: str, message: str, user, outils: List[str]) -> str:
    """Ajoute une formule d'accueil et de clôture courtoises autour d'une réponse factuelle."""
    if not texte or outils == ["conversation"]:
        return texte
    nom = f" {_prenom(user)}" if _prenom(user) else ""
    debut = _choix([f"Avec plaisir{nom} ! ", f"Certainement{nom}, voici ce que je peux vous dire. ",
                    f"Très volontiers{nom} ! ", f"Je vous remercie de votre question{nom}. "], message + "d")
    fin = _choix(["Je reste à votre disposition pour toute autre question. 🌿",
                  "N'hésitez pas à me demander des précisions, ce sera un plaisir de vous aider. 🌱",
                  "Si vous le souhaitez, je peux vous détailler n'importe quel point. 🌾",
                  "Je vous souhaite une excellente récolte ! 🌽 Je suis là si vous avez besoin de moi."], message + "f")
    if outils == ["garde-fou"]:
        return texte
    return f"{debut}\n\n{texte}\n\n{fin}"
