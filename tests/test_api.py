import pytest
from fastapi.testclient import TestClient
from app.main import app
from pathlib import Path

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_tasks_file(tmp_path):
    """Ensure a clean tasks.json file before each test."""
    data_file = Path(__file__).resolve().parents[1] / "data" / "tasks.json"
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text("[]")
    yield

# --- ROOT & HEALTH ---
def test_root_message():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json() == {"message": "Witaj w prostym API"}

def test_root_docs_redirect():
    r = client.get("/?docs")
    assert r.status_code == 200 or r.status_code == 307  # redirect
    assert "Swagger" in r.text or "swagger" in r.text

def test_root_redoc_redirect():
    r = client.get("/?redoc")
    assert r.status_code == 200 or r.status_code == 307
    assert "ReDoc" in r.text or "redoc" in r.text

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

# --- CREATE TASK ---
def test_create_task_success():
    payload = {"title": "T1", "description": "Opis"}
    r = client.post("/tasks", json=payload)
    assert r.status_code == 201
    created = r.json()
    assert created["id"] == 1
    assert created["title"] == "T1"
    assert created["description"] == "Opis"
    assert created["completed"] is False
    assert "created_at" in created

def test_create_task_too_long_title():
    payload = {"title": "X" * 100, "description": "ok"}
    r = client.post("/tasks", json=payload)
    assert r.status_code == 422

def test_create_task_too_long_description():
    payload = {"title": "ok", "description": "Y" * 500}
    r = client.post("/tasks", json=payload)
    assert r.status_code == 422

def test_create_task_missing_title():
    payload = {"description": "no title"}
    r = client.post("/tasks", json=payload)
    assert r.status_code == 422

# --- LIST TASKS ---
def test_list_tasks_empty():
    r = client.get("/tasks")
    assert r.status_code == 200
    assert r.json() == []

def test_list_tasks_with_created():
    client.post("/tasks", json={"title": "T1", "description": "d"})
    r = client.get("/tasks")
    tasks = r.json()
    assert any(t["title"] == "T1" for t in tasks)

def test_list_tasks_filter_completed():
    client.post("/tasks", json={"title": "T1", "description": "d"})
    client.post("/tasks", json={"title": "T2", "description": "d", "completed": True})
    r = client.get("/tasks?completed=true")
    tasks = r.json()
    assert all(t["completed"] is True for t in tasks)

def test_list_tasks_search_query():
    client.post("/tasks", json={"title": "Zakupy", "description": "spożywcze"})
    r = client.get("/tasks?q=zakupy")
    tasks = r.json()
    assert any("Zakupy" in t["title"] for t in tasks)

# --- UPDATE TASK ---
def test_update_task_title_and_completed():
    r = client.post("/tasks", json={"title": "T1", "description": "d"})
    created = r.json()
    r2 = client.put(f"/tasks/{created['id']}", json={"title": "T1-mod", "completed": True})
    assert r2.status_code == 200
    updated = r2.json()
    assert updated["title"] == "T1-mod"
    assert updated["completed"] is True
    assert "completed_at" in updated

def test_update_task_uncomplete_sets_completed_at_none():
    r = client.post("/tasks", json={"title": "T1", "description": "d", "completed": True})
    created = r.json()
    r2 = client.put(f"/tasks/{created['id']}", json={"completed": False})
    updated = r2.json()
    assert updated["completed"] is False
    assert updated["completed_at"] is None

def test_update_task_not_found():
    r = client.put("/tasks/999", json={"title": "nope"})
    assert r.status_code == 404
    assert r.json()["detail"] == "Task not found"

def test_update_task_no_changes():
    r = client.post("/tasks", json={"title": "T1", "description": "d"})
    created = r.json()
    r2 = client.put(f"/tasks/{created['id']}", json={})
    assert r2.status_code == 200
    updated = r2.json()
    assert updated["title"] == "T1"  # unchanged
    assert updated["description"] == "d"

def test_delete_task_success():
    # utwórz zadanie
    r = client.post("/tasks", json={"title": "T1", "description": "d"})
    created = r.json()

    # usuń zadanie
    r2 = client.delete(f"/tasks/{created['id']}")
    assert r2.status_code == 204

    # sprawdź, że nie ma go na liście
    r3 = client.get("/tasks")
    tasks = r3.json()
    assert all(t["id"] != created["id"] for t in tasks)


def test_delete_task_not_found():
    r = client.delete("/tasks/999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Task not found"