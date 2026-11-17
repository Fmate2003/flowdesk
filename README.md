# Flowdesk

Professzionális, reszponzív feladatmenedzsment webalkalmazás. Háromszolgáltatásos architektúra: Nginx frontend, Python Flask API (3 példány), PostgreSQL adatbázis. Docker Swarm stack, overlay hálózatok, Docker Secret és tartós PostgreSQL volume.

## Funkciók

- Feladatok létrehozása, szerkesztése, lezárása és törlése
- Leírás, kategória (munka/személyes/tanulás/egyéb), prioritás, határidő
- Élő összesítők, keresés, állapot szerinti szűrés és rendezés
- Telefonon is használható felület
- Meglévő feladatok megőrzése automatikus adatbázisséma-bővítéssel

## Telepítés Docker Swarm alatt

A projekt gyökerében:

```bash
sudo docker swarm init  # csak ha még nincs aktív Swarm
openssl rand -base64 32 | sudo docker secret create todo_db_password -  # csak első alkalommal
sudo docker build -t flowdesk-backend:2.0 ./backend
sudo docker build -t flowdesk-frontend:2.0 ./frontend
sudo docker stack deploy --resolve-image never -c stack.yml todoapp
sudo docker service ls
```

**Meglévő telepítés frissítése:** a secretet és a `swarm init` parancsot NEM kell megismételni; csak a két image build és a `stack deploy` szükséges. A PostgreSQL adatokat tároló `todoapp_postgres_data` volume változatlan marad.

Helyi elérés: http://127.0.0.1:8080

## API

- `GET /api/health` – adatbázis-ellenőrzés
- `GET /api/tasks` – feladatlista
- `POST /api/tasks` – létrehozás (`title`, `description`, `category`, `priority`, `due_date`)
- `PATCH /api/tasks/{id}` – részleges módosítás (pl. `completed`)
- `DELETE /api/tasks/{id}` – törlés

## Fontos

A publikus demo jelenleg nem használ felhasználói bejelentkezést, így aki ismeri a linket, megtekintheti és módosíthatja a közös feladatlistát. Éles személyes vagy üzleti adatokkal ne használd. Termelési használathoz autentikáció, jogosultságkezelés és biztonsági felülvizsgálat szükséges.
