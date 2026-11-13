import os, sys, tempfile, pathlib
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"      # base jetable : n'abîme jamais smartagri.db
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:      # déclenche le démarrage : compte démo + données de démonstration
        yield c


@pytest.fixture(scope="session")
def auth(client):
    r = client.post("/api/auth/login", json={"email": "demo@smartagri.com", "password": "Demo1234!"})
    assert r.status_code == 200
    return {"Authorization": "Bearer " + r.json()["access_token"]}
