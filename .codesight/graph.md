# Dependency Graph

## Most Imported Files (change these carefully)

- `frontend/src/context/AuthContext.jsx` — imported by **3** files
- `frontend/src/pages/LoginPage.jsx` — imported by **1** files
- `frontend/src/pages/DashboardPage.jsx` — imported by **1** files
- `frontend/src/pages/SettingsPage.jsx` — imported by **1** files
- `frontend/src/App.jsx` — imported by **1** files
- `/exchange_rate.py` — imported by **1** files

## Import Map (who imports what)

- `frontend/src/context/AuthContext.jsx` ← `frontend/src/App.jsx`, `frontend/src/pages/DashboardPage.jsx`, `frontend/src/pages/LoginPage.jsx`
- `frontend/src/pages/LoginPage.jsx` ← `frontend/src/App.jsx`
- `frontend/src/pages/DashboardPage.jsx` ← `frontend/src/App.jsx`
- `frontend/src/pages/SettingsPage.jsx` ← `frontend/src/App.jsx`
- `frontend/src/App.jsx` ← `frontend/src/main.jsx`
- `/exchange_rate.py` ← `modules/convert.py`
