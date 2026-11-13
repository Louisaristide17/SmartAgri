"""
Données de démonstration SmartAgri.
Appelé au démarrage : ne crée les données que si le compte démo n'a encore aucune parcelle.
Ainsi, même si Render efface la base SQLite, la démo retrouve des données réalistes.
"""
import random
from datetime import datetime, timedelta, timezone

from models import Parcelle, Prediction, Conversation

# (nom, superficie ha, sol, culture, latitude, longitude, ville, statut, description)
PARCELLES = [
    ("Plantation Cacao Daloa",   4.5, "ferrallitique", "cacao",    6.8774, -6.4502, "Daloa",    "active",   "Cacaoyère de 12 ans, ombrage modéré."),
    ("Champ Riz Bouaké",         2.0, "hydromorphe",   "riz",      7.6906, -5.0303, "Bouaké",   "active",   "Bas-fond aménagé, riz irrigué."),
    ("Verger Anacarde Korhogo",  6.0, "sableux",       "anacarde", 9.4580, -5.6295, "Korhogo",  "active",   "Anacardiers de 8 ans."),
    ("Manioc Yamoussoukro",      1.5, "lateritique",   "manioc",   6.8276, -5.2893, "Yamoussoukro", "active", "Parcelle vivrière, variété améliorée."),
    ("Igname Bondoukou",         1.2, "limoneux",      "igname",   8.0402, -2.8000, "Bondoukou","en_repos", "Mise en jachère après récolte."),
    ("Hévéa San-Pédro",          8.0, "argileux",      "hevea",    4.7485, -6.6363, "San-Pédro","active",   "Hévéaculture en saignée."),
]

# rendement moyen de référence (t/ha) et pluviométrie typique (mm) par culture
REF = {
    "cacao":    (0.6, 1400), "riz": (3.5, 1200), "anacarde": (0.7, 1100),
    "manioc":  (12.0, 1300), "igname": (10.0, 1250), "hevea": (1.5, 1600),
}

MESSAGES = [
    ("user",      "Quel est le meilleur moment pour semer le riz à Bouaké ?"),
    ("assistant", "À Bouaké, le riz pluvial se sème au début de la grande saison des pluies, "
                  "généralement entre avril et mai. Pour le riz irrigué en bas-fond, un second cycle est possible en août-septembre."),
    ("user",      "Comment améliorer le rendement de mon cacao ?"),
    ("assistant", "Taillez régulièrement, maintenez un ombrage de 30 à 40 %, éliminez les cabosses malades "
                  "et apportez de la matière organique. Un conseiller agricole peut analyser votre sol."),
]


def seed_demo_data(db, user) -> bool:
    """Crée parcelles, prédictions et conversation d'exemple. Retourne True si des données ont été créées."""
    if db.query(Parcelle).filter(Parcelle.user_id == user.id).count() > 0:
        return False

    rnd = random.Random(2026)           # résultats identiques à chaque démarrage
    now = datetime.now(timezone.utc)

    parcelles = []
    for i, (nom, sup, sol, culture, lat, lon, ville, statut, desc) in enumerate(PARCELLES):
        p = Parcelle(user_id=user.id, nom=nom, superficie=sup, type_sol=sol, culture=culture,
                     latitude=lat, longitude=lon, ville=ville, statut=statut, description=desc,
                     created_at=now - timedelta(days=90 - i * 12))
        db.add(p)
        parcelles.append(p)
    db.flush()                           # récupère les identifiants

    for k in range(14):
        p = parcelles[k % len(parcelles)]
        base, pluie = REF[p.culture]
        pluvio = round(pluie * rnd.uniform(0.8, 1.2))
        temp   = round(rnd.uniform(24, 31), 1)
        engrais = round(rnd.uniform(0, 200), 1)
        rendement = round(base * rnd.uniform(0.8, 1.2) * (1 + engrais / 1500), 2)
        db.add(Prediction(
            user_id=user.id, parcelle_id=p.id, culture=p.culture,
            pluviometrie=pluvio, temperature=temp, engrais_kg=engrais,
            superficie=p.superficie, type_sol=p.type_sol,
            rendement_predit=rendement, confiance=round(rnd.uniform(78, 96), 1),
            created_at=now - timedelta(days=rnd.randint(0, 60), hours=rnd.randint(0, 23)),
        ))

    for j, (role, content) in enumerate(MESSAGES):
        db.add(Conversation(user_id=user.id, role=role, content=content,
                            created_at=now - timedelta(days=2, minutes=10 - j)))

    db.commit()
    return True
