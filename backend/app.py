"""Flowdesk task-management REST API."""
import logging
import os
import socket
from datetime import date

from flask import Flask, jsonify, request
import psycopg
from db import get_connection

app = Flask(__name__)
app.json.ensure_ascii = False
app.logger.setLevel(logging.INFO)

TASK_FIELDS = "id, title, completed, created_at, description, category, priority, due_date"
PRIORITIES = {"low", "medium", "high"}
CATEGORIES = {"work", "personal", "study", "other"}


def json_task(row):
    return {
        "id": row["id"], "title": row["title"], "completed": row["completed"],
        "created_at": row["created_at"].isoformat(),
        "description": row.get("description") or "",
        "category": row.get("category") or "work",
        "priority": row.get("priority") or "medium",
        "due_date": row["due_date"].isoformat() if row.get("due_date") else None,
    }


def db_error(exc):
    app.logger.error("Database error: %s", exc)
    return jsonify({"error": "Az adatbázis átmenetileg nem érhető el."}), 503


def validate(payload, create=False):
    if not isinstance(payload, dict):
        return None, "Érvényes JSON objektum szükséges."
    allowed = {"title", "description", "category", "priority", "due_date", "completed"}
    if not payload or any(key not in allowed for key in payload):
        return None, "Hiányzó vagy ismeretlen mező."
    if create and "title" not in payload:
        return None, "A feladat neve kötelező."
    clean = {}
    if "title" in payload:
        v = payload["title"]
        if not isinstance(v, str) or not 1 <= len(v.strip()) <= 160:
            return None, "A feladat neve 1–160 karakter lehet."
        clean["title"] = v.strip()
    if "description" in payload:
        v = payload["description"]
        if not isinstance(v, str) or len(v) > 1000:
            return None, "A leírás legfeljebb 1000 karakter lehet."
        clean["description"] = v.strip()
    for field, choices in (("category", CATEGORIES), ("priority", PRIORITIES)):
        if field in payload:
            if payload[field] not in choices:
                return None, f"Érvénytelen {field} érték."
            clean[field] = payload[field]
    if "due_date" in payload:
        v = payload["due_date"]
        if v is None or v == "":
            clean["due_date"] = None
        elif isinstance(v, str):
            try:
                parsed = date.fromisoformat(v)
                if parsed.isoformat() != v:
                    raise ValueError
                clean["due_date"] = parsed
            except ValueError:
                return None, "A határidő YYYY-MM-DD formátumú legyen."
        else:
            return None, "Érvénytelen határidő."
    if "completed" in payload:
        if type(payload["completed"]) is not bool:
            return None, "A completed mező true vagy false legyen."
        clean["completed"] = payload["completed"]
    return clean, None


@app.after_request
def add_headers(response):
    response.headers["X-Backend-Instance"] = socket.gethostname()
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/api/health")
def health():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return jsonify({"status": "ok", "database": "ok"})
    except psycopg.Error as exc:
        return db_error(exc)


@app.get("/api/meta")
def meta():
    return jsonify({"name": "Flowdesk", "version": "2.0", "instance": socket.gethostname()})


@app.get("/api/tasks")
def list_tasks():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT {TASK_FIELDS} FROM tasks ORDER BY id DESC")
                records = cur.fetchall()
        return jsonify({"tasks": [json_task(row) for row in records], "instance": socket.gethostname()})
    except psycopg.Error as exc:
        return db_error(exc)


@app.post("/api/tasks")
def add_task():
    clean, error = validate(request.get_json(silent=True), create=True)
    if error:
        return jsonify({"error": error}), 400
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"INSERT INTO tasks (title, description, category, priority, due_date, completed) "
                    f"VALUES (%s, %s, %s, %s, %s, %s) RETURNING {TASK_FIELDS}",
                    (clean["title"], clean.get("description", ""), clean.get("category", "work"),
                     clean.get("priority", "medium"), clean.get("due_date"), clean.get("completed", False)),
                )
                record = cur.fetchone()
        return jsonify({"task": json_task(record)}), 201
    except psycopg.Error as exc:
        return db_error(exc)


@app.patch("/api/tasks/<int:task_id>")
def update_task(task_id):
    clean, error = validate(request.get_json(silent=True))
    if error:
        return jsonify({"error": error}), 400
    fields = list(clean)
    assignments = ", ".join(f"{field} = %s" for field in fields)  # fields restricted by validate()
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE tasks SET {assignments} WHERE id = %s RETURNING {TASK_FIELDS}",
                    (*[clean[field] for field in fields], task_id),
                )
                record = cur.fetchone()
        if record is None:
            return jsonify({"error": "Nincs ilyen feladat."}), 404
        return jsonify({"task": json_task(record)})
    except psycopg.Error as exc:
        return db_error(exc)


@app.delete("/api/tasks/<int:task_id>")
def delete_task(task_id):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM tasks WHERE id = %s RETURNING id", (task_id,))
                record = cur.fetchone()
        if record is None:
            return jsonify({"error": "Nincs ilyen feladat."}), 404
        return jsonify({"deleted": True, "id": record["id"]})
    except psycopg.Error as exc:
        return db_error(exc)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
