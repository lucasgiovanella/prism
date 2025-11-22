import sys
import ctypes
import base64
import asyncio
import threading
import uiautomation as auto
import mss
import cv2
import numpy as np
import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, List
from pynput import mouse, keyboard
import json
import queue
import uuid
import time
import comtypes
import database

# --- DPI Awareness ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception as e:
    print(f"Warning: Could not set DPI awareness: {e}", file=sys.stderr)

app = FastAPI(title="DocGen AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---

class CaptureRequest(BaseModel):
    x: int
    y: int

class CaptureResponse(BaseModel):
    id: str
    element_name: str
    description: str
    screenshot_base64: str
    bounding_box: Dict[str, int]
    element_type: str

class ProcessStepRequest(BaseModel):
    image_base64: str
    bounding_box: Dict[str, int]
    context: Optional[str] = None

class ProcessStepResponse(BaseModel):
    processed_image_base64: str
    final_description: str

# --- Global State ---
is_recording = False
event_queue = queue.Queue()
typing_buffer = []
last_typed_time = 0

# --- Constants ---
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL_TEXT = "llama3"
OLLAMA_MODEL_VISION = "llava"

# --- Helper Functions ---

def get_screenshot_with_offset(bbox: Dict[str, int], padding: int = 150):
    with mss.mss() as sct:
        # Determine the region to capture (bbox + padding)
        
        # We need to find the monitor that contains the center of the bbox
        cx = (bbox["left"] + bbox["right"]) // 2
        cy = (bbox["top"] + bbox["bottom"]) // 2
        
        monitor_idx = 1 # Default to primary
        for i, m in enumerate(sct.monitors[1:], 1):
             if (cx >= m["left"] and cx < m["left"] + m["width"] and
                 cy >= m["top"] and cy < m["top"] + m["height"]):
                 monitor_idx = i
                 break
        
        monitor = sct.monitors[monitor_idx]
        
        # Calculate padded coordinates
        left = max(monitor["left"], bbox["left"] - padding)
        top = max(monitor["top"], bbox["top"] - padding)
        right = min(monitor["left"] + monitor["width"], bbox["right"] + padding)
        bottom = min(monitor["top"] + monitor["height"], bbox["bottom"] + padding)
        
        width = right - left
        height = bottom - top
        
        region = {
            "top": top,
            "left": left,
            "width": width,
            "height": height
        }

        try:
            sct_img = sct.grab(region)
            img_np = np.array(sct_img)
            
            _, buffer = cv2.imencode(".png", img_np)
            b64 = base64.b64encode(buffer).decode("utf-8")
            return b64, {"left": left, "top": top}
        except Exception as e:
            print(f"Screenshot error: {e}")
            return "", {"left": 0, "top": 0}

def validate_geometry(control, x: int, y: int) -> bool:
    try:
        rect = control.BoundingRectangle
        margin = 5
        if (rect.left - margin <= x <= rect.right + margin) and \
           (rect.top - margin <= y <= rect.bottom + margin):
            return True
        return False
    except Exception:
        return False

def apply_spotlight(image_b64: str, bbox: Dict[str, int]) -> str:
    try:
        img_data = base64.b64decode(image_b64)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None: return image_b64
        
        # Draw border
        border_color = (0, 0, 255) # Red for visibility
        thickness = 3
        
        # Draw rectangle. Bbox is assumed to be relative to the image now.
        cv2.rectangle(img, (bbox["left"], bbox["top"]), (bbox["right"], bbox["bottom"]), border_color, thickness)
        
        _, buffer = cv2.imencode(".png", img)
        return base64.b64encode(buffer).decode("utf-8")
    except Exception as e:
        print(f"Spotlight error: {e}")
        return image_b64

async def call_ollama_vision(image_b64: str) -> str:
    try:
        payload = {
            "model": OLLAMA_MODEL_VISION,
            "prompt": "Descreva este elemento de interface UI brevemente em PT-BR.",
            "images": [image_b64],
            "stream": False
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(OLLAMA_URL, json=payload, timeout=10.0)
            if resp.status_code == 200:
                return resp.json().get("response", "Elemento Visual").strip()
    except:
        pass
    return "Elemento Visual"

async def call_ollama_text(prompt: str) -> str:
    try:
        payload = {
            "model": OLLAMA_MODEL_TEXT,
            "prompt": prompt,
            "stream": False
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(OLLAMA_URL, json=payload, timeout=10.0)
            if resp.status_code == 200:
                return resp.json().get("response", "").strip()
    except:
        pass
    return ""

async def perform_capture(x: int, y: int, is_typing: bool = False, typed_text: str = "") -> CaptureResponse:
    try:
        if is_typing:
             control = auto.GetFocusedControl()
        else:
            control = auto.ControlFromPoint(x, y)
            if not validate_geometry(control, x, y):
                control = None
    except:
        control = None

    element_name = ""
    description = ""
    element_type = "Unknown"
    rect = None
    
    if control:
        element_name = control.Name
        element_type = control.ControlTypeName
        rect = control.BoundingRectangle
    
    # Fallback rect if control not found
    if not rect:
        if x == 0 and y == 0: # Typing case with no control
             rect = type('obj', (object,), {'left': 0, 'top': 0, 'right': 100, 'bottom': 100})
        else:
             rect = type('obj', (object,), {
                 'left': x - 25, 'top': y - 25, 
                 'right': x + 25, 'bottom': y + 25
             })
    
    bbox = {"left": rect.left, "top": rect.top, "right": rect.right, "bottom": rect.bottom}
    
    # Capture with padding
    screenshot_b64, offset = get_screenshot_with_offset(bbox, padding=150)
    
    # Convert bbox to relative coordinates for the frontend/spotlight
    relative_bbox = {
        "left": bbox["left"] - offset["left"],
        "top": bbox["top"] - offset["top"],
        "right": bbox["right"] - offset["left"],
        "bottom": bbox["bottom"] - offset["top"]
    }
    
    # Apply spotlight immediately so it is visible in the UI
    screenshot_b64 = apply_spotlight(screenshot_b64, relative_bbox)
    
    if is_typing:
        target = element_name if element_name else "Campo de texto"
        description = f"Digitar '{typed_text}' em '{target}'"
    elif element_name:
        description = f"Clique em '{element_name}'"
    else:
        description = "Clique neste local"

    return CaptureResponse(
        id=str(uuid.uuid4()),
        element_name=element_name,
        description=description,
        screenshot_base64=screenshot_b64,
        bounding_box=relative_bbox,
        element_type=element_type
    )

async def flush_typing_buffer():
    global typing_buffer
    if not typing_buffer:
        return
    
    text = "".join(typing_buffer)
    typing_buffer = []
    
    x, y = auto.GetCursorPos()
    
    try:
        loop = asyncio.get_event_loop()
    except:
        pass
        
    result = await perform_capture(x, y, is_typing=True, typed_text=text)
    event_queue.put(result)

def process_typing_flush_sync():
    global typing_buffer
    if not typing_buffer:
        return
        
    text = "".join(typing_buffer)
    typing_buffer = []
    x, y = auto.GetCursorPos()
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(perform_capture(x, y, is_typing=True, typed_text=text))
        loop.close()
        event_queue.put(result)
    except Exception as e:
        print(f"Typing flush error: {e}")

# --- Hook Logic ---
def on_click(x, y, button, pressed):
    global is_recording
    if not is_recording:
        return
    
    if pressed and button == mouse.Button.left:
        try:
            comtypes.CoInitialize()
        except:
            pass

        try:
            # 1. Check if we need to flush typing
            process_typing_flush_sync()

            # 2. Basic capture (sync parts)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(perform_capture(int(x), int(y)))
            loop.close()
            
            # Push to SSE queue
            event_queue.put(result)
        except Exception as e:
            print(f"Hook error: {e}")
        finally:
            try:
                comtypes.CoUninitialize()
            except:
                pass

def on_press(key):
    global is_recording, typing_buffer, last_typed_time
    if not is_recording:
        return

    try:
        char = ""
        if hasattr(key, 'char') and key.char:
            char = key.char
        elif key == keyboard.Key.space:
            char = " "
        elif key == keyboard.Key.enter:
            # Flush
            process_typing_flush_sync()
            return
        elif key == keyboard.Key.tab:
            # Flush
            process_typing_flush_sync()
            return
        elif key == keyboard.Key.backspace:
            if typing_buffer:
                typing_buffer.pop()
            return
        
        # Ignore other special keys for text content, but maybe we want to capture them?
        if char:
            typing_buffer.append(char)
            last_typed_time = time.time()
            
    except Exception as e:
        print(f"Key error: {e}")

# Start Listeners
# We need non-blocking listeners
keyboard_listener = keyboard.Listener(on_press=on_press)
mouse_listener = mouse.Listener(on_click=on_click)

keyboard_listener.start()
mouse_listener.start()

# --- Endpoints ---

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/start-recording")
def start_recording():
    global is_recording
    is_recording = True
    return {"status": "started"}

@app.post("/stop-recording")
def stop_recording():
    global is_recording
    is_recording = False
    return {"status": "stopped"}

@app.get("/events")
async def event_stream(request: Request):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            
            try:
                # Non-blocking get
                item = event_queue.get_nowait()
                yield f"data: {item.model_dump_json()}\n\n"
            except queue.Empty:
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"Stream error: {e}")
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/capture", response_model=CaptureResponse)
async def manual_capture(req: CaptureRequest):
    return await perform_capture(req.x, req.y)

@app.post("/process-step", response_model=ProcessStepResponse)
async def process_step(req: ProcessStepRequest):
    processed_img = apply_spotlight(req.image_base64, req.bounding_box)
    
    final_desc = "Passo processado." 
    if req.context:
        final_desc = await call_ollama_text(f"Melhore esta instrução (seja direto): {req.context}")
    else:
        final_desc = "Ação registrada."

    return ProcessStepResponse(
        processed_image_base64=processed_img,
        final_description=final_desc
    )

# --- Tutorial Management Endpoints ---

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "online", "message": "DocGen AI Backend is running"}

@app.post("/tutorials")
async def create_tutorial_endpoint(request: Request):
    """Create a new tutorial."""
    data = await request.json()
    title = data.get('title', 'Untitled Tutorial')
    steps = data.get('steps', [])
    
    tutorial_id = database.create_tutorial(title, steps)
    return {"id": tutorial_id, "message": "Tutorial created successfully"}

@app.get("/tutorials")
async def get_tutorials():
    """Get recent tutorials."""
    tutorials = database.get_recent_tutorials(limit=10)
    return {"tutorials": tutorials}

@app.get("/tutorials/{tutorial_id}")
async def get_tutorial_endpoint(tutorial_id: str):
    """Get a specific tutorial."""
    tutorial = database.get_tutorial(tutorial_id)
    if not tutorial:
        return {"error": "Tutorial not found"}, 404
    return tutorial

@app.put("/tutorials/{tutorial_id}")
async def update_tutorial_endpoint(tutorial_id: str, request: Request):
    """Update an existing tutorial."""
    data = await request.json()
    title = data.get('title', 'Untitled Tutorial')
    steps = data.get('steps', [])
    
    success = database.update_tutorial(tutorial_id, title, steps)
    if success:
        return {"message": "Tutorial updated successfully"}
    return {"error": "Failed to update tutorial"}, 500

@app.delete("/tutorials/{tutorial_id}")
async def delete_tutorial_endpoint(tutorial_id: str):
    """Delete a tutorial."""
    success = database.delete_tutorial(tutorial_id)
    if success:
        return {"message": "Tutorial deleted successfully"}
    return {"error": "Failed to delete tutorial"}, 500

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
