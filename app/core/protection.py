import secrets, time, threading, hashlib
from urllib.parse import urlsplit
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.core.config import BASE_URL, PRODUCTION
import os
_lock = threading.Lock()
_buckets = {}
LIMITS = {"/login": 20, "/register": 5, "/forgot-password": 5, "/resend-verification": 5}
def rate_allowed(key, limit):
    window = int(time.time() // 900)
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        import redis
        client = redis.Redis.from_url(redis_url, socket_timeout=3)
        name = "modium:rate:" + hashlib.sha256(f"{key}:{window}".encode()).hexdigest()
        # Atomic increment and expiry, shared by all workers.
        count = client.eval("local n=redis.call('INCR',KEYS[1]); if n==1 then redis.call('EXPIRE',KEYS[1],900) end; return n", 1, name)
        return count <= limit
    with _lock:
        for k in list(_buckets):
            if _buckets[k][0] != window: del _buckets[k]
        count = _buckets.get(key, (window, 0))[1] + 1
        _buckets[key] = (window, count)
        return count <= limit
class ProtectionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request.session.setdefault("csrf", secrets.token_urlsafe(32))
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            origin = request.headers.get("origin")
            if origin and origin.rstrip("/") != BASE_URL:
                return JSONResponse({"detail":"Otillåtet ursprung."}, status_code=403)
            supplied = request.headers.get("x-csrf-token", "")
            if not supplied and request.headers.get("content-type", "").startswith(("application/x-www-form-urlencoded", "multipart/form-data")):
                await request.body()  # Cache the body for the downstream form handler.
                supplied = str((await request.form()).get("csrf_token", ""))
            if not secrets.compare_digest(supplied, request.session["csrf"]):
                return JSONResponse({"detail":"Formuläret har gått ut. Ladda om sidan."}, status_code=403)
            limit = LIMITS.get(request.url.path, 20 if request.url.path.startswith("/reset-password/") else None)
            if limit:
                import asyncio
                try: allowed = await asyncio.to_thread(rate_allowed, (request.client.host if request.client else "unknown") + request.url.path.split("/reset-password/")[0], limit)
                except Exception: return JSONResponse({"detail":"Försök igen senare."}, status_code=503)
                if not allowed: return JSONResponse({"detail":"För många försök. Vänta 15 minuter."}, status_code=429, headers={"Retry-After":"900"})
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        if PRODUCTION: response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response
