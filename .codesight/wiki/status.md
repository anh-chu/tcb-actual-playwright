# Status

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Status subsystem handles **1 routes** and touches: auth, db.

## Routes

- `GET` `/api/status` → in: Use, out: StatusResponse [auth, db, upload]
  `app.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `app.py`

---
_Back to [overview.md](./overview.md)_