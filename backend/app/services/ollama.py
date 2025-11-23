import httpx
import traceback

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL_TEXT = "llama3"
OLLAMA_MODEL_VISION = "llava"

async def call_ollama_vision_ocr(image_b64: str) -> str:
    """
    Extract functional text from UI element using vision AI with OCR focus.
    Returns actionable instruction in Portuguese.
    """
    try:
        payload = {
            "model": OLLAMA_MODEL_VISION,
            "prompt": (
                "SYSTEM: Você é um motor de OCR semântico. Sua ÚNICA função é ler o texto ou identificar o ícone dentro do retângulo vermelho.\n"
                "REGRAS ESTRITAS:\n"
                "1. NÃO use frases completas.\n"
                "2. NÃO descreva a imagem ('Vejo um botão...', 'O retângulo...').\n"
                "3. NÃO mencione cores ou formas.\n"
                "4. SAÍDA DEVE SER APENAS: [VERBO] + [NOME DO ELEMENTO]\n"
                "5. Verbos permitidos: Clicar, Digitar, Selecionar.\n\n"
                "Exemplos:\n"
                "- Bom: 'Clicar em Salvar'\n"
                "- Bom: 'Clicar no ícone de Configurações'\n"
                "- Ruim: 'O usuário deve clicar no botão azul que diz Salvar'"
            ),
            "images": [image_b64],
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
