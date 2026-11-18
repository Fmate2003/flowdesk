
# Flowdesk 2.0 – Feladatmenedzsment alkalmazás Docker Swarm környezetben

A **Flowdesk** egy reszponzív, böngészőből használható feladatmenedzsment alkalmazás, amely Docker Swarm környezetben működik.

A rendszer három együttműködő szolgáltatásból áll: Nginx frontendből, Python Flask backendből és PostgreSQL-adatbázisból.

A projekt megvalósítja a konténeralapú telepítést, a szolgáltatások közötti kommunikációt, a tartós adattárolást, a horizontális skálázást és az automatikus konténer-helyreállítást. Az alkalmazás Cloudflare Tunnel használatával nyilvános HTTPS-címen is elérhetővé tehető.

**Forráskód:** https://github.com/Fmate2003/flowdesk

## Tartalomjegyzék

1. [A projekt célja és funkciói](#1-a-projekt-célja-és-funkciói)
2. [Rendszerarchitektúra](#2-rendszerarchitektúra)
3. [Felhasznált technológiák](#3-felhasznált-technológiák)
4. [Fejlesztői környezet](#4-fejlesztői-környezet)
5. [Projektstruktúra és megvalósítás](#5-projektstruktúra-és-megvalósítás)
6. [Telepítés Docker Swarm alatt](#6-telepítés-docker-swarm-alatt)
7. [API és alkalmazásműködés](#7-api-és-alkalmazásműködés)
8. [Docker Swarm konfiguráció ellenőrzése](#8-docker-swarm-konfiguráció-ellenőrzése)
9. [Skálázás és automatikus helyreállítás](#9-skálázás-és-automatikus-helyreállítás)
10. [Nyilvános HTTPS-elérés](#10-nyilvános-https-elérés)
11. [Automatizált tesztelés](#11-automatizált-tesztelés)
12. [Leállítás és újraindítás](#12-leállítás-és-újraindítás)
13. [Verziókövetés GitHubon](#13-verziókövetés-githubon)
14. [Hibaelhárítás](#14-hibaelhárítás)
15. [Biztonság és továbbfejlesztés](#15-biztonság-és-továbbfejlesztés)
16. [Tesztelési dokumentáció](#16-tesztelési-dokumentáció)

---

## 1. A projekt célja és funkciói

A Flowdesk célja egy egyszerűen használható feladatmenedzsment rendszer kialakítása, amely a hagyományos alkalmazásfunkciók mellett konténeres infrastruktúrán működik.

Az alkalmazás lehetővé teszi a feladatok létrehozását, módosítását, rendszerezését, teljesítettnek jelölését és törlését.

### Felhasználói funkciók

- Feladatok létrehozása, szerkesztése és törlése.
- Feladatok teljesítettnek jelölése.
- Feladatleírások megadása.
- Kategóriák kezelése: munka, személyes, tanulás és egyéb.
- Prioritások beállítása: alacsony, normál és magas.
- Határidők rögzítése.
- Feladatok keresése, szűrése és rendezése.
- Áttekintő statisztikák megjelenítése.
- Reszponzív felület asztali és mobilos használatra.

### Infrastrukturális funkciók

- Három együttműködő Docker Swarm-szolgáltatás.
- Saját Dockerfile-ok és Docker image-ek.
- Több példányban futó backend.
- Overlay hálózatok.
- PostgreSQL-adatok tárolása Docker Volume használatával.
- Adatbázis-jelszó kezelése Docker Secrettel.
- Konténer-egészségellenőrzések.
- Automatikus konténer-helyreállítás.
- Dinamikus skálázás.
- Nyilvános HTTPS-elérés Cloudflare Tunnel segítségével.

---

## 2. Rendszerarchitektúra

A Flowdesk háromrétegű architektúrát használ.

```text
               Böngésző / mobiltelefon
                         |
                         | HTTP / HTTPS
                         v
                 Nginx Frontend
               flowdesk-frontend:2.0
                      1 replika
                         |
                         | /api/*
                         | todoapp_webnet
                         v
                 Python Flask API
               flowdesk-backend:2.0
                      3 replika
                         |
                         | todoapp_dbnet
                         v
                 PostgreSQL 16
                      1 replika
                         |
                         v
             todoapp_postgres_data
                 Docker Volume
```

### 2.1. Frontend

A frontend Nginx webszerveren keresztül szolgálja ki a HTML-, CSS- és JavaScript-fájlokat.

Az Nginx az `/api/` útvonalra érkező kéréseket továbbítja a backend szolgáltatásnak.

A frontend Docker image neve:

`flowdesk-frontend:2.0`

### 2.2. Backend

A Python Flask alkalmazás valósítja meg a feladatkezelés üzleti logikáját.

A backend REST API-végpontokon keresztül végzi a feladatok létrehozását, lekérdezését, módosítását és törlését.

A szolgáltatás alapértelmezetten három példányban fut.

A backend Docker image neve:

`flowdesk-backend:2.0`

A több backendpéldány lehetővé teszi a beérkező kérések elosztását, valamint a kiesett konténerpéldányok automatikus pótlását.

### 2.3. Adatbázis

Az alkalmazás PostgreSQL 16 adatbázist használ.

A feladatok adatai nem a böngésző memóriájában, hanem az adatbázisban tárolódnak.

A PostgreSQL a `todoapp_postgres_data` nevű Docker Volume-ot használja.

A tartós adattárolásnak köszönhetően a mentett feladatok a PostgreSQL-konténer újraindítását vagy cseréjét követően is megmaradnak.

### 2.4. Hálózati felépítés

A rendszer két külön overlay hálózatot használ.

| Hálózat | Kapcsolódó szolgáltatások |
|---|---|
| `todoapp_webnet` | Frontend, backend |
| `todoapp_dbnet` | Backend, adatbázis |

A frontend nem kapcsolódik közvetlenül az adatbázishoz. Az adatbázis kizárólag a backend számára elérhető belső hálózaton kommunikál.

Ez a felépítés elkülöníti a webes és az adatbázis-réteget.

---

## 3. Felhasznált technológiák

| Technológia | Feladat |
|---|---|
| Windows 10 | Hoszt operációs rendszer |
| WSL 2 | Linux futtatókörnyezet Windows alatt |
| Ubuntu | Fejlesztési és Docker-környezet |
| Visual Studio Code | Forráskódszerkesztés |
| Docker Engine | Konténerek futtatása |
| Dockerfile | Saját Docker image-ek felépítése |
| Docker Swarm | Szolgáltatások kezelése |
| Docker Stack | Többszolgáltatásos telepítés |
| Nginx | Webszerver és reverse proxy |
| Python Flask | Backend API |
| Gunicorn | Python alkalmazásszerver |
| PostgreSQL | Relációs adatbázis |
| Docker Volume | Tartós adattárolás |
| Docker Secret | Bizalmas konfigurációs adatok kezelése |
| Cloudflare Tunnel | Nyilvános HTTPS-elérés |
| Git | Verziókövetés |
| GitHub | Forráskód és dokumentáció tárolása |

---

## 4. Fejlesztői környezet

A Flowdesk Windows 10 operációs rendszeren, Ubuntu WSL 2 környezetben készült.

A forráskód szerkesztéséhez Visual Studio Code-ot, a Docker-parancsok végrehajtásához Ubuntu terminált használtunk.

### 4.1. WSL ellenőrzése

Windows PowerShellben:

```powershell
wsl --list --verbose
wsl --version
```

A WSL 2 Linux virtuális környezetet biztosít Windows alatt.

### 4.2. Projekt megnyitása

A projekt helyi fejlesztési könyvtára:

```bash
cd ~/flowdesk-v2/flowdesk-swarm
pwd
code .
```

A `pwd` megjeleníti a jelenlegi könyvtárat, a `code .` pedig megnyitja azt a Visual Studio Code-ban.

### 4.3. Docker Engine

A Docker telepítése Ubuntu alatt:

```bash
sudo apt-get update
sudo apt-get install -y docker.io
```

A Docker szolgáltatás indítása:

```bash
sudo systemctl start docker
```

A működés ellenőrzése:

```bash
systemctl is-active docker
sudo docker version
sudo docker run --rm hello-world
```

Az `active` állapot a Docker Engine működését jelzi. A `hello-world` konténer a Docker futtatókörnyezet alapvető működésének ellenőrzésére szolgál.

---

## 5. Projektstruktúra és megvalósítás

### 5.1. Könyvtárszerkezet

```text
flowdesk-swarm/
├── .env.example
├── .gitignore
├── README.md
├── stack.yml
├── backend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── requirements.txt
│   ├── app.py
│   ├── db.py
│   └── init_db.py
├── frontend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── nginx.conf
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── docs/
│   ├── architecture.md
│   ├── Flowdesk_Vedesi_Attekintes.pdf
│   ├── VEDES_TESZTEK.md
│   └── images/
├── scripts/
│   └── smoke_test.py
├── tests/
│   ├── test_api.py
│   └── test_structure.py
└── dev-requirements.txt
```

### 5.2. Frontend megvalósítása

A `frontend/index.html` tartalmazza a felhasználói felület struktúráját.

A `frontend/styles.css` biztosítja a megjelenést és a reszponzív kialakítást.

A `frontend/app.js` kezeli a felhasználói műveleteket, és HTTP-kéréseket küld a backend API-nak.

A `frontend/nginx.conf` konfigurálja az Nginx webszervert és az API-kérések továbbítását.

### 5.3. Backend megvalósítása

A `backend/app.py` tartalmazza a Flask API-végpontokat.

A `backend/db.py` kezeli a PostgreSQL-adatbázishoz történő kapcsolódást.

A `backend/init_db.py` az adatbázis tábláinak létrehozását és szükség szerinti bővítését végzi.

Az adatbázisséma bővítése lehetővé teszi az új feladatmezők hozzáadását a korábban mentett feladatok megtartásával.

### 5.4. Docker image-ek

A backend saját Dockerfile alapján épül, `python:3.12-slim` alapimage használatával.

A frontend `nginx:stable-alpine` alapimage-re épül.

Az image-ek előállítása:

```bash
sudo docker build -t flowdesk-backend:2.0 ./backend
sudo docker build -t flowdesk-frontend:2.0 ./frontend
```

Az elkészült image-ek listázása:

```bash
sudo docker images
```

A rendszer két saját Docker image-et és egy hivatalos PostgreSQL image-et használ.

---

## 6. Telepítés Docker Swarm alatt

### 6.1. Forráskód letöltése

```bash
git clone https://github.com/Fmate2003/flowdesk.git
cd flowdesk
```

A `git clone` a GitHubon tárolt forráskódot másolja a helyi környezetbe.

### 6.2. Docker Swarm

A Swarm aktuális állapotának lekérdezése:

```bash
sudo docker info --format '{{.Swarm.LocalNodeState}}'
```

Az `active` eredmény aktív Docker Swarm környezetet jelent.

Új Docker-környezetben a Swarm inicializálása:

```bash
sudo docker swarm init
```

A csomópontok ellenőrzése:

```bash
sudo docker node ls
```

A projekt egy manager szerepkörű, egycsomópontos Docker Swarm-környezetben fut.

A manager csomópont a szolgáltatások kívánt állapotát kezeli, és gondoskodik a feladatok ütemezéséről.

### 6.3. Docker Secret

A PostgreSQL és a backend ugyanazt az adatbázis-jelszót használja.

A jelszót a rendszer Docker Secret segítségével kezeli, így annak tényleges értéke nem szerepel a `stack.yml` fájlban.

A Secret létrehozása az első telepítéskor:

```bash
openssl rand -base64 32 | sudo docker secret create todo_db_password -
```

A létrehozott Secretek listázása:

```bash
sudo docker secret ls
```

A `stack.yml` a `todo_db_password` Secretet külső erőforrásként hivatkozza.

**Adatbázis-hitelesítés:** meglévő PostgreSQL-adatkötet használatakor a hitelesítési adatoknak összhangban kell maradniuk az adatbázis eredeti konfigurációjával. A Secret tényleges értéke nem része a GitHubon közzétett forráskódnak.

### 6.4. Docker image-ek építése

```bash
sudo docker build -t flowdesk-backend:2.0 ./backend
sudo docker build -t flowdesk-frontend:2.0 ./frontend
```

A két image tartalmazza a frontend és a backend futtatásához szükséges alkalmazásfájlokat és függőségeket.

### 6.5. Docker Stack telepítése

```bash
sudo docker stack deploy --resolve-image never -c stack.yml todoapp
```

A parancs a `stack.yml` konfigurációja alapján létrehozza a Docker Swarm-szolgáltatásokat és a hozzájuk tartozó hálózatokat.

A `todoapp` a stack neve.

A `--resolve-image never` beállítás a helyben létrehozott image-ekkel működő, egycsomópontos környezethez illeszkedik.

### 6.6. Szolgáltatások ellenőrzése

```bash
sudo docker service ls
```

A működő rendszer szolgáltatásai:

| Szolgáltatás | Image | Példányszám |
|---|---|---|
| `todoapp_frontend` | `flowdesk-frontend:2.0` | 1/1 |
| `todoapp_backend` | `flowdesk-backend:2.0` | 3/3 |
| `todoapp_database` | `postgres:16-alpine` | 1/1 |

A `REPLICAS` oszlop a futó és az előírt példányok számát mutatja.

### 6.7. Alkalmazás elérése

A frontend a 8080-as porton érhető el:

http://127.0.0.1:8080

A webes felületen elérhetők a feladatkezelési funkciók és az áttekintő statisztikák.

---

## 7. API és alkalmazásműködés

A Flowdesk REST API-t használ a frontend és a backend közötti kommunikációhoz.

### 7.1. API-végpontok

| HTTP-metódus | Végpont | Funkció |
|---|---|---|
| GET | `/api/health` | Alkalmazás és adatbázis állapotának lekérdezése |
| GET | `/api/tasks` | Feladatok listázása |
| POST | `/api/tasks` | Új feladat létrehozása |
| PATCH | `/api/tasks/{id}` | Feladat módosítása |
| DELETE | `/api/tasks/{id}` | Feladat törlése |

### 7.2. API állapotának ellenőrzése

```bash
curl -i --max-time 10 http://127.0.0.1:8080/api/health
```

Sikeres működés esetén az alkalmazás HTTP 200-as választ ad.

A válasz törzse:

```json
{
  "database": "ok",
  "status": "ok"
}
```

A `database: ok` érték azt mutatja, hogy a backend kapcsolatot tud létesíteni a PostgreSQL-adatbázissal.

### 7.3. Feladatok lekérdezése

```bash
curl -s --max-time 10 http://127.0.0.1:8080/api/tasks
```

A backend JSON-formátumban visszaadja az adatbázisban tárolt feladatokat.

A válasz tartalmazhatja a feladat azonosítóját, nevét, leírását, kategóriáját, prioritását, határidejét és állapotát.

### 7.4. Új feladat létrehozása

```bash
curl -sS -X POST http://127.0.0.1:8080/api/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"API tesztfeladat","description":"Feladat létrehozása","category":"study","priority":"high"}'
```

A POST kérés új rekordot hoz létre a PostgreSQL-adatbázisban.

### 7.5. Feladat módosítása

```bash
curl -sS -X PATCH http://127.0.0.1:8080/api/tasks/42 \
  -H 'Content-Type: application/json' \
  -d '{"completed":true}'
```

A `42` példaazonosító. A módosítási végpont a megadott azonosítóval rendelkező feladat adatait frissíti.

### 7.6. Feladat törlése

```bash
curl -sS -X DELETE http://127.0.0.1:8080/api/tasks/42
```

A DELETE kérés eltávolítja a megadott azonosítójú feladatot.

---

## 8. Docker Swarm konfiguráció ellenőrzése

### 8.1. Docker Swarm állapota

```bash
sudo docker node ls
```

A parancs megjeleníti a Docker Swarm-csomópontokat.

A projekt egy manager csomópontot használ, amely `Ready` állapotban működik.

### 8.2. Szolgáltatások

```bash
sudo docker service ls
```

A parancs megjeleníti a Swarm által kezelt frontend, backend és adatbázis-szolgáltatásokat.

### 8.3. Saját Docker image-ek

```bash
sudo docker images
```

A kimenetben szerepel a `flowdesk-backend:2.0` és a `flowdesk-frontend:2.0` image.

### 8.4. Overlay hálózatok

```bash
sudo docker network ls
```

A Flowdesk két overlay hálózata:

- `todoapp_webnet`
- `todoapp_dbnet`

A hálózati driver ellenőrzése:

```bash
sudo docker network inspect todoapp_webnet --format '{{.Driver}}'
sudo docker network inspect todoapp_dbnet --format '{{.Driver}}'
```

Mindkét hálózat `overlay` drivert használ.

### 8.5. Docker Volume

```bash
sudo docker volume ls
```

A PostgreSQL tartós adattárolója:

`todoapp_postgres_data`

A szolgáltatáshoz tartozó csatolás lekérdezése:

```bash
sudo docker service inspect todoapp_database --format '{{json .Spec.TaskTemplate.ContainerSpec.Mounts}}'
```

A PostgreSQL az adatokat a `/var/lib/postgresql/data` könyvtárban tárolja, amelyhez a Docker Volume csatlakozik.

### 8.6. Docker Secret

```bash
sudo docker secret ls
```

A szolgáltatások a `todo_db_password` nevű Docker Secretet használják.

A Secret elkülöníti a bizalmas hitelesítési adatot a forráskódtól és a Docker Stack konfigurációjától.

---

## 9. Skálázás és automatikus helyreállítás

### 9.1. Backend skálázása

A Docker Swarm lehetővé teszi a backend példányszámának dinamikus módosítását.

A backend alapértelmezett példányszáma három.

A szolgáltatás öt példányra történő skálázása:

```bash
sudo docker service scale todoapp_backend=5
```

Az állapot ellenőrzése:

```bash
sudo docker service ls
sudo docker service ps todoapp_backend
```

A Swarm két új backendkonténert indít a meglévő három mellé.

A sikeres skálázás eredménye `5/5` futó backendpéldány.

### 9.2. Visszaskálázás

```bash
sudo docker service scale todoapp_backend=3
sudo docker service ls
```

A Swarm leállítja a két további backendpéldányt.

A szolgáltatás ismét az alapértelmezett `3/3` állapotban működik.

A skálázás során a frontend és az adatbázis konfigurációja változatlan marad.

### 9.3. Automatikus helyreállítás

A Docker Swarm folyamatosan figyeli a szolgáltatások tényleges és elvárt példányszámát.

A backendkonténerek listázása:

```bash
sudo docker ps --filter "label=com.docker.swarm.service.name=todoapp_backend"
```

Egy backendkonténer szándékos leállítása az aktuális konténerazonosító alapján:

```bash
sudo docker kill KONTAINER_AZONOSITO
```

A konténer kiesése után a Docker Swarm automatikusan új példányt indít.

A helyreállítás ellenőrzése:

```bash
sudo docker service ps todoapp_backend
sudo docker service ls
```

A korábbi feladat `Failed` állapotban jelenhet meg, míg az új feladat `Running` állapotba kerül.

A backend szolgáltatás ismét `3/3` példányszámmal működik.

A rendszerben ezt a működést tényleges konténerleállítással ellenőriztük.

### 9.4. Tartós adattárolás

A PostgreSQL az adatokat a `todoapp_postgres_data` Docker Volume-ban tárolja.

Az adatbázis-konténer cseréje során a Swarm új konténert indít, amely ugyanazt a tartós adatkötetet használja.

Az adatmegőrzést korábban létrehozott feladatokkal ellenőriztük.

A PostgreSQL-konténer leállítása és automatikus pótlása után a mentett feladatok továbbra is elérhetők maradtak.

A teljes WSL-környezet és a számítógép újraindítása után is megmaradtak az adatbázisban tárolt rekordok.

### 9.5. Naplók

```bash
sudo docker service logs --tail 50 todoapp_frontend
sudo docker service logs --tail 50 todoapp_backend
sudo docker service logs --tail 50 todoapp_database
```

A szolgáltatásnaplók az alkalmazás indulásáról, működéséről és az esetleges hibákról tartalmaznak információkat.

---

## 10. Nyilvános HTTPS-elérés

A Flowdesk alapértelmezetten helyi hálózati címen működik.

A Cloudflare Tunnel lehetővé teszi az alkalmazás internetes elérését a helyi Docker Swarm-környezetből.

### 10.1. Cloudflared telepítése

Ubuntu alatt a hivatalos Debian-csomag használható:

```bash
curl -fL --output /tmp/cloudflared.deb \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb

sudo apt install -y /tmp/cloudflared.deb
```

A telepített verzió ellenőrzése:

```bash
cloudflared --version
```

### 10.2. Tunnel indítása

```bash
cloudflared tunnel --url http://127.0.0.1:8080
```

A Cloudflare Tunnel egy kimenő kapcsolatot hoz létre a helyi alkalmazás és a Cloudflare hálózata között.

A program egy ideiglenes HTTPS-címet generál:

```text
https://veletlenszeru-nev.trycloudflare.com
```

A nyilvános cím a helyi `127.0.0.1:8080` címre továbbítja a webes kéréseket.

A Flowdesk nyilvános elérését másik eszközről is ellenőriztük. A feladatok létrehozása és visszaolvasása külső hálózatról is működött.

A TryCloudflare Quick Tunnel ideiglenes elérést biztosít, nem állandó alkalmazáshosztingot. A szolgáltatás csak a helyi alkalmazás és a tunnel működése alatt érhető el.

---

## 11. Automatizált tesztelés

A projekt Python-alapú automatizált teszteket is tartalmaz.

### 11.1. Tesztkörnyezet

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r dev-requirements.txt
```

A virtuális Python-környezet elkülöníti a teszteléshez szükséges függőségeket a rendszer többi Python-csomagjától.

### 11.2. Egység- és konfigurációs tesztek

```bash
python3 -m pytest -q
```

A `tests/test_api.py` a backend API működését ellenőrzi.

A `tests/test_structure.py` a Docker Swarm-konfiguráció egyes elemeit vizsgálja, például a szolgáltatásokat, hálózatokat, replikákat és adattárolási beállításokat.

### 11.3. API-gyorsteszt

Futó alkalmazás mellett:

```bash
python3 scripts/smoke_test.py
```

A gyorsteszt az alkalmazás fő API-műveleteit ellenőrzi:

1. Alkalmazás- és adatbázis-kapcsolat.
2. Feladat létrehozása.
3. Feladat visszaolvasása.
4. Feladat módosítása.
5. Tesztfeladat törlése.

A teszt a saját maga által létrehozott próbaadatokat használja.

---

## 12. Leállítás és újraindítás

### 12.1. Alkalmazás leállítása

A Cloudflare Tunnel a futó terminálban `Ctrl + C` billentyűkombinációval állítható le.

A Docker Swarm stack eltávolítása:

```bash
sudo docker stack rm todoapp
```

A szolgáltatások ellenőrzése:

```bash
sudo docker service ls
```

A `docker stack rm` eltávolítja a stack szolgáltatásait és hálózatait.

A parancs nem törli automatikusan a PostgreSQL tartós Docker Volume-ot vagy a helyi Docker image-eket.

### 12.2. Docker Engine leállítása

```bash
sudo systemctl stop docker docker.socket
```

A Docker állapotának ellenőrzése:

```bash
systemctl is-active docker
```

A leállított szolgáltatás állapota `inactive`.

A WSL-környezet Windows PowerShellből leállítható:

```powershell
wsl --shutdown
```

### 12.3. Alkalmazás újraindítása

```bash
cd ~/flowdesk-v2/flowdesk-swarm

sudo systemctl start docker

sudo docker info --format '{{.Swarm.LocalNodeState}}'

sudo docker stack deploy --resolve-image never -c stack.yml todoapp

sudo docker service ls
```

A korábban létrehozott Docker image-ek, Docker Secret és PostgreSQL Volume újra felhasználhatók.

A Docker Swarm újra létrehozza a stack szolgáltatásait.

A PostgreSQL a meglévő adatkötetet használja, így a mentett feladatok az alkalmazás újraindítása után is elérhetők maradnak.

### 12.4. Adatmegőrzés

A `todoapp_postgres_data` Docker Volume az alkalmazás tartós adatait tárolja.

Az adatmegőrzés szempontjából a Volume és a WSL virtuális lemezének megőrzése meghatározó.

A `docker volume rm`, a `docker system prune --volumes` és a WSL-disztribúció eltávolítása adatvesztést okozhat.

A Docker Volume nem helyettesíti a külön biztonsági mentést.

---

## 13. Verziókövetés GitHubon

A Flowdesk forráskódja Git verziókövetéssel készült, és nyilvános GitHub-repozitóriumban található.

**Repository:**

https://github.com/Fmate2003/flowdesk

A repozitórium tartalmazza a frontend és backend forráskódját, a Dockerfile-okat, a Docker Swarm-konfigurációt, a teszteket és a dokumentációt.

### 13.1. Git-repozitórium

A helyi Git-repozitórium inicializálása:

```bash
git init
git branch -M main
```

A GitHub-repozitórium összekapcsolása:

```bash
git remote add origin https://github.com/Fmate2003/flowdesk.git
```

### 13.2. Verziómentés

```bash
git add .
git commit -m "Initial release of Flowdesk 2.0"
```

A commit egy adott állapotban rögzíti a projekt forrásfájljait.

### 13.3. Feltöltés GitHubra

```bash
git push -u origin main
```

A parancs a helyi `main` ág commitjait feltölti a távoli GitHub-repozitóriumba.

A további módosítások ugyanebben a verziókövetési rendszerben kezelhetők.

---

## 14. Hibaelhárítás

| Jelenség | Lehetséges ok | Ellenőrzés |
|---|---|---|
| Docker Engine nem érhető el | Docker nem fut | `systemctl is-active docker` |
| Swarm inaktív | Nincs aktív Swarm | `sudo docker info` |
| Szolgáltatás nem indul | Konténerhiba vagy hiányzó image | `sudo docker service ps` |
| Backend nem érhető el | Hálózati vagy alkalmazáshiba | `sudo docker service logs` |
| Adatbázis-kapcsolati hiba | PostgreSQL vagy Secret probléma | `curl /api/health`, szolgáltatásnaplók |
| Frontend nem tölt be | Port vagy Nginx probléma | `curl http://127.0.0.1:8080` |
| Cloudflare-link nem működik | A tunnel leállt | Cloudflared naplóinak ellenőrzése |
| GitHub-feltöltés sikertelen | Hitelesítési vagy kapcsolati probléma | `git remote -v`, `git status` |

A Docker Swarm hibakeresésénél a szolgáltatások példányszáma, a konténerek állapota, a szolgáltatásnaplók és az API-válaszok együttesen adnak képet a rendszer működéséről.

---

## 15. Biztonság és továbbfejlesztés

### 15.1. Megvalósított biztonsági megoldások

- Az adatbázis nincs közvetlenül publikálva az internetre.
- A PostgreSQL és a backend elkülönített belső hálózaton kommunikál.
- Az adatbázis-jelszó Docker Secret segítségével kerül a konténerekhez.
- A `.gitignore` kizárja a helyi konfigurációs és bizalmas fájlok meghatározott típusait.
- A backend ellenőrzi a beérkező adatokat.
- A külső elérés HTTPS-kapcsolaton keresztül történik.

### 15.2. Jelenlegi korlátok

A Flowdesk jelenlegi verziója egy felhasználói fiókok nélküli, közös feladatlistát kezelő alkalmazás.

A rendszer nem tartalmaz felhasználói bejelentkezést vagy szerepköralapú jogosultságkezelést.

A nyilvános alkalmazáscímet ismerő felhasználók ugyanazokat a feladatokat érhetik el.

A Docker Swarm egyetlen csomóponton fut. A backend replikációja konténerkiesés esetén biztosít automatikus pótlást, de a teljes számítógép kiesése ellen nem nyújt védelmet.

A PostgreSQL helyi Docker Volume-ot használ, amely tartós adattárolást biztosít, de önmagában nem jelent többgépes replikációt vagy külön adatbázis-mentést.

### 15.3. Lehetséges továbbfejlesztések

- Felhasználói regisztráció és bejelentkezés.
- Felhasználónként elkülönített feladatok.
- Szerepkörök és jogosultságkezelés.
- Több munkaterület.
- Feladatok felelősökhöz rendelése.
- Címkék és értesítések.
- Automatikus adatbázis-mentések.
- Többcsomópontos Docker Swarm-környezet.
- Felhőalapú, folyamatosan működő alkalmazásszerver.
- Állandó domain és HTTPS-konfiguráció.
- Automatizált build- és tesztfolyamat.

---

## 16. Tesztelési dokumentáció

A Flowdesk működését és Docker Swarm-konfigurációját külön dokumentáció foglalja össze.

A tesztelés során ellenőriztük a három együttműködő szolgáltatást, a saját Docker image-eket, az overlay hálózatokat, a PostgreSQL tartós adattárolását, a backend skálázását, az automatikus helyreállítást, az API működését és a nyilvános HTTPS-elérést.

### Kapcsolódó dokumentumok

- **[Rendszerellenőrzési áttekintés (PDF)](docs/Flowdesk_Vedesi_Attekintes.pdf)** – A végrehajtott Docker-parancsok, működési magyarázatok és képernyőképek összefoglalása.
- **[Tesztlépések és parancsok](docs/VEDES_TESZTEK.md)** – A szolgáltatások, hálózatok, adattárolás, skálázás és helyreállítás részletes ellenőrzése.

A dokumentációban szereplő tesztek Ubuntu WSL környezetben, egy Docker Swarm-csomóponton készültek.

---

## Összegzés

A Flowdesk 2.0 egy háromszolgáltatásos, Docker Swarm alatt működő feladatmenedzsment alkalmazás.

A rendszer saját Docker image-eket, elkülönített overlay hálózatokat, PostgreSQL-alapú tartós adattárolást és több példányban futó backend szolgáltatást használ.

A megvalósított infrastruktúra támogatja a szolgáltatások skálázását és a kiesett konténerpéldányok automatikus pótlását.

A forráskód, a telepítési konfiguráció és a működési tesztek dokumentációja a GitHub-repozitóriumban érhető el.
