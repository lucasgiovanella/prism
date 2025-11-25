from app.services import llm_engine
import base64
import io
from PIL import Image

async def call_ollama_vision_ocr(image_base64: str, bbox: dict = None) -> str:
    """
    Analisa uma imagem base64 usando o motor local llama.cpp via LLMEngine.
    """
    try:
        img_data = base64.b64decode(image_base64)
        original_image = Image.open(io.BytesIO(img_data))
        if original_image.mode in ("RGBA", "P"):
            original_image = original_image.convert("RGB")
            
        final_image = original_image
        context_prompt = ""
        
        if bbox and 'left' in bbox and 'top' in bbox:
            try:
                width, height = original_image.size
                padding = 20
                left = max(0, int(bbox['left']) - padding)
                top = max(0, int(bbox['top']) - padding)
                right = min(width, int(bbox['right']) + padding)
                bottom = min(height, int(bbox['bottom']) + padding)
                
                if (right - left) > 10 and (bottom - top) > 10:
                    final_image = original_image.crop((left, top, right, bottom))
                    context_prompt = "CONTEXTO: Elemento focado. "
            except Exception as e:
                print(f"Crop error: {e}")

        # Convert back to base64 for the engine
        buffered = io.BytesIO()
        final_image.save(buffered, format="JPEG", quality=90)
        final_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        prompt = (
            f"{context_prompt}"
            "Identifique o elemento de interface no centro. "
            "Responda com uma instrução IMPERATIVA CURTA (ex: 'Clique no botão Salvar')."
        )
        
        return llm_engine.engine.generate_description(final_b64, prompt)

    except Exception as e:
        print(f"Local LLM Error: {e}")
        return "Clicar no elemento destacado"

async def call_ollama_text(prompt: str) -> str:
    # Text-only not fully implemented in LLMEngine yet for LLaVA (it expects image),
    # but we can pass a blank image or update LLMEngine.
    # For now, let's return the prompt or implement text-only later.
    return prompt