from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional

from database import get_session
from models import User, Settings
from auth import get_current_user, encrypt_value, decrypt_value

router = APIRouter(prefix="/api/settings", tags=["settings"])

class SettingsSchema(BaseModel):
    tcb_username: str
    tcb_password: str
    actual_url: str
    actual_password: str
    actual_budget_id: str
    actual_budget_password: Optional[str] = None
    accounts_mapping: str = "{}"

@router.get("/", response_model=SettingsSchema)
def get_settings(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    settings_db = session.exec(select(Settings).where(Settings.user_id == current_user.id)).first()
    if not settings_db:
        # Return empty/default
        return {
            "tcb_username": "",
            "tcb_password": "",
            "actual_url": "",
            "actual_password": "",
            "actual_budget_id": "",
            "actual_budget_password": "",
            "accounts_mapping": "{}"
        }
    
    # Decrypt
    return {
        "tcb_username": settings_db.tcb_username,
        "tcb_password": decrypt_value(settings_db.tcb_password_enc),
        "actual_url": settings_db.actual_url,
        "actual_password": decrypt_value(settings_db.actual_password_enc),
        "actual_budget_id": settings_db.actual_budget_id,
        "actual_budget_password": decrypt_value(settings_db.actual_budget_password_enc) if settings_db.actual_budget_password_enc else "",
        "accounts_mapping": settings_db.accounts_mapping
    }

@router.post("/")
def save_settings(settings: SettingsSchema, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    settings_db = session.exec(select(Settings).where(Settings.user_id == current_user.id)).first()
    
    # Encrypt
    tcb_enc = encrypt_value(settings.tcb_password)
    act_pass_enc = encrypt_value(settings.actual_password)
    act_bud_pass_enc = encrypt_value(settings.actual_budget_password) if settings.actual_budget_password else None
    
    if not settings_db:
        settings_db = Settings(
            user_id=current_user.id,
            tcb_username=settings.tcb_username,
            tcb_password_enc=tcb_enc,
            actual_url=settings.actual_url,
            actual_password_enc=act_pass_enc,
            actual_budget_id=settings.actual_budget_id,
            actual_budget_password_enc=act_bud_pass_enc,
            accounts_mapping=settings.accounts_mapping
        )
        session.add(settings_db)
    else:
        settings_db.tcb_username = settings.tcb_username
        settings_db.tcb_password_enc = tcb_enc
        settings_db.actual_url = settings.actual_url
        settings_db.actual_password_enc = act_pass_enc
        settings_db.actual_budget_id = settings.actual_budget_id
        settings_db.actual_budget_password_enc = act_bud_pass_enc
        settings_db.accounts_mapping = settings.accounts_mapping
        session.add(settings_db)
        
    session.commit()
    return {"message": "Settings saved"}
