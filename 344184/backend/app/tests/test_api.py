from fastapi.testclient import TestClient
from app.main import app


def test_demo_flow(tmp_path, monkeypatch):
    # TestClient triggers schema creation and deterministic seed data.
    with TestClient(app) as client:
        assert client.get("/health").json()["status"] == "healthy"
        created = client.post("/api/auth/register", json={"name": "Demo Student", "email": "demo@example.com", "password": "secure-pass-123"})
        assert created.status_code == 201
        token = created.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        assert client.put("/api/users/me", headers=headers, json={"target_role": "AI Engineer"}).status_code == 200
        assert client.post("/api/users/me/skills", headers=headers, json={"name": "Python", "proficiency": 80}).status_code == 200
        assert client.get("/api/skills/gaps", headers=headers).status_code == 200
        roadmap = client.post("/api/roadmap/generate", headers=headers, json={"target_role": "AI Engineer", "duration_months": 3, "hours_per_week": 8})
        assert roadmap.status_code == 201
        assert len(roadmap.json()["data"]["items"]) > 0
        assert client.get("/api/jobs", headers=headers).json()["data"]
        assert client.post("/api/assistant/chat", headers=headers, json={"message": "What should I learn?"}).status_code == 200
