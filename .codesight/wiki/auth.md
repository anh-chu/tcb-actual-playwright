# Auth

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Auth subsystem handles **3 routes** and touches: auth, db.

## Routes

- `POST` `/register` → in: UserRegister, out: Token [auth, db]
  `routers/auth.py`
- `POST` `/token` → in: UserRegister, out: Token [auth, db]
  `routers/auth.py`
- `GET` `/me` → out: Token [auth, db]
  `routers/auth.py`

## Middleware

- **auth** (auth) — `auth.py`
- **auth** (auth) — `routers/auth.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `routers/auth.py`

---
_Back to [overview.md](./overview.md)_