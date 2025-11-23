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
def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json() == {"message": "Witaj w prostym API"} 


def test_health():
    r = client.get("/health") 
    assert r.status_code == 200 
    assert r.json() == {"status": "ok"}

def test_create_task():
    payload = {"title": "T1", "description": "d"}
    r = client.post("/tasks", json=payload)
    assert r.status_code == 201
    created = r.json()
    assert created["id"] == 1
    assert created["title"] == "T1"
    assert created["description"] == "d"
    assert created["completed"] is False  # domyślnie powinno być False


def test_list_tasks():
    # najpierw utwórz zadanie
    client.post("/tasks", json={"title": "T1", "description": "d"})
    r = client.get("/tasks")
    assert r.status_code == 200
    tasks = r.json()
    assert isinstance(tasks, list)
    assert any(t["title"] == "T1" for t in tasks)


def test_update_task():
    # utwórz zadanie
    r = client.post("/tasks", json={"title": "T1", "description": "d"})
    created = r.json()

    # zaktualizuj zadanie
    r2 = client.put(
        f"/tasks/{created['id']}",
        json={"title": "T1-mod", "completed": True}
    )
    assert r2.status_code == 200
    updated = r2.json()
    assert updated["title"] == "T1-mod"
    assert updated["completed"] is True  # jednoznaczne sprawdzenie