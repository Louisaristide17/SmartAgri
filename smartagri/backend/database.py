"""
Configuration de la base de données SQLAlchemy.
Utilise SQLite pour le développement (facilement remplaçable par PostgreSQL).
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# URL de connexion — SQLite par défaut, PostgreSQL en prod
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smartagri.db")

# Pour SQLite uniquement : désactiver le check same_thread
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dépendance FastAPI — fournit une session DB et la ferme après usage."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
