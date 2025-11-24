import httpx
import traceback
import base64
import io
from PIL import Image

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL_TEXT = "llama3"
OLLAMA_MODEL_VISION = "llava"

async def call_ollama_vision_ocr(image_b64: str, click_coords: dict = None) -> str:
    """
    Extract functional text from UI element using vision AI with OCR focus.
    Returns actionable instruction in Portuguese.
    
    Args:
        image_b64: Base64 encoded image string.
        click_coords: Optional dict with 'x' and 'y' keys relative to the image.
    """
    try:
        # Smart Cropping Logic
        final_image_b64 = image_b64
        is_cropped = False
        
        if click_coords and 'x' in click_coords and 'y' in click_coords:
            try:
                # Decode image
                img_data = base64.b64decode(image_b64)
                img = Image.open(io.BytesIO(img_data))
                
                # Calculate crop bounds (500x500 centered on click)
                crop_size = 500
                half_size = crop_size // 2
                
                img_width, img_height = img.size
                x, y = click_coords['x'], click_coords['y']
                
                left = max(0, x - half_size)
                top = max(0, y - half_size)
                right = min(img_width, left + crop_size)
                bottom = min(img_height, top + crop_size)
                
                # Adjust if crop is smaller than 500x500 (near edges)
                if right - left < crop_size:
                    if left == 0:
                        right = min(img_width, crop_size)
                    elif right == img_width:
                        left = max(0, img_width - crop_size)
                        
                if bottom - top < crop_size:
                    if top == 0:
                        bottom = min(img_height, crop_size)
                    elif bottom == img_height:
                        top = max(0, img_height - crop_size)
                
                # Perform crop
                cropped_img = img.crop((left, top, right, bottom))
                
                # Re-encode to base64
                buffered = io.BytesIO()
                cropped_img.save(buffered, format="PNG")
                final_image_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
                is_cropped = True
                print(f"[Smart Cropping] Applied 500x500 crop at ({x}, {y})")
                
            except Exception as e:
                print(f"[Smart Cropping] Error: {e}")
                # Fallback to original image
                final_image_b64 = image_b64

        # Construct System Prompt
        system_prompt = (
            "SYSTEM: Você é um motor de OCR semântico. Sua ÚNICA função é ler o texto ou identificar o ícone dentro do retângulo vermelho.\n"
            "REGRAS ESTRITAS:\n"
            "1. NÃO use frases completas.\n"
            "2. NÃO descreva a imagem ('Vejo um botão...', 'O retângulo...').\n"
            "3. NÃO mencione cores ou formas.\n"
            "4. SAÍDA DEVE SER APENAS: [VERBO] + [NOME DO ELEMENTO]\n"
            "5. Verbos permitidos: Clicar, Digitar, Selecionar.\n\n"
        )
        
        if is_cropped:
            system_prompt += (
                "CONTEXTO: Esta imagem é um recorte ampliado (zoom) onde a ação ocorreu no CENTRO.\n"
                "Identifique o texto ou função do elemento central.\n\n"
            )
            
        system_prompt += (
            "Exemplos:\n"
            "- Bom: 'Clicar em Salvar'\n"
            "- Bom: 'Clicar no ícone de Configurações'\n"
            "- Ruim: 'O usuário deve clicar no botão azul que diz Salvar'"
        )

        payload = {
            "model": OLLAMA_MODEL_VISION,
            "prompt": system_prompt,
            "images": [final_image_b64],
            "stream": False
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(OLLAMA_URL, json=payload, timeout=15.0)
            print(f"[Vision OCR] Status: {resp.status_code}")
            if resp.status_code == 200:
                result = resp.json().get("response", "").strip()
                print(f"[Vision OCR] Raw response: {result[:100]}...")
                
                # Cleanup common hallucinations
                clean_result = result.replace("O retângulo vermelho destaca ", "").replace("Na imagem, ", "")
                
                # Ensure it starts with a verb if possible, or add "Clicar em"
                if not any(clean_result.lower().startswith(v) for v in ["clicar", "digitar", "selecionar"]):
                     clean_result = f"Clicar em '{clean_result}'"
                     
                return clean_result
            else:
                print(f"[Vision OCR] Error response: {resp.text[:200]}")
    except httpx.TimeoutException as e:
        print(f"[Vision OCR] Timeout error: {e}")
    except Exception as e:
        print(f"[Vision OCR] Error: {type(e).__name__}: {e}")
        traceback.print_exc()
    return "Clicar no elemento destacado"

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
