import pytest
from starlette.testclient import TestClient
from app.main import app
from app.database import init_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def ensure_db():
    init_db()

def test_api_health_route():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "TRIPWIRE"

def test_api_create_and_get_task():
    # 1. Create a task without auto_run
    res = client.post("/api/tasks", json={
        "user_goal": "Inspect workspace files and report findings",
        "auto_run": False
    })
    assert res.status_code == 201
    task_data = res.json()
    task_id = task_data["id"]
    assert task_id.startswith("task_")
    assert task_data["state"] == "PENDING"
    assert task_data["user_goal"] == "Inspect workspace files and report findings"

    # 2. Get the task
    get_res = client.get(f"/api/tasks/{task_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == task_id

    # 3. List tasks
    list_res = client.get("/api/tasks")
    assert list_res.status_code == 200
    task_ids = [t["id"] for t in list_res.json()]
    assert task_id in task_ids

def test_api_stop_task():
    res = client.post("/api/tasks", json={
        "user_goal": "A task to be stopped",
        "auto_run": False
    })
    task_id = res.json()["id"]

    stop_res = client.post(f"/api/tasks/{task_id}/stop")
    assert stop_res.status_code == 200
    assert stop_res.json()["state"] == "STOPPED"

def test_api_dangerous_action_requires_approval():
    # Create task with dangerous goal -> will PAUSE at step 1
    res = client.post("/api/tasks", json={
        "user_goal": "Demonstrate dangerous deletion of source files",
        "auto_run": True
    })
    assert res.status_code == 201
    task_data = res.json()
    assert task_data["state"] == "WAITING_APPROVAL"
    assert len(task_data["actions"]) >= 1

    action = task_data["actions"][0]
    action_id = action["id"]
    assert action["action_name"] == "delete_file"
    assert action["decision"] == "PAUSE"
    assert action["status"] == "PAUSED"
    assert len(action["overrides_applied"]) > 0

    # Test GET /api/actions/{action_id}
    act_res = client.get(f"/api/actions/{action_id}")
    assert act_res.status_code == 200
    assert act_res.json()["id"] == action_id

    # Test Reject Action
    rej_res = client.post(f"/api/actions/{action_id}/reject")
    assert rej_res.status_code == 200
    rej_data = rej_res.json()
    assert rej_data["human_approval"] is False
    assert rej_data["status"] == "REJECTED"

    # Task should now be STOPPED
    updated_task = client.get(f"/api/tasks/{task_data['id']}").json()
    assert updated_task["state"] == "STOPPED"

def test_api_stats_dynamic():
    res = client.get("/api/stats")
    assert res.status_code == 200
    stats = res.json()
    assert "total_tasks" in stats
    assert "completed_tasks" in stats
    assert "waiting_approval_tasks" in stats
    assert "average_trust_score" in stats
    assert stats["total_tasks"] >= 1
    assert stats["total_actions"] >= 1

def test_api_snapshots_list():
    res = client.get("/api/snapshots")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_api_events_sse_connection():
    # Connect to SSE endpoint and verify it yields initial connection event
    with client.stream("GET", "/api/events") as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        first_line = next(response.iter_lines())
        assert "event: connected" in first_line

