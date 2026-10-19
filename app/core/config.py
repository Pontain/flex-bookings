import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
APP_DIR = Path(__file__).resolve().parents[1]
PRODUCTION = os.getenv("APP_ENV", "development") == "production"
SECRET = os.environ["SESSION_SECRET"]
if len(SECRET) < 32 or SECRET == "byt-den-har-i-env" or SECRET.startswith("REPLACE_"):
    raise RuntimeError("SESSION_SECRET måste vara minst 32 slumpmässiga tecken.")
BASE_URL = os.getenv("APP_BASE_URL", "http://127.0.0.1:8010").rstrip("/")
if PRODUCTION:
    if not BASE_URL.startswith("https://"):
        raise RuntimeError("APP_BASE_URL måste använda HTTPS.")
    if not os.getenv("DATABASE_URL", "").startswith("postgresql"):
        raise RuntimeError("Produktion kräver PostgreSQL.")
    if not os.getenv("REDIS_URL"):
        raise RuntimeError("Produktion kräver REDIS_URL för delad anropsbegränsning.")
    if os.getenv("SMTP_PORT", "587") not in ("465", "587"):
        raise RuntimeError("Produktion kräver SMTP med TLS på port 465 eller 587.")
    for key in ("SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM_EMAIL"):
        if not os.getenv(key): raise RuntimeError(f"{key} saknas.")
