# Flex Bookings

A booking system for organizations that need to manage shared spaces and reservations. The project focuses on access control, email verification, double-booking prevention, and correct handling of Swedish local time.

## Features

- Separate organizations with owners, administrators, and members
- Venue and booking management
- Email verification and account protection
- Database safeguards against overlapping bookings
- Time zone handling for Europe/Stockholm
- API with the same session and CSRF protections as the web app

## Technology

Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL, Redis, and pytest.

## Getting started

Python 3.12 is recommended. From the project root, run these commands in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set the local values in `.env`. Then create a new, empty development database and start the app:

```powershell
.\.venv\Scripts\python.exe -m scripts.migrate
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8010 --no-access-log
```

Open http://127.0.0.1:8010. On Linux or macOS, use `.venv/bin/python` instead.

## Documentation

See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for email settings, migrating existing databases, production configuration, permissions, and testing. Before migrating an existing database, check how its legacy timestamps should be interpreted.
