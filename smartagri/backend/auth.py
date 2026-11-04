"""
Gestion de l'authentification JWT.
- Hashage des mots de passe avec bcrypt (directement, sans passlib)
- Création et vérification des tokens JWT

Note : passlib a un bug de compatibilité avec Python 3.14+.
       On utilise le module bcrypt directement.
"""
from datetime import datetime, timedelta
from typing import Optional
import os
import bcrypt

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import TokenData

# ─── Configuration ───────────────────────────────────────────────
SECRET_KEY    = os.getenv("SECRET_KEY", "smartagri-secret-key-change-in-production-2026")
ALGORITHM     = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24h

# ─── OAuth2 scheme ────────────────────────────────────────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ─── Fonctions de hashage (bcrypt direct) ────────────────────────
def hash_password(plain: str) -> str:
    """Hashe le mot de passe avec bcrypt."""
    pwd_bytes = plain.encode("utf-8")[:72]   # bcrypt limite à 72 octets
    hashed = bcrypt.hashpw(pwd_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Vérifie un mot de passe contre son hash bcrypt."""
    try:
        pwd_bytes    = plain.encode("utf-8")[:72]
        hashed_bytes = hashed.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hashed_bytes)
    except Exception:
        return False


# ─── Fonctions JWT ────────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload  = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return TokenData(user_id=int(user_id))
    except JWTError:
        raise credentials_exception


# ─── Dépendance : utilisateur courant ─────────────────────────────
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db:    Session = Depends(get_db)
) -> User:
    token_data = decode_token(token)
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable ou inactif.",
        )
    return user
