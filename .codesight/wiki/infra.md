# Infra

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Infra subsystem handles **2 routes** and touches: auth, db.

## Routes

- `GET` `/` → in: Use, out: SettingsSchema [auth, db]
  `routers/settings.py`
- `POST` `/` → in: SettingsSchema, out: SettingsSchema [auth, db]
  `routers/settings.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `routers/settings.py`

---
_Back to [overview.md](./overview.md)_