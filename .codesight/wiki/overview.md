# tcb-actual-playwright — Overview

> **Navigation aid.** This article shows WHERE things live (routes, models, files). Read actual source files before implementing new features or making changes.

**tcb-actual-playwright** is a python project built with fastapi, using sqlalchemy for data persistence.

## Scale

10 API routes · 2 database models · 5 UI components · 12 library files · 3 middleware layers · 8 environment variables

## Subsystems

- **[Auth](./auth.md)** — 3 routes — touches: auth, db
- **[Status](./status.md)** — 1 routes — touches: auth, db, upload
- **[Stream](./stream.md)** — 1 routes — touches: auth, db, upload
- **[Sync](./sync.md)** — 2 routes — touches: auth, db, upload
- **[Infra](./infra.md)** — 2 routes — touches: auth, db
- **[Api](./api.md)** — 1 routes — touches: auth, db, upload

**Database:** sqlalchemy, 2 models — see [database.md](./database.md)

**UI:** 5 components (react) — see [ui.md](./ui.md)

**Libraries:** 12 files — see [libraries.md](./libraries.md)

## High-Impact Files

Changes to these files have the widest blast radius across the codebase:

- `frontend/src/context/AuthContext.jsx` — imported by **3** files
- `frontend/src/pages/LoginPage.jsx` — imported by **1** files
- `frontend/src/pages/DashboardPage.jsx` — imported by **1** files
- `frontend/src/pages/SettingsPage.jsx` — imported by **1** files
- `frontend/src/App.jsx` — imported by **1** files
- `/exchange_rate.py` — imported by **1** files

## Required Environment Variables

- `ACTUAL_BUDGET_ID` — `modules/config.py`
- `ACTUAL_BUDGET_PASSWORD` — `modules/config.py`
- `ACTUAL_PASSWORD` — `modules/config.py`
- `ACTUAL_URL` — `modules/config.py`
- `SECRET_KEY` — `auth.py`
- `TCB_ACCOUNTS_MAPPING` — `modules/config.py`
- `TCB_PASSWORD` — `modules/config.py`
- `TCB_USERNAME` — `modules/config.py`

---
_Back to [index.md](./index.md) · Generated 2026-05-02_