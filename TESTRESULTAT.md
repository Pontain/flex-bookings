# Verifiering av den korrigerade versionen

Verifierat 2026-10-19 i Python 3.12 på Linux.

## Genomfört

- **32 automatiserade Python-tester godkända** mot en tillfällig SQLite-databas.
- Registrering, engångsverifiering av e-post, utgångna länkar och omsändning.
- Inloggning, lösenordskrav, återställning för känd/okänd adress och utgångna återställningslänkar.
- Gamla sessioner avvisas efter lösenordsåterställning och utloggning.
- Två organisationer kan inte läsa eller ändra varandras bokningar/lokaler via de testade API- och webbrutterna.
- Vanliga medlemmar avvisas från lokaladministration.
- CSRF-kontroll och kontroll av ursprung; anropsbegränsningens lokala utvecklingsläge.
- Skapa och redigera bokningar via webbformulär och API; validering av ogiltiga tider och inaktiva lokaler.
- Databasen avvisar överlappning vid både direkt insättning och uppdatering. Två samtidiga direkta insättningar ger en lyckad bokning och en konflikt.
- Intilliggande tider accepteras och avbokade bokningar frigör tiden.
- Pågående bokningar hindrar borttagning av lokalen.
- De centrala HTML-sidorna renderas, även med innehåll i listor och CSRF i åtgärdsformulär.
- Simulerad gammal SQLite-databas uppgraderas utan förlust av bokningen. Upprepad migrering ändrar inte data igen. Vid konflikt backas även schemaändringarna tillbaka.
- Obefintliga och tvetydiga lokala tider vid sommartidsbyten avvisas.
- JavaScript-tester av båda kalenderernas renderingskod med en liten DOM-simulering: bokningstext HTML-escapas och svenska datum/tider fungerar i tre olika process-tidszoner (UTC, Stockholm och Los Angeles).

Kör själv:

```text
python -m pytest -q
node tests/test_calendar.js
```

Node-testet kräver Node.js men inga npm-paket. Python-testkörningen ger en deprecieringsvarning om Starlettes framtida övergång från httpx till httpx2; testerna är godkända med bifogad versionslista.

## Inte verifierat i denna miljö

- **PostgreSQL-körning:** tillfällig PostgreSQL kunde inte startas med miljöns processbehörigheter. PostgreSQL-migreringen och dess exclusion constraint finns i koden, men har inte körts mot en riktig PostgreSQL-server här. Kör testerna med en separat PostgreSQL-testdatabas före publik drift.
- **Webbläsare och responsiv layout:** Chromium-nedladdningen misslyckades. Ingen visuell mobil-/desktopkontroll har därför genomförts. HTML-rendering och DOM-simuleringen ersätter inte en riktig webbläsarkontroll.
- **Riktig e-postleverans:** testen fångar utskicken lokalt; leverans, TLS och avsändardomän behöver kontrolleras med din SMTP-leverantör.
- **Redis i drift:** Redis-varianten använder en atomär räknare med utgångstid; testerna kör den lokala utvecklingsvarianten. Verifiera Redis-anslutning och anropsbegränsning över flera processer i driftmiljön.
- Din befintliga databas ingick inte. Migreringen måste provas på en säkerhetskopia av den, särskilt för att välja rätt tolkning av gamla tider.

Det här är ett korrigerat och lokalt testat projektpaket, inte ett intyg om att en okänd driftsmiljö redan är lanseringsklar.
