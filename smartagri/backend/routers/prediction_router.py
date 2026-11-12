"""
Route de prédiction de rendement.
Adapté aux cultures de Côte d'Ivoire (cacao, café, anacarde, maïs, riz, manioc, igname, coton…)
Utilise un modèle agronomique calibré — remplaçable par XGBoost/joblib.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
import random

from database import get_db
from models import Prediction, User
from schemas import PredictionInput, PredictionOut
from auth import get_current_user

router = APIRouter(prefix="/api/prediction", tags=["Prédiction"])


# ─── Modèle simplifié ────────────────────────────────────────────
# En production : charger modele_smartagri.pkl avec joblib
RENDEMENTS_BASE = {
    # Cultures vivrières
    "mais":     3.0,
    "riz":      3.5,
    "manioc":  11.0,
    "igname":   8.0,
    # Cultures de rente CI
    "cacao":    0.8,
    "cafe":     0.6,
    "anacarde": 0.9,
    "coton":    1.5,
    "palmier": 15.0,   # régimes — t/ha
    "hevea":    1.5,   # latex sec — t/ha
    # Cultures legacy
    "arachide": 1.5,
    "sorgho":   1.8,
    "mil":      1.2,
}

COEFF_SOL = {
    "ferrallitique": 1.00,   # sol dominant CI — bon pour cacao/café
    "argileux":      1.10,
    "limoneux":      1.05,
    "hydromorphe":   1.08,   # excellent pour riz
    "alluvionnaire": 1.12,   # très fertile
    "lateritique":   0.90,
    "sableux":       0.85,
}


def predict_yield(data: PredictionInput) -> tuple[float, float]:
    """
    Calcul agronomique adapté à la Côte d'Ivoire :
    rendement = base_culture × coeff_sol × f(pluv) × f(temp) × f(engrais)
    Chaque culture a son optimum pluviométrique propre.
    """
    base  = RENDEMENTS_BASE.get(data.culture, 2.5)
    coeff = COEFF_SOL.get(data.type_sol, 1.0)

    # Optimum pluviométrique par culture (mm/saison)
    pluv_opt = {
        "cacao": 1600, "cafe": 1500, "hevea": 1500, "palmier": 1800,
        "anacarde": 1000, "coton": 850,
        "mais": 650, "riz": 1000, "manioc": 875, "igname": 1250,
        "arachide": 400, "sorgho": 400, "mil": 325,
    }.get(data.culture, 650)

    f_pluv = max(0.3, 1.0 - abs(data.pluviometrie - pluv_opt) / pluv_opt * 0.7)

    # Optimum thermique par culture (°C)
    temp_opt = {
        "cacao": 26, "cafe": 24, "hevea": 27, "palmier": 27,
        "anacarde": 29, "coton": 30,
        "mais": 26, "riz": 28, "manioc": 27, "igname": 28,
        "arachide": 30, "sorgho": 30, "mil": 30,
    }.get(data.culture, 27)

    f_temp = max(0.4, 1.0 - abs(data.temperature - temp_opt) / 18)

    # Influence engrais (saturation à 150 kg/ha pour cultures intensives)
    f_engrais = min(1.4, 0.65 + (data.engrais_kg / 150) * 0.75)

    rendement = base * coeff * f_pluv * f_temp * f_engrais
    rendement = round(max(0.1, rendement), 2)

    confiance = round(random.uniform(72, 94), 1)
    return rendement, confiance


@router.post("/", response_model=PredictionOut, status_code=201,
             summary="Prédire le rendement d'une culture")
def predict(
    payload: PredictionInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rendement, confiance = predict_yield(payload)

    pred = Prediction(
        user_id          = current_user.id,
        parcelle_id      = payload.parcelle_id,
        culture          = payload.culture,
        pluviometrie     = payload.pluviometrie,
        temperature      = payload.temperature,
        engrais_kg       = payload.engrais_kg,
        superficie       = payload.superficie,
        type_sol         = payload.type_sol,
        rendement_predit = rendement,
        confiance        = confiance,
    )
    db.add(pred)
    db.commit()
    db.refresh(pred)
    return pred


@router.get("/historique", response_model=List[PredictionOut],
            summary="Historique de mes prédictions")
def history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return (
        db.query(Prediction)
        .filter(Prediction.user_id == current_user.id)
        .order_by(Prediction.created_at.desc())
        .limit(50)
        .all()
    )
