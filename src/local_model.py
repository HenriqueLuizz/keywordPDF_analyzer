import subprocess
import requests
from typing import List

class LocalModelManager:
    """Gerencia modelos locais via Ollama"""

    base_url = "http://localhost:11434"

    def list_models(self) -> List[str]:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            data = resp.json()
            return [m['name'] for m in data.get('models', [])]
        except Exception:
            return []

    def model_exists(self, model: str) -> bool:
        return model in self.list_models()

    def pull_model(self, model: str) -> bool:
        try:
            subprocess.run(["ollama", "pull", model], check=True)
            return True
        except Exception:
            return False
