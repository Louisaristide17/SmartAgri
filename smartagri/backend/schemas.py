"""
Schémas Pydantic — validation des données entrantes et sortantes de l'API.
"""
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime


# ─────────────────────────────────────────
#  AUTH
# ─────────────────────────────────────────

class UserCreate(BaseModel):
    firstname: str
    lastname:  str
    email:     EmailStr
    password:  str
    phone:     Optional[str] = None
    role:      Optional[str] = "agriculteur"

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères.")
        return v

    @field_validator("role")
    @classmethod
    def role_valid(cls, v):
        allowed = {"agriculteur", "cooperative", "conseiller", "chercheur"}
        if v not in allowed:
            raise ValueError(f"Rôle invalide. Valeurs acceptées : {allowed}")
        return v


class UserLogin(BaseModel):
    email:    EmailStr
    password: str


class UserOut(BaseModel):
    id:         int
    firstname:  str
    lastname:   str
    email:      str
    phone:      Optional[str]
    role:       str
    is_active:  bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token:  str
    token_type:    str = "bearer"
    user:          UserOut


class TokenData(BaseModel):
    user_id: Optional[int] = None


# ─────────────────────────────────────────
#  PARCELLES
# ─────────────────────────────────────────

class ParcelleCreate(BaseModel):
    nom:        str
    superficie: float
    type_sol:   str
    culture:    str
    latitude:   Optional[float] = None
    longitude:  Optional[float] = None
    ville:      Optional[str]   = None
    statut:     Optional[str]   = "active"
    description: Optional[str] = None

    @field_validator("type_sol")
    @classmethod
    def sol_valid(cls, v):
        allowed = {"sableux", "argileux", "limoneux", "lateritique", "ferrallitique", "hydromorphe", "alluvionnaire"}
        if v not in allowed:
            raise ValueError(f"Type de sol invalide. Valeurs : {allowed}")
        return v

    @field_validator("culture")
    @classmethod
    def culture_valid(cls, v):
        allowed = {
            # Cultures vivrières
            "mais", "riz", "manioc", "igname",
            # Cultures de rente CI
            "cacao", "cafe", "anacarde", "coton", "palmier", "hevea",
            # Cultures legacy (compatibilité)
            "arachide", "sorgho", "mil",
        }
        if v not in allowed:
            raise ValueError(f"Culture invalide. Valeurs : {allowed}")
        return v

    @field_validator("superficie")
    @classmethod
    def superficie_positive(cls, v):
        if v <= 0:
            raise ValueError("La superficie doit être positive.")
        return v


class ParcelleUpdate(BaseModel):
    nom:         Optional[str]   = None
    superficie:  Optional[float] = None
    type_sol:    Optional[str]   = None
    culture:     Optional[str]   = None
    latitude:    Optional[float] = None
    longitude:   Optional[float] = None
    ville:       Optional[str]   = None
    statut:      Optional[str]   = None
    description: Optional[str]   = None


class ParcelleOut(BaseModel):
    id:          int
    nom:         str
    superficie:  float
    type_sol:    str
    culture:     str
    latitude:    Optional[float]
    longitude:   Optional[float]
    ville:       Optional[str]
    statut:      str
    description: Optional[str]
    created_at:  datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
#  PRÉDICTIONS
# ─────────────────────────────────────────

class PredictionInput(BaseModel):
    culture:      str
    pluviometrie: float   # mm
    temperature:  float   # °C
    engrais_kg:   float   # kg/ha
    superficie:   float   # ha
    type_sol:     str
    parcelle_id:  Optional[int] = None
    ville:        Optional[str] = None      # ville ivoirienne (pour déterminer la zone agro-écologique)

    @field_validator("culture")
    @classmethod
    def culture_valid(cls, v):
        from referentiel_ci import CULTURES
        if v not in CULTURES:
            raise ValueError(f"Culture non prise en charge en Côte d'Ivoire. Valeurs : {sorted(CULTURES)}")
        return v

    @field_validator("type_sol")
    @classmethod
    def sol_valid(cls, v):
        from referentiel_ci import SOLS
        if v not in SOLS:
            raise ValueError(f"Type de sol invalide. Valeurs : {sorted(SOLS)}")
        return v

    @field_validator("pluviometrie")
    @classmethod
    def pluv_range(cls, v):
        from referentiel_ci import PLUV_API
        if not (PLUV_API[0] <= v <= PLUV_API[1]):
            raise ValueError(f"Pluviométrie hors plage pour la Côte d'Ivoire ({PLUV_API[0]}-{PLUV_API[1]} mm).")
        return v

    @field_validator("temperature")
    @classmethod
    def temp_range(cls, v):
        from referentiel_ci import TEMP_API
        if not (TEMP_API[0] <= v <= TEMP_API[1]):
            raise ValueError(f"Température hors plage pour la Côte d'Ivoire ({TEMP_API[0]}-{TEMP_API[1]} °C).")
        return v


class PredictionOut(BaseModel):
    id:               int
    culture:          str
    pluviometrie:     float
    temperature:      float
    engrais_kg:       float
    superficie:       float
    type_sol:         str
    rendement_predit: float
    confiance:        Optional[float]
    created_at:       datetime
    zone:             Optional[str] = None            # zone agro-écologique (renseignée à la prédiction)
    avertissement:    Optional[str] = None            # ex. culture peu adaptée à la zone

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
#  AGRIBOT
# ─────────────────────────────────────────

class MessageIn(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def not_empty(cls, v):
        if not v.strip():
            raise ValueError("Le message ne peut pas être vide.")
        if len(v) > 2000:
            raise ValueError("Message trop long (max 2000 caractères).")
        return v.strip()


class MessageOut(BaseModel):
    role:       str
    content:    str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
#  MÉTÉO
# ─────────────────────────────────────────

class MeteoOut(BaseModel):
    ville:       str
    temperature: float
    ressenti:    float
    humidite:    int
    description: str
    icone:       str
    vent:        float
    pression:    int
