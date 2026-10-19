from datetime import datetime,timedelta
from concurrent.futures import ThreadPoolExecutor
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal,engine
from app.models import User,Booking
from app.core.time import as_local
from conftest import post,csrf,register,venue,booking

def test_unverified_account_cannot_login(client,mailbox):
    r=post(client,'/register',dict(organization_name='A',full_name='A',email='a@example.com',password='LongPassword123!'))
    assert r.status_code==200
    post(client,'/login',dict(email='a@example.com',password='LongPassword123!'))
    assert client.get('/dashboard').status_code==401
    link=mailbox[-1][1].split(':8010')[1]
    assert client.get(link).status_code==200
    assert client.get('/dashboard').status_code==401  # GET never consumes token
    assert post(client,link).status_code==200
    assert post(client,link).status_code==400

def test_anonymous_endpoints(client):
    for path in ['/calendar/events?start=2026-11-01&end=2026-11-02','/api/bookings/','/api/venues/','/api/venues/1/availability?date=2026-11-01','/calendar/week']:
        assert client.get(path).status_code==401,path
    assert post(client,'/api/venues/',json={'name':'Room','organization_id':1}).status_code==401

def test_two_organizations_are_isolated(client,mailbox):
    register(client,mailbox,'Alpha'); v1=venue(client); b1=booking(client,v1).json()['id']
    with TestClient(app,base_url='http://127.0.0.1:8010',follow_redirects=False) as other:
        register(other,mailbox,'Beta'); v2=venue(other,'Beta Room')
        assert other.get('/api/bookings/').json()==[]
        assert [v['id'] for v in other.get('/api/venues/').json()]==[v2]
        assert other.get('/calendar/events?start=2026-11-01&end=2026-11-02').json()==[]
        for path in [f'/bookings/{b1}',f'/bookings/{b1}/edit',f'/bookings/{b1}/modal',f'/venues/{v1}/edit',f'/api/venues/{v1}/availability?date=2026-11-01']:
            assert other.get(path).status_code==404,path
        assert booking(other,v1).status_code==404
        assert post(other,f'/venues/{v1}/delete').status_code==404
        assert post(other,'/api/venues/',json={'name':'Foreign','organization_id':999}).status_code==403

def test_csrf_and_origin(client,mailbox):
    assert client.post('/login',data={'email':'a@example.com','password':'x'}).status_code==403
    token=csrf(client)
    assert client.post('/login',data={'csrf_token':token},headers={'Origin':'https://evil.example'}).status_code==403
    register(client,mailbox)
    assert client.post('/api/venues/',json={'name':'No token'}).status_code==403

def test_reset_unknown_and_session_revocation(client,mailbox):
    uid=register(client,mailbox)
    old_cookie=client.cookies.get('session')
    unknown=post(client,'/forgot-password',{'email':'missing@example.com'})
    known=post(client,'/forgot-password',{'email':'ALPHA@example.com'})
    assert unknown.status_code==known.status_code==200
    assert unknown.text==known.text
    link=mailbox[-1][1].split(':8010')[1]
    token=link.rsplit('/',1)[-1]
    with SessionLocal() as db: assert db.get(User,uid).reset_token != token
    assert post(client,link,{'password':'NewPassword123!'}).status_code==303
    assert post(client,link,{'password':'AnotherPassword123!'}).status_code==400
    client.cookies.clear();client.cookies.set('session',old_cookie)
    assert client.get('/dashboard').status_code==401
    assert post(client,'/login',{'email':'alpha@example.com','password':'NewPassword123!'}).status_code==303

def test_expired_tokens_and_password_policy(client,mailbox):
    assert post(client,'/register',dict(organization_name='A',full_name='A',email='a@example.com',password='short')).status_code==400
    uid=register(client,mailbox)
    post(client,'/forgot-password',{'email':'alpha@example.com'})
    link=mailbox[-1][1].split(':8010')[1]
    with SessionLocal() as db:
        db.get(User,uid).reset_token_expires_at=datetime.now()-timedelta(days=1);db.commit()
    assert post(client,link,{'password':'LongPassword123!'}).status_code==400

def test_rate_limit(client):
    codes=[post(client,'/forgot-password',{'email':'missing@example.com'}).status_code for _ in range(6)]
    assert codes==[200]*5+[429]

def test_regular_member_cannot_manage_venues(client,mailbox):
    uid=register(client,mailbox);v=venue(client)
    with SessionLocal() as db: db.get(User,uid).is_superuser=False;db.commit()
    assert post(client,'/venues/new',{'name':'R'}).status_code==403
    assert post(client,f'/venues/{v}/delete').status_code==403
    assert post(client,'/api/venues/',json={'name':'R'}).status_code==403
    assert client.get(f'/venues/{v}/edit').status_code==403

def test_overlap_adjacent_cancelled_and_timezone(client,mailbox):
    register(client,mailbox);v=venue(client)
    r=booking(client,v);assert r.status_code==201,r.text
    assert r.json()['start_time']=='2026-11-01T10:00:00+01:00'
    assert booking(client,v).status_code==409
    assert booking(client,v,start='2026-11-01T11:00:00+01:00',end='2026-11-01T12:00:00+01:00').status_code==201
    with SessionLocal() as db: db.get(Booking,r.json()['id']).status='cancelled';db.commit()
    assert booking(client,v).status_code==201

def test_database_guards_direct_writes(client,mailbox):
    register(client,mailbox);v=venue(client);r=booking(client,v)
    with SessionLocal() as db:
        original=db.get(Booking,r.json()['id'])
        values={key:getattr(original,key) for key in ('organization_id','venue_id','title','contact_name','contact_email','start_time','end_time','status')}
    with SessionLocal() as db:
        db.add(Booking(**values))
        with pytest.raises(IntegrityError): db.commit()
    with SessionLocal() as db:
        values.update(organization_id=999,status='cancelled');db.add(Booking(**values))
        with pytest.raises(IntegrityError): db.commit()

def test_concurrent_booking_only_one_wins(client,mailbox):
    uid=register(client,mailbox);v=venue(client)
    with SessionLocal() as db: org=db.get(User,uid).organization_id
    # Bypass the application precheck to exercise the DB concurrency guarantee.
    def insert(_):
        try:
            with SessionLocal() as db:
                db.add(Booking(organization_id=org,venue_id=v,title='Race',contact_name='P',contact_email='p@example.com',start_time=as_local(datetime(2026,11,1,10)),end_time=as_local(datetime(2026,11,1,11)),status='confirmed'))
                db.commit();return 'ok'
        except IntegrityError: return 'conflict'
    with ThreadPoolExecutor(max_workers=2) as pool: assert sorted(pool.map(insert,range(2)))==['conflict','ok']

@pytest.mark.parametrize('value',['2026-03-29T02:30:00','2026-10-25T02:30:00'])
def test_dst_ambiguous_or_missing(value):
    with pytest.raises(ValueError): as_local(datetime.fromisoformat(value))

@pytest.mark.parametrize('path',['/dashboard','/calendar/week','/calendar/month','/bookings','/bookings/new','/venues','/venues/new','/users','/users/new'])
def test_pages_render(client,mailbox,path):
    register(client,mailbox)
    response=client.get(path)
    assert response.status_code==200,response.text
    assert response.headers['X-Content-Type-Options']=='nosniff'

def test_forms_create_and_edit(client,mailbox):
    register(client,mailbox)
    assert post(client,'/venues/new',dict(name='Form Room',capacity=10,color='#123456')).status_code==303
    v=client.get('/api/venues/').json()[0]['id']
    data=dict(venue_id=v,title='Form booking',contact_name='P',contact_email='p@example.com',start_date='2026-11-01',end_date='2026-11-01',start_hour='10',start_minute='00',end_hour='11',end_minute='00')
    response=post(client,'/bookings/new',data)
    assert response.status_code==303,response.text
    b=client.get('/api/bookings/').json()[0]['id']
    for path in [f'/bookings/{b}',f'/bookings/{b}/edit',f'/bookings/{b}/modal',f'/venues/{v}/edit']:
        assert client.get(path).status_code==200
    assert post(client,f'/bookings/{b}/edit',dict(data,start_hour='12',end_hour='13')).status_code==303
    assert post(client,f'/bookings/{b}/edit',dict(data,start_hour='99')).status_code==400

def test_populated_lists_and_user_management(client,mailbox):
    register(client,mailbox);v=venue(client);assert booking(client,v).status_code==201
    response=post(client,'/users/new',dict(full_name='Member',email=' MEMBER@example.com ',password='LongPassword123!'))
    assert response.status_code==303,response.text
    link=mailbox[-1][1].split(':8010')[1]
    assert post(client,link).status_code==200
    with SessionLocal() as db: member=db.query(User).filter_by(email='member@example.com').first().id
    for path in ['/venues','/bookings','/users',f'/users/{member}/edit']:
        r=client.get(path);assert r.status_code==200,r.text
        assert 'name="csrf_token"' in r.text
    assert post(client,f'/users/{member}/edit',dict(full_name='Member',email='member2@example.com',password='')).status_code==303
    with SessionLocal() as db: assert not db.get(User,member).email_verified
    assert post(client,f'/users/{member}/delete').status_code==303

def test_booking_input_errors_and_inactive_venue(client,mailbox):
    register(client,mailbox);v=venue(client)
    assert booking(client,v,start='2026-11-01T11:00:00+01:00',end='2026-11-01T10:00:00+01:00').status_code==422
    assert post(client,'/api/venues/',json={'name':'  ','color':'bad'}).status_code==422
    from app.models import Venue
    with SessionLocal() as db: db.get(Venue,v).is_active=False;db.commit()
    assert booking(client,v).status_code==404

def test_verification_expiry_and_resend(client,mailbox):
    post(client,'/register',dict(organization_name='A',full_name='A',email='a@example.com',password='LongPassword123!'))
    link=mailbox[-1][1].split(':8010')[1]
    with SessionLocal() as db:
        u=db.query(User).first();u.verification_expires_at=datetime.now()-timedelta(days=1);db.commit()
    assert post(client,link).status_code==400
    assert post(client,'/resend-verification',{'email':'a@example.com'}).status_code==200
    assert post(client,mailbox[-1][1].split(':8010')[1]).status_code==200

def test_logout_revokes_cookie(client,mailbox):
    register(client,mailbox);cookie=client.cookies.get('session')
    assert post(client,'/logout').status_code==303
    client.cookies.clear();client.cookies.set('session',cookie)
    assert client.get('/dashboard').status_code==401

def test_database_update_cannot_overlap(client,mailbox):
    register(client,mailbox);v=venue(client)
    assert booking(client,v).status_code==201
    second=booking(client,v,start='2026-11-01T12:00:00+01:00',end='2026-11-01T13:00:00+01:00').json()['id']
    with SessionLocal() as db:
        item=db.get(Booking,second);item.start_time=as_local(datetime(2026,11,1,10,30))
        with pytest.raises(IntegrityError): db.commit()

def test_running_booking_prevents_venue_delete(client,mailbox):
    from app.core.time import local_now
    register(client,mailbox);v=venue(client)
    now=local_now()
    assert booking(client,v,start=(now-timedelta(minutes=10)).isoformat(),end=(now+timedelta(minutes=20)).isoformat()).status_code==201
    assert post(client,f'/venues/{v}/delete').status_code==400
