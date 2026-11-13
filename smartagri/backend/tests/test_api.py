"""Tests automatiques SmartAgri :  cd backend && python -m pytest -v"""
import json, pathlib

ML = pathlib.Path(__file__).resolve().parent.parent / "ml"

# ───────── Authentification ─────────
def test_login_ok(client):
    r = client.post("/api/auth/login", json={"email": "demo@smartagri.com", "password": "Demo1234!"})
    assert r.status_code == 200 and r.json()["access_token"]

def test_login_mauvais_mot_de_passe(client):
    r = client.post("/api/auth/login", json={"email": "demo@smartagri.com", "password": "faux"})
    assert r.status_code == 401

def test_route_protegee_sans_jeton(client):
    assert client.get("/api/parcelles/").status_code in (401, 403)

def test_inscription_mot_de_passe_trop_court(client):
    r = client.post("/api/auth/register", json={"firstname": "A", "lastname": "B", "email": "a@b.ci", "password": "123"})
    assert r.status_code == 422

# ───────── CRUD parcelles ─────────
def test_crud_parcelle(client, auth):
    corps = {"nom": "Test", "superficie": 2.5, "type_sol": "argileux", "culture": "cacao", "ville": "Daloa"}
    r = client.post("/api/parcelles/", json=corps, headers=auth); assert r.status_code == 201
    pid = r.json()["id"]
    assert client.get(f"/api/parcelles/{pid}", headers=auth).json()["nom"] == "Test"
    r = client.put(f"/api/parcelles/{pid}", json={"nom": "Test modifié"}, headers=auth)
    assert r.status_code == 200 and r.json()["nom"] == "Test modifié"
    assert client.delete(f"/api/parcelles/{pid}", headers=auth).status_code == 204
    assert client.get(f"/api/parcelles/{pid}", headers=auth).status_code == 404

def test_parcelle_invalide_refusee(client, auth):
    r = client.post("/api/parcelles/", json={"nom": "X", "superficie": -1, "type_sol": "argileux", "culture": "cacao"}, headers=auth)
    assert r.status_code == 422
    r = client.post("/api/parcelles/", json={"nom": "X", "superficie": 1, "type_sol": "argileux", "culture": "banane"}, headers=auth)
    assert r.status_code == 422

def test_donnees_de_demo_presentes(client, auth):
    assert len(client.get("/api/parcelles/", headers=auth).json()) >= 6

# ───────── Prédiction ─────────
def _predire(client, auth, **kw):
    base = {"culture": "cacao", "pluviometrie": 1600, "temperature": 26, "engrais_kg": 100, "superficie": 1,
            "type_sol": "ferrallitique", "ville": "Daloa"}
    base.update(kw)
    return client.post("/api/prediction/", json=base, headers=auth)

def test_prediction_cacao_foret(client, auth):
    r = _predire(client, auth); assert r.status_code == 201
    j = r.json(); assert 0.4 < j["rendement_predit"] < 1.5 and 55 <= j["confiance"] <= 95
    assert "forestière" in j["zone"]

def test_cacao_nord_moins_bon_et_alerte(client, auth):
    nord = _predire(client, auth, ville="Korhogo").json()
    foret = _predire(client, auth, ville="Daloa").json()
    assert nord["rendement_predit"] < foret["rendement_predit"] / 2
    assert nord["avertissement"]

def test_valeurs_hors_cote_d_ivoire_refusees(client, auth):
    assert _predire(client, auth, temperature=45).status_code == 422
    assert _predire(client, auth, pluviometrie=50).status_code == 422
    assert _predire(client, auth, culture="pommier").status_code == 422

def test_modele_ml_charge_et_utilise():
    from routers import prediction_router as p
    assert p._MODEL is not None, "ml/model.joblib doit être chargé"

# ───────── Modèle : qualité minimale (garde-fou de non-régression) ─────────
def test_metriques_du_modele():
    m = json.load(open(ML / "metrics.json", encoding="utf-8"))
    assert m["resultats"][m["modele_retenu"]]["R2"] > 0.9
    assert m["resultats"][m["modele_retenu"]]["MAPE"] < 20

# ───────── Agent AgriBot ─────────
def _dire(client, auth, texte):
    r = client.post("/api/agribot/message", json={"content": texte}, headers=auth); assert r.status_code == 200
    return r.json()["content"]

def test_agent_utilise_la_base_de_donnees(client, auth):
    rep = _dire(client, auth, "Combien de parcelles ai-je ?")
    assert "parcelle" in rep and "mes_parcelles" in rep

def test_agent_appelle_le_modele_et_garde_le_contexte(client, auth):
    rep1 = _dire(client, auth, "Quel rendement pour le cacao à Daloa ?")
    assert "t/ha" in rep1 and "predire_rendement" in rep1
    rep2 = _dire(client, auth, "Et pour le café ?")          # mémoire : la ville Daloa est reprise
    assert "Café" in rep2 and "Daloa" in rep2

def test_agent_refuse_produit_interdit(client, auth):
    rep = _dire(client, auth, "Où acheter du paraquat pour mon champ ?")
    assert "homologu" in rep

def test_agent_refuse_hors_sujet(client, auth):
    assert "domaine" in _dire(client, auth, "Donne-moi une ordonnance pour mon mal de tête")

def test_agent_question_inconnue_ne_plante_pas(client, auth):
    assert _dire(client, auth, "azertyuiop qsdfghjkl")

# ───────── GPS (mobile) ─────────
def test_zone_gps(client):
    r = client.get("/api/prediction/zone?latitude=9.46&longitude=-5.63").json()     # Korhogo
    assert r["dans_le_pays"] and r["zone"] == "nord"
    r = client.get("/api/prediction/zone?latitude=6.88&longitude=-6.45").json()     # Daloa
    assert r["zone"] == "foret" and r["cultures_conseillees"]
    assert not client.get("/api/prediction/zone?latitude=14.7&longitude=-17.4").json()["dans_le_pays"]   # Dakar

# ───────── Politesse de l'agent ─────────
def test_agent_salue_poliment(client, auth):
    rep = _dire(client, auth, "Bonjour")
    assert "Bonjour" in rep and "plaisir" in rep and "aider" in rep

def test_agent_remercie_et_prend_conge(client, auth):
    rep = _dire(client, auth, "Merci beaucoup").lower()
    assert any(mot in rep for mot in ("plaisir", "prie", "confiance"))
    assert "Au revoir" in _dire(client, auth, "Au revoir")

def test_reponses_factuelles_courtoises(client, auth):
    rep = _dire(client, auth, "Quel rendement pour le maïs à Bouaké ?")
    assert "t/ha" in rep and ("disposition" in rep or "plaisir" in rep or "récolte" in rep or "précisions" in rep)
    assert "Je vous prie de m'excuser" in _dire(client, auth, "azertyuiop qsdfghjkl")
