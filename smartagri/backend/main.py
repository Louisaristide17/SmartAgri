"""
SmartAgri – API Backend principal (FastAPI)
===========================================
Lance avec : uvicorn main:app --reload --port 8000
Swagger UI  : http://localhost:8000/docs
ReDoc       : http://localhost:8000/redoc
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os

from database import engine, Base
from routers import auth_router, parcelles_router, prediction_router, meteo_router, agribot_router

# ─── Créer les tables au démarrage ───────────────────────────────
Base.metadata.create_all(bind=engine)

# ─── Application FastAPI ──────────────────────────────────────────
app = FastAPI(
    title       = "SmartAgri API",
    description = (
        "API intelligente pour la prédiction de rendement agricole, "
        "la gestion des parcelles et l'assistant IA AgriBot.\n\n"
        "**Compte de démo** : `demo@smartagri.com` / `Demo1234!`"
    ),
    version     = "1.0.0",
    docs_url    = "/docs",
    redoc_url   = "/redoc",
)

# ─── CORS — autoriser le frontend ─────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # En prod : remplacer par l'URL de votre frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Inclusion des routers ────────────────────────────────────────
app.include_router(auth_router.router)
app.include_router(parcelles_router.router)
app.include_router(prediction_router.router)
app.include_router(meteo_router.router)
app.include_router(agribot_router.router)


# ─── Routes utilitaires ───────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    # Si le frontend est disponible, rediriger vers la page de connexion
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "login", "index.html")
    if os.path.exists(frontend_path):
        return RedirectResponse(url="/login/index.html")
    return {
        "message": "🌱 SmartAgri API opérationnelle",
        "version": "1.0.0",
        "docs":    "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}


# ─── Seed : compte de démo ────────────────────────────────────────
@app.on_event("startup")
def seed_demo():
    """Crée un compte de démo au premier démarrage."""
    from sqlalchemy.orm import Session
    from database import SessionLocal
    from models import User
    from auth import hash_password

    db: Session = SessionLocal()
    try:
        if not db.query(User).filter(User.email == "demo@smartagri.com").first():
            demo = User(
                firstname  = "Jean",
                lastname   = "Koné",
                email      = "demo@smartagri.com",
                phone      = "+225 07 00 00 00 00",
                role       = "agriculteur",
                hashed_pwd = hash_password("Demo1234!"),
            )
            db.add(demo)
            db.commit()
            print("✅ Compte démo créé : demo@smartagri.com / Demo1234!")

        # Données d'exemple (parcelles, prédictions, conversation) si le compte démo est vide
        from seed import seed_demo_data
        demo_user = db.query(User).filter(User.email == "demo@smartagri.com").first()
        if seed_demo_data(db, demo_user):
            print("✅ Données de démonstration créées")
    finally:
        db.close()


# ─── Lancement direct ─────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


# ─── Serveur de fichiers statiques (frontend) ─────────────────────
# Monte le frontend APRÈS les routes API pour ne pas les masquer
_frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(_frontend_dir):
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")
