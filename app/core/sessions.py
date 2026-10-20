import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from app.models.auth_session import AuthSession
from app.models import User

COOKIE = "endowal_session"
DAYS = 30

def digest(token): return hashlib.sha256(token.encode()).hexdigest()

def session_user(db, token):
    if not token: return None
    session = db.query(AuthSession).filter_by(token_hash=digest(token)).first()
    if not session or session.expires_at.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc): return None
    user = db.get(User, session.user_id)
    return user if user and user.is_active else None

def remember(db, user, request, response):
    # Reuse a valid device session; raw tokens never go into the database.
    token = request.cookies.get(COOKIE)
    existing = session_user(db, token)
    if existing and existing.id == user.id: return
    if token:
        db.query(AuthSession).filter_by(token_hash=digest(token)).delete()
    raw = secrets.token_urlsafe(48)
    db.add(AuthSession(user_id=user.id, token_hash=digest(raw), expires_at=datetime.now(timezone.utc)+timedelta(days=DAYS)))
    db.commit()
    response.set_cookie(COOKIE, raw, max_age=DAYS*86400, httponly=True,
                        secure=request.url.scheme == "https", samesite="lax", path="/auth")
