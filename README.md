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
