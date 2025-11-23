import sys
import ctypes
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import health, tutorials, recording

# --- DPI Awareness ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception as e:
    print(f"Warning: Could not set DPI awareness: {e}", file=sys.stderr)

app = FastAPI(title="Prism AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health.router)
app.include_router(tutorials.router)
app.include_router(recording.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
