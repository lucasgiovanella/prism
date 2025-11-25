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

def capture_screen_region(x: int, y: int, width: int, height: int) -> tuple[np.ndarray, dict]:
    """
    Captures a specific region of the screen immediately.
    Returns the image as a numpy array and the region dictionary.
    """
    try:
        with mss.mss() as sct:
            # Get monitor info to clamp coordinates
            monitor = sct.monitors[1] # Primary monitor
            
            left = max(monitor["left"], x)
            top = max(monitor["top"], y)
            w = min(width, monitor["width"] - (left - monitor["left"]))
            h = min(height, monitor["height"] - (top - monitor["top"]))
            
            region = {"top": top, "left": left, "width": w, "height": h}
            sct_img = sct.grab(region)
            img_np = np.array(sct_img)
            return img_np, region
    except Exception as e:
        print(f"Capture error: {e}")
        return None, None

def get_smart_bbox(x: int, y: int, pre_captured_img: np.ndarray = None, origin_x: int = 0, origin_y: int = 0) -> dict:
    """
    Uses OpenCV to find the smallest enclosing contour around the click point (x, y).
    Uses pre-captured image if available to ensure timing accuracy.
    """
    try:
        img_np = None
        left, top = 0, 0
        
        if pre_captured_img is not None:
            # Use the pre-captured image
            # We need to crop a search region from the large pre-captured image
            # The pre-captured image is likely centered around the click or full screen
            # For now, let's assume pre-captured image IS the search region or we crop from it
            
            # Let's assume pre_captured_img is a large region centered on click
            h, w = pre_captured_img.shape[:2]
            img_np = pre_captured_img
            left = origin_x
            top = origin_y
        else:
            # Fallback to capturing now (should be avoided for timing issues)
            search_size = 400
            half_size = search_size // 2
            
            with mss.mss() as sct:
                monitor = sct.monitors[1]
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
            
            # Heuristic for Menus/Lists:
            # If the detected element is very tall (> 150px), it's likely a container (menu, list).
            # In this case, the user likely clicked a specific ROW, but we only found the container border.
            # We should create a "row" bbox: full width of container, but small height centered on click.
            
            final_left = left + rx
            final_right = left + rx + rw
            final_top = top + ry
            final_bottom = top + ry + rh
            
            if rh > 150:
                print(f"[Smart Shrink-Wrap] Detected tall container (h={rh}). Forcing row selection.")
                # Center row on the click Y
                # Use a standard row height, e.g., 30px (15px up, 15px down)
                row_height_half = 15
                
                # Clamp to container bounds
                new_top = max(final_top, y - row_height_half)
                new_bottom = min(final_bottom, y + row_height_half)
                
                final_top = new_top
                final_bottom = new_bottom
            
            # Convert back to absolute screen coordinates
            return {
                "left": final_left,
                "top": final_top,
                "right": final_right,
                "bottom": final_bottom
            }
                
    except Exception as e:
        print(f"[Smart Shrink-Wrap] Error: {e}")
    
    # Fallback: Small fixed rect if detection fails
    return {
        "left": x - 20, "top": y - 10,
        "right": x + 20, "bottom": y + 10
    }

def get_screenshot_with_offset(bbox: Dict[str, int], padding: int = 150, pre_captured_img: np.ndarray = None, origin_x: int = 0, origin_y: int = 0):
    # Determine the region to capture (bbox + padding)
    
    # Calculate padded coordinates
    # We need to find the monitor limits. For simplicity, let's assume primary monitor or use mss to find it.
    # If we have a pre-captured image, we should try to crop from it if possible, 
    # BUT the pre-captured image might be smaller than the requested padded area.
    # So, for the final screenshot (which needs context), it's actually safer to capture AGAIN 
    # or capture a very large area initially.
    
    # Strategy: 
    # The user wants to see the state "before" the click.
    # So we MUST use the pre-captured image.
    # If the pre-captured image is not big enough, we pad with black or repeat.
    
    if pre_captured_img is not None:
        try:
            # Calculate where the bbox is relative to the pre-captured image
            # pre-captured image starts at origin_x, origin_y
            
            # Desired crop in absolute coords
            target_left = bbox["left"] - padding
            target_top = bbox["top"] - padding
            target_right = bbox["right"] + padding
            target_bottom = bbox["bottom"] + padding
            target_w = target_right - target_left
            target_h = target_bottom - target_top
            
            # Coordinates relative to the pre-captured image
            rel_left = target_left - origin_x
            rel_top = target_top - origin_y
            
            img_h, img_w = pre_captured_img.shape[:2]
            
            # Create a blank canvas for the result
            result_img = np.zeros((target_h, target_w, 4), dtype=np.uint8)
            
            # Calculate intersection between desired crop and available image
            src_x = max(0, rel_left)
            src_y = max(0, rel_top)
            src_w = min(img_w - src_x, target_w - (0 if rel_left >= 0 else -rel_left)) # Simplified
            src_h = min(img_h - src_y, target_h - (0 if rel_top >= 0 else -rel_top))
            
            # This logic is getting complex. Let's simplify:
            # Just crop what we can.
            
            # Safe crop coordinates within the image
            start_x = max(0, rel_left)
            start_y = max(0, rel_top)
            end_x = min(img_w, rel_left + target_w)
            end_y = min(img_h, rel_top + target_h)
            
            if end_x > start_x and end_y > start_y:
                crop = pre_captured_img[start_y:end_y, start_x:end_x]
                
                # Place it in the result image
                # Calculate placement offsets
                dest_x = max(0, -rel_left)
                dest_y = max(0, -rel_top)
                
                h_crop, w_crop = crop.shape[:2]
                result_img[dest_y:dest_y+h_crop, dest_x:dest_x+w_crop] = crop
            
            _, buffer = cv2.imencode(".png", result_img)
            b64 = base64.b64encode(buffer).decode("utf-8")
            return b64, {"left": target_left, "top": target_top}
            
        except Exception as e:
            print(f"Screenshot from buffer error: {e}")
            # Fallback to fresh capture if buffer fails (though it might be late)
            pass

    # Fallback to fresh capture
    with mss.mss() as sct:
        cx = (bbox["left"] + bbox["right"]) // 2
        cy = (bbox["top"] + bbox["bottom"]) // 2
        
        monitor_idx = 1
        for i, m in enumerate(sct.monitors[1:], 1):
             if (cx >= m["left"] and cx < m["left"] + m["width"] and
                 cy >= m["top"] and cy < m["top"] + m["height"]):
                 monitor_idx = i
                 break
        
        monitor = sct.monitors[monitor_idx]
        
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
    # Capture a large region around the click point immediately to preserve state
    # We capture a 800x800 region centered on the click to ensure we have enough context
    capture_size = 800
    half_size = capture_size // 2
    
    pre_captured_img, capture_region = capture_screen_region(
        x - half_size, 
        y - half_size, 
        capture_size, 
        capture_size
    )

    if capture_region:
        capture_origin_x = capture_region['left']
        capture_origin_y = capture_region['top']
    
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
        # Pass the pre-captured image!
        bbox = get_smart_bbox(x, y, pre_captured_img=pre_captured_img, origin_x=capture_origin_x, origin_y=capture_origin_y)
        
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
    
    # Capture screenshot with padding using the PRE-CAPTURED image
    screenshot_b64, offset = get_screenshot_with_offset(
        bbox, 
        padding=150, 
        pre_captured_img=pre_captured_img, 
        origin_x=capture_origin_x, 
        origin_y=capture_origin_y
    )
    
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
