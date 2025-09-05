from fastapi.testclient import TestClient
from ui.main import app

client = TestClient(app)

def test_index_route():
    response = client.get("/")
    assert response.status_code == 200
    assert "Financial Close Executive Summary" in response.text


def test_intercompany_route():
    response = client.get("/intercompany")
    assert response.status_code == 200
    assert "Intercompany Reconciliation" in response.text


def test_hitl_route():
    response = client.get("/hitl")
    assert response.status_code == 200
    assert "HITL Review Queue" in response.text

