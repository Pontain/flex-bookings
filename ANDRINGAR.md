# Ändringar

- Alla monterade boknings-, kalender- och lokal-API:er kräver inloggning och begränsar data till aktuell organisation.
- Skapande av lokaler härleder organisations-ID från sessionen; ett främmande ID avvisas.
- Organisationsadministratörer krävs konsekvent för att skapa, redigera och ta bort lokaler.
- Webbläsartext i bokningskort HTML-escapas. Bekräftelsetext för radering ligger i ett data-attribut, inte i genererad JavaScript-kod.
- CSRF-token i POST-formulär, kontroll av Origin, säkerhetsheaders, obligatorisk sessionsnyckel och HTTPS-cookies i produktion.
- Inloggning, registrering, glömt lösenord, omsändning och återställning får anropsbegränsning; Redis krävs i produktion.
- E-postnormalisering, validering, lösenordslängd och verifiering innan kontot kan användas. Token lagras hashade och gäller en timme.
- Lösenordsåterställning för okänd adress ger samma bekräftelsesida som för känd adress. Token skrivs inte längre i loggen.
- Sessionsversion återkallar gamla sessioner efter konto-/lösenordsändring och utloggning.
- Ägare skyddas mot borttagning/degradering via medlemsadministrationen.
- Boknings-API:ets felaktiga funktionsanrop och dubbla URL-prefix är rättade. Lokal-API:ets saknade färgfält är också rättat.
- Samma tids- och fältvalidering används vid skapande och redigering av bokningar.
- Enhetliga statusvärden, UTC-lagring och svensk tidszon i presentationen.
- Databasskydd mot samtidiga dubbelbokningar, ogiltiga tidsintervall och bokningar i fel organisations lokal. PostgreSQL använder exclusion constraint; SQLite använder triggers.
- Lokal med pågående eller framtida bokning kan inte raderas. Historiska bokningar kan fortfarande påverkas av lokalradering enligt det ursprungliga kaskadbeteendet; exportera/säkerhetskopiera innan sådan radering.
- Sökvägar beräknas från appens placering. Projektrot, beroendelista, miljöexempel, versionsmärkt migrering, tester och svensk uppstartsguide ingår.
- Gamla bytekodscacher och oanvända äldre CSS/dashboard-filer följer inte med.

Utseendet har inte designats om. Ingen server har publicerats och inga riktiga kontomejl har skickats under arbetet.
