from fastapi import FastAPI

from app.routes import (
    assignments_router,
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
