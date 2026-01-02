from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import os

from service import banking_service, AppStatus

app = FastAPI(title="Techcombank Sync")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from typing import List

class StatusResponse(BaseModel):
    status: AppStatus
    last_error: str
    logs: List[str]

@app.get("/api/status", response_model=StatusResponse)
def get_status():
    return StatusResponse(
        status=banking_service.status,
        last_error=banking_service.last_error,
        logs=banking_service.logs
    )

@app.post("/api/sync/start")
async def start_sync():
    try:
        await banking_service.start_sync()
        return {"message": "Sync started"}
    except Exception as e:
        # If it's just "already in progress", maybe return 200 or 409
        if "already in progress" in str(e):
             raise HTTPException(status_code=409, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/sync/stop")
async def stop_sync():
    await banking_service.stop_sync()
    return {"message": "Sync stopping..."}

async def generate_mjpeg_stream():
    while True:
        # Non-blocking check for latest screenshot
        screenshot = banking_service.get_latest_screenshot()
        if screenshot:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + screenshot + b'\r\n')
        else:
            # If no screenshot, just wait.
            # We could send a placeholder image here if desired.
            pass
        
        await asyncio.sleep(0.5) # 2 FPS

@app.get("/api/stream")
async def video_feed():
    return StreamingResponse(generate_mjpeg_stream(), media_type="multipart/x-mixed-replace; boundary=frame")

# Serve frontend static files
# We assume the frontend is built to /app/frontend/dist
if os.path.exists("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")
else:
    print("Frontend build not found at frontend/dist. API mode only.")

if __name__ == "__main__":
    import uvicorn
    # In async mode, one worker is standard for simple apps
    uvicorn.run(app, host="0.0.0.0", port=8000)
