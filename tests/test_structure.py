"""A Swarm kötelező elemeit ellenőrző egyszerű konfigurációs tesztek."""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
STACK = yaml.safe_load((ROOT / "stack.yml").read_text(encoding="utf-8"))


def test_three_services():
    assert set(STACK["services"]) == {"frontend", "backend", "database"}


def test_overlay_networks():
    assert len(STACK["networks"]) >= 1
    assert all(n["driver"] == "overlay" for n in STACK["networks"].values())
    assert "webnet" in STACK["services"]["frontend"]["networks"]
    assert "dbnet" in STACK["services"]["database"]["networks"]


def test_persistent_storage_and_security():
    db = STACK["services"]["database"]
    assert db["volumes"] == ["postgres_data:/var/lib/postgresql/data"]
    assert STACK["secrets"]["todo_db_password"]["external"] is True
    assert not db.get("ports"), "Az adatbázist nem tesszük közzé az interneten"
    assert not STACK["services"]["backend"].get("ports")


def test_scaling_and_recovery_settings():
    api = STACK["services"]["backend"]
    assert api["deploy"]["replicas"] >= 3
    assert api["deploy"]["restart_policy"]["condition"] == "any"
    assert api["deploy"]["update_config"]["parallelism"] == 1


def test_custom_images():
    assert (ROOT / "frontend" / "Dockerfile").is_file()
    assert (ROOT / "backend" / "Dockerfile").is_file()
    assert STACK["services"]["frontend"]["image"] == "flowdesk-frontend:2.0"
    assert STACK["services"]["backend"]["image"] == "flowdesk-backend:2.0"


def test_public_http_port():
    assert STACK["services"]["frontend"]["ports"][0]["published"] == 8080
