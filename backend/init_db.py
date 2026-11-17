"""Idempotent PostgreSQL schema migration; safe for concurrent Swarm replicas."""
import logging
import time
import psycopg
from db import get_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
  id BIGSERIAL PRIMARY KEY,
  title VARCHAR(160) NOT NULL CHECK (length(btrim(title)) > 0),
  completed BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS description VARCHAR(1000) NOT NULL DEFAULT '';
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS category VARCHAR(20) NOT NULL DEFAULT 'work';
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS priority VARCHAR(20) NOT NULL DEFAULT 'medium';
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS due_date DATE;
"""

for attempt in range(1, 61):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT pg_advisory_xact_lock(20261115)")
                for statement in SCHEMA.strip().split(';'):
                    if statement.strip():
                        cur.execute(statement)
        logging.info("Database schema up to date.")
        break
    except (psycopg.Error, OSError) as exc:
        if attempt == 60:
            raise
        logging.warning("Waiting for database (%s/60): %s", attempt, exc)
        time.sleep(2)
