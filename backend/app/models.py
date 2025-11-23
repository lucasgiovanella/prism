from pydantic import BaseModel
from typing import Optional, Dict, List

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
