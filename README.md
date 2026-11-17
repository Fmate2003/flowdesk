# Flowdesk 2.0 – Feladatmenedzsment alkalmazás Docker Swarm környezetben

> **Projekt:** három együttműködő szolgáltatásból álló, reszponzív webalkalmazás, saját Docker image-ekkel, Docker Swarm orchesztrációval, overlay hálózatokkal, PostgreSQL-adatmegőrzéssel, skálázással és nyilvános HTTPS-elérési lehetőséggel.
>
> **Forráskód:** https://github.com/Fmate2003/flowdesk  
> **Állapot:** működő helyi demó; a nyilvános TryCloudflare-link ideiglenes, csak futó tunnel mellett elérhető.

## Tartalomjegyzék

1. [A projekt célja és a megvalósított funkciók](#1-a-projekt-célja-és-a-megvalósított-funkciók)
2. [Architektúra és szolgáltatások](#2-architektúra-és-szolgáltatások)
3. [Felhasznált technológiák és alapfogalmak](#3-felhasznált-technológiák-és-alapfogalmak)
4. [Fejlesztői környezet előkészítése Windows és WSL alatt](#4-fejlesztői-környezet-előkészítése-windows-és-wsl-alatt)
5. [A projekt felépítése és fejlesztési folyamata](#5-a-projekt-felépítése-és-fejlesztési-folyamata)
6. [Telepítés nulláról – pontos parancsok](#6-telepítés-nulláról--pontos-parancsok)
7. [Működési ellenőrzés és API-tesztek](#7-működési-ellenőrzés-és-api-tesztek)
8. [Feladatkövetelmények és igazoló parancsok](#8-feladatkövetelmények-és-igazoló-parancsok)
9. [Részletes demonstráció: skálázás, önjavítás, adatmegőrzés](#9-részletes-demonstráció-skálázás-önjavítás-adatmegőrzés)
10. [Nyilvános HTTPS-elérés Cloudflare Tunnel segítségével](#10-nyilvános-https-elérés-cloudflare-tunnel-segítségével)
11. [Automatizált tesztek](#11-automatizált-tesztek)
12. [Leállítás, újraindítás, adatok megőrzése](#12-leállítás-újraindítás-adatok-megőrzése)
13. [Git és GitHub – forráskód publikálása](#13-git-és-github--forráskód-publikálása)
14. [Hibaelhárítás](#14-hibaelhárítás)
15. [Biztonság, korlátok és továbbfejlesztési lehetőségek](#15-biztonság-korlátok-és-továbbfejlesztési-lehetőségek)
16. [Bemutató forgatókönyv és ellenőrzőlista](#16-bemutató-forgatókönyv-és-ellenőrzőlista)

---

## 1. A projekt célja és a megvalósított funkciók

A **Flowdesk** egy böngészőből használható feladatmenedzsment alkalmazás. A felhasználó feladatokat hozhat létre, módosíthat, befejezettnek jelölhet és törölhet. A feladatok PostgreSQL-adatbázisban tárolódnak, nem a böngésző memóriájában. A projekt célja emellett egy működő, több szolgáltatásból álló konténeres rendszer összeállítása és üzemeltetési viselkedésének bemutatása.

### Felhasználói funkciók

- Feladat **létrehozása**, **listázása**, **szerkesztése**, **elkészültnek jelölése** és **törlése**.
- Feladat neve, részletes leírása, kategóriája (`work`, `personal`, `study`, `other`), prioritása (`low`, `medium`, `high`) és opcionális határideje.
- Áttekintő kártyák: összes, folyamatban lévő, elkészült és lejárt feladatok.
- Szöveges keresés, állapot szerinti szűrés, rendezés, mobilon is használható megjelenés.
- Mentett feladatok visszaolvasása oldalfrissítés vagy konténercsere után.

### Infrastruktúra-funkciók

- Saját Dockerfile-ból felépített frontend és backend image.
- Három Swarm-szolgáltatás: `frontend`, `backend`, `database`.
- Három backendpéldány alapértelmezetten; dinamikus skálázás.
- Két elkülönített overlay hálózat.
- Docker Secret alapú adatbázis-jelszókezelés.
- Tartós PostgreSQL Docker Volume.
- Egészségellenőrzések és a kiesett konténerfeladatok automatikus pótlása.
- Ideiglenes, külső hálózatról elérhető HTTPS-demó Cloudflare Tunnel használatával.

## 2. Architektúra és szolgáltatások

```text
Böngésző / telefon
        |
        | HTTP :8080 vagy HTTPS (Cloudflare Tunnel)
        v
+---------------------------+
| Nginx frontend            |  1 replika
| flowdesk-frontend:2.0     |  statikus HTML, CSS, JavaScript
+---------------------------+
        | /api/* proxy
        | overlay: webnet
        v
+---------------------------+
| Python Flask REST API     |  alapból 3 replika
| flowdesk-backend:2.0      |  Gunicorn alkalmazásszerver
+---------------------------+
        | PostgreSQL :5432
        | overlay: dbnet
        v
+---------------------------+
| PostgreSQL 16-alpine      |  1 replika
| database                  |
+---------------------------+
        |
        v
Docker Volume: todoapp_postgres_data
```

| Szolgáltatás | Szerepe | Image | Replikák | Hálózat |
|---|---|---|---:|---|
| `todoapp_frontend` | Felhasználói felület és API-továbbítás | `flowdesk-frontend:2.0` | 1 | `todoapp_webnet` |
| `todoapp_backend` | Üzleti logika és adatbázis-hozzáférés | `flowdesk-backend:2.0` | 3 | `todoapp_webnet`, `todoapp_dbnet` |
| `todoapp_database` | Feladatok tartós tárolása | `postgres:16-alpine` | 1 | `todoapp_dbnet` |

**Miért két hálózat?** A böngésző a frontendhez csatlakozik, az Nginx a backendhez továbbítja az `/api/` kéréseket. A PostgreSQL csak a belső `dbnet` hálózaton érhető el, nincs közvetlenül publikált `5432`-es portja. Ez elkülöníti az adatbázist a webes belépési ponttól.

**Miért több backendpéldány?** A Swarm szolgáltatásfelfedezése és belső forgalomelosztása lehetővé teszi, hogy a frontend egyetlen `backend` szolgáltatásnéven keresztül érje el a több példányban futó API-t.

**Korlát:** a bemutatott rendszer **egyetlen WSL-alapú Swarm node-on** fut. A replikáció konténerkiesés ellen segít, de nem véd a teljes fizikai gép vagy WSL-környezet kiesése ellen. A helyi PostgreSQL Volume sem többgépes, automatikusan replikált adattár.

## 3. Felhasznált technológiák és alapfogalmak

| Technológia | Feladat |
|---|---|
| **Windows + WSL 2 + Ubuntu** | Linux fejlesztői és futtatási környezet Windows alatt |
| **Visual Studio Code + WSL bővítmény** | Forráskódszerkesztés és Ubuntu terminál |
| **Docker Engine** | Konténerek és image-ek kezelése |
| **Dockerfile** | Saját alkalmazás-image felépítésének receptje |
| **Docker Swarm** | Szolgáltatások, replikák, hálózatok és helyreállítás kezelése |
| **Docker Stack / `stack.yml`** | A teljes háromszolgáltatásos telepítés deklaratív leírása |
| **Nginx** | Statikus weboldal és fordított proxy (*reverse proxy*) |
| **Flask + Gunicorn** | Python-alapú REST API és alkalmazásszerver |
| **PostgreSQL** | Relációs adatbázis |
| **Docker Volume** | Konténercserét túlélő adattárolás |
| **Docker Secret** | Adatbázis-jelszó átadása fájlként a konténereknek |
| **Cloudflare Tunnel** | Ideiglenes HTTPS-elérés internet felől |
| **Git / GitHub** | Verziókövetés és forráskód-megosztás |

**Image:** futtatható konténer-sablon. **Konténer:** egy image-ből indított izolált folyamat. **Szolgáltatás (service):** a Swarm által kezelt, megadott számú konténerfeladat. **Replika:** ugyanabból a szolgáltatásból futó példány. **Overlay hálózat:** Swarm-szolgáltatásokat összekötő virtuális hálózat. **Volume:** a konténerek életciklusától független adatkötet. **REST API:** HTTP-végpontokat használó alkalmazásprogramozási interfész.

## 4. Fejlesztői környezet előkészítése Windows és WSL alatt

A projekt Windows 10 alatt, Ubuntu WSL 2 környezetben, a VS Code WSL-integrációjával készült.

### 4.1. WSL / Ubuntu ellenőrzése (Windows PowerShell)

```powershell
wsl --list --verbose
wsl --version
```

Elvárt: az `Ubuntu` disztribúció **VERSION 2** módban szerepeljen. Ha a WSL vagy az Ubuntu nincs telepítve, azt Windowsban külön telepíteni kell. A telepítés módja a Windows-verziótól függ; egy újabb rendszeren például `wsl --install -d Ubuntu` használható. **Meglévő, működő Ubuntut ne állítsunk alaphelyzetbe és ne töröljünk a projekt miatt.**

### 4.2. Terminál megnyitása VS Code-ban

Az Ubuntu terminálból a projektmappát így nyitottuk meg:

```bash
cd ~/flowdesk-v2/flowdesk-swarm
pwd
code .
```

A `pwd` a jelenlegi munkamappát írja ki. A `code .` megnyitja a mappát VS Code-ban. A VS Code terminálja legyen **WSL: Ubuntu** környezetben, ne Windows PowerShellben, mert az itt dokumentált `sudo` és `systemctl` parancsok Linux-parancsok.

### 4.3. Docker Engine telepítése és indítása

A projektben az Ubuntu `docker.io` csomagját használtuk. Új Ubuntu-környezetben, ha még nincs Docker:

```bash
sudo apt-get update
sudo apt-get install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker
```

Már telepített rendszeren csak indítás és ellenőrzés szükséges:

```bash
sudo systemctl start docker
systemctl is-active docker
sudo docker version
sudo docker run --rm hello-world
```

**Elvárt eredmény:** a szolgáltatás állapota `active`, a Docker kliens/szerver verziója látható, a `hello-world` teszt sikeresen lefut.

> A `hello-world` csak az első környezeti ellenőrzéshez kell, nem része a Flowdesk háromszolgáltatásos stackjének.

## 5. A projekt felépítése és fejlesztési folyamata

### 5.1. Könyvtárszerkezet

```text
flowdesk-swarm/
├── .env.example                  # helyi fejlesztési változók MINTÁJA, nem valódi titok
├── .gitignore                    # nem publikálandó fájlok kizárása
├── README.md                     # jelen dokumentáció
├── stack.yml                     # Docker Swarm stack
├── backend/
│   ├── Dockerfile                # saját Python image
│   ├── .dockerignore
│   ├── requirements.txt
│   ├── app.py                    # Flask API, végpontok és validálás
│   ├── db.py                     # PostgreSQL-kapcsolat, Docker Secret olvasása
│   └── init_db.py                # adatbázisséma létrehozása/bővítése
├── frontend/
│   ├── Dockerfile                # saját Nginx image
│   ├── .dockerignore
│   ├── nginx.conf                # /api/ proxyszabály
│   ├── index.html               # oldalstruktúra
│   ├── styles.css               # reszponzív megjelenés
│   └── app.js                   # böngészőbeli működés és API-hívások
├── docs/
│   └── architecture.md          # rövid architektúraleírás
├── scripts/
│   └── smoke_test.py            # működő alkalmazáson végzett API-gyorsteszt
├── tests/
│   ├── test_api.py               # API-egységtesztek, adatbázis-szimulációval
│   └── test_structure.py         # Swarm-konfigurációs követelmények ellenőrzése
└── dev-requirements.txt          # fejlesztői Python-csomagok
```

### 5.2. Fejlesztési sorrend

1. **Kezdeti megoldás:** egyszerű feladatlista három szolgáltatással (Nginx, Flask, PostgreSQL).
2. **Konténerizálás:** külön backend és frontend `Dockerfile`, saját image-ek készítése.
3. **Orchesztráció:** `stack.yml` összeállítása, replikák, overlay hálózatok, Secret és Volume hozzáadása.
4. **Első működési tesztek:** helyi HTTP-elérés, feladat létrehozása és frissítést követő visszaolvasása.
5. **Üzemeltetési tesztek:** adatbázis-konténer szándékos megszakítása, automatikus pótlás és adatok megmaradásának ellenőrzése; backend 3 → 5 → 3 skálázás.
6. **Külső hozzáférés:** TryCloudflare Tunnel és másik eszközről végzett feladatmentési teszt.
7. **Flowdesk 2.0:** teljesen új megjelenés, leírás/kategória/prioritás/határidő, statisztikák, keresés, szűrés és szerkesztés hozzáadása.
8. **Adatbázis-frissítés:** a `backend/init_db.py` meglévő táblát is bővíteni képes, az előző feladatok törlése nélkül.
9. **Verziókövetés:** Git-repozitórium és GitHub-forráskódfeltöltés.

### 5.3. Hogyan működik a forráskód?

- A `frontend/index.html` adja a felület HTML-struktúráját, a `styles.css` a stílusokat, az `app.js` pedig `fetch` hívásokkal kezeli az adatokat.
- A `frontend/nginx.conf` az `/api/` végpontokra érkező kéréseket a `backend:5000` címre továbbítja a belső hálózaton.
- A `backend/app.py` Flask útvonalai végzik az adatok ellenőrzését, létrehozását, módosítását és törlését.
- A `backend/db.py` a `/run/secrets/todo_db_password` fájlból olvassa a jelszót, és `psycopg` segítségével csatlakozik a PostgreSQL-hez.
- A `backend/init_db.py` induláskor létrehozza vagy bővíti a `tasks` táblát. Az `ADD COLUMN IF NOT EXISTS` miatt meglévő mezőket és feladatokat nem ír felül. A PostgreSQL tranzakciós advisory lock egyszerre induló backendpéldányok mellett is rendezi a sémamódosításokat.
- A `stack.yml` rögzíti az image-neveket, portokat, hálózatokat, replikaszámokat, erőforráskorlátokat és healthcheckeket.

### 5.4. A saját image-ek létrehozásának parancsai

```bash
sudo docker build -t flowdesk-backend:2.0 ./backend
sudo docker build -t flowdesk-frontend:2.0 ./frontend
sudo docker images
```

A backend image `python:3.12-slim` alapra épül, feltelepíti a `requirements.txt` függőségeket, és Gunicornnal szolgálja ki a Flask API-t. A frontend image `nginx:stable-alpine` alapra épül, és bemásolja a statikus webes fájlokat, valamint az Nginx-konfigurációt.

**Ellenőrzés:** a `docker images` listában a `flowdesk-backend` és `flowdesk-frontend` image-eknél a `2.0` tag látható.

## 6. Telepítés nulláról – pontos parancsok

A parancsokat **Ubuntu/WSL terminálban, a projekt gyökérmappájában** kell kiadni. Feltételezzük, hogy a Docker Engine már működik.

### 6.1. A forráskód beszerzése

Új gépen, telepített Gittel:

```bash
git clone https://github.com/Fmate2003/flowdesk.git
cd flowdesk
```

Ha a projekt már helyileg megvan:

```bash
cd ~/flowdesk-v2/flowdesk-swarm
```

### 6.2. A Swarm állapotának ellenőrzése

```bash
sudo docker info --format '{{.Swarm.LocalNodeState}}'
```

- Ha `active`: a Swarm már létezik, **ne futtasd újra a `swarm init` parancsot**.
- Ha `inactive`: új telepítésnél indítsd el:

```bash
sudo docker swarm init
```

Ellenőrzés:

```bash
sudo docker node ls
```

Egynode-os demónál egy `Ready`, `Active`, `Leader` állapotú manager node-ot várunk.

### 6.3. Docker Secret létrehozása – csak első alkalommal

```bash
sudo docker secret ls
```

Ha még **nem** létezik `todo_db_password` nevű Secret:

```bash
openssl rand -base64 32 | sudo docker secret create todo_db_password -
```

Ellenőrzés:

```bash
sudo docker secret ls
```

**Miért szükséges?** A PostgreSQL és a backend ugyanazt a jelszót fájlon keresztül olvassa a Docker Secretből. A `stack.yml` a Secretet `external: true` megjelöléssel hivatkozza, tehát a stack nem hozza létre helyettünk.

**Fontos:** már használt PostgreSQL Volume mellett **ne hozz létre másik jelszót ugyanazzal a céllal**, mert eltérő hitelesítési adatok kapcsolódhatnak a meglévő adatbázishoz. Ne írd ki a Secret értékét a terminálba vagy a GitHubra.

### 6.4. Image-ek felépítése

```bash
sudo docker build -t flowdesk-backend:2.0 ./backend
sudo docker build -t flowdesk-frontend:2.0 ./frontend
sudo docker images
```

### 6.5. Stack telepítése

```bash
sudo docker stack deploy --resolve-image never -c stack.yml todoapp
```

A `todoapp` a **stack neve**, ezért a Swarm a szolgáltatásokat `todoapp_frontend`, `todoapp_backend`, `todoapp_database` néven hozza létre. A hálózatok neve `todoapp_webnet` és `todoapp_dbnet`; a tároló neve `todoapp_postgres_data`.

A `--resolve-image never` a helyben felépített image-ek használatához illeszkedik. **Ez az egynode-os demó azért működik, mert a build és a futtatás ugyanazon a Docker Engine-en történik.** Több Swarm node esetén az image-eket elérhető registrybe kellene feltölteni, hogy minden node le tudja tölteni őket.

### 6.6. Szolgáltatások ellenőrzése

```bash
sudo docker service ls
sudo docker stack services todoapp
sudo docker service ps todoapp_backend
sudo docker service ps todoapp_database
sudo docker service ps todoapp_frontend
```

Elvárt állapot:

```text
NAME               MODE         REPLICAS   IMAGE
 todoapp_backend    replicated   3/3        flowdesk-backend:2.0
 todoapp_database   replicated   1/1        postgres:16-alpine
 todoapp_frontend   replicated   1/1        flowdesk-frontend:2.0
```

A frontendnél a `*:8080->80/tcp` portleképezést is látni kell. Indítás közben átmenetileg `0/1`, `1/3` vagy `Starting` szerepelhet; újra ellenőrizni kell.

### 6.7. Alkalmazás megnyitása

```text
http://127.0.0.1:8080
```

A felületen a Flowdesk munkaterület, a feladatlista, az új feladat gomb és a rendszerállapot-jelzés jelenik meg.

## 7. Működési ellenőrzés és API-tesztek

### 7.1. Frontend HTTP-válasz

```bash
curl --noproxy '*' -I --connect-timeout 3 --max-time 8 http://127.0.0.1:8080/
```

Elvárt: **`HTTP/1.1 200 OK`** vagy más sikeres `200` státuszkód. A HTML letöltésének ellenőrzése:

```bash
curl --noproxy '*' http://127.0.0.1:8080/
```

### 7.2. Backend és adatbázis egészsége

```bash
curl -sS http://127.0.0.1:8080/api/health
```

Elvárt JSON-válasz:

```json
{"database":"ok","status":"ok"}
```

Ez azt ellenőrzi, hogy a frontend útvonalán keresztül az API elérhető, a Flask backend pedig végre tud hajtani egy `SELECT 1` lekérdezést a PostgreSQL-ben.

### 7.3. Feladatlista

```bash
curl -sS http://127.0.0.1:8080/api/tasks
```

Elvárt: JSON-válasz egy `tasks` tömbbel és egy `instance` mezővel. Ha nincsenek feladatok, a lista üres lehet.

### 7.4. Feladat létrehozása és módosítása

```bash
curl -sS -X POST http://127.0.0.1:8080/api/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"README tesztfeladat","description":"API teszt","category":"study","priority":"high","due_date":"2026-11-21"}'
```

A válaszban keresd a létrehozott feladat **`id`** értékét. Az alábbi `42` csak példa; helyettesítsd a tényleges ID-val:

```bash
curl -sS -X PATCH http://127.0.0.1:8080/api/tasks/42 \
  -H 'Content-Type: application/json' \
  -d '{"completed":true}'
```

Törlés, ha már nincs szükség a tesztfeladatra:

```bash
curl -sS -X DELETE http://127.0.0.1:8080/api/tasks/42
```

**Egyszerűbb alternatíva:** a `scripts/smoke_test.py` létrehoz egy külön próba-feladatot, ellenőrzi a CRUD-műveleteket, majd törli a saját próba-feladatát (lásd 11. fejezet).

## 8. Feladatkövetelmények és igazoló parancsok

Az alábbi ellenőrző mátrix a projektben megvalósított fő, bemutatandó követelményekhez készült. **A hivatalos pontozási lap részletes alszempontjait külön össze kell vetni az oktató által kiadott feladatleírással**, mert ez a README nem helyettesíti a hivatalos értékelési dokumentumot.

| Követelmény | Megvalósítás | Ellenőrző parancs / bizonyíték | Elvárt eredmény |
|---|---|---|---|
| Legalább 3 együttműködő szolgáltatás | Nginx, Flask, PostgreSQL | `sudo docker service ls` | 3 szolgáltatás, `1/1`, `3/3`, `1/1` |
| Saját Dockerfile-ok | `backend/Dockerfile`, `frontend/Dockerfile` | `ls backend/Dockerfile frontend/Dockerfile` | Mindkét fájl létezik |
| Saját Docker image-ek | `flowdesk-frontend:2.0`, `flowdesk-backend:2.0` | `sudo docker images` | Mindkét image szerepel |
| Docker Swarm használata | Aktív Swarm manager | `sudo docker info --format '{{.Swarm.LocalNodeState}}'` | `active` |
| Stack-alapú telepítés | `stack.yml` és `todoapp` stack | `sudo docker stack services todoapp` | 3 Swarm service |
| Overlay hálózat | `webnet`, `dbnet` | `sudo docker network ls` | `todoapp_webnet`, `todoapp_dbnet` |
| Overlay driver ellenőrzése | Mindkettő overlay | `sudo docker network inspect todoapp_webnet --format '{{.Driver}}'` | `overlay` |
| Tartós adatbázis-volume | `postgres_data` | `sudo docker volume inspect todoapp_postgres_data` | Meglévő volume metadata |
| Jelszó Secretben | `todo_db_password` | `sudo docker secret ls` | A Secret neve szerepel, az értéke nem |
| Backend replikáció | 3 alapértelmezett replika | `sudo docker service ps todoapp_backend` | 3 aktív Running task |
| Dinamikus skálázás | 3 → 5 → 3 | `sudo docker service scale todoapp_backend=5` | `5/5` a service listában |
| Automatikus helyreállítás | Swarm task reconciliation | Konténer leállítása után `sudo docker service ps todoapp_database` | Új task indul, majd `1/1` |
| Adatmegőrzés újraindítás után | PostgreSQL named volume | Feladat létrehozása → adatbázis task cseréje → oldal frissítése | A feladat továbbra is látható |
| Backend–adatbázis kapcsolat | Flask `/api/health` | `curl -sS http://127.0.0.1:8080/api/health` | `status: ok`, `database: ok` |
| Nyilvános HTTPS-elérés | Cloudflare Tunnel | Nyilvános URL másik eszközön | A Flowdesk megnyílik és menteni tud |
| Forráskód és leírás | GitHub README és kód | https://github.com/Fmate2003/flowdesk | A fájlok böngészőből elérhetők |
| Dokumentált tesztelés | Egység- és API-tesztek | `python3 -m pytest -q`; `python3 scripts/smoke_test.py` | A tesztek sikeresek |

### 8.1. Konkrét Swarm/stack információk

```bash
sudo docker node ls
sudo docker stack ls
sudo docker stack services todoapp
sudo docker service ls
sudo docker service ps todoapp_backend
```

**Mit magyarázzunk a bemutatón?** A `stack.yml` meghatározza a kívánt állapotot (*desired state*), a Swarm pedig folyamatosan ehhez igazítja a futó feladatokat.

### 8.2. Overlay hálózatok részletes vizsgálata

```bash
sudo docker network ls
sudo docker network inspect todoapp_webnet --format '{{.Name}} / {{.Driver}}'
sudo docker network inspect todoapp_dbnet --format '{{.Name}} / {{.Driver}}'
```

Elvárt: a hálózatok `overlay` drivert használnak. A frontend a `webnet` hálózathoz kapcsolódik, az adatbázis kizárólag a `dbnet` hálózathoz, a backend mindkettőhöz.

### 8.3. Persistent Volume és Secret ellenőrzése

```bash
sudo docker volume ls
sudo docker volume inspect todoapp_postgres_data
sudo docker secret ls
```

**Fontos:** a Volume megléte önmagában nem bizonyítja az adatmegőrzést; ehhez a 9.3. fejezetben leírt gyakorlati teszt szükséges. A Secret **értékét nem mutatjuk meg**.

## 9. Részletes demonstráció: skálázás, önjavítás, adatmegőrzés

### 9.1. Dinamikus skálázás: 3 → 5 → 3

**Előfeltétel:** mindhárom szolgáltatás működik; a backend `3/3` állapotú.

```bash
sudo docker service ls
sudo docker service scale todoapp_backend=5
sudo docker service ls
sudo docker service ps todoapp_backend
```

**Elvárt:** a backend `5/5`, a listában az `.1` … `.5` példányok futnak. Az új példányok a meglévők mellé indulnak. A böngészős alkalmazás továbbra is elérhető ugyanazon a `:8080` porton.

Visszaállítás az eredeti konfigurációra:

```bash
sudo docker service scale todoapp_backend=3
sudo docker service ls
```

**Elvárt:** `todoapp_backend` ismét `3/3`.

> Figyelem: a `service scale` a **futó állapotot** változtatja meg; a `stack.yml` továbbra is `replicas: 3` értéket tartalmaz. Egy későbbi újratelepítésnél ez a deklarált kiinduló állapot.

### 9.2. Automatikus konténer-helyreállítás (self-healing)

**Biztonságos demonstrációs környezet:** saját tesztalkalmazás; az adatbázis rövid időre elérhetetlenné válhat. Nem éles üzleti rendszeren végezzük.

Először azonosítjuk a ténylegesen futó adatbázis-konténert:

```bash
sudo docker ps --filter 'name=todoapp_database'
```

Az egyszerű, pontos konténerazonosító-kiolvasás:

```bash
DB_CONTAINER=$(sudo docker ps --filter 'name=todoapp_database' --format '{{.ID}}' | head -n 1)
echo "$DB_CONTAINER"
```

Ha van azonosító, szándékosan megszakítjuk a konténert:

```bash
test -n "$DB_CONTAINER" && sudo docker kill "$DB_CONTAINER"
```

Ellenőrzés:

```bash
sudo docker service ps todoapp_database
sudo docker service ls
```

**Elvárt:** a régi task `Failed` / `Shutdown` állapotba kerül (a `docker kill` miatt például `exit 137`), a Swarm új taskot indít; végül az adatbázis ismét `1/1` állapotú lesz. A `CURRENT STATE` kezdetben `Starting` lehet.

**Mit igazol?** A Swarm a konténer kiesését észlelve pótolja a kívánt egy adatbázispéldányt. **Nem** bizonyít teljes gép- vagy többnode-os hibatűrést.

### 9.3. Tartós adatmegőrzés tesztje

Ezt a tesztet célszerű a 9.2. lépéssel egy menetben végrehajtani.

1. A böngészőben (`http://127.0.0.1:8080`) hozzunk létre egy `Adatmegőrzési teszt` nevű feladatot.
2. Frissítsük az oldalt (**F5**) és ellenőrizzük, hogy a feladat megvan.
3. Hajtsuk végre a 9.2. fejezetben szereplő adatbázis-konténer leállítását.
4. Várjuk meg, amíg `sudo docker service ls` szerint az adatbázis újra `1/1`.
5. Frissítsük az oldalt, és ellenőrizzük, hogy az **Adatmegőrzési teszt** feladat továbbra is látható.

**Elvárt:** az adat nem vész el, mivel a PostgreSQL fájljai a `todoapp_postgres_data` Docker Volume-ban vannak, nem a megszüntetett konténer ideiglenes rétegében.

A projektben ezt a működést ténylegesen kipróbáltuk: a PostgreSQL-konténer pótlása után a korábban mentett feladat megmaradt. A teljes WSL-/számítógép-leállítás után újratelepített stacket is ellenőriztük, és a korábbi feladatok továbbra is elérhetők voltak.

### 9.4. Kapcsolódó naplók és diagnosztika

```bash
sudo docker service logs --tail 50 todoapp_frontend
sudo docker service logs --tail 50 todoapp_backend
sudo docker service logs --tail 50 todoapp_database
sudo docker service ps todoapp_backend --no-trunc
```

A naplók segítségével ellenőrizhető a frontend indulása, a backend adatbázis-kapcsolódása és az adatbázis inicializálása. Indulási sorrendtől függően átmeneti kapcsolatfelvételi hibák előfordulhatnak; a végső service-állapotot és HTTP-választ is ellenőrizni kell.

## 10. Nyilvános HTTPS-elérés Cloudflare Tunnel segítségével

### 10.1. Miért szükséges a tunnel?

A `127.0.0.1:8080` a helyi gépen használható. A Cloudflare Tunnel egy kimenő kapcsolatot épít ki, amelyen keresztül egy külső, HTTPS-es `trycloudflare.com` címről lehet elérni a helyi szolgáltatást, router-porttovábbítás nélkül.

### 10.2. `cloudflared` telepítése Ubuntu/WSL alatt

A projektben a hivatalos kiadásból származó 64 bites Debian-csomagot használtuk:

```bash
curl -fL --output /tmp/cloudflared.deb \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo apt install -y /tmp/cloudflared.deb
cloudflared --version
```

Az `amd64` csomag Intel/AMD x86-64 géphez való; ARM64 rendszeren a megfelelő másik kiadást kell választani.

### 10.3. Tunnel indítása

A Flowdesk szolgáltatások működése mellett **egy külön VS Code Ubuntu terminálban**:

```bash
cloudflared tunnel --url http://127.0.0.1:8080
```

A terminál kiír egy véletlenszerű címet, például:

```text
https://pelda-veletlen-nev.trycloudflare.com
```

**A tényleges címet a terminálból kell kimásolni; egy korábbi tunnel címe újraindítás után nem feltétlenül működik.** A tunnel futása alatt a parancs nem tér vissza a promptba, ez normális. Leállítás: `Ctrl+C`.

### 10.4. Ellenőrzés külső eszközről

1. Nyissuk meg az aktuális HTTPS-címet egy másik telefonról vagy számítógépről.
2. Hozzunk létre egy tesztfeladatot.
3. Frissítsük az oldalt.
4. Ellenőrizzük, hogy a feladat megmaradt.

A projekt során ez a teszt másik személy eszközéről is sikeresen lefutott. A tunnel önmagában nem garantál 24 órás rendelkezésre állást: ha a számítógép, a Docker vagy a `cloudflared` leáll, a link nem működik. A TryCloudflare Quick Tunnel **nem produkciós hoszting**.

## 11. Automatizált tesztek

### 11.1. Python-függőségek és unit/konfigurációs tesztek

A projekt gyökerében:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r dev-requirements.txt
python3 -m pytest -q
```

A `tests/test_structure.py` ellenőrzi a szolgáltatások számát, a hálózatokat, a Volume/Secret deklarációját, a replika- és restartbeállításokat, a saját image-eket és a publikált HTTP-portot. A `tests/test_api.py` a Flask-végpontok létrehozás/olvasás/módosítás/törlés viselkedését teszteli szimulált adatbáziskapcsolattal; ehhez nem szükséges futó PostgreSQL.

**Sikeres eredmény:** a `pytest` `passed` eredménnyel zár, és 0-s kilépési kódot ad. A tesztek teljesítését a saját gépen kell megerősíteni; a README nem állítja, hogy minden környezetben automatikusan sikeresek.

### 11.2. Végponttól végpontig tartó API-gyorsteszt

Futó Docker Swarm alkalmazás mellett:

```bash
python3 scripts/smoke_test.py
```

A script sorban ellenőrzi:

1. `GET /api/health` – API és adatbázis válasza;
2. `POST /api/tasks` – tesztfeladat létrehozása;
3. `GET /api/tasks` – visszaolvasás;
4. `PATCH /api/tasks/{id}` – készre állítás;
5. `DELETE /api/tasks/{id}` – tesztfeladat törlése.

Elvárt: minden ellenőrzés `OK`, a végén `SIKER`. A script csak a saját maga által létrehozott próbafeladatot törli. Ha az ellenőrzés közben váratlan hiba történik, előfordulhat, hogy manuális takarítás szükséges.

Nyilvános végponthoz is használható az **aktuális**, működő tunnelcímmel:

```bash
BASE_URL=https://pelda-veletlen-nev.trycloudflare.com python3 scripts/smoke_test.py
```

## 12. Leállítás, újraindítás, adatok megőrzése

### 12.1. Szabályos leállítás

1. Cloudflare Tunnel terminál: `Ctrl+C`.
2. Ubuntu terminálban a Flowdesk stack eltávolítása:

```bash
sudo docker stack rm todoapp
sudo docker service ls
```

Várjuk meg, hogy a Flowdesk-szolgáltatások eltűnjenek a listából.

3. Docker Engine és socket leállítása:

```bash
sudo systemctl stop docker docker.socket
systemctl is-active docker
```

Elvárt: `inactive`.

4. VS Code / Ubuntu terminálok bezárása; szükség esetén **Windows PowerShellben**:

```powershell
wsl --shutdown
```

**Lényeg:** a `docker stack rm todoapp` eltávolítja a Swarm-szolgáltatásokat és a stackhálózatokat, de **nem törli automatikusan** a meglévő `todoapp_postgres_data` named Volume-ot, a lokális image-eket és a forráskódot.

### 12.2. Másnapi újraindítás

Ubuntu terminálban:

```bash
cd ~/flowdesk-v2/flowdesk-swarm
sudo systemctl start docker
systemctl is-active docker
sudo docker info --format '{{.Swarm.LocalNodeState}}'
sudo docker stack deploy --resolve-image never -c stack.yml todoapp
sudo docker service ls
```

Elvárt: `active` Docker Engine, `active` Swarm, backend `3/3`, frontend `1/1`, adatbázis `1/1`. Ezután `http://127.0.0.1:8080` megnyitása és a korábbi feladatok ellenőrzése. Ha nyilvános elérés kell, külön újraindítandó a Cloudflare Tunnel.

### 12.3. Amit adatmegőrzéshez tilos véletlenül végrehajtani

```text
NE töröld a todoapp_postgres_data volume-ot!
NE futtass docker volume prune parancsot, ha fontosak a mentett adatok!
NE futtass docker system prune --volumes parancsot!
NE használd a wsl --unregister Ubuntu parancsot!
NE állítsd alaphelyzetbe az Ubuntu alkalmazást!
```

A Docker Volume nem helyettesíti a külön adatbázis- vagy WSL-biztonsági mentést. Éles adatokhoz rendszeres mentési stratégia szükséges.

## 13. Git és GitHub – forráskód publikálása

A projekt forráskódját a GitHubon publikáltuk, így a konfigurációk és az alkalmazáskód ellenőrizhetők.

### 13.1. Első helyi Git-mentés és összekapcsolás

A projekt gyökérmappájában:

```bash
git init
git branch -M main
git remote add origin https://github.com/Fmate2003/flowdesk.git
git status --short
```

Az első feltöltés előtt ellenőrizzük a `.gitignore` tartalmát és a feltöltendő fájlokat:

```bash
cat .gitignore
git add .
git diff --cached --name-only
git grep --cached -n -i -E 'password|secret|token|api_key|private.key'
```

A keresés **csak segítség**, nem teljes titokvizsgálat. A `DB_PASSWORD_FILE` és a `todo_db_password` változónevek önmagukban nem valódi jelszavak. Valódi titkos értékeket nem szabad commitolni.

### 13.2. Első commit és push

A Git szerzői adatait a felhasználónak saját fiókjához kell beállítania. A GitHub privát `noreply` e-mail-címe használható, ha nem szeretnénk nyilvános személyes címet:

```bash
git config --global user.name "Fmate2003"
git config --global user.email "SAJAT_GITHUB_NOREPLY_CIM"
git commit -m "Initial release of Flowdesk 2.0"
git push -u origin main
```

A `SAJAT_GITHUB_NOREPLY_CIM` **helyőrző**, tényleges GitHub-fiókhoz tartozó címre kell cserélni. A `git push` hitelesítést kérhet. Sikeres feltöltéskor a `main -> main` kapcsolat megjelenik.

### 13.3. A README frissítése a GitHubon

Ha most ezt a részletes README-t másolod be a projekt `README.md` fájljába, a következőket kell futtatni:

```bash
git status
git add README.md
git commit -m "Add detailed architecture and Docker Swarm verification guide"
git push
```

Ez frissíti a GitHubon az automatikusan megjelenített README-t. A meglévő repositoryt **nem kell újra létrehozni**.

## 14. Hibaelhárítás

| Jelenség | Lehetséges ok | Vizsgálat / megoldás |
|---|---|---|
| `Cannot connect to the Docker daemon` | Docker Engine nem fut | `sudo systemctl start docker`; `systemctl is-active docker` |
| Swarm állapota `inactive` | Swarm nincs inicializálva | `sudo docker info --format '{{.Swarm.LocalNodeState}}'`; új telepítésnél `sudo docker swarm init` |
| `secret not found` | Nincs külső Docker Secret | `sudo docker secret ls`; első telepítésnél hozd létre |
| Szolgáltatás `0/1` vagy `1/3` | Indulás / crash / hiányzó image | `sudo docker service ps <service>`; `sudo docker service logs --tail 50 <service>` |
| `localhost:8080` nem tölt be | Böngésző/WSL/Swarm ingress gond | `curl --noproxy '*' -v --connect-timeout 3 --max-time 8 http://127.0.0.1:8080/` |
| Nginx `host not found in upstream` | Backend még nem volt elérhető induláskor | `sudo docker service ls`; `sudo docker service logs todoapp_frontend`; ellenőrizd, elindult-e később |
| `/api/health` hibát jelez | Backend / PostgreSQL / Secret hiba | `sudo docker service logs --tail 50 todoapp_backend`; `...database` |
| A feladatok eltűntek | Másik / új / törölt Volume | `sudo docker volume inspect todoapp_postgres_data`; ne törölj Volume-ot |
| `cloudflared: command not found` | Tunnel program nincs telepítve | 10.2. fejezetben szereplő `.deb` telepítés |
| Régi TryCloudflare-link nem él | A tunnel leállt vagy változott az URL | Indíts új tunnelt, használd az új címet |
| Git `Author identity unknown` | Hiányzik a Git szerzői neve/e-mailje | `git config --global user.name ...`; `user.email ...` |
| Git `Authentication failed` | Nincs érvényes GitHub-hitelesítés | GitHub böngészős bejelentkezés vagy támogatott credential manager; tokent ne oszd meg |

A Swarm hibakeresésénél mindig külön ellenőrizzük a **szolgáltatás replikaszámát**, a **taskok állapotát**, a **HTTP-választ** és az **alkalmazásadatok meglétét**. A `3/3` vagy `1/1` önmagában még nem helyettesíti az üzleti funkció tesztelését.

## 15. Biztonság, korlátok és továbbfejlesztési lehetőségek

### 15.1. Biztonsági megoldások

- Az adatbázis nincs közvetlenül publikálva az internetre.
- Az adatbázis-jelszó Docker Secretből kerül a konténerekbe, nem a `stack.yml` fájlban szerepel.
- A `.gitignore` kizárja az általánosan használt helyi `.env`, `secrets/`, kulcs- és naplófájlokat.
- A backend bemeneti validációval ellenőrzi a mezőket; az adatbázis-hozzáférés paraméterezett SQL-lekérdezéseket használ.
- A külső Quick Tunnel HTTPS-kapcsolatot ad a nyilvános kliensoldali eléréshez.

### 15.2. Jelenlegi korlátok

- **Nincs bejelentkezés és felhasználónkénti jogosultságkezelés.** A publikus link ismerői ugyanazt a közös feladatlistát érhetik el és módosíthatják.
- A TryCloudflare nem állandó tárhely és nem garantál folyamatos rendelkezésre állást.
- Egynode-os Swarmot használtunk, nincs külön manager/worker géppark.
- A PostgreSQL helyi volume-ja nem automatikus, többgépes adatbázis-replikáció.
- A replikák ugyanazon a hoston futnak, ezért a teljes gép leállásakor az egész alkalmazás leáll.
- A Docker Volume **nem** biztonsági mentés; kritikus adatokhoz külön backup szükséges.

### 15.3. Lehetséges továbbfejlesztések

Felhasználó-regisztráció és bejelentkezés, szerepkörök, több munkaterület, feladatokhoz rendelt felelősök, címkék, határidős értesítések, PostgreSQL-mentések, automatikus build/test pipeline, konténer registry, többnode-os Swarm, felhőben futó állandó szerver, állandó domain és megfigyelhetőségi dashboard.

## 16. Bemutató forgatókönyv és ellenőrzőlista

Az alábbi sorrendben néhány perc alatt bemutathatók a legfontosabb technikai tulajdonságok.

| Sorrend | Mit mutatunk meg? | Parancs / tevékenység | Elvárt bizonyíték |
|---:|---|---|---|
| 1 | Aktív Swarm | `sudo docker node ls` | `Ready`, manager `Leader` |
| 2 | Három szolgáltatás | `sudo docker service ls` | backend 3/3, frontend 1/1, adatbázis 1/1 |
| 3 | Saját Docker image-ek | `sudo docker images` | `flowdesk-backend:2.0`, `flowdesk-frontend:2.0` |
| 4 | Overlay hálózatok | `sudo docker network ls` | `todoapp_webnet`, `todoapp_dbnet` |
| 5 | Volume és Secret | `sudo docker volume ls`; `sudo docker secret ls` | megvannak, titok értékét nem mutatjuk |
| 6 | API–adatbázis kapcsolat | `curl -sS http://127.0.0.1:8080/api/health` | `status: ok` |
| 7 | Felhasználói működés | Böngésző: `127.0.0.1:8080` | feladat létrehozható, listázható |
| 8 | Skálázás | `sudo docker service scale todoapp_backend=5` | `5/5` |
| 9 | Visszaskálázás | `sudo docker service scale todoapp_backend=3` | `3/3` |
| 10 | Önjavítás | adatbázis-konténer `docker kill` tesztje | új task, majd `1/1` |
| 11 | Adatmegőrzés | előre mentett feladat F5 után | konténercsere után is megvan |
| 12 | Nyilvános HTTPS | aktuális Cloudflare Tunnel URL | működik másik eszközön |
| 13 | Forráskód és leírás | GitHub repository | README, Dockerfile, stack, tesztek |

### Bemutató előtt javasolt parancsok

```bash
cd ~/flowdesk-v2/flowdesk-swarm
sudo systemctl start docker
sudo docker service ls
curl -sS http://127.0.0.1:8080/api/health
python3 scripts/smoke_test.py
```

Ha nincs futó stack, előbb:

```bash
sudo docker stack deploy --resolve-image never -c stack.yml todoapp
```

**Bemutató közben figyeljünk arra**, hogy az adatbázis-konténer kill-tesztjét csak tesztadatokkal végezzük, a skálázást a végén 3 replikára állítsuk vissza, és a TryCloudflare aktuális címét ellenőrizzük másik eszközről is.

---

**Összegzés:** A Flowdesk egyszerre mutat be működő üzleti funkciókat (feladatkezelés és tartós adattárolás) és Docker Swarm üzemeltetési feladatokat (stack telepítés, replikáció, overlay hálózat, Secret, Volume, skálázás, önjavítás, nyilvános elérés). A GitHub-repozitórium tartalmazza az alkalmazás forráskódját, konfigurációját és tesztjeit, így a megoldás felépítése és működése mások számára is ellenőrizhető.
