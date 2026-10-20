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

## Account balance integrity

Wallet balances are calculated from the full ledger (deposits minus withdrawals).
Opening funds are recorded as an opening deposit. Change balances through ledger
entries rather than patching a wallet balance. Amounts must be positive, finite,
and have at most two decimal places. Withdrawals and changes that would overdraw
an account are rejected. Writers are serialized per wallet. Classroom transfers
commit both entries together, and paired entries cannot be edited individually.

`GET /wallets/overview` returns authorized accounts with their calculated balances
and ten most recent entries from a single database query. The student Bank page
refreshes this snapshot every ten seconds and when the window regains focus.

Apply migrations before starting the updated API:

```bash
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m unittest discover -s tests -v
```

Existing wallets with ledger activity use that activity as the source of truth.
Existing nonzero balances without any ledger activity are preserved as opening
entries by migration `0002_ledger_balances`.

## Full classroom workflow demo

```bash
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m scripts.seed_workflow
```

The workflow seed adds data without resetting existing records and can be rerun.
It provides two teachers, eight students, four demo classrooms, assignments,
wallet activity, sample text submissions, grades, and classroom conversations.
Demo due dates use `ENDOWAL_DEMO_DATE` (default `2026-10-19`) as a baseline.

- `teacher@endowal.app` and `teacher2@endowal.app`: `Teacher123!`
- `student1@endowal.app` through `student8@endowal.app`: `Student123!`

Open Classrooms to select a classroom. Students can turn in text responses on
Assignments. Teachers can expand submissions or click a student to open a
read-only dashboard scoped to that classroom, and use Grades to record results.
The floating Messages button opens human-to-human teacher/student chat, persisted
in the database. Open conversations poll every four seconds; unread counts poll
every ten seconds. The widget shows the newest 200 messages per conversation.

## Remembered sign-in and dashboard

Sign-in sets a persistent 30-day HttpOnly session cookie; the database stores only
its SHA-256 token hash. Access tokens remain short-lived and the frontend renews
them through `/auth/refresh` when needed. `/auth/logout` revokes the remembered
session and clears its cookie. Existing signed-in browsers can upgrade through
`/auth/remember` without entering their password again. HTTP localhost cookies
work for development; HTTPS cookies use Secure. Frontend API calls include
credentials and CORS permits the two configured local frontend origins.

The login form remembers the last email and supports browser password-manager
autofill. Passwords are never saved in frontend local storage.

`GET /dashboard/summary` returns role-scoped balances, recent activity, current
classroom assignments, submission/grade totals, and teacher review counts. The
live dashboard polls every 15 seconds. Bank preview visibility and amount masking
are stored per user on the browser, alongside existing credit-lesson progress.

## Student assignment banking

Students can record simulated deposits and expenses from Bank. The assignment is
required and must be open in the selected account’s classroom; the student must
own that account and have an active enrollment. `/wallets/{id}/assignments`
provides the classroom assignment picker. `/wallets/{id}/transactions` records
student activity with a forced `student_action` source and a required UUID
`request_id`; retries with the same contents return the existing entry.

Assignment titles appear in Bank activity, teacher statements, and dashboard
previews. The assignment page links to Bank with its classroom and assignment
preselected. Student expenses use the existing locked balance checks and cannot
overdraft an account. Students cannot edit or delete ledger history.
