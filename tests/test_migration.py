from datetime import datetime
from sqlalchemy import create_engine,text,inspect
import pytest
from app.core.database import Base
import scripts.migrate as migration

@pytest.fixture
def legacy(tmp_path,monkeypatch):
    engine=create_engine('sqlite:///'+str(tmp_path/'legacy.db'))
    Base.metadata.create_all(engine)
    with engine.begin() as c:
        for col in ['session_version','email_verified','verification_token','verification_expires_at']:
            c.execute(text('ALTER TABLE users DROP COLUMN '+col))
        c.execute(text("INSERT INTO organizations(id,name) VALUES(1,'Legacy')"))
        c.execute(text("INSERT INTO users(id,organization_id,email,full_name,hashed_password,is_active,is_superuser) VALUES(1,1,'OLD@EXAMPLE.COM','Old','unused',1,1)"))
        c.execute(text("INSERT INTO venues(id,organization_id,name,is_active,color) VALUES(1,1,'Room',1,'#123456')"))
        c.execute(text("INSERT INTO bookings(id,organization_id,venue_id,title,contact_name,contact_email,start_time,end_time,status) VALUES(1,1,1,'Meeting','Name','p@example.com','2026-11-01 10:00:00','2026-11-01 11:00:00','Bokad')"))
    monkeypatch.setattr(migration,'engine',engine)
    return engine

def test_existing_requires_explicit_timezone(legacy):
    with pytest.raises(RuntimeError,match='legacy-times'): migration.migrate()
    assert 'session_version' not in [c['name'] for c in inspect(legacy).get_columns('users')]

def test_upgrade_preserves_data_and_is_idempotent(legacy):
    migration.migrate('stockholm')
    with legacy.connect() as c:
        u=c.execute(text('SELECT * FROM users')).mappings().one()
        assert u['email']=='old@example.com' and u['email_verified']==0
        assert u['session_version']==1
        b=c.execute(text('SELECT * FROM bookings')).mappings().one()
        assert b['status']=='confirmed'
        assert datetime.fromisoformat(b['start_time']).hour==9
    migration.migrate('stockholm')
    with legacy.connect() as c:
        assert c.execute(text('SELECT session_version FROM users')).scalar()==1
        assert datetime.fromisoformat(c.execute(text('SELECT start_time FROM bookings')).scalar()).hour==9

def test_conflicting_legacy_data_rolls_back(legacy):
    with legacy.begin() as c:
        c.execute(text("INSERT INTO bookings(id,organization_id,venue_id,title,contact_name,contact_email,start_time,end_time,status) VALUES(2,1,1,'Conflict','Name','p@example.com','2026-11-01 10:30:00','2026-11-01 11:30:00','Bokad')"))
    with pytest.raises(RuntimeError,match='Överlappande'): migration.migrate('stockholm')
    assert 'session_version' not in [c['name'] for c in inspect(legacy).get_columns('users')]
    with legacy.connect() as c:
        assert c.execute(text('SELECT status FROM bookings WHERE id=1')).scalar()=='Bokad'
