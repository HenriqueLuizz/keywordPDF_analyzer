import subprocess
import requests
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

class LocalModelManager:
    """Gerencia modelos locais via Ollama"""

    def __init__(self):
        load_dotenv()
        # Pode ser configurado via variável de ambiente
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        print(f"Base URL: {self.base_url}")
        self._available_models = None

    def list_models(self) -> List[str]:
        """Lista todos os modelos disponíveis localmente"""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            data = resp.json()
            models = [m['name'] for m in data.get('models', [])]
            self._available_models = models
            return models
        except Exception as e:
            print(f"Erro ao listar modelos: {e}")
            return []

    def model_exists(self, model: str) -> bool:
        """Verifica se um modelo específico existe localmente"""
        if self._available_models is None:
            self.list_models()
        return model in (self._available_models or [])

    def pull_model(self, model: str) -> bool:
        """Baixa um modelo do Ollama Hub"""
        try:
            print(f"Baixando modelo {model}...")
            result = subprocess.run(
                ["ollama", "pull", model], 
                check=True, 
                capture_output=True, 
                text=True
            )
            print(f"Modelo {model} baixado com sucesso!")
            # Atualiza a lista de modelos disponíveis
            self._available_models = None
            return True
        except subprocess.CalledProcessError as e:
            print(f"Erro ao baixar modelo {model}: {e}")
            return False
        except FileNotFoundError:
            print("Ollama não encontrado. Instale o Ollama primeiro: https://ollama.ai")
            return False

    def get_model_info(self, model: str) -> Optional[Dict]:
        """Obtém informações sobre um modelo específico"""
        try:
            resp = requests.get(f"{self.base_url}/api/show", json={"name": model}, timeout=5)
            return resp.json()
        except Exception:
            return None

    def is_ollama_running(self) -> bool:
        """Verifica se o Ollama está rodando"""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return resp.status_code == 200
        except Exception:
            return False

    def get_supported_models(self) -> List[str]:
        """Retorna lista de modelos suportados pelo sistema"""
        return [
            "llama2",
            "llama2:7b",
            "llama2:13b",
            "llama2:70b",
            "llama3",
            "llama3:8b",
            "llama3:70b",
            "gemma:2b",
            "gemma:7b",
            "gemma3:latest",
            "gemma3:4b",
            "deepseek-coder:6.7b",
            "deepseek-coder:33b",
            "codellama:7b",
            "codellama:13b",
            "codellama:34b",
            "mistral:7b",
            "mistral:latest",
            "mixtral:8x7b",
            "qwen:7b",
            "qwen:14b",
            "qwen:72b"
        ]
