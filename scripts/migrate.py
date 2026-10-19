"""Versioned, transactional bootstrap/upgrade. Back up existing databases first."""
import argparse
from datetime import datetime, timezone
from sqlalchemy import inspect, text
from app.core.database import Base, engine
import app.models
from app.core.time import as_local
VERSION = "20261018_security_v1"
def migrate(legacy_times=None):
    if engine.dialect.name not in ("sqlite", "postgresql"): raise RuntimeError("Endast SQLite och PostgreSQL stöds.")
    with engine.begin() as conn:
        if engine.dialect.name == "sqlite":
            conn.exec_driver_sql("BEGIN")  # Include DDL in rollback on legacy sqlite drivers.
        tables = inspect(conn).get_table_names()
        if "modium_migrations" in tables and conn.execute(text("SELECT 1 FROM modium_migrations WHERE version=:v"), {"v":VERSION}).first(): return
        existing = "users" in tables
        if existing and legacy_times not in ("utc", "stockholm"):
            raise RuntimeError("Befintlig databas: ange --legacy-times utc eller stockholm efter kontroll av gamla bokningstider.")
        if existing:
            cols = {c["name"] for c in inspect(conn).get_columns("users")}
            for name, ddl in {
                "session_version":"INTEGER NOT NULL DEFAULT 0",
                "email_verified":"BOOLEAN NOT NULL DEFAULT FALSE",
                "verification_token":"VARCHAR(64)",
                "verification_expires_at":"TIMESTAMP"}.items():
                if name not in cols: conn.execute(text(f"ALTER TABLE users ADD COLUMN {name} {ddl}"))
            # Existing users must verify their mailbox; no existing session survives.
            conn.execute(text("UPDATE users SET session_version=session_version+1, reset_token=NULL, reset_token_expires_at=NULL"))
            conn.execute(text("UPDATE users SET email=lower(trim(email))"))
            conn.execute(text("UPDATE bookings SET status=CASE WHEN status IN ('Avbruten','cancelled') THEN 'cancelled' WHEN status IN ('Bokad','confirmed') THEN 'confirmed' ELSE status END"))
            if legacy_times == "stockholm":
                for row in conn.execute(text("SELECT id,start_time,end_time FROM bookings")).mappings().all():
                    values = {}
                    for key in ("start_time", "end_time"):
                        value = row[key]
                        if isinstance(value, str): value = datetime.fromisoformat(value)
                        if engine.dialect.name == "postgresql" and value.tzinfo is not None:
                            # Reinterpret the UTC clock fields as Swedish wall time only
                            # when the operator explicitly selected legacy Stockholm mode.
                            value = value.astimezone(timezone.utc).replace(tzinfo=None)
                        value = as_local(value).astimezone(timezone.utc)
                        values[key] = value.replace(tzinfo=None).isoformat(sep=" ") if engine.dialect.name == "sqlite" else value
                    conn.execute(text("UPDATE bookings SET start_time=:start_time,end_time=:end_time WHERE id=:id"), dict(values,id=row["id"]))
        Base.metadata.create_all(conn)
        # Refuse to silently delete or alter conflicting legacy bookings.
        if conn.execute(text("SELECT id FROM bookings WHERE end_time <= start_time OR status NOT IN ('confirmed','cancelled') LIMIT 1")).first():
            raise RuntimeError("Ogiltiga bokningstider/statusar finns. Rätta datan i en kopia först.")
        if conn.execute(text("SELECT b.id FROM bookings b JOIN venues v ON v.id=b.venue_id WHERE b.organization_id<>v.organization_id LIMIT 1")).first():
            raise RuntimeError("En bokning tillhör fel organisation. Rätta datan först.")
        if conn.execute(text("SELECT a.id FROM bookings a JOIN bookings b ON a.id<b.id AND a.venue_id=b.venue_id AND a.start_time<b.end_time AND a.end_time>b.start_time WHERE a.status<>'cancelled' AND b.status<>'cancelled' LIMIT 1")).first():
            raise RuntimeError("Överlappande bokningar finns. Rätta datan innan migrering.")
        if engine.dialect.name == "postgresql":
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))
            conn.execute(text("ALTER TABLE bookings ADD CONSTRAINT bookings_valid_time CHECK (end_time>start_time)"))
            conn.execute(text("ALTER TABLE bookings ADD CONSTRAINT bookings_valid_status CHECK (status IN ('confirmed','cancelled'))"))
            conn.execute(text("ALTER TABLE venues ADD CONSTRAINT venues_id_org UNIQUE (id,organization_id)"))
            conn.execute(text("ALTER TABLE bookings ADD CONSTRAINT bookings_venue_org FOREIGN KEY (venue_id,organization_id) REFERENCES venues(id,organization_id) ON DELETE CASCADE"))
            conn.execute(text("ALTER TABLE bookings ADD CONSTRAINT bookings_no_overlap EXCLUDE USING gist (venue_id WITH =, tstzrange(start_time,end_time,'[)') WITH &&) WHERE (status<>'cancelled')"))
        else:
            for operation in ("INSERT", "UPDATE"):
                conn.execute(text(f"""CREATE TRIGGER bookings_guard_{operation.lower()} BEFORE {operation} ON bookings BEGIN
                    SELECT RAISE(ABORT,'Invalid booking time') WHERE NEW.end_time<=NEW.start_time;
                    SELECT RAISE(ABORT,'Invalid booking status') WHERE NEW.status NOT IN ('confirmed','cancelled');
                    SELECT RAISE(ABORT,'Wrong organization') WHERE NOT EXISTS (SELECT 1 FROM venues WHERE id=NEW.venue_id AND organization_id=NEW.organization_id);
                    SELECT RAISE(ABORT,'Booking overlap') WHERE NEW.status<>'cancelled' AND EXISTS(SELECT 1 FROM bookings WHERE id<>NEW.id AND venue_id=NEW.venue_id AND status<>'cancelled' AND start_time<NEW.end_time AND end_time>NEW.start_time);
                    END"""))
        conn.execute(text("CREATE TABLE IF NOT EXISTS modium_migrations (version VARCHAR(80) PRIMARY KEY)"))
        conn.execute(text("INSERT INTO modium_migrations(version) VALUES (:v)"), {"v":VERSION})
if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--legacy-times", choices=["utc","stockholm"])
    migrate(parser.parse_args().legacy_times)
    print("Databasen är uppdaterad.")
