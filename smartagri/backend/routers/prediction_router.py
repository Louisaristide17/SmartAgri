"""
Route de prédiction de rendement — spécifique à la Côte d'Ivoire.
Le calcul tient compte : de la culture, du sol, de la pluviométrie, de la température,
de l'engrais et de la zone agro-écologique de la parcelle (Sud, Forêt, Centre, Nord).
Modèle Gradient Boosting (scikit-learn) chargé depuis ml/model.joblib ; formule agronomique en secours.
"""
from pathlib import Path
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple

from database import get_db
from models import Prediction, Parcelle, User
from schemas import PredictionInput, PredictionOut
from auth import get_current_user
from referentiel_ci import (
    CULTURES, SOLS, ZONES, PLAGES_UI, zone_depuis_ville,
)

router = APIRouter(prefix="/api/prediction", tags=["Prédiction"])

# ── Modèle de Machine Learning (entraîné par ml/train_model.py) ──
_MODEL_PATH = Path(__file__).resolve().parent.parent / "ml" / "model.joblib"
_MODEL = None
try:
    import joblib, pandas as pd
    if _MODEL_PATH.exists():
        _MODEL = joblib.load(_MODEL_PATH)
except Exception as exc:                      # sklearn absent ou fichier illisible -> repli sur la formule
    print(f"[SmartAgri] modèle ML indisponible, formule agronomique utilisée : {exc}")


def _predict_ml(data, zone) -> Optional[float]:
    if _MODEL is None or data.culture not in CULTURES:
        return None
    try:
        X = pd.DataFrame([{"culture": data.culture, "type_sol": data.type_sol, "zone": zone or "inconnue",
                           "pluviometrie": data.pluviometrie, "temperature": data.temperature,
                           "engrais_kg": data.engrais_kg}])
        return round(max(0.1, float(_MODEL.predict(X)[0])), 2)
    except Exception:
        return None


def predict_yield(data: PredictionInput, zone: Optional[str]) -> Tuple[float, float, Optional[str]]:
    """
    rendement = base × coeff_sol × f(pluie) × f(température) × f(engrais) × aptitude_zone
    Retourne (rendement t/ha, confiance %, avertissement éventuel).
    """
    c = CULTURES.get(data.culture)
    base      = c["base"] if c else 2.5
    pluv_opt  = c["pluv"] if c else 800
    temp_opt  = c["temp"] if c else 27
    coeff_sol = SOLS.get(data.type_sol, {}).get("coeff", 1.0)

    dev_pluv = abs(data.pluviometrie - pluv_opt) / pluv_opt
    f_pluv   = max(0.3, 1.0 - dev_pluv * 0.7)

    dev_temp = abs(data.temperature - temp_opt) / 18
    f_temp   = max(0.4, 1.0 - dev_temp)

    f_engrais = min(1.4, 0.65 + (data.engrais_kg / 150) * 0.75)

    apt_zone = c["zones"].get(zone, 1.0) if (c and zone) else 1.0

    rendement_regles = round(max(0.1, base * coeff_sol * f_pluv * f_temp * f_engrais * apt_zone), 2)
    rendement = _predict_ml(data, zone) or rendement_regles   # ML en priorité, formule en secours

    # Confiance : d'autant plus faible que les conditions s'écartent de l'optimum ivoirien
    confiance = 93 - min(18, dev_pluv * 20) - min(15, dev_temp * 25)
    if zone and apt_zone < 0.7:
        confiance -= 10
    confiance = round(max(55.0, min(95.0, confiance)), 1)

    avertissement = None
    if c and zone and apt_zone < 0.6:
        avertissement = (
            f"{c['label']} est peu adapté à la zone « {ZONES[zone]} » en Côte d'Ivoire : "
            "le rendement est fortement réduit."
        )
    return rendement, confiance, avertissement


@router.get("/referentiel", summary="Cultures, sols, zones et plages de la Côte d'Ivoire")
def referentiel():
    """Listes utilisées par le web et le mobile (une seule source de vérité)."""
    return {
        "pays": "Côte d'Ivoire",
        "cultures": [{"code": k, "label": v["label"], "emoji": v["emoji"]} for k, v in CULTURES.items()],
        "sols":     [{"code": k, "label": v["label"]} for k, v in SOLS.items()],
        "zones":    [{"code": k, "label": v} for k, v in ZONES.items()],
        "plages":   PLAGES_UI,
    }


@router.get("/zone", summary="Zone agro-écologique d'une position GPS (Côte d'Ivoire)")
def zone_gps(latitude: float, longitude: float):
    """Utilisé par le mobile : le GPS du téléphone -> zone (Sud, Forêt, Centre, Nord) + cultures conseillées."""
    if not (4.0 <= latitude <= 10.8 and -8.7 <= longitude <= -2.4):
        return {"dans_le_pays": False, "message": "Position hors de la Côte d'Ivoire."}
    z = zone_depuis_ville(None, latitude)
    top = sorted(CULTURES.items(), key=lambda kv: -kv[1]["zones"].get(z, 0))[:4]
    return {"dans_le_pays": True, "zone": z, "zone_label": ZONES[z],
            "cultures_conseillees": [v["label"] for _, v in top]}


@router.post("/", response_model=PredictionOut, status_code=201,
             summary="Prédire le rendement d'une culture (Côte d'Ivoire)")
def predict(
    payload: PredictionInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Zone agro-écologique : ville envoyée, sinon ville/latitude de la parcelle liée
    ville, lat = payload.ville, None
    if payload.parcelle_id:
        parc = db.query(Parcelle).filter(Parcelle.id == payload.parcelle_id,
                                         Parcelle.user_id == current_user.id).first()
        if parc:
            ville = ville or parc.ville
            lat = parc.latitude
    zone = zone_depuis_ville(ville, lat)

    rendement, confiance, avertissement = predict_yield(payload, zone)

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

    out = PredictionOut.model_validate(pred)
    out.zone = ZONES.get(zone) if zone else None
    out.avertissement = avertissement
    return out


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
