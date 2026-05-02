# Libraries

> **Navigation aid.** Library inventory extracted via AST. Read the source files listed here before modifying exported functions.

**12 library files** across 11 modules

## Routers (2 files)

- `routers/auth.py` — UserRegister, Token
- `routers/settings.py` — SettingsSchema

## Actual.py (1 files)

- `modules/actual.py` — init_actual, import_transactions

## App.py (1 files)

- `app.py` — on_startup, generate_mjpeg_stream, video_feed, StatusResponse

## Auth.py (1 files)

- `auth.py` — verify_password, get_password_hash, encrypt_value, decrypt_value, create_access_token

## Config.py (1 files)

- `modules/config.py` — get_config

## Convert.py (1 files)

- `modules/convert.py` — convert_to_actual_transaction, convert_to_actual_import

## Database.py (1 files)

- `database.py` — create_db_and_tables, get_session

## Exchange_rate.py (1 files)

- `modules/exchange_rate.py` — get_exchange_rate

## Logger.py (1 files)

- `modules/logger.py` — consoleHandler, fileHandler, Logger

## Models.py (1 files)

- `models.py` — User, Settings

## Service.py (1 files)

- `service.py` — AppStatus, ListHandler, BankingService

---
_Back to [overview.md](./overview.md)_