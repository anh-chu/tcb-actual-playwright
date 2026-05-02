# Routes

- `GET` `/api/status` params() → in: Use, out: StatusResponse [auth, db, upload]
- `POST` `/api/sync/start` params() → out: StatusResponse [auth, db, upload]
- `POST` `/api/sync/stop` params() → out: StatusResponse [auth, db, upload]
- `GET` `/api/stream` params() → in: Use, out: StatusResponse [auth, db, upload]
- `GET` `/{full_path:path}` params(path) → in: Use, out: StatusResponse [auth, db, upload]
- `POST` `/register` params() → in: UserRegister, out: Token [auth, db]
- `POST` `/token` params() → in: UserRegister, out: Token [auth, db]
- `GET` `/me` params() → out: Token [auth, db]
- `GET` `/` params() → in: Use, out: SettingsSchema [auth, db]
- `POST` `/` params() → in: SettingsSchema, out: SettingsSchema [auth, db]
