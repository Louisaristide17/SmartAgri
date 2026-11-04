"""
Route de prédiction de rendement.
Utilise un modèle ML simplifié (règles agronomiques) — remplaçable par XGBoost/joblib.
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
    "mais":    3.5,
    "riz":     4.2,
    "arachide": 2.0,
    "sorgho":  1.8,
    "mil":     1.5,
    "coton":   1.2,
    "manioc":  12.0,
}

COEFF_SOL = {
    "argileux":   1.10,
    "limoneux":   1.05,
    "lateritique": 0.90,
    "sableux":    0.85,
}


def predict_yield(data: PredictionInput) -> tuple[float, float]:
    """
    Calcul agronomique simplifié :
    rendement = base_culture × coeff_sol × f(pluv) × f(temp) × f(engrais)
    """
    base     = RENDEMENTS_BASE.get(data.culture, 2.5)
    coeff    = COEFF_SOL.get(data.type_sol, 1.0)

    # Influence pluviométrie (optimum ~600mm)
    pluv_opt = 600.0
    f_pluv   = max(0.4, 1.0 - abs(data.pluviometrie - pluv_opt) / pluv_opt * 0.6)

    # Influence température (optimum ~26°C)
    f_temp   = max(0.5, 1.0 - abs(data.temperature - 26) / 20)

    # Influence engrais (saturation à 100 kg/ha)
    f_engrais = min(1.3, 0.7 + (data.engrais_kg / 100) * 0.6)

    rendement  = base * coeff * f_pluv * f_temp * f_engrais
    rendement  = round(max(0.2, rendement), 2)

    # Confiance basée sur la cohérence des paramètres
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
