from typing import Optional
from sqlmodel import Field, SQLModel

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str

class Settings(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    
    # Techcombank Credentials
    tcb_username: str
    tcb_password_enc: str # Encrypted
    
    # Actual Credentials
    actual_url: str
    actual_password_enc: str # Encrypted
    actual_budget_id: str
    actual_budget_password_enc: Optional[str] = None # Encrypted, optional
    
    # Mappings (JSON string)
    accounts_mapping: str = "{}"
