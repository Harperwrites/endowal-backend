from app.routes.dashboard import router as dashboard_router
from app.routes.learning import router as learning_router
from app.routes.messages import router as messages_router
from fastapi import FastAPI
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
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
