from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json() == {"message": "Witaj w prostym API"}


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}



def test_tasks_crud(tmp_path):
    # ensure a clean tasks file for the test
    from pathlib import Path
    data_file = Path(__file__).resolve().parents[1] / "data" / "tasks.json"
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text("[]")

    # create a task
    payload = {"title": "T1", "description": "d"}
    r = client.post("/tasks", json=payload)
    assert r.status_code == 201
    created = r.json()
    assert created["id"] == 1
    assert created["title"] == "T1"

    # list tasks
    r2 = client.get("/tasks")
    assert r2.status_code == 200
    tasks = r2.json()
    assert any(t["id"] == created["id"] for t in tasks)

    # update task
    r3 = client.put(f"/tasks/{created['id']}", json={"title": "T1-mod", "completed": True})
    assert r3.status_code == 200
    updated = r3.json()
    assert updated["title"] == "T1-mod"
    assert updated["completed"] is True
