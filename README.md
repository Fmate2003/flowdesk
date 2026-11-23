# Flowdesk 3.0

Feladatkezelő webalkalmazás Docker Swarm környezetben. A felületet Nginx szolgálja ki, a feladatok kezelését Python Flask API végzi, az adatokat PostgreSQL tárolja. A rendszer egy Ubuntu WSL 2 alapú, egynode-os Docker Swarmon fut.

A Flowdesk felületén feladatokat lehet felvenni, szerkeszteni, lezárni és törölni. A teendőkhöz leírás, kategória, prioritás és határidő is tartozhat. A keresés, a szűrés és az összesítő számok az aktuális feladatok áttekintését segítik. A 3.0-s verzióban a korábbi dashboard helyett a feladatlista került előtérbe; az adatok és a backend API változatlanok maradtak.

**Forráskód:** https://github.com/Fmate2003/flowdesk  
**Helyi elérés:** http://127.0.0.1:8080  
**Futtatási környezet:** Windows 10, WSL 2, Ubuntu, Docker Swarm

## Tartalom

1. [Az alkalmazás működése](#1-az-alkalmazás-működése)
2. [Architektúra](#2-architektúra)
3. [Technológiák és projektfájlok](#3-technológiák-és-projektfájlok)
4. [Fejlesztői környezet](#4-fejlesztői-környezet)
5. [Docker image-ek és Swarm-telepítés](#5-docker-image-ek-és-swarm-telepítés)
6. [API és adatkezelés](#6-api-és-adatkezelés)
7. [Hálózatok, adattárolás és Secret](#7-hálózatok-adattárolás-és-secret)
8. [Skálázás és helyreállítás](#8-skálázás-és-helyreállítás)
9. [Cloudflare Tunnel](#9-cloudflare-tunnel)
10. [Tesztek](#10-tesztek)
11. [Leállítás és újraindítás](#11-leállítás-és-újraindítás)
12. [GitHub és verziókövetés](#12-github-és-verziókövetés)
13. [Hibakeresés](#13-hibakeresés)
14. [Korlátok és továbbfejlesztések](#14-korlátok-és-továbbfejlesztések)
15. [Működési dokumentáció](#15-működési-dokumentáció)

## 1. Az alkalmazás működése

A Flowdesk a napi teendők kezelésére készült. Új feladat létrehozásakor megadható a cím, a leírás, a kategória, a prioritás és a határidő. A feladatok később módosíthatók, elkészültnek jelölhetők vagy törölhetők.

A munkalista kereshető, állapot szerint szűrhető és rendezhető. A fejlécben az összes, a folyamatban lévő, az elkészült és a lejárt feladatok száma jelenik meg. A felület asztali böngészőben és mobilon is használható.

A feladatokat a PostgreSQL tárolja. Oldalfrissítéskor a frontend újra lekéri az adatokat a backendtől, ezért a lista nem a böngésző ideiglenes állapotától függ.

## 2. Architektúra

```text
Böngésző / mobiltelefon
        |
        | HTTP :8080 / HTTPS Cloudflare Tunnel esetén
        v
Nginx frontend                 1 példány
flowdesk-frontend:3.0
        |
        | /api/*, todoapp_webnet
        v
Flask API + Gunicorn           3 példány
flowdesk-backend:2.0
        |
        | PostgreSQL :5432, todoapp_dbnet
        v
PostgreSQL 16                  1 példány
        |
        v
todoapp_postgres_data Docker Volume
```

| Szolgáltatás | Feladat | Image | Alapértelmezett példányszám |
|---|---|---|---:|
| `todoapp_frontend` | Webes felület, API-kérések továbbítása | `flowdesk-frontend:3.0` | 1 |
| `todoapp_backend` | Feladatok kezelése, adatbázis-műveletek | `flowdesk-backend:2.0` | 3 |
| `todoapp_database` | Feladatok tárolása | `postgres:16-alpine` | 1 |

A böngésző az Nginx frontendhez csatlakozik. Az Nginx az `/api/` útvonalon érkező hívásokat a Flask szolgáltatásnak továbbítja. A backend kapcsolódik a PostgreSQL-hez. Az adatbázisnak nincs nyilvánosan közzétett 5432-es portja.

A három backendpéldányt a Docker Swarm kezeli. A frontend ugyanazon a szolgáltatásnéven éri el az API-t akkor is, ha a backend példányszáma változik. A replikák ugyanazon a WSL-gépen futnak; ez konténerkiesés esetén segít, a teljes számítógép leállását nem kezeli.

## 3. Technológiák és projektfájlok

A fejlesztői környezet Windows 10 alatt, Ubuntu WSL 2 rendszerben működik. A forráskód szerkesztéséhez Visual Studio Code-ot használtunk a WSL-bővítménnyel. A Docker Engine futtatja a konténereket, a Docker Swarm pedig a szolgáltatások kívánt állapotát kezeli.

A webes felület HTML, CSS és JavaScript alapú. A backend Flask és Gunicorn használatával fut; az adatbázis PostgreSQL 16. A Cloudflare Tunnel opcionális, ideiglenes HTTPS-elérést ad a helyi szolgáltatáshoz.

```text
flowdesk-swarm/
├── .env.example
├── .gitignore
├── README.md
├── stack.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app.py
│   ├── db.py
│   └── init_db.py
├── frontend/
│   ├── Dockerfile
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
├── dev-requirements.txt
├── DESIGN.md
└── TELEPITES_UI_3.md
```

A `frontend/index.html` a felület szerkezete, a `styles.css` határozza meg a megjelenést, az `app.js` pedig az interakciókat és az API-hívásokat kezeli. Az Nginx proxybeállításai a `frontend/nginx.conf` fájlban találhatók.

A `backend/app.py` tartalmazza az API-végpontokat, a `db.py` az adatbázis-kapcsolatot, az `init_db.py` pedig a tábla létrehozását és szükség szerinti bővítését kezeli. Az adatbázisséma kiegészítésekor a korábbi feladatok megmaradtak.

A `stack.yml` írja le a Swarm-szolgáltatásokat, a példányszámokat, a hálózatokat, a Volume-ot és a Secret használatát.

## 4. Fejlesztői környezet

A WSL állapota Windows PowerShellből ellenőrizhető:

```powershell
wsl --list --verbose
wsl --version
```

A projekt Ubuntu terminálból megnyitható a VS Code-ban:

```bash
cd ~/flowdesk-v2/flowdesk-swarm
pwd
code .
```

A Docker telepítése Ubuntu alatt:

```bash
sudo apt-get update
sudo apt-get install -y docker.io
```

A Docker indítása és ellenőrzése:

```bash
sudo systemctl start docker
systemctl is-active docker
sudo docker version
sudo docker run --rm hello-world
```

A `hello-world` egy egyszerű próbakonténer, amellyel a Docker telepítését ellenőriztük. Nem része a Flowdesk stacknek.

## 5. Docker image-ek és Swarm-telepítés

### Forráskód

Új gépen a projekt a GitHubról tölthető le:

```bash
git clone https://github.com/Fmate2003/flowdesk.git
cd flowdesk
```

A már használt fejlesztői gépen a projekt könyvtára:

```bash
cd ~/flowdesk-v2/flowdesk-swarm
```

### Saját image-ek

A frontend és a backend külön Dockerfile-ból épül. A backend `python:3.12-slim`, a frontend `nginx:stable-alpine` alapimage-et használ.

```bash
sudo docker build -t flowdesk-backend:2.0 ./backend
sudo docker build -t flowdesk-frontend:3.0 ./frontend
sudo docker images
```

A `docker images` kimenetében a két Flowdesk image és a PostgreSQL image is ellenőrizhető.

### Swarm inicializálása

```bash
sudo docker info --format '{{.Swarm.LocalNodeState}}'
```

Új telepítésnél, inaktív Swarm esetén:

```bash
sudo docker swarm init
```

A csomópont állapota:

```bash
sudo docker node ls
```

A helyi rendszerben egy manager csomópont fut, `Ready` és `Leader` állapottal. Már aktív Swarm esetén nincs szükség új inicializálásra.

### Adatbázis-jelszó

A backend és a PostgreSQL ugyanazt a `todo_db_password` Docker Secretet használja. A Secretet az első telepítés előtt kell létrehozni:

```bash
openssl rand -base64 32 | sudo docker secret create todo_db_password -
sudo docker secret ls
```

A `stack.yml` a Secretet külső erőforrásként hivatkozza. A jelszó értéke nem szerepel a repozitóriumban.

Meglévő PostgreSQL-adatkötet esetén a Secretnek a már inicializált adatbázis hitelesítési adataival kell egyeznie. Új jelszó létrehozása önmagában nem változtatja meg a PostgreSQL-ben korábban beállított felhasználói jelszót.

### Stack telepítése

```bash
sudo docker stack deploy --resolve-image never -c stack.yml todoapp
sudo docker service ls
```

A `todoapp` a stack neve, így a szolgáltatások `todoapp_frontend`, `todoapp_backend` és `todoapp_database` néven jelennek meg. A `--resolve-image never` a helyben épített image-eket használó, egycsomópontos környezethez illeszkedik. Több Swarm-csomópontnál az image-ek közös registryből történő terjesztése is szükséges lehet.

A rendszer normál állapota:

| Szolgáltatás | Replikák |
|---|---:|
| `todoapp_frontend` | `1/1` |
| `todoapp_backend` | `3/3` |
| `todoapp_database` | `1/1` |

Az alkalmazás helyi címe: http://127.0.0.1:8080

## 6. API és adatkezelés

A frontend HTTP-kérésekkel éri el a backend API-t. A támogatott végpontok:

| Metódus | Útvonal | Művelet |
|---|---|---|
| `GET` | `/api/health` | Alkalmazás- és adatbázis-kapcsolat |
| `GET` | `/api/tasks` | Feladatok lekérdezése |
| `POST` | `/api/tasks` | Új feladat |
| `PATCH` | `/api/tasks/{id}` | Feladat módosítása |
| `DELETE` | `/api/tasks/{id}` | Feladat törlése |

Az API és az adatbázis kapcsolatának ellenőrzése:

```bash
curl -i --max-time 10 http://127.0.0.1:8080/api/health
```

Sikeres válasz esetén a HTTP-státusz `200`, a JSON-törzs pedig:

```json
{"database":"ok","status":"ok"}
```

A mentett feladatok lekérdezése:

```bash
curl -sS --max-time 10 http://127.0.0.1:8080/api/tasks
```

Új feladat API-n keresztül:

```bash
curl -sS -X POST http://127.0.0.1:8080/api/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"API tesztfeladat","description":"Feladat létrehozása","category":"study","priority":"high"}'
```

Feladat módosítása, a tényleges azonosítóval:

```bash
curl -sS -X PATCH http://127.0.0.1:8080/api/tasks/42 \
  -H 'Content-Type: application/json' \
  -d '{"completed":true}'
```

Feladat törlése:

```bash
curl -sS -X DELETE http://127.0.0.1:8080/api/tasks/42
```

A `42` itt példaazonosító. A módosítás és a törlés mindig a megadott azonosítójú rekordra vonatkozik.

## 7. Hálózatok, adattárolás és Secret

### Overlay hálózatok

```bash
sudo docker network ls
sudo docker network inspect todoapp_webnet --format '{{.Driver}}'
sudo docker network inspect todoapp_dbnet --format '{{.Driver}}'
```

A két alkalmazáshálózat `overlay` típusú. A frontend és a backend a `webnet` hálózaton kommunikál, a backend és az adatbázis a `dbnet` hálózaton. Az adatbázis nem csatlakozik a frontend hálózatához.

### PostgreSQL Volume

```bash
sudo docker volume ls
sudo docker volume inspect todoapp_postgres_data
sudo docker service inspect todoapp_database --format '{{json .Spec.TaskTemplate.ContainerSpec.Mounts}}'
```

A `todoapp_postgres_data` nevű Volume a PostgreSQL `/var/lib/postgresql/data` könyvtárához kapcsolódik. A tároló a konténer cseréje után is megmarad, ezért a korábban mentett feladatok visszaolvashatók.

### Secret

```bash
sudo docker secret ls
```

A `todo_db_password` Secret a jelszót fájlon keresztül adja át az adatbázisnak és a backendnek. A lista a Secret nevét mutatja, az értékét nem.

## 8. Skálázás és helyreállítás

### Backend skálázása

A backend alaphelyzetben három példányban fut. A Swarm képes a példányszám növelésére és csökkentésére:

```bash
sudo docker service scale todoapp_backend=5
sudo docker service ls
sudo docker service ps todoapp_backend
```

Az öt példányra történő skálázáskor a meglévő három backendkonténer mellé két új indul. A szolgáltatás állapota ekkor `5/5`.

Az eredeti konfiguráció visszaállítása:

```bash
sudo docker service scale todoapp_backend=3
sudo docker service ls
```

A backend ismét `3/3` állapotú. A `stack.yml` alapértelmezett példányszáma továbbra is három.

### Automatikus konténer-helyreállítás

A Swarm összeveti a ténylegesen futó példányok számát a szolgáltatás konfigurációjával. Ha egy backendkonténer leáll, új feladatot indít a helyén.

A backendkonténerek lekérdezése:

```bash
sudo docker ps --filter 'label=com.docker.swarm.service.name=todoapp_backend'
```

A teszt során az egyik backendkonténert szándékosan megszakítottuk:

```bash
sudo docker kill KONTAINER_AZONOSITO
```

Az aktuális konténerazonosító a `docker ps` kimenetéből olvasható ki. A helyreállítás után a korábbi Swarm-feladat `Failed` állapotban, az új pedig `Running` állapotban jelent meg:

```bash
sudo docker service ps todoapp_backend
sudo docker service ls
```

A backend automatikusan visszaállt `3/3` példányszámra. Ez konténerszintű helyreállítás egyetlen gépen, nem teljes gépkiesés elleni védelem.

### Adatmegőrzés

Az adatbázis-konténer cseréjét is ellenőriztük. A Swarm új PostgreSQL-feladatot indított, a mentett feladatok pedig megmaradtak a `todoapp_postgres_data` Volume-ban. Az adatokat a számítógép és a WSL újraindítása után is sikerült visszaolvasni.

A Docker Volume tartós adatkötet, de nem helyettesíti a külön adatbázis-mentést.

## 9. Cloudflare Tunnel

A helyi `127.0.0.1:8080` címet a számítógépen kívüli eszközök alaphelyzetben nem érik el. A Cloudflare Tunnel egy kimenő kapcsolatot létesít, és ideiglenes HTTPS-címet ad a Flowdeskhez.

A projektben használt `cloudflared` telepítése Ubuntu alatt:

```bash
curl -fL --output /tmp/cloudflared.deb \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo apt install -y /tmp/cloudflared.deb
cloudflared --version
```

A tunnel indítása futó Flowdesk mellett:

```bash
cloudflared tunnel --url http://127.0.0.1:8080
```

A parancs egy `https://...trycloudflare.com` címre mutató elérést hoz létre. Külső eszközről is sikerült feladatot hozzáadni, majd oldalfrissítés után visszaolvasni.

Ez a cím ideiglenes. A tunnel leállításakor megszűnik az elérés, újraindításkor pedig másik cím keletkezhet. A Quick Tunnel nem folyamatos rendelkezésre állást biztosító tárhelyszolgáltatás.

## 10. Tesztek

A projekt egységteszteket, Swarm-konfigurációs ellenőrzéseket és API-gyorstesztet tartalmaz.

A Python-tesztkörnyezet létrehozása:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r dev-requirements.txt
```

A tesztek futtatása:

```bash
python3 -m pytest -q
```

A `tests/test_structure.py` a stack szolgáltatásait, hálózatait és főbb konfigurációs beállításait vizsgálja. A `tests/test_api.py` a Flask API működését ellenőrzi szimulált adatbázis-hozzáféréssel.

Futó Docker Swarm-alkalmazáson a következő gyorsteszt használható:

```bash
python3 scripts/smoke_test.py
```

A script ellenőrzi az egészség-végpontot, a feladat létrehozását, lekérdezését, módosítását és törlését. A saját maga által létrehozott próbarekordot törli.

A tényleges Swarm- és adatmegőrzési tesztek képernyőképei a [működési dokumentációban](#15-működési-dokumentáció) találhatók. A helyi Python-tesztek futtatási eredménye ettől külön ellenőrizhető.

## 11. Leállítás és újraindítás

A Cloudflare Tunnel futó terminálban `Ctrl+C` billentyűkombinációval állítható le.

A Swarm-stack leállítása:

```bash
sudo docker stack rm todoapp
sudo docker service ls
```

A Docker Engine és a socket leállítása:

```bash
sudo systemctl stop docker docker.socket
systemctl is-active docker
```

A WSL Windows PowerShellből állítható le:

```powershell
wsl --shutdown
```

A stack eltávolítása a szolgáltatásokat és a hálózatokat megszünteti, de a `todoapp_postgres_data` Volume-ot nem törli automatikusan. A forráskód és a helyben elkészített image-ek is megmaradnak.

Újraindítás a meglévő fejlesztői környezetben:

```bash
cd ~/flowdesk-v2/flowdesk-swarm
sudo systemctl start docker
sudo docker info --format '{{.Swarm.LocalNodeState}}'
sudo docker stack deploy --resolve-image never -c stack.yml todoapp
sudo docker service ls
```

A PostgreSQL a meglévő Volume-hoz csatlakozik, így a korábbi feladatok újra elérhetők.

A Volume törlése (`docker volume rm`, illetve megfelelő feltételek mellett a `docker system prune --volumes`) és az Ubuntu WSL-disztribúció eltávolítása adatvesztéssel járhat. A tartós adatokról ettől függetlenül érdemes biztonsági mentést készíteni.

## 12. GitHub és verziókövetés

A projekt nyilvános GitHub-repozitóriumban található:

https://github.com/Fmate2003/flowdesk

A forráskód, a Docker-konfiguráció, a tesztek és a dokumentáció ugyanabban a Git-repozitóriumban szerepel. A változtatásokat commitok rögzítik, így a korábbi verziók is visszakereshetők.

A repozitórium helyi inicializálásakor használt parancsok:

```bash
git init
git branch -M main
git remote add origin https://github.com/Fmate2003/flowdesk.git
git add .
git commit -m "Initial release of Flowdesk 2.0"
git push -u origin main
```

A frontend 3.0-s változata a korábbi verzió után került a `main` ágra. Későbbi módosítások feltöltése:

```bash
git add README.md
git commit -m "Update project documentation for Flowdesk 3.0"
git push origin main
```

A `.gitignore` a helyi környezetből származó és bizalmas fájlok egy részét kizárja a verziókövetésből. Az adatbázis-jelszó tényleges értéke nem kerül a repozitóriumba.

## 13. Hibakeresés

| Jelenség | Ellenőrzés vagy teendő |
|---|---|
| Docker Engine nem elérhető | `systemctl is-active docker` és `sudo systemctl start docker` |
| Swarm nem aktív | `sudo docker info --format '{{.Swarm.LocalNodeState}}'` |
| Egy szolgáltatás nem indul | `sudo docker service ps todoapp_frontend`, illetve a megfelelő szolgáltatás neve |
| Backend- vagy adatbázishiba | `sudo docker service logs --tail 50 todoapp_backend` |
| A weboldal nem tölt be | `curl --noproxy '*' -v --connect-timeout 3 --max-time 8 http://127.0.0.1:8080/` |
| API nem éri el az adatbázist | `curl -sS http://127.0.0.1:8080/api/health` |
| Mentett feladatok hiányoznak | `sudo docker volume inspect todoapp_postgres_data` |
| Régi TryCloudflare-link nem működik | Új tunnel indítása és az aktuális cím ellenőrzése |
| GitHub elutasítja a push műveletet | Távoli változások beolvasása, például `git pull --rebase origin main` |

A Docker Swarm által jelzett replikaszám önmagában nem ellenőrzi az alkalmazás minden funkcióját. A szolgáltatásállapot mellett a HTTP-válaszokat és a tárolt feladatok elérését is vizsgáltuk.

## 14. Korlátok és továbbfejlesztések

A Flowdesk jelenlegi változatában nincs bejelentkezés vagy felhasználónkénti jogosultságkezelés. A nyilvános címet ismerők ugyanazt a közös feladatlistát érhetik el és módosíthatják. A nyilvános próbakörnyezet ezért tesztadatokhoz használható.

A Docker Swarm egyetlen csomóponton fut, így a konténerek automatikus pótlása nem jelent többgépes hibatűrést. A PostgreSQL helyi Volume-ja megtartja az adatokat konténercsere esetén, de nem automatikus biztonsági mentés, és nem replikál több gép között. A Cloudflare Quick Tunnel szintén ideiglenes elérés.

A továbbfejlesztés lehetséges irányai: bejelentkezés, jogosultságok, külön munkaterületek, feladatfelelősök, értesítések, automatizált adatbázis-mentések, többcsomópontos Swarm, állandó felhős tárhely és automatizált build- és tesztfolyamat.

## 15. Működési dokumentáció

Az alkalmazás felépítéséről, a Docker Swarm beállításairól és a végrehajtott ellenőrzésekről külön dokumentumok készültek. A képernyőképek a szolgáltatások futását, a saját Docker image-eket, a hálózatokat, a PostgreSQL Volume használatát, a skálázást, a konténer-helyreállítást és a nyilvános elérést mutatják.

- [Működési áttekintés – PDF](docs/Flowdesk_Vedesi_Attekintes.pdf)
- [Ellenőrzési parancsok és képernyőképek](docs/VEDES_TESZTEK.md)

A PDF a korábbi tesztekből összeállított dokumentum, ezért egyes képeken még a Flowdesk 2.0 előző megjelenése látható. A 3.0-s frontend ugyanazt a backend API-t és PostgreSQL-adatbázist használja.
