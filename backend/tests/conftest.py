"""Configuração comum: banco SQLite temporário e cliente HTTP autenticado."""
import os
import tempfile

_TMP = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/teste.db"
os.environ["ADMIN_USER"] = "teste"
os.environ["ADMIN_PASSWORD"] = "senha-teste"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture
def cliente():
    c = TestClient(app)
    token = c.post("/api/auth/login", json={"username": "teste", "password": "senha-teste"})
    c.headers["Authorization"] = f"Bearer {token.json()['access_token']}"
    return c
