"""Adatbázis-kapcsolat; a jelszó Docker Swarm secretből érkezik."""
import os
from pathlib import Path
import psycopg
from psycopg.rows import dict_row


def db_password():
    secret = os.getenv("DB_PASSWORD_FILE", "/run/secrets/todo_db_password")
    if Path(secret).is_file():
        return Path(secret).read_text(encoding="utf-8").strip()
    # Csak helyi fejlesztéskor használható; stack.yml-ben NINCS DB_PASSWORD.
    password = os.getenv("DB_PASSWORD")
    if password:
        return password
    raise RuntimeError("Hiányzik a DB_PASSWORD_FILE Docker secret.")


def get_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "database"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "tasksdb"),
        user=os.getenv("DB_USER", "todo_user"),
        password=db_password(),
        connect_timeout=4,
        row_factory=dict_row,
    )
