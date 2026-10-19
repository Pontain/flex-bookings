from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from sqlalchemy.types import TypeDecorator, DateTime
LOCAL = ZoneInfo("Europe/Stockholm")
def local_now(): return datetime.now(LOCAL)
def as_local(value):
    if value.tzinfo is not None: return value.astimezone(LOCAL)
    first = value.replace(tzinfo=LOCAL, fold=0)
    second = value.replace(tzinfo=LOCAL, fold=1)
    if first.astimezone(timezone.utc).astimezone(LOCAL).replace(tzinfo=None) != value:
        raise ValueError("Klockslaget finns inte vid bytet till sommartid.")
    if first.utcoffset() != second.utcoffset():
        raise ValueError("Klockslaget är tvetydigt vid bytet till vintertid. Välj en annan tid eller ange UTC-offset via API.")
    return first
class BookingTime(TypeDecorator):
    impl = DateTime
    cache_ok = True
    def load_dialect_impl(self, dialect): return dialect.type_descriptor(DateTime(timezone=True))
    def process_bind_param(self, value, dialect):
        if value is None: return None
        value = as_local(value).astimezone(timezone.utc)
        return value.replace(tzinfo=None) if dialect.name == "sqlite" else value
    def process_result_value(self, value, dialect):
        if value is None: return None
        if value.tzinfo is None: value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(LOCAL)
