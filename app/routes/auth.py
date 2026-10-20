from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from app.core.sessions import COOKIE, remember, session_user, digest
from app.models.auth_session import AuthSession
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash, verify_password
from app.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    role = payload.role if payload.role in {"student", "teacher"} else "student"
    user = User(
        email=payload.email,
        name=payload.name,
        role=role,
        is_active=payload.is_active,
        password_hash=get_password_hash(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is inactive")

    remember(db, user, request, response)
    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    return Token(access_token=access_token)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/remember")
def remember_device(request: Request, response: Response, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    # Never resurrect a cookie session that was just revoked on logout.
    token = request.cookies.get(COOKIE)
    if token and not session_user(db, token):
        raise HTTPException(401, "Please sign in again")
    remember(db, user, request, response)
    return {"status": "remembered"}


@router.post("/refresh", response_model=Token)
def refresh(request: Request, db: Session = Depends(get_db)):
    user = session_user(db, request.cookies.get(COOKIE))
    if not user: raise HTTPException(401, "Please sign in again")
    return Token(access_token=create_access_token({"sub":str(user.id),"role":user.role}))


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(COOKIE)
    if token:
        db.query(AuthSession).filter_by(token_hash=digest(token)).delete()
        db.commit()
    response.delete_cookie(COOKIE, path="/auth", httponly=True, samesite="lax")
    return {"status":"signed out"}
