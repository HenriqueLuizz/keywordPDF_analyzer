"""
Analisador IA - Extração de informações de documentos
"""

import os
import json
import pandas as pd
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

from .ai_connector import AIConnectorFactory, AIConnector
from .config_manager import ConfigManager

MAX_TOKENS = os.getenv("MAX_TOKENS", 128000)

class AIAnalyzer:
    """Analisador que utiliza IA para extrair informações de documentos"""
    
    def __init__(self, provider: str = "openai", model_name: str = None):
        load_dotenv()
        self.config_manager = ConfigManager()
        self.provider = provider
        self.model_name = model_name
        self.connector = None
        
        # Inicializa o conector apropriado
        self._initialize_connector()
    
    def _initialize_connector(self):
        """Inicializa o conector de IA apropriado"""
        try:
            if self.provider == "openai":
                self.connector = AIConnectorFactory.create_connector("openai")
            elif self.provider == "local":
                if not self.model_name:
                    raise ValueError("Nome do modelo é obrigatório para provedores locais")
                self.connector = AIConnectorFactory.create_connector("local", self.model_name)
            else:
                raise ValueError(f"Provedor não suportado: {self.provider}")
        except Exception as e:
            print(f"❌ Erro ao inicializar conector: {e}")
            self.connector = None
    
    def set_provider(self, provider: str, model_name: str = None) -> None:
        """Atualiza o provedor e modelo a ser utilizado"""
        self.provider = provider
        self.model_name = model_name
        self._initialize_connector()
    
    def is_configured(self) -> bool:
        """Verifica se o conector está configurado"""
        return self.connector is not None and self.connector.is_configured()
    
    def analyze_document(
        self, 
        document_content: str, 
        keywords: List[str],
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Analisa um documento extraindo informações obrigatórias e frases para cada palavra-chave
        
        Args:
            document_content: Conteúdo do documento
            keywords: Lista de palavras-chave para buscar
            verbose: Modo verboso
            
        Returns:
            Dicionário com informações extraídas
        """
        if not self.is_configured():
            return {"error": "Conector de IA não configurado"}
        
        # Cria prompt para extração de informações
        keywords_str = ', '.join(keywords)
        
        context_system = f'''
        Você é um assistente especializado em analisar documentos e extrair informações específicas.
        
        Sua tarefa é analisar o documento fornecido e extrair as seguintes informações OBRIGATÓRIAS:
        
        1. "company": Nome da empresa/companhia mencionada no documento
        2. "date": Data de emissão ou referência do documento (formato YYYY-MM-DD)
        3. "resumo": Resumo do documento em até 200 caracteres
        
        E para cada palavra-chave, extrair frases completas que a contenham:
        
        Palavras-chave para buscar: {keywords_str}
        
        Para cada palavra-chave encontrada, você deve extrair TODAS as frases completas que a contenham.
        Se uma palavra-chave aparecer em múltiplas frases, inclua todas elas.
        
        REGRAS IMPORTANTES:
        - Você DEVE retornar APENAS um JSON válido
        - NÃO inclua explicações, comentários ou texto adicional
        - NÃO use markdown ou formatação
        - Se uma informação não for encontrada, use string vazia ""
        - Para cada palavra-chave, retorne um array com todas as frases encontradas
        - O resumo deve ser conciso e informativo
        - Use o nome exato da palavra-chave como chave no JSON
        - Escape corretamente caracteres especiais no JSON
        
        Exemplo de retorno (APENAS JSON):
        {{
            "company": "Nome da Empresa",
            "date": "2023-10-15",
            "resumo": "Documento sobre aumento de capital",
            "aumento de capital": [
                "A empresa anunciou um aumento de capital de R$ 10 milhões",
                "O aumento de capital foi aprovado pelos acionistas"
            ],
            "ações": [
                "Foram emitidas 100.000 ações ordinárias",
                "As ações serão negociadas na B3"
            ]
        }}
        '''
        
        question = f"""Analise o documento e extraia as informações solicitadas em um JSON valido. 
        Para cada palavra-chave encontrada, extraia TODAS as frases completas que a contenham: {keywords_str}. 
        A resposta deve conter apenas o JSON, sem nenhum outro texto adicional.
        Informações obrigatórias:
        - company: Nome da empresa/companhia mencionada no documento
        - date: Data de emissão ou referência do documento (formato YYYY-MM-DD)
        - resumo: Resumo do documento em até 200 caracteres
        - Para cada palavra-chave, extrair frases completas que a contenham.
        - Se uma palavra-chave aparecer em múltiplas frases, inclua todas elas.

        Exemplo de retorno (APENAS JSON):
        {{
            "company": "Nome da Empresa",
            "date": "2023-10-15",
            "resumo": "Documento sobre aumento de capital",
            "aumento de capital": [
                "A empresa anunciou um aumento de capital de R$ 10 milhões",
                "O aumento de capital foi aprovado pelos acionistas"
            ],
            "ações": [
                "Foram emitidas 100.000 ações ordinárias",
                "As ações serão negociadas na B3"
            ]
        }}
        """
        
        messages = [
            {
                "role": "system",
                "content": context_system
            },
            {
                "role": "user",
                "content": f"Documento: {document_content}\n\nPergunta: {question}"
            }
        ]
        

        # Verifica se o número de tokens excede o limite
        tokens = self.connector.count_tokens(messages)
        if tokens > MAX_TOKENS:
            return {
                "error": "Documento muito longo. Número de tokens excede o limite do modelo."
            }
        
        max_tokens = min(tokens * 2, MAX_TOKENS)
        
        # Gera resposta via conector
        try:
            resposta_texto = self.connector.generate_response(messages, max_tokens)
            
            # if verbose:
            #     print(f"🤖 Resposta da IA: {resposta_texto[:200]}...")
            
            # Tenta fazer parse do JSON
            try:
                # Limpa possíveis formatações markdown
                cleaned_result = resposta_texto.strip()
                if cleaned_result.startswith('```json'):
                    cleaned_result = cleaned_result[7:]
                if cleaned_result.endswith('```'):
                    cleaned_result = cleaned_result[:-3]
                cleaned_result = cleaned_result.strip()
                
                # Remove possíveis caracteres de escape problemáticos
                cleaned_result = cleaned_result.replace('\\n', ' ').replace('\\r', ' ')
                
                data = json.loads(cleaned_result)
                
                # Garante que todas as chaves obrigatórias existam
                required_keys = ["company", "date", "resumo"]
                for key in required_keys:
                    if key not in data:
                        data[key] = ""
                
                data['tokens'] = tokens

                return data
                
            except json.JSONDecodeError as e:
                if verbose:
                    print(f"❌ Erro ao fazer parse do JSON: {e}")
                    print(f"Resposta recebida: {resposta_texto}")
                return {
                    "company": "",
                    "date": "",
                    "resumo": "",
                    "error": "Erro no formato da resposta",
                    "tokens": tokens
                }
                
        except Exception as e:
            return {
                "company": "",
                "date": "",
                "resumo": "",
                "error": f"Erro na análise: {e}",
                "tokens": tokens
            }


# Mantém compatibilidade com código existente
class OpenAIAnalyzer(AIAnalyzer):
    """Alias para compatibilidade com código existente"""
    pass 