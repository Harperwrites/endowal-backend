from app.routes.interest import router as interest_router
from app.routes.credit import router as credit_router
from app.routes.dashboard import router as dashboard_router
from app.routes.learning import router as learning_router
from app.routes.messages import router as messages_router
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.deployment import verify_client_database
from fastapi.middleware.cors import CORSMiddleware

from app.routes.grades import router as grades_router

from app.routes import (
    assignments_router,
    auth_router,
    budget_line_items_router,
    budget_submissions_router,
    buckets_router,
    classrooms_router,
    enrollments_router,
    ledger_entries_router,
    users_router,
    wallets_router,
)

app = FastAPI(title="Endowal API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interest_router)
app.include_router(credit_router)
app.include_router(dashboard_router)
app.include_router(learning_router)
app.include_router(messages_router)
app.include_router(grades_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(classrooms_router)
app.include_router(enrollments_router)
app.include_router(assignments_router)
app.include_router(wallets_router)
app.include_router(buckets_router)
app.include_router(ledger_entries_router)
app.include_router(budget_submissions_router)
app.include_router(budget_line_items_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.on_event("startup")
def verify_deployment():
    verify_client_database()


@app.middleware("http")
async def client_features(request: Request, call_next):
    requested_client = request.headers.get("X-Endowal-Client")
    if requested_client is not None and requested_client != settings.client_id:
        return JSONResponse(status_code=409, content={"detail": "Client configuration mismatch"})
    disabled = ((not settings.credit_enabled and request.url.path.startswith("/credit"))
                or (not settings.messaging_enabled and request.url.path.startswith("/messages"))
                or (not settings.interest_enabled and request.url.path.startswith("/interest")))
    if disabled:
        return JSONResponse(status_code=404, content={"detail": "Feature is not enabled for this client"})
    return await call_next(request)


@app.get("/client")
def public_client_config():
    return {"client_id": settings.client_id, "features": {"credit": settings.credit_enabled,
            "messaging": settings.messaging_enabled, "interest": settings.interest_enabled},
            "self_registration": settings.allow_self_registration}
