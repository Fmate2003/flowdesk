# Flowdesk 3.0 – UI frissítés telepítése

Ez a csomag csak a `frontend/` mappa fájljait és a `stack.yml` frontend image-azonosítóját frissíti. Az adatbázis és a backend változatlan.

1. A jelenlegi projektfájlokról érdemes Git commitot készíteni. A PostgreSQL volume-ot nem szabad törölni.
2. A ZIP-et a Windows Downloads mappából a Flowdesk projektgyökerébe kell kicsomagolni:

```bash
cd ~/flowdesk-v2/flowdesk-swarm
unzip -o /mnt/c/Users/user/Downloads/Flowdesk_3_UI_Frissites.zip -d .
```

3. Új frontend image építése:

```bash
sudo systemctl start docker
sudo docker build -t flowdesk-frontend:3.0 ./frontend
```

4. A futó stack frissítése vagy újbóli indítása:

```bash
sudo docker stack deploy --resolve-image never -c stack.yml todoapp
sudo docker service ls
```

Elvárt: `todoapp_frontend` → `flowdesk-frontend:3.0` és `1/1`; backend `flowdesk-backend:2.0` `3/3`; adatbázis `postgres:16-alpine` `1/1`.

5. Böngésző: `http://127.0.0.1:8080` (Ctrl+F5), majd feladatok, keresés, szűrés, pipálás, szerkesztés és törlés ellenőrzése.

6. Visszaállítás: `stack.yml` frontend image-je `flowdesk-frontend:2.0`, majd `sudo docker stack deploy --resolve-image never -c stack.yml todoapp`. A forrásfájlok visszaállításához `git restore frontend/` használható, amennyiben a régi verzió Git-commitban van, és az új fájlokat még nem commitoltuk.

A GitHubra az ellenőrzött változat tölthető fel: `git add frontend stack.yml DESIGN.md TELEPITES_UI_3.md && git commit -m "Redesign Flowdesk UI" && git push`.
