from app.routes.assignments import router as assignments_router
from app.routes.auth import router as auth_router
from app.routes.budget_line_items import router as budget_line_items_router
from app.routes.budget_submissions import router as budget_submissions_router
from app.routes.buckets import router as buckets_router
from app.routes.classrooms import router as classrooms_router
from app.routes.enrollments import router as enrollments_router
from app.routes.ledger_entries import router as ledger_entries_router
from app.routes.users import router as users_router
from app.routes.wallets import router as wallets_router

__all__ = [
    "assignments_router",
    "auth_router",
    "budget_line_items_router",
    "budget_submissions_router",
    "buckets_router",
    "classrooms_router",
    "enrollments_router",
    "ledger_entries_router",
    "users_router",
    "wallets_router",
]
