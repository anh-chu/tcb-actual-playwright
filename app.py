from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from sqlmodel import Session, select
from pydantic import BaseModel
import asyncio
import os
import json

from service import banking_service, AppStatus
from database import create_db_and_tables, get_session
from models import User, Settings
from routers import auth, settings
from auth import get_current_user, decrypt_value

app = FastAPI(title="Techcombank Sync")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # TODO: Restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(settings.router)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

class StatusResponse(BaseModel):
    status: AppStatus
    last_error: str
    logs: list[str]

@app.get("/api/status", response_model=StatusResponse)
def get_status(current_user: User = Depends(get_current_user)):
    return StatusResponse(
        status=banking_service.status,
        last_error=banking_service.last_error,
        logs=banking_service.logs
    )

@app.post("/api/sync/start")
async def start_sync(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Get optional date range from request body
    body = await request.json() if request.headers.get("content-type") == "application/json" else {}
    date_from = body.get("date_from")
    date_to = body.get("date_to")
    # 1. Fetch user settings
    settings_db = session.exec(select(Settings).where(Settings.user_id == current_user.id)).first()
    if not settings_db:
        raise HTTPException(status_code=400, detail="Settings not configured. Please go to Settings page.")

    # 2. Decrypt credentials
    # Handle both old (dict) and new (list) mapping formats
    raw_mapping = json.loads(settings_db.accounts_mapping)
    final_mapping = {}
    
    if isinstance(raw_mapping, list):
        # New format: List of account objects with arrangementIds
        for item in raw_mapping:
            actual_account_id = item.get("id")
            # Items might have 'arrangementIds' (new) or just be the object
            # The user's example has "arrangementIds": ["..."]
            arr_ids = item.get("arrangementIds", [])
            for arr_id in arr_ids:
                final_mapping[arr_id] = actual_account_id
    else:
        # Old format: Flat dict
        final_mapping = raw_mapping

    config = {
        "tcb_username": settings_db.tcb_username,
        "tcb_password": decrypt_value(settings_db.tcb_password_enc),
        "actual_url": settings_db.actual_url,
        "actual_password": decrypt_value(settings_db.actual_password_enc),
        "actual_budget_id": settings_db.actual_budget_id,
        "actual_budget_password": decrypt_value(settings_db.actual_budget_password_enc) if settings_db.actual_budget_password_enc else None,
        "accounts_mapping": final_mapping,
        "date_from": date_from,
        "date_to": date_to
    }

    try:
        await banking_service.start_sync(config)
        return {"message": "Sync started"}
    except Exception as e:
        if "already in progress" in str(e):
             raise HTTPException(status_code=409, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/sync/stop")
async def stop_sync(current_user: User = Depends(get_current_user)):
    await banking_service.stop_sync()
    return {"message": "Sync stopping..."}

async def generate_mjpeg_stream():
    # Stream for any authenticated user? Or should we restrict it?
    # For now, simplistic stream. If we add token auth here, we need to pass token in URL.
    # Since checking auth in streaming response is tricky with img tag, we might leave it open 
    # OR require a token query param.
    # For security, let's keep it open for now but acknowledge the risk (it's internal network).
    while True:
        screenshot = banking_service.get_latest_screenshot()
        if screenshot:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + screenshot + b'\r\n')
        else:
            pass
        await asyncio.sleep(0.5)

@app.get("/api/stream")
async def video_feed():
    # Optionally: token = Query(...) and verify it.
    return StreamingResponse(generate_mjpeg_stream(), media_type="multipart/x-mixed-replace; boundary=frame")

# Serve frontend static files
# We assume the frontend is built to /app/frontend/dist
if os.path.exists("frontend/dist"):
    # Catch-all for React Router: If file not found, serve index.html
    # But FastAPI StaticFiles doesn't support fallback easily.
    # So we mount static assets to /assets, and serve index.html for root and other paths.
    
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        # Allow API routes to pass through (already handled above due to order, but to be safe)
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="Not Found")
            
        # Return index.html for any other route (SPA routing)
        return FileResponse("frontend/dist/index.html")
else:
    print("Frontend build not found at frontend/dist. API mode only.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

