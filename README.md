# Proste API w Pythonie (FastAPI)

Krótkie demo prostego API z użyciem FastAPI.

To repozytorium zawiera proste API napisane w Pythonie (FastAPI) oraz
lekki frontend (HTML/CSS/JS) pełniący rolę "TOO DO Manager" (lista zadań).

Poniżej znajduje się szczegółowe README: opis użytych technologii, struktura
pliku, endpointy, instrukcje uruchomienia i uwagi dotyczące bezpieczeństwa.

**Spis treści**
- **Przegląd**
- **Technologie**
- **Struktura projektu**
- **Backend — endpointy**
- **Frontend — pliki i działanie**
- **Przechowywanie danych i backup**
- **Uruchomienie lokalne (PowerShell)**
- **Testy**
- **Uwagi o bezpieczeństwie i dalsze kroki**


**Przegląd**
- Prosty backend w `FastAPI` obsługujący CRUD zadań (Tasks) zapisanych w pliku
	JSON (`data/tasks.json`).
- Frontend to pojedyncza strona (vanilla JS) umieszczona w `frontend/`, która
	komunikuje się z backendem przez fetch (REST).


**Technologie**
- Python 3.12 (zalecane)
- FastAPI — framework webowy
- Uvicorn — ASGI server (do uruchamiania aplikacji)
- Pydantic (v2) — walidacja modeli (Task, TaskUpdate)
- pytest — testy jednostkowe
- httpx — dependency wymagane przez TestClient
- Vanilla HTML/CSS/JS dla frontendu


**Struktura projektu**
- `app/main.py` — cały backend (endpointy, I/O JSON, obsługa backupu)
- `data/tasks.json` — plik przechowujący listę zadań (lista obiektów JSON)
- `frontend/index.html` — UI aplikacji
- `frontend/styles.css` — style frontend
- `frontend/app.js` — logika frontend (fetch, rendering, filtry)
- `tests/test_api.py` — testy integracyjne używające `TestClient`
- `requirements.txt` — lista zależności
- `README.md` — ten plik


**Backend — endpointy (krótko)**
- `GET /` — prosty endpoint powitalny (zwraca JSON z wiadomością).
- `GET /health` — endpoint zdrowia aplikacji (zwraca {"status":"ok"}).
- `GET /tasks` — zwraca listę zadań. Obsługuje query params:
	- `completed=true|false` — filtr po statusie,
	- `q=tekst` — wyszukiwanie w tytule i opisie (case-insensitive).
- `POST /tasks` — tworzy nowe zadanie. Body JSON: `{ "title": "...", "description": "..." }`.
	- Backend automatycznie nadaje `id`, ustawia `created_at` (UTC ISO8601) i zapisuje do `data/tasks.json`.
- `PUT /tasks/{id}` — aktualizuje zadanie. Można wysłać częściowy obiekt
	(np. `{ "completed": true }`) — jeśli `completed` przełącza się na `true`,
	ustawiane jest `completed_at` (UTC ISO8601); jeśli na `false`, pole `completed_at` jest czyszczone.
- Dodatkowo w projekcie są testowe endpointy `items` (in-memory), wymagane przez
	istniejące testy: `POST /items/`, `GET /items/{id}`, `GET /items/`.


**Frontend — pliki i działanie**
- `frontend/index.html` — prosty SPA interfejs: pole dodawania zadania, lista zadań,
	filtry (wyszukiwanie i status), przyciski do edycji i oznaczania ukończenia.
- `frontend/app.js` — używa `fetch` do wywołań REST:
	- pobiera listę z `GET /tasks` (z parametrami filtrów),
	- tworzy zadania `POST /tasks`,
	- aktualizuje zadania `PUT /tasks/{id}`.
- `frontend/styles.css` — nowoczesny, ciemny motyw, responsywne elementy, badge stanu.


**Przechowywanie danych i backup / bezpieczeństwo pliku**
- Dane są przechowywane w `data/tasks.json` jako lista obiektów JSON.
- Mechanizmy bezpieczeństwa przy zapisie/odczycie:
	- Zapis jest atomowy: zapis do pliku tymczasowego w tej samej lokalizacji,
		fsync, a następnie `os.replace` — redukuje ryzyko uszkodzenia pliku jeśli
		proces zostanie przerwany podczas zapisu.
	- Przed zamianą tworzona jest kopia zapasowa `tasks.json.bak` (jeśli plik
		wcześniej istniał).
	- Przy odczycie, jeżeli plik JSON jest uszkodzony (JSONDecodeError) lub ma
		nieoczekiwany format, stary plik jest przemianowywany na
		`tasks.json.corrupt.<timestamp>`. Następnie aplikacja próbuje przywrócić
		zawartość z `tasks.json.bak`. Jeśli to się nie uda, tworzy pusty `tasks.json`.
	- Mechanizm ten minimalizuje utratę danych i pozwala kontynuować pracę
		aplikacji nawet gdy plik ulegnie uszkodzeniu.


**Uruchomienie lokalne (PowerShell, Windows)**
1) Stwórz i aktywuj środowisko wirtualne (opcjonalnie, ale zalecane):

```powershell
# z katalogu projektu e:\Zadanie_23_11_2025
python -m venv .venv
# jeśli PowerShell blokuje uruchamianie skryptów:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

2) Uruchom backend (FastAPI + Uvicorn):

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

3) Uruchom frontend:
- Najprościej serwować statycznie katalog `frontend/` w osobnym terminalu:

```powershell
# w nowym oknie terminala (nie musisz mieć venv aktywnego)
python -m http.server 5500 -d frontend
# otwórz: http://127.0.0.1:5500
```

Uwaga: Backend ma domyślnie włączony CORS dla developmentu (`allow_origins=["*"]`).
Jeśli serwujesz frontend z innego portu, żądania powinny działać; w produkcji
ogranicz `allow_origins` do konkretnych hostów.


**Testy**
- Uruchomienie wszystkich testów:

```powershell
python -m pytest -q
```

- Testy znajdują się w `tests/test_api.py`. Test `test_tasks_crud` nadpisuje
	`data/tasks.json` — jeśli masz ważne dane, zrób kopię:

```powershell
Copy-Item .\data\tasks.json .\data\tasks.json.bak
# po testach:
Move-Item .\data\tasks.json.bak .\data\tasks.json
```


**Ostrzeżenia i uwagi**
- W środowisku deweloperskim zastosowano uproszczone zabezpieczenia (CORS = *,
	plik JSON jako magazyn danych). Dla użycia produkcyjnego rozważ:
	- migrację do prawdziwej bazy danych (SQLite/Postgres),
	- ograniczenie `allow_origins` w CORS,
	- zabezpieczenie dostępu (autentykacja/autoryzacja),
	- lepszy system backup/retencji i monitoring.


**Dalsze propozycje rozwoju**
- Dodać endpoint `DELETE /tasks/{id}` i obsługę usuwania w UI.
- Serwować frontend jako statyczne pliki bezpośrednio z FastAPI (ułatwia deploy).
- Dodać paging/sortowanie do `GET /tasks` i obsługę użytkowników.
- Dodać testy end-to-end (np. Playwright) aby sprawdzić UI i backend razem.


Jeśli chcesz, mogę zintegrować frontend z backendem (serwowanie statyczne),
dodać endpoint usuwania lub przygotować prosty Dockerfile do uruchomienia
aplikacji w kontenerze.


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

