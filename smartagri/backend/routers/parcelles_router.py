"""
CRUD complet des parcelles agricoles.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Parcelle, User
from schemas import ParcelleCreate, ParcelleUpdate, ParcelleOut
from auth import get_current_user

router = APIRouter(prefix="/api/parcelles", tags=["Parcelles"])


@router.get("/", response_model=List[ParcelleOut], summary="Mes parcelles")
def list_parcelles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Parcelle).filter(Parcelle.user_id == current_user.id).all()


@router.post("/", response_model=ParcelleOut, status_code=201,
             summary="Créer une parcelle")
def create_parcelle(
    payload: ParcelleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    parcelle = Parcelle(**payload.model_dump(), user_id=current_user.id)
    db.add(parcelle)
    db.commit()
    db.refresh(parcelle)
    return parcelle


@router.get("/{parcelle_id}", response_model=ParcelleOut, summary="Détail d'une parcelle")
def get_parcelle(
    parcelle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    parcelle = db.query(Parcelle).filter(
        Parcelle.id == parcelle_id,
        Parcelle.user_id == current_user.id
    ).first()
    if not parcelle:
        raise HTTPException(status_code=404, detail="Parcelle introuvable.")
    return parcelle


@router.put("/{parcelle_id}", response_model=ParcelleOut, summary="Modifier une parcelle")
def update_parcelle(
    parcelle_id: int,
    payload: ParcelleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    parcelle = db.query(Parcelle).filter(
        Parcelle.id == parcelle_id,
        Parcelle.user_id == current_user.id
    ).first()
    if not parcelle:
        raise HTTPException(status_code=404, detail="Parcelle introuvable.")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(parcelle, field, value)
    db.commit()
    db.refresh(parcelle)
    return parcelle


@router.delete("/{parcelle_id}", status_code=204, summary="Supprimer une parcelle")
def delete_parcelle(
    parcelle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    parcelle = db.query(Parcelle).filter(
        Parcelle.id == parcelle_id,
        Parcelle.user_id == current_user.id
    ).first()
    if not parcelle:
        raise HTTPException(status_code=404, detail="Parcelle introuvable.")
    db.delete(parcelle)
    db.commit()
