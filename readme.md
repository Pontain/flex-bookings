# Flex Bookings

Ett bokningssystem för organisationer som behöver hantera lokaler och gemensamma bokningar. Projektet fokuserar på åtkomstkontroll, e-postverifiering, skydd mot dubbelbokning och korrekt hantering av svenska tider.

## Funktioner

- Separata organisationer med ägare, administratörer och medlemmar
- Hantering av lokaler och bokningar
- E-postverifiering och kontoskydd
- Databasskydd mot överlappande bokningar
- Tidszonshantering för Europe/Stockholm
- API med samma sessions- och CSRF-skydd som webbappen

## Teknik

Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL, Redis och pytest.

## Kom igång

Python 3.12 rekommenderas. I PowerShell från projektroten:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Fyll i de lokala värdena i `.env`. Skapa sedan en ny, tom utvecklingsdatabas och starta appen:

```powershell
.\.venv\Scripts\python.exe -m scripts.migrate
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8010 --no-access-log
```

Öppna http://127.0.0.1:8010. För Linux/macOS använder du `.venv/bin/python` i stället.

## Dokumentation

Se [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) för e-postinställningar, migrering av befintliga databaser, produktionskonfiguration, behörigheter och testning. Migreringskommandon för befintliga databaser kräver att du först kontrollerar hur deras gamla tider ska tolkas.
