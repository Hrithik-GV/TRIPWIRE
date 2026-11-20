import pytest
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "TRIPWIRE"
    assert data["subtitle"] == "SUPERNOVA"

def test_api_list_files():
    res = client.get("/api/actions/files")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    file_names = [f["name"] for f in data["data"]]
    assert "app.py" in file_names
    assert "test_app.py" in file_names

def test_api_read_app_file():
    res = client.post("/api/actions/execute", json={
        "action": "read_file",
        "params": {"path": "app.py"}
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "def login" in data["data"]["content"]

def test_api_security_path_traversal():
    res = client.post("/api/actions/execute", json={
        "action": "read_file",
        "params": {"path": "../backend/app/main.py"}
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert "Path traversal" in data["error"]

def test_api_run_tests():
    res = client.post("/api/actions/run-tests?target=test_app.py")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    # Initial tests fail due to intentional bug in app.py
    assert data["data"]["passed"] is False
    assert data["data"]["exit_code"] != 0
    assert "FAILED (failures=3)" in data["data"]["output"]

