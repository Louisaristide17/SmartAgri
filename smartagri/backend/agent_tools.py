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
     "⚠️ Je ne peux pas conseiller de produits non homologués en Côte d'Ivoire. Adressez-vous à l'ANADER ou à un revendeur agréé."),
    (r"m[ée]dicament|maladie humaine|diagnostic|ordonnance|avocat|proc[èe]s|imp[ôo]t",
     "Cette question sort de mon domaine (agriculture). Pour un avis médical ou juridique, consultez un professionnel."),
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
    return None


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
def run_agent(message: str, db: Session, user: User, history: List[dict]) -> Tuple[Optional[str], List[str]]:
    """Retourne (réponse, outils utilisés). Réponse None -> laisser le LLM / la base de règles répondre."""
    m = message.lower()
    for pattern, reponse in REFUS:                       # garde-fous
        if re.search(pattern, m):
            return reponse, ["garde-fou"]

    # mémoire : si la culture/ville n'est pas dans le message, reprendre celle de la conversation
    culture, ville = _culture_dans(message), _ville_dans(message)
    for h in reversed(history[-10:]):
        if h["role"] == "user" and h["content"] != message:
            culture = culture or _culture_dans(h["content"]); ville = ville or _ville_dans(h["content"])

    if re.search(r"mes parcelles|mes champs|combien de parcelles|mes plantations", m):
        return mes_parcelles(db, user), ["mes_parcelles"]
    if re.search(r"mes pr[ée]dictions|mon historique|derni[èe]res? pr[ée]diction", m):
        return mes_predictions(db, user), ["mes_predictions"]
    if re.search(r"(combien|quel).*(rend|produ|r[ée]colt)|pr[ée]di|estim|rendement|^\s*et (pour|avec|si|le|la|l')", m) and culture:
        return predire_rendement(culture, ville), ["predire_rendement (modèle ML)"]
    if re.search(r"que (planter|cultiver)|quelle culture|quoi (planter|cultiver)|adapt", m) and ville:
        z = zone_depuis_ville(ville)
        if z:
            return cultures_de_la_zone(z), ["cultures_de_la_zone"]
    return None, []
