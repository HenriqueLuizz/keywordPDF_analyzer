"""
Conectores de IA - Interface unificada para diferentes provedores de IA
"""

import os
import json
import requests
import tiktoken
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from dotenv import load_dotenv

from .local_model import LocalModelManager


class AIConnector(ABC):
    """Classe abstrata para conectores de IA"""
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Verifica se o conector está configurado"""
        pass
    
    @abstractmethod
    def generate_response(self, messages: List[Dict[str, str]], max_tokens: int = 16384) -> str:
        """Gera resposta do modelo de IA"""
        pass
    
    @abstractmethod
    def count_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Conta tokens em uma lista de mensagens"""
        pass


class OpenAIConnector(AIConnector):
    """Conector para OpenAI API"""
    
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self._configured = False
        
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI()
                self._configured = True
            except ImportError:
                print("Aviso: openai não está instalado. Execute: pip install openai")
            except Exception as e:
                print(f"Aviso: OpenAI não configurada: {e}")
    
    def is_configured(self) -> bool:
        return self._configured and self.api_key is not None
    
    def count_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Conta tokens usando tiktoken"""
        try:
            encoding = tiktoken.encoding_for_model("gpt-4o")
            num_tokens = 0
            
            for message in messages:
                num_tokens += 4  # overhead por mensagem
                for key, value in message.items():
                    num_tokens += len(encoding.encode(value))
            
            num_tokens += 2  # tokens adicionais do sistema
            return num_tokens
        except Exception as e:
            print(f"Erro ao contar tokens: {e}")
            return 0
    
    def generate_response(self, messages: List[Dict[str, str]], max_tokens: int = 16384) -> str:
        """Gera resposta via OpenAI API"""
        if not self.is_configured():
            raise Exception("OpenAI não está configurada")
        
        tokens = self.count_tokens(messages)
        if tokens > 16384:
            raise Exception(f"Mensagem muito longa. Tokens: {tokens}")
        
        if tokens * 2 > 16384:
            max_tokens = tokens * 2
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.0,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Erro na API OpenAI: {e}")


class LocalAIConnector(AIConnector):
    """Conector para modelos locais via Ollama"""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.local_manager = LocalModelManager()
        self._configured = self.local_manager.is_ollama_running()
    
    def is_configured(self) -> bool:
        """Verifica se Ollama está rodando e modelo existe"""
        if not self._configured:
            return False
        
        if not self.local_manager.model_exists(self.model_name):
            print(f"Modelo '{self.model_name}' não encontrado localmente.")
            print("Modelos disponíveis:")
            for model in self.local_manager.list_models():
                print(f"  - {model}")
            return False
        
        return True
    
    def count_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Estimativa simples de tokens para modelos locais"""
        # Estimativa conservadora: 1 token ≈ 4 caracteres
        total_chars = sum(len(msg.get('content', '')) for msg in messages)
        return total_chars // 4
    
    def generate_response(self, messages: List[Dict[str, str]], max_tokens: int = 16384) -> str:
        """Gera resposta via Ollama API local"""
        if not self.is_configured():
            raise Exception(f"Modelo local '{self.model_name}' não está configurado")
        
        try:
            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.0,
                    "top_p": 1.0,
                    "num_predict": min(max_tokens, 4096)  # Limite conservador para modelos locais
                }
            }
            
            response = requests.post(
                f"{self.local_manager.base_url}/v1/chat/completions",
                json=payload,
                timeout=120,  # Timeout maior para modelos locais
            )
            
            if response.status_code != 200:
                raise Exception(f"Erro na API Ollama: {response.status_code} - {response.text}")
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except requests.exceptions.Timeout:
            raise Exception("Timeout na resposta do modelo local")
        except Exception as e:
            raise Exception(f"Erro no modelo local: {e}")


class AIConnectorFactory:
    """Factory para criar conectores de IA"""
    
    @staticmethod
    def create_connector(provider: str, model_name: str = None) -> AIConnector:
        """
        Cria um conector de IA baseado no provedor
        
        Args:
            provider: 'openai' ou 'local'
            model_name: Nome do modelo (apenas para local)
        
        Returns:
            Instância do conector apropriado
        """
        if provider.lower() == "openai":
            return OpenAIConnector()
        elif provider.lower() == "local":
            if not model_name:
                raise ValueError("Nome do modelo é obrigatório para conectores locais")
            return LocalAIConnector(model_name)
        else:
            raise ValueError(f"Provedor não suportado: {provider}")
    
    @staticmethod
    def get_available_providers() -> List[str]:
        """Retorna lista de provedores disponíveis"""
        return ["openai", "local"]
    
    @staticmethod
    def get_supported_local_models() -> List[str]:
        """Retorna lista de modelos locais suportados"""
        local_manager = LocalModelManager()
        return local_manager.get_supported_models() 