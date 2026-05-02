# Database

> **Navigation aid.** Schema shapes and field types extracted via AST. Read the actual schema source files before writing migrations or query logic.

**sqlalchemy** — 2 models

### User

pk: `id` (integer)

- `id`: integer _(pk)_
- `username`: string
- `password_hash`: string

### Settings

pk: `id` (integer) · fk: user_id

- `id`: integer _(pk)_
- `user_id`: integer _(fk)_
- `tcb_username`: string
- `tcb_password_enc`: string
- `actual_url`: string
- `actual_password_enc`: string
- `actual_budget_id`: string
- `actual_budget_password_enc`: string
- `accounts_mapping`: string

## Schema Source Files

Search for ORM schema declarations:
- Drizzle: `pgTable` / `mysqlTable` / `sqliteTable`
- Prisma: `prisma/schema.prisma`
- TypeORM: `@Entity()` decorator
- SQLAlchemy: class inheriting `Base`

---
_Back to [overview.md](./overview.md)_