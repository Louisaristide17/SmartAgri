"""
Modèles SQLAlchemy — définissent les tables de la base de données.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    firstname  = Column(String(100), nullable=False)
    lastname   = Column(String(100), nullable=False)
    email      = Column(String(255), unique=True, index=True, nullable=False)
    phone      = Column(String(30), nullable=True)
    role       = Column(String(50), default="agriculteur")   # agriculteur | cooperative | conseiller | chercheur
    hashed_pwd = Column(String(255), nullable=False)
    is_active  = Column(Boolean, default=True)
    avatar_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations
    parcelles     = relationship("Parcelle",     back_populates="owner",   cascade="all, delete")
    conversations = relationship("Conversation", back_populates="user",    cascade="all, delete")
    predictions   = relationship("Prediction",   back_populates="user",    cascade="all, delete")


class Parcelle(Base):
    __tablename__ = "parcelles"

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    nom          = Column(String(150), nullable=False)
    superficie   = Column(Float, nullable=False)           # en hectares
    type_sol     = Column(String(50), nullable=False)      # sableux | argileux | limoneux | lateritique
    culture      = Column(String(80), nullable=False)      # mais | riz | arachide | sorgho | mil
    latitude     = Column(Float, nullable=True)
    longitude    = Column(Float, nullable=True)
    ville        = Column(String(100), nullable=True)
    statut       = Column(String(30), default="active")    # active | en_repos | recoltee
    description  = Column(Text, nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), onupdate=func.now())

    owner       = relationship("User",       back_populates="parcelles")
    predictions = relationship("Prediction", back_populates="parcelle", cascade="all, delete")


class Prediction(Base):
    __tablename__ = "predictions"

    id               = Column(Integer, primary_key=True, index=True)
    user_id          = Column(Integer, ForeignKey("users.id"), nullable=False)
    parcelle_id      = Column(Integer, ForeignKey("parcelles.id"), nullable=True)
    culture          = Column(String(80), nullable=False)
    pluviometrie     = Column(Float, nullable=False)   # mm
    temperature      = Column(Float, nullable=False)   # °C
    engrais_kg       = Column(Float, nullable=False)   # kg/ha
    superficie       = Column(Float, nullable=False)   # ha
    type_sol         = Column(String(50), nullable=False)
    rendement_predit = Column(Float, nullable=False)   # t/ha
    confiance        = Column(Float, nullable=True)    # 0-100 %
    created_at       = Column(DateTime(timezone=True), server_default=func.now())

    user     = relationship("User",     back_populates="predictions")
    parcelle = relationship("Parcelle", back_populates="predictions")


class Conversation(Base):
    __tablename__ = "conversations"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    role       = Column(String(10), nullable=False)   # user | assistant
    content    = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="conversations")
