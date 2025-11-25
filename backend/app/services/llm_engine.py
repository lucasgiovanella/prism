import os
from llama_cpp import Llama
from llama_cpp.llama_chat_format import Llava15ChatHandler
from app.services import model_manager

class LLMEngine:
    _instance = None
    _model = None
    _model_id = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = LLMEngine()
        return cls._instance
    
    def load_model(self, model_id: str):
        """
        Loads the specified model into memory. Unloads previous model if exists.
        """
        if self._model_id == model_id and self._model is not None:
            return # Already loaded
            
        print(f"Loading model: {model_id}...")
        
        # Find model config
        config = next((m for m in model_manager.SUPPORTED_MODELS if m["id"] == model_id), None)
        if not config:
            raise ValueError(f"Model {model_id} not found configuration")
            
        model_path = os.path.join(model_manager.MODELS_DIR, config["filename"])
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
            
        # Setup Chat Handler (needed for Vision)
        chat_handler = None
        if "llava" in model_id:
            mmproj_path = os.path.join(model_manager.MODELS_DIR, config["mmproj"])
            if not os.path.exists(mmproj_path):
                 raise FileNotFoundError(f"Projector file not found: {mmproj_path}")
                 
            chat_handler = Llava15ChatHandler(clip_model_path=mmproj_path)
        
        # Initialize Llama
        # n_ctx=2048 is usually enough for single image + short description
        # n_gpu_layers=-1 tries to offload all to GPU if available
        try:
            self._model = Llama(
                model_path=model_path,
                chat_handler=chat_handler,
                n_ctx=2048,
                n_gpu_layers=-1, 
                verbose=True
            )
            self._model_id = model_id
            print(f"Model {model_id} loaded successfully.")
        except Exception as e:
            print(f"Failed to load model: {e}")
            raise e

    def generate_description(self, image_base64: str, prompt: str = "Describe this UI element.") -> str:
        if not self._model:
            raise RuntimeError("No model loaded. Please load a model first.")
            
        # Prepare message for LLaVA
        # LLaVA expects a specific format with image URI
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            }
        ]
        
        try:
            response = self._model.create_chat_completion(
                messages=messages,
                max_tokens=100,
                temperature=0.2
            )
            
            return response["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"Inference error: {e}")
            return f"Error generating description: {e}"

# Global instance
engine = LLMEngine.get_instance()
