# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Diablo supports UC Berkeley's Course Capture service. It schedules and manages lecture recordings via Kaltura, syncing with SIS (Student Information System) course data and notifying instructors by email.

## Commands

```bash
# Run all tests and linters in parallel
tox -p

# Run pytest only
tox -e test

# Run a specific test file or directory
tox -e test -- tests/test_models/test_foo.py
tox -e test -- tests/test_jobs/

# Python linter (Ruff)
tox -e lint-py

# Vue/TS linter (ESLint)
tox -e lint-vue

# Auto-fix Vue/TS lint errors
tox -e lint-vue-fix

# Lint specific Python files
tox -e lint-py -- scripts/foo.py

# Build Vue frontend
tox -e build-vue  # or: npm run build-vue

# Run Vue dev server (port 8080)
npm run serve-vue

# Run Flask backend (port 5000)
python application.py

# Initialize DB schema
export FLASK_APP=application.py
flask initdb

# Interactive console with Flask app context
python -i consoler.py
```

## Architecture

### Backend (Flask + PostgreSQL)

The Flask app is in `diablo/` and follows a layered architecture:

- **`diablo/api/`** — REST controllers (one per resource). All routes are `/api/*`.
- **`diablo/merged/`** — Business logic that aggregates externals with caching: `calnet.py` (user lookup with `@cachify`) and `emailer.py` (email composition/dispatch).
- **`diablo/externals/`** — Raw integrations: `kaltura.py`, `canvas.py`, `calnet.py` (LDAP), `loch.py` (SIS via dblink), `rds.py`, `s3.py`, `b_connected.py` (SMTP).
- **`diablo/models/`** — SQLAlchemy models. `sis_section.py` is the central model representing a course section.
- **`diablo/jobs/`** — Background jobs inheriting from `BaseJob`. Job schedules are stored in the `jobs` DB table and loaded at app startup by `BackgroundJobManager`.
- **`diablo/lib/`** — Pure utilities: `berkeley.py` (term/date calculations), `kaltura_util.py`, `db.py`, etc.
- **`config/`** — Layered config: `default.py` → `{DIABLO_ENV}.py` → `{DIABLO_LOCAL_CONFIGS}/{DIABLO_ENV}-local.py`. Sensitive values go in the local file (outside the repo). `DIABLO_ENV` defaults to `development`.

### Frontend (Vue 3 + TypeScript)

SPA using Vue 3, Vuetify 3, Pinia, and vue-router. Source lives in `src/`.

- **`src/views/`** — Page-level components. Admin routes (Ouija board, Jobs, Rooms, Email Templates, Blackouts) require admin role; course/home views require instructor role.
- **`src/stores/`** — Pinia stores: `context.ts` (current user/session), `course.ts`, `ouija.ts`.
- **`src/api/`** — Axios API client wrappers.
- **`src/router.ts`** — Route guards call `requiresAdmin` or `requiresInstructor` from `src/auth.ts`.

In development, Vue runs at `http://localhost:8080` (via `npm run serve-vue`) and Flask at port 5000. Flask returns CORS headers in development mode to allow cross-origin requests. In production/staging, Flask serves `dist/static/index.html` for all non-API routes.

### Key patterns

**DB commits** — Always call `std_commit()` (from `diablo/__init__.py`) instead of `db.session.commit()`. In test mode, `std_commit()` only flushes; it never actually commits, keeping test transactions isolated.

**Test fixtures** — External service calls (CalNet, Canvas, Kaltura, Loch/Nessie) are replaced by JSON files under `fixtures/{calnet,canvas,kaltura,loch_ness,sis}/` when `DIABLO_ENV == 'test'`. External modules check this env var directly or use the `@skip_when_pytest` decorator.

**Caching** — Use the `@cachify(key_pattern, timeout)` decorator (from `diablo/__init__.py`) for functions that should be cached in Flask-Cache. Key patterns can reference function argument names using `{arg_name}` syntax.

**Background jobs** — New jobs must inherit `BaseJob`, implement `_run()` and `description()`, and be imported in `diablo/factory.py`'s `_register_jobs()`. Schedule configuration is managed via the admin UI and stored in the DB.

**Authentication** — CAS (UC Berkeley) in production. Development uses `DEV_AUTH_ENABLED = True` + `DEV_AUTH_PASSWORD` for the `/api/auth/dev_auth_login` bypass. Tests use the `fake_auth` pytest fixture.

### E2E tests (Xena)

Selenium-based browser tests live in `xena/`. Run interactively via `./xena/xena.sh`, which prompts for browser (Chrome/Firefox), headless mode, test filter, and credentials. Requires chromedriver or geckodriver installed separately.
