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
