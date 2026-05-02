# Project Context

This is a python project using fastapi with sqlalchemy.

The API has 10 routes. See .codesight/routes.md for the full route map with methods, paths, and tags.
The database has 2 models. See .codesight/schema.md for the full schema with fields, types, and relations.
The UI has 5 components. See .codesight/components.md for the full list with props.
Middleware includes: auth, custom.

High-impact files (most imported, changes here affect many other files):
- frontend/src/context/AuthContext.jsx (imported by 3 files)
- frontend/src/pages/LoginPage.jsx (imported by 1 files)
- frontend/src/pages/DashboardPage.jsx (imported by 1 files)
- frontend/src/pages/SettingsPage.jsx (imported by 1 files)
- frontend/src/App.jsx (imported by 1 files)
- /exchange_rate.py (imported by 1 files)

Required environment variables (no defaults):
- ACTUAL_BUDGET_ID (modules/config.py)
- ACTUAL_BUDGET_PASSWORD (modules/config.py)
- ACTUAL_PASSWORD (modules/config.py)
- ACTUAL_URL (modules/config.py)
- SECRET_KEY (auth.py)
- TCB_ACCOUNTS_MAPPING (modules/config.py)
- TCB_PASSWORD (modules/config.py)
- TCB_USERNAME (modules/config.py)

Read .codesight/wiki/index.md for orientation (WHERE things live). Then read actual source files before implementing. Wiki articles are navigation aids, not implementation guides.
Read .codesight/CODESIGHT.md for the complete AI context map including all routes, schema, components, libraries, config, middleware, and dependency graph.
