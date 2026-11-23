# Flowdesk 3.0 – Felület újratervezése

A felület az Oil UI munkamódszerének Flowdesk-specifikus feldolgozásával készült, nem az eredeti repository komponenseinek másolata.

**Dizájnirány:** Editorial Workspace. Precíz, nyugodt munkaeszköz; a feladatlista az elsődleges tartalom. Világos navigáció, meleg semleges háttér, sötétzöld akcentus, tömör összegző sor és visszafogott kezelőszervek.

**A régi felülethez képest:** eltűnt a sötét dashboard-sidebar, a négy méretes statisztikakártya, a nagy üdvözlő hero és a fölösleges dekoráció. Egy elsődleges feladatfelvételi gomb maradt. A meglévő táblázat mobilon egymás alatti adattömbökké alakul. A készre jelölés finom visszajelzést kap.

**Megőrzött működés:** `GET/POST/PATCH/DELETE /api/tasks`, `GET /api/health`, kategóriák, prioritás, határidő, keresés, szűrés, rendezés, CRUD és a modális űrlap. Backend, PostgreSQL, Secret, hálózatok és a `todoapp_postgres_data` volume változatlanok.

**Elérhetőség:** billentyűzetes fókuszjelölések, címkézett mezők, HTML-dialog, `prefers-reduced-motion`. A külső betűtípus betöltése nem szükséges: lokális, rendszerbeli fallback fontokat használ.

**Ellenőrzés:** a statikus felületet 1440×900 és 390×844 méretben megjelenítettük; a 390 px széles mobilképen nem jelentkezett vízszintes dokumentumszintű túlcsordulás. A HTML-azonosítók meglétét és egyediségét, valamint a JavaScript szintaxisát ellenőriztük. A valódi Flask/PostgreSQL végpontokkal végzett végponttól végpontig tartó integrációs tesztet a felhasználó WSL Docker-környezetében kell elvégezni.

**Visszaállítás:** `stack.yml` frontend image-jének visszaállítása `flowdesk-frontend:2.0` értékre és `sudo docker stack deploy --resolve-image never -c stack.yml todoapp`. A régi frontend image maradjon a gépen. A frontend forráskódjának visszaállításához a Git előző commitja vagy a korábbi ZIP használható.
