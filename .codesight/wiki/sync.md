# Sync

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Sync subsystem handles **2 routes** and touches: auth, db.

## Routes

- `POST` `/api/sync/start` → out: StatusResponse [auth, db, upload]
  `app.py`
- `POST` `/api/sync/stop` → out: StatusResponse [auth, db, upload]
  `app.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `app.py`

---
_Back to [overview.md](./overview.md)_