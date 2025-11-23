import uiautomation as auto
import mss
import cv2
import numpy as np
import base64
import uuid
from typing import Dict, Optional
from app.models import CaptureResponse

# --- Constants for Chromium Detection ---
CHROMIUM_BLIND_CLASSES = [
    "Chrome_RenderWidgetHostHWND",
    "Chrome_WidgetWin_0",
    "Chrome_WidgetWin_1",
    "Intermediate D3D Window",
    "Chrome Legacy Window"
]

# Size threshold for detecting oversized controls (likely container)
MAX_CONTROL_WIDTH = 500

def is_chromium_blind_window(control) -> bool:
    """
    Detect if a control is from a Chromium-based app where accessibility API
    cannot see individual UI elements (returns only a large container).
    """
    try:
        class_name = control.ClassName
        
        # Check if it's a known blind window class
        if class_name not in CHROMIUM_BLIND_CLASSES:
            return False
        
        # Sanity check: if the control is very wide, it's likely the whole window
        rect = control.BoundingRectangle
        width = rect.right - rect.left
        
        if width > MAX_CONTROL_WIDTH:
            return True
            
        return False
    except Exception as e:
        return False

def get_smart_bbox(x: int, y: int) -> dict:
    """
    Uses OpenCV to find the smallest enclosing contour around the click point (x, y).
    """
    try:
        # Capture a search region around the click (e.g., 400x400)
        search_size = 400
        half_size = search_size // 2
        
        with mss.mss() as sct:
            # Get monitor info to clamp coordinates
            monitor = sct.monitors[1] # Primary monitor
            
            left = max(monitor["left"], x - half_size)
            top = max(monitor["top"], y - half_size)
            width = min(search_size, monitor["width"] - (left - monitor["left"]))
            height = min(search_size, monitor["height"] - (top - monitor["top"]))
            
            region = {"top": top, "left": left, "width": width, "height": height}
            sct_img = sct.grab(region)
            img_np = np.array(sct_img)
            
            # Convert to Grayscale
            gray = cv2.cvtColor(img_np, cv2.COLOR_BGRA2GRAY)
            
            # Adaptive Threshold
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY_INV, 11, 2
            )
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Coordinates of click relative to the captured region
            rel_x = x - left
            rel_y = y - top
            
            best_rect = None
            min_area = float('inf')
            
            for cnt in contours:
                # Check if point is inside contour
                if cv2.pointPolygonTest(cnt, (rel_x, rel_y), False) >= 0:
                    rect = cv2.boundingRect(cnt)
                    area = rect[2] * rect[3]
                    
                    # Filter noise (too small) and huge containers (too big)
                    if 100 < area < min_area:
                        min_area = area
                        best_rect = rect
            
            if best_rect:
                rx, ry, rw, rh = best_rect
                # Convert back to absolute screen coordinates
                return {
                    "left": left + rx,
                    "top": top + ry,
                    "right": left + rx + rw,
                    "bottom": top + ry + rh
                }
                
    except Exception as e:
        print(f"[Smart Shrink-Wrap] Error: {e}")
    
    # Fallback: Small fixed rect if detection fails
    return {
        "left": x - 20, "top": y - 10,
        "right": x + 20, "bottom": y + 10
    }

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

async def perform_capture(x: int, y: int, is_typing: bool = False, typed_text: str = "") -> CaptureResponse:
    """
    Capture UI element at specified coordinates with intelligent fallback for Chromium apps.
    """
    control = None
    is_chromium_fallback = False
    
    try:
        if is_typing:
            control = auto.GetFocusedControl()
        else:
            control = auto.ControlFromPoint(x, y)
            
            # CHROMIUM DETECTION: Check if this is a "blind" Chromium window
            if control and is_chromium_blind_window(control):
                print(f"[Chromium Fallback] Detected blind window: {control.ClassName}")
                is_chromium_fallback = True
                control = None  # Discard the useless container control
            elif not validate_geometry(control, x, y):
                control = None
    except Exception as e:
        print(f"[Capture] Control detection error: {e}")
        control = None

    element_name = ""
    description = ""
    element_type = "Unknown"
    rect = None
    
    # Extract control information if available
    if control:
        element_name = control.Name
        element_type = control.ControlTypeName
        rect = control.BoundingRectangle
    
    # Generate bounding box
    if rect:
        # Normal case: use the control's actual bounding rectangle
        bbox = {"left": rect.left, "top": rect.top, "right": rect.right, "bottom": rect.bottom}
    elif is_chromium_fallback:
        # CHROMIUM FALLBACK: Use Smart Shrink-Wrap (OpenCV)
        print(f"[Chromium Fallback] Applying Smart Shrink-Wrap at ({x}, {y})...")
        bbox = get_smart_bbox(x, y)
        
        element_name = "Interface Visual (Chromium)"
        element_type = "VisualElement"
        description = "Clicar no destaque"
        print(f"[Chromium Fallback] Smart bbox result: {bbox}")
    elif x == 0 and y == 0:
        # Typing case with no control
        bbox = {"left": 0, "top": 0, "right": 100, "bottom": 100}
    else:
        # Generic fallback: small box around click point
        bbox = {
            "left": x - 25, "top": y - 25,
            "right": x + 25, "bottom": y + 25
        }
    
    # Capture screenshot with padding
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
    
    # Generate description
    if is_typing:
        target = element_name if element_name else "Campo de texto"
        description = f"Digitar '{typed_text}' em '{target}'"
    elif is_chromium_fallback:
        # Already set above: "Clicar no destaque"
        pass
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
