import os, tempfile, re
from pathlib import Path
import pytest
os.environ['SESSION_SECRET']='test-only-secret-not-for-production-123456789'
os.environ['DATABASE_URL']=os.getenv('TEST_DATABASE_URL', 'sqlite:///' + str(Path(tempfile.mkdtemp())/'test.db'))
os.environ['APP_ENV']='development'
os.environ['APP_BASE_URL']='http://127.0.0.1:8010'
os.environ.pop('REDIS_URL',None)
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import engine, SessionLocal
from scripts.migrate import migrate
from app.web.routes import auth
from app.core.protection import _buckets
from app.models import User, Organization, Venue, Booking

@pytest.fixture(autouse=True)
def database():
    migrate()
    with engine.begin() as conn:
        from sqlalchemy import text
        for table in ['bookings','organization_members','users','venues','organizations']:
            conn.execute(text('DELETE FROM '+table))
    _buckets.clear()

@pytest.fixture
def mailbox(monkeypatch):
    messages=[]
    async def capture(email, link, purpose): messages.append((email,link,purpose))
    monkeypatch.setattr(auth,'send_account_email',capture)
    return messages

@pytest.fixture
def client():
    with TestClient(app,base_url='http://127.0.0.1:8010',follow_redirects=False) as c: yield c

def csrf(client, path='/login'):
    response=client.get(path)
    assert response.status_code == 200, response.text
    return re.search(r'name="csrf_token" value="([^"]+)"', response.text).group(1)

def post(client, path, data=None, json=None):
    token=csrf(client)
    if json is not None: return client.post(path,json=json,headers={'X-CSRF-Token':token})
    return client.post(path,data=dict(data or {},csrf_token=token))

def register(client,mailbox,name='Alpha'):
    email=name.lower()+'@example.com'
    r=post(client,'/register',dict(organization_name=name,full_name=name,email=email,password='LongPassword123!'))
    assert r.status_code==200,r.text
    link=mailbox[-1][1].split(':8010')[1]
    assert post(client,link).status_code==200
    assert post(client,'/login',dict(email=email,password='LongPassword123!')).status_code==303
    with SessionLocal() as db: return db.query(User).filter_by(email=email).first().id

def venue(client,name='Room'):
    r=post(client,'/api/venues/',json={'name':name})
    assert r.status_code==201,r.text
    return r.json()['id']

def booking(client,venue_id,start='2026-11-01T10:00:00+01:00',end='2026-11-01T11:00:00+01:00',**kwargs):
    return post(client,'/api/bookings/',json=dict(venue_id=venue_id,title='Meeting',contact_name='Person',contact_email='person@example.com',start_time=start,end_time=end,**kwargs))
