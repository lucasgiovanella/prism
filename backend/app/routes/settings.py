from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services import model_manager, llm_engine

router = APIRouter()

class DownloadRequest(BaseModel):
    model_id: str

class LoadModelRequest(BaseModel):
    model_id: str

@router.get("/models")
def list_models():
    """List available models and their status"""
    return model_manager.get_models_status()

@router.post("/models/download")
def download_model(req: DownloadRequest):
    """Start downloading a model"""
    result = model_manager.start_download(req.model_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.get("/models/progress")
def get_progress():
    """Get current download progress"""
    return model_manager.get_current_download_progress()

@router.post("/models/load")
def load_model(req: LoadModelRequest):
    """Load a model into memory for inference"""
    try:
        llm_engine.engine.load_model(req.model_id)
        return {"status": "loaded", "model_id": req.model_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
