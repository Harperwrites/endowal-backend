# Endowal Backend

FastAPI + SQLAlchemy starter for the Endowal school finance app.

## Local setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Database

Default SQLite is used if `DATABASE_URL` is not set.

## Migrations

```bash
alembic upgrade head
```

## Run

```bash
uvicorn app.main:app --reload
```

## OpenAPI docs

Start the server, then visit:

- `http://127.0.0.1:8000/docs` (Swagger UI)
- `http://127.0.0.1:8000/openapi.json` (raw schema)

Request/response examples are included in the OpenAPI schema via Pydantic model examples.

## Endpoint summary

Auth
- `POST /auth/register` — Create a user (student/teacher)
- `POST /auth/login` — Get an access token
- `GET /auth/me` — Current user

Users (admin-only)
- `GET /users`
- `POST /users`
- `GET /users/{user_id}`
- `PATCH /users/{user_id}`
- `DELETE /users/{user_id}`

Classrooms
- `GET /classrooms`
- `POST /classrooms`
- `GET /classrooms/{classroom_id}`
- `PATCH /classrooms/{classroom_id}`
- `DELETE /classrooms/{classroom_id}`

Enrollments
- `GET /enrollments`
- `POST /enrollments`
- `GET /enrollments/{enrollment_id}`
- `PATCH /enrollments/{enrollment_id}`
- `DELETE /enrollments/{enrollment_id}`

Assignments
- `GET /assignments`
- `POST /assignments`
- `GET /assignments/{assignment_id}`
- `PATCH /assignments/{assignment_id}`
- `DELETE /assignments/{assignment_id}`

Wallets
- `GET /wallets`
- `POST /wallets`
- `GET /wallets/{wallet_id}`
- `PATCH /wallets/{wallet_id}`
- `DELETE /wallets/{wallet_id}`

Buckets
- `GET /buckets`
- `POST /buckets`
- `GET /buckets/{bucket_id}`
- `PATCH /buckets/{bucket_id}`
- `DELETE /buckets/{bucket_id}`

Ledger entries
- `GET /ledger-entries`
- `POST /ledger-entries`
- `GET /ledger-entries/{entry_id}`
- `PATCH /ledger-entries/{entry_id}`
- `DELETE /ledger-entries/{entry_id}`

Budget submissions
- `GET /budget-submissions`
- `POST /budget-submissions`
- `GET /budget-submissions/{submission_id}`
- `PATCH /budget-submissions/{submission_id}`
- `DELETE /budget-submissions/{submission_id}`

Budget line items
- `GET /budget-line-items`
- `POST /budget-line-items`
- `GET /budget-line-items/{line_item_id}`
- `PATCH /budget-line-items/{line_item_id}`
- `DELETE /budget-line-items/{line_item_id}`

## Seed demo data

```bash
python scripts/seed_demo.py
```

Reset + seed (drops and recreates tables):

```bash
python scripts/seed_demo.py --reset
```

### Demo request script

```bash
bash scripts/demo_requests.sh
```

Environment overrides:

- `BASE_URL` (default `http://127.0.0.1:8000`)
- `EMAIL` (default `teacher@endowal.app`)
- `PASSWORD` (default `Teacher123!`)

### Seed overrides (optional)

You can customize the demo users without editing the script:

```bash
ENDOWAL_ADMIN_EMAIL="admin@yourdomain.com" \
ENDOWAL_ADMIN_PASSWORD="AdminPass123!" \
ENDOWAL_TEACHER_EMAIL="teacher@yourdomain.com" \
ENDOWAL_TEACHER_PASSWORD="TeacherPass123!" \
ENDOWAL_STUDENT_PASSWORD="StudentPass123!" \
ENDOWAL_STUDENT_EMAILS="s1@yourdomain.com,s2@yourdomain.com" \
ENDOWAL_STUDENT_NAMES="Taylor Kim,Jordan Lee" \
python scripts/seed_demo.py --reset
```

Defaults are used if any value is missing.
