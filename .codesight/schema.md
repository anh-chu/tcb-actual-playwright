# Schema

### User
- id: integer (pk)
- username: string
- password_hash: string

### Settings
- id: integer (pk)
- user_id: integer (fk)
- tcb_username: string
- tcb_password_enc: string
- actual_url: string
- actual_password_enc: string
- actual_budget_id: string
- actual_budget_password_enc: string
- accounts_mapping: string
