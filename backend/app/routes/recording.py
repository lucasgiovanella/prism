from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.models import CaptureRequest, CaptureResponse, ProcessStepRequest, ProcessStepResponse
from app.services import recorder, ollama
import asyncio
import queue
import threading
from pynput import mouse, keyboard
import time
import comtypes

router = APIRouter()

# --- Global State ---
is_recording = False
event_queue = queue.Queue()
typing_buffer = []
last_typed_time = 0

# --- Helper Functions ---

def process_typing_flush_sync():
    global typing_buffer
    if not typing_buffer:
        return
        
    text = "".join(typing_buffer)
    typing_buffer = []
    x, y = recorder.auto.GetCursorPos()
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(recorder.perform_capture(x, y, is_typing=True, typed_text=text))
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
            result = loop.run_until_complete(recorder.perform_capture(int(x), int(y)))
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

@router.post("/start-recording")
def start_recording():
    global is_recording
    is_recording = True
    return {"status": "started"}

@router.post("/stop-recording")
def stop_recording():
    global is_recording
    is_recording = False
    return {"status": "stopped"}

@router.get("/events")
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

@router.post("/capture", response_model=CaptureResponse)
async def manual_capture(req: CaptureRequest):
    return await recorder.perform_capture(req.x, req.y)

@router.post("/process-step", response_model=ProcessStepResponse)
async def process_step(req: ProcessStepRequest):
    """
    Process a captured step, refining generic descriptions with vision AI.
    """
    # Apply spotlight if not already applied
    processed_img = recorder.apply_spotlight(req.image_base64, req.bounding_box)
    
    final_desc = req.context or "Ação registrada."
    
    # SEMANTIC REFINEMENT: Detect generic Chromium fallback descriptions
    generic_patterns = ["Clicar no destaque", "Interface Visual", "Elemento Visual"]
    is_generic = any(pattern in final_desc for pattern in generic_patterns)
    
    if is_generic:
        print(f"[Semantic Refinement] Detected generic description: {final_desc}")
        # Use vision AI to extract functional text
        # Calculate center of the bounding box for smart cropping
        click_coords = None
        if req.bounding_box:
            # Bounding box is relative to the image (from recorder.py)
            cx = (req.bounding_box.left + req.bounding_box.right) // 2
            cy = (req.bounding_box.top + req.bounding_box.bottom) // 2
            click_coords = {'x': cx, 'y': cy}
            
        final_desc = await ollama.call_ollama_vision_ocr(req.image_base64, click_coords=click_coords)
        print(f"[Semantic Refinement] Refined to: {final_desc}")
    elif req.context:
        # Normal text refinement for non-generic descriptions
        final_desc = await ollama.call_ollama_text(
            f"Melhore esta instrução (seja direto): {req.context}"
        )

    return ProcessStepResponse(
        processed_image_base64=processed_img,
        final_description=final_desc
    )
