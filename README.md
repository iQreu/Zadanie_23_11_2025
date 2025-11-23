# TODO API - Menadżer Zadań

**Autor:** Robert Narloch
**Grupa:** ININ4(hybryda)
**Data:** 23.11.2025

## Opis projektu
REST API dla menadżera zadań z zapisem do pliku JSON oraz prostym frontendem.

## Technologie
- Python 3.12
- FastAPI
- Uvicorn (ASGI server)
- Pydantic (v2)
- pytest, httpx (testy)
- Vanilla HTML/CSS/JS (frontend)

## Instalacja i uruchomienie

### Wymagania
- Python 3.12+

### Krok po kroku (PowerShell)
```powershell
# 1. Sklonuj repozytorium
git clone <https://github.com/iQreu/Zadanie_23_11_2025.git>

# 2. Przejdź do katalogu projektu
cd ZADANIE_23_11_2025

# 3. Utwórz i aktywuj wirtualne środowisko
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\.venv\Scripts\Activate.ps1

# 4. Zainstaluj zależności
python -m pip install --upgrade pip
pip install -r requirements.txt

# 5. Uruchom backend (FastAPI)
python -m uvicorn app.main:app --reload --port 8000

# 6. (Opcjonalnie) Serwuj frontend (jeśli chcesz otworzyć UI jako statyczne pliki)
python -m http.server 5500 -d frontend
```

Frontend będzie dostępny pod `http://127.0.0.1:5500` (jeśli serwujesz go
statycznie). Backend domyślnie działa na `http://127.0.0.1:8000`.

Interaktywna dokumentacja OpenAPI (Swagger UI): `http://127.0.0.1:8000/docs`

## Endpointy (wybrane)
- `GET /` — powitanie, dodatkowo `/?docs` przekierowuje do UI dokumentacji.
- `GET /health` — status aplikacji.
- `GET /tasks` — lista zadań; obsługuje query params: `completed` i `q`.
- `POST /tasks` — utwórz zadanie (body JSON: `title`, `description`).
- `PUT /tasks/{id}` — zaktualizuj zadanie (polowe aktualizacje; ustawiane jest `completed_at`).

## Testy
Uruchom testy przy pomocy:
```powershell
python -m pytest -q
```

Uwaga: test `test_tasks_crud` resetuje `data/tasks.json` do `[]` — jeśli masz
ważne dane, wykonaj kopię przed uruchomieniem testów:
```powershell
Copy-Item .\data\tasks.json .\data\tasks.json.bak
# po testach przywróć
Move-Item .\data\tasks.json.bak .\data\tasks.json
```

## Informacje dodatkowe
- Dane są przechowywane w `data/tasks.json`. Zaimplementowano prosty mechanizm
	backupu i atomowego zapisu, aby zminimalizować ryzyko utraty danych.
- Backend ma włączone CORS dla developmentu (`allow_origins=["*"]`). W
	środowisku produkcyjnym ogranicz pochodzenia i dodaj autoryzację.

---

Jeśli chcesz, mogę uzupełnić pola autora/grupy/daty, dodać Dockerfile albo
zintegrować frontend, aby był serwowany bezpośrednio przez FastAPI.


Frontend (TOO DO Manager)

Pliki frontendu znajdują się w `frontend/`. Możesz je uruchomić na kilka sposobów:

- Serwować statycznie (szybkie dla developmentu):

```powershell
# z katalogu projektu
python -m http.server 5500 -d frontend
# potem otwórz http://127.0.0.1:5500
```

- Albo uruchomić backend i otworzyć pliki statyczne bezpośrednio (jeśli frontend i backend są na różnych portach, backend ma włączony CORS):

```powershell
# uruchom backend
python -m uvicorn app.main:app --reload --port 8000
# otwórz plik frontend/index.html w przeglądarce lub serwuj go jak wyżej
```

Jeśli frontend jest serwowany z innego portu niż backend, backend ma już włączone CORS (dozwolone origins: `*`) — to ustawienie jest OK dla developmentu, ale nie powinno być używane w produkcji.

