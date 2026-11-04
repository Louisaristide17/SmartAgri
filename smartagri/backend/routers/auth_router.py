"""
Routes d'authentification : inscription, connexion, profil.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import UserCreate, UserLogin, UserOut, TokenOut
from auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentification"])


@router.post("/register", response_model=TokenOut, status_code=201,
             summary="Créer un compte")
def register(payload: UserCreate, db: Session = Depends(get_db)):
    # Vérifier unicité email
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte avec cet email existe déjà."
        )

    user = User(
        firstname  = payload.firstname,
        lastname   = payload.lastname,
        email      = payload.email,
        phone      = payload.phone,
        role       = payload.role,
        hashed_pwd = hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut, summary="Se connecter")
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_pwd):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect."
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Compte désactivé.")

    token = create_access_token({"sub": str(user.id)})
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut, summary="Mon profil")
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserOut, summary="Modifier mon profil")
def update_me(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    allowed = {"firstname", "lastname", "phone"}
    for field, value in payload.items():
        if field in allowed:
            setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user
