import os
import requests
from huggingface_hub import hf_hub_download
from typing import List, Dict, Optional
import threading
import time

# Directory to store models
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")
os.makedirs(MODELS_DIR, exist_ok=True)

# Supported Models Configuration
SUPPORTED_MODELS = [
    {
        "id": "llava-v1.5-7b",
        "name": "LLaVA v1.5 7B (GGUF)",
        "repo_id": "mys/ggml_llava-v1.5-7b",
        "filename": "ggml-model-q4_k.gguf",
        "mmproj": "mmproj-model-f16.gguf", # Projector file needed for LLaVA
        "description": "Good balance of speed and quality. Requires ~8GB RAM.",
        "size": "4.08 GB"
    },
    # NOTE: Llama 3.2 Vision uses 'mllama' architecture which requires llama.cpp with mllama support
    # Current llama-cpp-python version may not support this yet
    # Uncomment when llama-cpp-python is updated with mllama support
    # {
    #     "id": "llama-3.2-11b-vision",
    #     "name": "Llama 3.2 11B Vision (GGUF) - NOT SUPPORTED YET",
    #     "repo_id": "leafspark/Llama-3.2-11B-Vision-Instruct-GGUF", 
    #     "filename": "Llama-3.2-11B-Vision-Instruct.Q4_K_M.gguf",
    #     "mmproj": "Llama-3.2-11B-Vision-Instruct-mmproj.f16.gguf",
    #     "description": "Requires llama.cpp with mllama architecture support",
    #     "size": "7.9 GB (5.96 GB model + 1.94 GB projector)"
    # }
]

# Download State
download_status = {
    "model_id": None,
    "progress": 0,
    "status": "idle", # idle, downloading, error, completed
    "error": None
}

def get_models_status() -> List[Dict]:
    """
    Returns list of supported models with their local availability status.
    """
    results = []
    for model in SUPPORTED_MODELS:
        path = os.path.join(MODELS_DIR, model["filename"])
        is_downloaded = os.path.exists(path)
        
        # Check projector if needed
        if model.get("mmproj"):
            proj_path = os.path.join(MODELS_DIR, model["mmproj"])
            if not os.path.exists(proj_path):
                is_downloaded = False
                
        results.append({
            **model,
            "downloaded": is_downloaded,
            "local_path": path if is_downloaded else None
        })
    return results

def download_file_thread(repo_id, filename, local_dir, is_last_file=True):
    global download_status
    try:
        download_status["status"] = "downloading"
        download_status["progress"] = 0
        
        print(f"Starting download: {repo_id}/{filename}")
        
        # Simulate progress in a separate thread since hf_hub_download is blocking
        stop_progress = False
        
        def simulate_progress():
            current = 0
            while not stop_progress and current < 95:
                # Slow down as we get closer to 95%
                step = 5 if current < 50 else (2 if current < 80 else 0.5)
                current += step
                download_status["progress"] = current
                time.sleep(0.5)
                
        progress_thread = threading.Thread(target=simulate_progress)
        progress_thread.start()
        
        try:
            hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=local_dir,
                local_dir_use_symlinks=False
            )
        finally:
            stop_progress = True
            progress_thread.join()
        
        if is_last_file:
            download_status["progress"] = 100
            download_status["status"] = "completed"
            print(f"Download completed: {filename} (All files finished)")
        else:
            print(f"Download completed: {filename} (Proceeding to next file...)")
            # Keep status as 'downloading' for the next file
        
    except Exception as e:
        print(f"Download error: {e}")
        download_status["status"] = "error"
        download_status["error"] = str(e)

def start_download(model_id: str):
    global download_status
    
    if download_status["status"] == "downloading":
        return {"error": "Download already in progress"}
    
    model = next((m for m in SUPPORTED_MODELS if m["id"] == model_id), None)
    if not model:
        return {"error": "Model not found"}
        
    download_status["model_id"] = model_id
    download_status["error"] = None
    
    # Start thread
    def run_download():
        # Download projector first if needed
        if model.get("mmproj"):
            # Pass is_last_file=False so it doesn't mark as completed yet
            download_file_thread(model["repo_id"], model["mmproj"], MODELS_DIR, is_last_file=False)
            if download_status["status"] == "error": return
            
            # Reset for next file
            time.sleep(1)
            
        # Download main model (is_last_file=True by default)
        download_file_thread(model["repo_id"], model["filename"], MODELS_DIR, is_last_file=True)
        
    thread = threading.Thread(target=run_download)
    thread.start()
    
    return {"status": "started"}

def get_current_download_progress():
    return download_status
