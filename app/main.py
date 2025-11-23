from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Dict
import os
import json
import threading
import shutil
import tempfile
import time

# ==================================================================
# Prosty backend w FastAPI dla aplikacji "TOO DO Manager"
# Ten plik definiuje API (adresy URL), które frontend wykorzystuje
# do tworzenia, odczytu i modyfikowania zadań przechowywanych w
# lokalnym pliku JSON. Komentarze niżej wyjaśniają każdy fragment.
# ==================================================================

app = FastAPI(title="Proste API", version="0.1.0")

# CORS (Cross-Origin Resource Sharing)
# - Kiedy frontend działa na innym porcie (np. 5500) niż backend (8000),
#   przeglądarka blokuje żądania z powodu zasad bezpieczeństwa.
# - Ta konfiguracja pozwala przeglądarce wysyłać żądania do tego API
#   z dowolnego pochodzenia. Jest to wygodne podczas developmentu,
#   ale w produkcji warto ograniczyć do konkretnych adresów.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class Task(BaseModel):
    # Reprezentacja zadania (Task) — to, co zapisujemy w pliku JSON.
    # Pola:
    # - id: unikalny identyfikator zadania
    # - title: tytuł zadania (krótka treść)
    # - description: dłuższy opis (opcjonalny)
    # - completed: czy zadanie jest ukończone (True/False)
    # - created_at: data utworzenia (format ISO8601 UTC)
    # - completed_at: data oznaczenia jako ukończone (ISO8601 UTC) lub None
    id: int | None = None
    title: str = Field(..., max_length=50)        # np. max 50 znaków
    description: str = Field(..., max_length=200)
    completed: bool = False
    created_at: str | None = None
    completed_at: str | None = None


class TaskUpdate(BaseModel):
    # Model używany przy aktualizacji zadania. Wszystkie pola są opcjonalne —
    # klient (frontend) może wysłać tylko to, co chce zmienić.
    title: str | None = None
    description: str | None = None
    completed: bool | None = None


# (Usunięto przykładowe endpointy `items` i związane zmienne – nie były
# potrzebne dla frontendu. Wszystkie operacje na zadaniach wykonujemy na
# pliku JSON `data/tasks.json`.)


@app.get("/")
def read_root(request: Request):
    """
    Strona główna API.

    Dodatkowo: jeśli w query string pojawi się `?docs` przekierowujemy
    użytkownika do interfejsu Swagger UI (/docs). Podobnie `?redoc`
    przekierowuje do /redoc.
    To ułatwia szybkie podejrzenie wszystkich endpointów.
    """
    if "docs" in request.query_params:
        return RedirectResponse(url="/docs")
    if "redoc" in request.query_params:
        return RedirectResponse(url="/redoc")
    return {"message": "Witaj w prostym API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


# --- Proste API "items" (in-memory) - używane w testach


# --- Tasks backed by a JSON file ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)
TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")

# Ensure the tasks file exists
if not os.path.exists(TASKS_FILE):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

_tasks_lock = threading.Lock()


def _load_tasks_raw():
    # Wczytuje zadania z pliku JSON, z prostą obsługą uszkodzeń pliku.
    # Jeśli plik JSON jest uszkodzony, spróbujemy przywrócić z kopii
    # zapasowej (TASKS_FILE + '.bak'). Jeśli to się nie uda, zachowamy
    # uszkodzony plik pod nazwą *.corrupt.TIMESTAMP i utworzymy nowy
    # pusty plik z listą []. Dzięki temu nie tracimy danych i nie
    # przerywamy działania aplikacji.
    with _tasks_lock:
        if not os.path.exists(TASKS_FILE):
            # brak pliku => zwróć pustą listę (plik zostanie utworzony przy zapisie)
            return []
        try:
            with open(TASKS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Upewnij się, że mamy listę (oczekiwany format)
            if isinstance(data, list):
                return data
            # jeśli format nie jest listą, traktujemy jako uszkodzony
            corrupt_name = TASKS_FILE + f".corrupt.{int(time.time())}"
            shutil.move(TASKS_FILE, corrupt_name)
            # spróbuj przywrócić z kopii zapasowej
            bak = TASKS_FILE + ".bak"
            if os.path.exists(bak):
                shutil.copy(bak, TASKS_FILE)
                try:
                    with open(TASKS_FILE, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    pass
            # nic nie pomogło -> utwórz nowy pusty plik
            with open(TASKS_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)
            return []
        except json.JSONDecodeError:
            # plik jest niepoprawnym JSON-em
            corrupt_name = TASKS_FILE + f".corrupt.{int(time.time())}"
            shutil.move(TASKS_FILE, corrupt_name)
            bak = TASKS_FILE + ".bak"
            if os.path.exists(bak):
                # przywróć z kopii zapasowej
                shutil.copy(bak, TASKS_FILE)
                try:
                    with open(TASKS_FILE, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    pass
            # utwórz nowy pusty plik i zwróć pustą listę
            with open(TASKS_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)
            return []
        except Exception:
            # Inny błąd I/O -> logujemy (print) i zwracamy pustą listę,
            # aplikacja nadal działa. W praktyce warto użyć loggera.
            print("Nieoczekiwany błąd podczas odczytu tasks.json", flush=True)
            return []


# _save_tasks_raw zapisuje listę zadań do pliku JSON.
# Używamy blokady (_tasks_lock), żeby uniknąć równoczesnych zapisów
# (gdyby kilka żądań przyszło jednocześnie). To proste zabezpieczenie
# wystarczające dla demo/small-scale usage.


def _save_tasks_raw(tasks_list):
    # Zapisujemy atomowo: zapis do pliku tymczasowego w tej samej
    # lokalizacji, potem zamiana (os.replace) — to minimalizuje ryzyko
    # powstania uszkodzonego pliku przy awarii podczas zapisu.
    # Dodatkowo tworzymy kopię zapasową (.bak) poprzedniej wersji.
    with _tasks_lock:
        dirpath = os.path.dirname(TASKS_FILE) or '.'
        fd, tmp_path = tempfile.mkstemp(prefix='tasks_', suffix='.tmp', dir=dirpath)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as tmpf:
                json.dump(tasks_list, tmpf, indent=2, ensure_ascii=False)
                tmpf.flush()
                os.fsync(tmpf.fileno())
            # utwórz kopię zapasową obecnego pliku przed zastąpieniem
            if os.path.exists(TASKS_FILE):
                try:
                    shutil.copy(TASKS_FILE, TASKS_FILE + '.bak')
                except Exception:
                    # jeśli backup się nie uda, kontynuujemy — nie chcemy
                    # przerwać zapisu głównego pliku
                    print('Nie udało się utworzyć backupu tasks.json', flush=True)
            # atomowa zamiana pliku
            os.replace(tmp_path, TASKS_FILE)
        finally:
            # w razie czego usuń plik tymczasowy
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass


@app.get("/tasks")
def get_tasks(completed: bool | None = None, q: str | None = None):
    """
    Zwraca listę zadań.

    Parametry opcjonalne (query params):
    - completed: filtruj po statusie (true/false)
    - q: wyszukaj frazę w tytule lub opisie (case-insensitive)

    Frontend wywołuje to endpoint, np. /tasks?completed=true&q=zakupy
    """
    tasks = _load_tasks_raw()
    # Filtruj po statusie ukończenia, jeśli podano
    if completed is not None:
        tasks = [t for t in tasks if bool(t.get("completed")) == bool(completed)]
    # Proste wyszukiwanie tekstu w title/description
    if q:
        q_l = q.lower()
        tasks = [t for t in tasks if q_l in (t.get("title","") or "").lower() or q_l in (t.get("description","") or "").lower()]
    return tasks


@app.post("/tasks", status_code=201)
def create_task(task: Task):
    tasks = _load_tasks_raw()
    next_id = max((t.get("id", 0) for t in tasks), default=0) + 1
    # Używamy `model_dump()` (Pydantic v2) zamiast przestarzałego `dict()`
    task_dict = task.model_dump()
    task_dict["id"] = next_id
    # set created_at in ISO 8601 UTC if not provided
    if not task_dict.get("created_at"):
        # używamy timezone-aware UTC i zamieniamy końcówkę na 'Z'
        task_dict["created_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    tasks.append(task_dict)
    _save_tasks_raw(tasks)
    return task_dict


# Tworzenie zadania (POST /tasks)
# - Otrzymujemy dane od klienta (tytuł, opcjonalny opis)
# - Nadajemy unikalne id i ustawiamy pole created_at na aktualny czas
# - Zapisujemy do pliku i zwracamy utworzone zadanie


@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdate):
    tasks = _load_tasks_raw()
    for i, t in enumerate(tasks):
        if t.get("id") == task_id:
            # model_dump(exclude_none=True) zwraca tylko pola nie-None — prościej niż filtrowanie
            updates = task.model_dump(exclude_none=True)
            if updates:
                prev_completed = bool(t.get("completed", False))
                # apply updates
                t.update(updates)
                # handle completed_at timestamp
                if "completed" in updates:
                    now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
                    if updates["completed"] and not prev_completed:
                        t["completed_at"] = now_iso
                    elif not updates["completed"] and prev_completed:
                        t["completed_at"] = None

                tasks[i] = t
                _save_tasks_raw(tasks)
            return t
    raise HTTPException(status_code=404, detail="Task not found")


# Aktualizacja zadania (PUT /tasks/{id})
# - Można wysłać tylko pola, które chcemy zmienić (title, description, completed)
# - Jeśli pole 'completed' zmienia się z False na True, ustawiamy 'completed_at'
# - Jeśli zmienia się z True na False, usuwamy datę 'completed_at'
