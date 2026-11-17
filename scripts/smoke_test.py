"""Végponttól végpontig tartó API teszt a futó, telepített alkalmazáshoz.

Futtatás: python3 scripts/smoke_test.py
Opcionális: BASE_URL=https://pelda.trycloudflare.com python3 scripts/smoke_test.py
Csak a saját TESZT-feladatát törli, az összes többi feladatot megőrzi.
"""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = os.environ.get("BASE_URL", "http://localhost:8080").rstrip("/")


def api(path, method="GET", payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = Request(BASE + path, data=data, method=method,
                  headers={"Content-Type": "application/json"} if data else {})
    with urlopen(req, timeout=15) as response:
        return response.status, json.loads(response.read())


def main():
    created_id = None
    try:
        status, health = api("/api/health")
        assert status == 200 and health["status"] == "ok", health
        print("OK: /api/health: backend és PostgreSQL elérhető")

        status, created = api("/api/tasks", "POST", {"title": "Automatikus Flowdesk-próbafeladat"})
        assert status == 201, created
        created_id = created["task"]["id"]
        print(f"OK: feladat létrehozása, ID={created_id}")

        status, result = api("/api/tasks")
        assert status == 200 and any(x["id"] == created_id for x in result["tasks"])
        print("OK: feladat visszaolvasása az adatbázisból")

        status, updated = api(f"/api/tasks/{created_id}", "PATCH", {"completed": True})
        assert status == 200 and updated["task"]["completed"] is True
        print("OK: feladat készre állítása")

        status, deleted = api(f"/api/tasks/{created_id}", "DELETE")
        assert status == 200 and deleted["deleted"] is True
        created_id = None
        print("OK: tesztfeladat törlése")
        print("SIKER: a futó frontend–backend–adatbázis rendszer API-ja működik.")
    except (HTTPError, URLError, OSError, AssertionError) as exc:
        print("HIBA: a teszt nem sikerült:", exc)
        raise SystemExit(1)
    finally:
        if created_id is not None:
            try:
                api(f"/api/tasks/{created_id}", "DELETE")
            except Exception:
                print(f"FIGYELEM: a {created_id} azonosítójú próba-feladatot kézzel töröld, ha szükséges.")


if __name__ == "__main__":
    main()
