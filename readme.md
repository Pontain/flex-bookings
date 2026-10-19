# Modium Booking – korrigerad version

Detta är en korrigerad projektkopia av den uppladdade koden. Originalets utseende och huvudsakliga struktur är bevarade. Källkoden ligger nu under `app/`, så importerna `app.*` fungerar från projektroten. Ingen befintlig driftsmiljö eller databas har ändrats.

## Börja här på Windows

Python 3.12 rekommenderas; det är versionen som använts i testerna. Öppna den uppackade mappen `Modium-booking` i VS Code. Kör i PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

Kopiera den genererade strängen till `SESSION_SECRET` i `.env`. Platshållaren accepteras inte. Behåll nyckeln hemlig och lägg aldrig `.env` i Git.

För en **ny, tom lokal databas**:

```powershell
.\.venv\Scripts\python.exe -m scripts.migrate
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8010 --no-access-log
```

Öppna http://127.0.0.1:8010. Använd samma adress som `APP_BASE_URL`, även när du öppnar verifieringslänkar. Formulärskyddet kontrollerar ursprunget.

På Linux/macOS motsvaras Python-kommandot av `.venv/bin/python`.

### E-post behövs för att aktivera konton

Registreringen skapar en egen organisation och ett ägarkonto. Kontot måste verifiera sin e-postadress innan inloggning. Även användare som skapas av administratören verifierar sin adress.

Fyll i SMTP-inställningarna i `.env`. Exempelfilen använder en lokal SMTP-fångare (exempelvis Mailpit) på port 1025. En sådan server måste startas separat; den medföljer inte. Där läser du meddelandet och följer verifieringslänken. Inga verifieringskoder eller återställningslänkar skrivs ut i applikationsloggen.

För riktig e-post använder du din leverantörs värd, användarnamn, lösenord och avsändaradress. Port 587 använder STARTTLS; port 465 använder TLS från anslutningens början. Om leveransen misslyckas finns länken ”Verifiera e-post / skicka ny länk” på inloggningssidan. Kontrollera SMTP-inställningarna och begär sedan en ny länk.

## Uppgradera en befintlig databas

**Byt inte ut din gamla databas mot den tomma utvecklingsdatabasen.** Den uppladdade zipfilen innehöll ingen databas eller migrationshistorik.

1. Säkerhetskopiera databasen och prova uppgraderingen på en kopia.
2. Stäng den gamla applikationen medan migreringen körs.
3. Sätt `DATABASE_URL` till kopian i `.env`.
4. Kontrollera några gamla bokningar mot deras faktiska avsedda tider. Originalet blandade tidszoner; det går inte att avgöra rätt tolkning enbart från källkoden.
5. Kör **ett** av alternativen nedan:

```powershell
# Tiderna representerar redan rätt UTC-tidpunkt:
.\.venv\Scripts\python.exe -m scripts.migrate --legacy-times utc

# Gamla klockslag representerar svensk lokal tid som behöver konverteras:
.\.venv\Scripts\python.exe -m scripts.migrate --legacy-times stockholm
```

`utc` lämnar gamla tidpunkter oförändrade. `stockholm` tolkar gamla SQLite-klockslag som svensk lokal tid. För PostgreSQL tolkar det de befintliga tidsstämplarnas **UTC-klockfält** som svenska klockslag. Använd inte detta alternativ om PostgreSQL redan lagrat rätt tidpunkt! Exempel: ett tidigare felaktigt lagrat `10:00 UTC` som egentligen betydde svensk `10:00` i november blir `09:00 UTC`.

Om den gamla databasen blandar korrekt UTC med felaktigt sparade lokala tider behövs en separat datarättning; ett enda alternativ kan då inte rätta alla poster. Tvetydiga eller obefintliga svenska klockslag vid sommartidsbyten stoppas vid konvertering.

Migreringen normaliserar e-post och bokningsstatus, lägger till kontoskydd och databasskydd mot överlappning. Den avbryter vid överlappande eller inkonsekventa gamla bokningar i stället för att radera dem. E-postadresser som kolliderar efter normalisering måste också rättas först. Migreringen är versionsmärkt och gör inget vid nästa körning efter lyckad uppgradering.

Alla gamla sessioner och återställningslänkar blir ogiltiga. Befintliga användare får begära en verifieringslänk på inloggningssidan. Befintliga lösenord behålls, men nya lösenord måste innehålla 12–128 tecken.

Kontrollera tider, lokaler och konton i kopian innan samma procedur genomförs i drift. Återställ säkerhetskopian och föregående kodversion om du behöver backa; något automatiskt nedgraderingsskript ingår inte.

## Inför publik drift

Sätt följande i driftmiljön:

- `APP_ENV=production`
- `APP_BASE_URL=https://din-domän.se`
- En unik, slumpmässig `SESSION_SECRET`.
- `DATABASE_URL=postgresql+psycopg://...` för PostgreSQL.
- `REDIS_URL` till en privat eller autentiserad Redis-instans, så alla processer delar anropsbegränsningen.
- Fullständiga SMTP-inställningar med autentisering och port 587 eller 465.

Kör migreringen före start. PostgreSQL-användaren som migrerar måste kunna skapa tillägget `btree_gist`, eller få det installerat av databasadministratören. Det används för att databasen ska avvisa överlappande bokningar, även vid samtidiga anrop. SQLite är för lokal utveckling; produktion vägrar starta med SQLite.

Exempel på start:

```text
python -m uvicorn app.main:app --host 0.0.0.0 --port 8010 --no-access-log
```

Terminera HTTPS i din plattform/proxy. Om klient-IP skickas genom proxy ska Uvicorn endast lita på den verkliga proxyns IP-adress (`--forwarded-allow-ips`); använd inte `*` på en server som kan nås direkt. Annars kan anropsbegränsningen få fel klient-IP. Om Redis inte kan nås stängs de begränsade kontoåtgärderna tillfälligt med HTTP 503.

Undvik loggning av kompletta verifierings- och återställningsadresser också i proxyn, eftersom URL:erna innehåller engångstoken. Kontrollen av migreringen sker vid uppstart; `/health` är en enkel livsteckenskontroll, inte ett fullständigt driftövervakningssystem.

Konfigurera säkerhetskopiering och prova återställning, e-postleverans och kontoflöden i din faktiska driftmiljö innan du bjuder in användare. Besluta också om integritetsinformation, gallring och rutiner för support/radering av organisationer; den här kodändringen innehåller ingen självbetjäningsfunktion för att radera en hel organisation.

## Behörigheter och beteende

- Varje registrering skapar en separat organisation. Det finns ingen automatisk anslutning till en befintlig organisation utifrån e-postdomän.
- Ägaren och administratörer hanterar organisationens användare och lokaler. `is_superuser` är här en **organisationsadministratör**, ingen global plattformsadministratör.
- Medlemmar ser och hanterar organisationens bokningar. Bokningar är gemensamma inom organisationen, inte privata per användare.
- Organisationens ägare kan inte tas bort eller degraderas genom medlemsadministrationen. Ägarbyte ingår inte.
- Utloggning och lösenordsbyte ogiltigförklarar alla kontots befintliga sessioner. Ändring av en användare via administrationen ogiltigförklarar också sessionerna; ändrad e-post kräver ny verifiering.
- Sessionen går ut efter åtta timmars inaktivitet och förnyas vid användning. HTTPS-cookie används i produktion.
- Nya bokningar lagras som UTC. Formulär, månadsvy och JavaScript-veckovyer använder Europe/Stockholm, även om webbläsaren har en annan tidszon.
- Intern bokningsstatus är `confirmed` eller `cancelled`. Avbokade bokningar blockerar inte tider. Någon ny avbokningsknapp har inte lagts till i denna säkerhetsändring.
- Boknings-API:t ligger på `/api/bookings/` (det gamla dubbla `/api/bookings/bookings/` är borttaget).
- API:t använder samma inloggade session och CSRF-skydd som webben. Ändrande JSON-anrop behöver `X-CSRF-Token`, med värdet från ett formulär i den aktuella sessionen.

## Tester

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Standardkörningen skapar en separat tillfällig SQLite-databas. För PostgreSQL kan `TEST_DATABASE_URL` sättas till en **helt separat, tom testdatabas**. Tester tömmer tabeller: använd aldrig en befintlig produktionsdatabas!

Se `TESTRESULTAT.md` för vad som faktiskt har verifierats och vilka kontroller som återstår i din miljö.

Teknisk referens för PostgreSQL-skyddet: https://www.postgresql.org/docs/17/rangetypes.html#RANGETYPES-CONSTRAINT
