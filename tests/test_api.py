"""Adatbázist szimuláló API-egységtesztek; NEM igényelnek futó Docker-t."""
from datetime import datetime, timezone
from pathlib import Path
import sys
from unittest.mock import patch

import psycopg
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import app as todo_app  # noqa: E402


class FakeStore:
    def __init__(self):
        self.tasks = {}
        self.next_id = 1

    def connection(self):
        return FakeConnection(self)


class FakeConnection:
    def __init__(self, store):
        self.store = store

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def cursor(self):
        return FakeCursor(self.store)


class FakeCursor:
    def __init__(self, store):
        self.store = store
        self.result = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, sql, params=None):
        normalized = " ".join(sql.split()).upper()
        self.result = []
        if normalized.startswith("SELECT 1"):
            self.result = [{"value": 1}]
        elif normalized.startswith("SELECT ID, TITLE"):
            self.result = sorted(self.store.tasks.values(), key=lambda row: row["id"], reverse=True)
        elif normalized.startswith("INSERT INTO TASKS"):
            task = {"id": self.store.next_id, "title": params[0], "completed": False,
                    "created_at": datetime.now(timezone.utc), "description": params[1],
                    "category": params[2], "priority": params[3], "due_date": params[4]}
            self.store.tasks[self.store.next_id] = task
            self.store.next_id += 1
            self.result = [task.copy()]
        elif normalized.startswith("UPDATE TASKS"):
            *values, task_id = params
            columns = [part.split("=")[0].strip().lower() for part in sql.split(" SET ", 1)[1].split(" WHERE ", 1)[0].split(",")]
            if task_id in self.store.tasks:
                self.store.tasks[task_id].update(dict(zip(columns, values)))
                self.result = [self.store.tasks[task_id].copy()]
        elif normalized.startswith("DELETE FROM TASKS"):
            row = self.store.tasks.pop(params[0], None)
            if row:
                self.result = [{"id": row["id"]}]
        else:
            raise AssertionError("Ismeretlen SQL a tesztben: " + sql)

    def fetchone(self):
        return self.result[0] if self.result else None

    def fetchall(self):
        return self.result


@pytest.fixture
def client():
    store = FakeStore()
    with patch.object(todo_app, "get_connection", side_effect=store.connection):
        yield todo_app.app.test_client()


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json == {"status": "ok", "database": "ok"}


def test_crud_cycle(client):
    created = client.post("/api/tasks", json={"title": "  Tanulás  "})
    assert created.status_code == 201
    task_id = created.json["task"]["id"]
    assert created.json["task"]["title"] == "Tanulás"
    assert created.json["task"]["completed"] is False
    assert created.json["task"]["created_at"]

    listed = client.get("/api/tasks")
    assert len(listed.json["tasks"]) == 1
    assert listed.headers["X-Backend-Instance"]

    updated = client.patch(f"/api/tasks/{task_id}", json={"completed": True})
    assert updated.status_code == 200
    assert updated.json["task"]["completed"] is True

    deleted = client.delete(f"/api/tasks/{task_id}")
    assert deleted.status_code == 200
    assert client.get("/api/tasks").json["tasks"] == []


@pytest.mark.parametrize("payload", [None, {}, {"title": ""}, {"title": "   "},
                                    {"title": 12}, {"title": "a" * 161}, [1, 2, 3]])
def test_bad_title(client, payload):
    if payload is None:
        response = client.post("/api/tasks", data="not-json", content_type="text/plain")
    else:
        response = client.post("/api/tasks", json=payload)
    assert response.status_code == 400


@pytest.mark.parametrize("payload", [{}, {"completed": "true"}, {"completed": 1}, {"completed": None}])
def test_bad_update(client, payload):
    assert client.patch("/api/tasks/5", json=payload).status_code == 400


def test_missing_task(client):
    assert client.patch("/api/tasks/999", json={"completed": True}).status_code == 404
    assert client.delete("/api/tasks/999").status_code == 404


def test_db_error_is_503(client):
    with patch.object(todo_app, "get_connection", side_effect=psycopg.OperationalError("secret details")):
        result = client.get("/api/tasks")
    assert result.status_code == 503
    assert "secret details" not in result.get_data(as_text=True)


def test_meta(client):
    response = client.get("/api/meta")
    assert response.status_code == 200
    assert response.json["version"] == "2.0"


def test_advanced_fields(client):
    created = client.post("/api/tasks", json={"title": "Jelentés", "priority": "high",
        "category": "work", "description": "Havi riport", "due_date": "2026-12-10"})
    assert created.status_code == 201
    task = created.json["task"]
    assert task["priority"] == "high"
    assert task["due_date"] == "2026-12-10"
    edited = client.patch(f"/api/tasks/{task['id']}", json={"title": "Havi jelentés", "priority": "low"})
    assert edited.status_code == 200
    assert edited.json["task"]["title"] == "Havi jelentés"
    assert edited.json["task"]["priority"] == "low"


def test_invalid_advanced_fields(client):
    for payload in ({"title": "T", "priority": "urgent"},
                    {"title": "T", "due_date": "holnap"},
                    {"title": "T", "description": "x" * 1001}):
        assert client.post("/api/tasks", json=payload).status_code == 400
