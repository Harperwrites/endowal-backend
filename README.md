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
