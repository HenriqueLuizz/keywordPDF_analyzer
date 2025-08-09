"""
Gerenciador de Configuração - Carrega configurações do sistema
"""

import os
import configparser
from typing import Dict, Any, List


class ConfigManager:
    """Gerencia configurações do sistema"""
    
    def __init__(self):
        self.default_config = {
            # Diretórios e arquivos
            "keywords_list": "keywords.txt",
            "pdf_dir": "files/",
            "output_path": "files/",
            
            # Configuração de IA
            "ai_provider": "openai",
            "ai_model": "gpt-4o",
            
            # Opções de processamento
            "verbose": True,
            "keep_markdown": False,
        }
    
    def load_config(self, config_file: str = "config.ini") -> Dict[str, Any]:
        """
        Carrega configuração do arquivo config.ini
        
        Args:
            config_file: Caminho para o arquivo de configuração
            
        Returns:
            Dicionário com configurações
        """
        config = self.default_config.copy()
        
        if os.path.exists(config_file):
            try:
                parser = configparser.ConfigParser()
                parser.read(config_file, encoding='utf-8')
                
                if 'CONFIG' in parser:
                    config_section = parser['CONFIG']
                    
                    # Diretórios e arquivos
                    config["keywords_list"] = config_section.get("keywords_list", "keywords.txt")
                    config["pdf_dir"] = config_section.get("pdf_dir", "files/")
                    config["output_path"] = config_section.get("output_path", "files/")
                    
                    # Configuração de IA
                    config["ai_provider"] = config_section.get("ai_provider", "openai")
                    config["ai_model"] = config_section.get("ai_model", "gpt-4o")
                    
                    # Opções de processamento
                    config["verbose"] = config_section.get("verbose", "true").lower() in ('1', 'true')
                    config["keep_markdown"] = config_section.get("keep_markdown", "false").lower() in ('1', 'true')
                    
            except Exception as e:
                print(f"⚠️  Aviso: Erro ao carregar configuração de '{config_file}': {e}")
                print("Usando configurações padrão")
        else:
            print(f"📝 Arquivo '{config_file}' não encontrado. Usando configurações padrão.")
        
        return config
    
    def create_default_config(self, config_file: str = "config.ini") -> None:
        """
        Cria arquivo de configuração padrão
        
        Args:
            config_file: Caminho para o arquivo de configuração
        """
        config = configparser.ConfigParser()
        config['CONFIG'] = {
            # Diretórios e arquivos
            "keywords_list": "keywords.txt",
            "pdf_dir": "files/",
            "output_path": "files/",
            
            # Configuração de IA
            "ai_provider": "local",
            "ai_model": "gemma3:4b",
            
            # Opções de processamento
            "verbose": "false",
            "keep_markdown": "false",
        }
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                config.write(f)
            print(f"✅ Arquivo de configuração criado: {config_file}")
        except Exception as e:
            print(f"❌ Erro ao criar arquivo de configuração: {e}")
    
    def load_keywords(self, keywords_file: str) -> List[str]:
        """
        Carrega lista de palavras-chave do arquivo
        
        Args:
            keywords_file: Caminho para o arquivo de keywords
            
        Returns:
            Lista de palavras-chave
        """
        keywords = []
        
        if os.path.exists(keywords_file):
            try:
                with open(keywords_file, 'r', encoding='utf-8') as f:
                    keywords = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            except Exception as e:
                print(f"❌ Erro ao carregar keywords de '{keywords_file}': {e}")
        else:
            print(f"❌ Arquivo de keywords '{keywords_file}' não encontrado")
        
        return keywords
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Valida configuração carregada
        
        Args:
            config: Configuração a ser validada
            
        Returns:
            True se válida, False caso contrário
        """
        # Valida diretório de PDFs
        pdf_dir = config.get("pdf_dir", "")
        if not pdf_dir:
            print("❌ Diretório de PDFs não especificado")
            return False
        
        if not os.path.exists(pdf_dir):
            print(f"❌ Diretório '{pdf_dir}' não existe")
            return False
        
        # Valida arquivo de keywords
        keywords_file = config.get("keywords_list", "")
        if not keywords_file:
            print("❌ Arquivo de keywords não especificado")
            return False
        
        if not os.path.exists(keywords_file):
            print(f"❌ Arquivo de keywords '{keywords_file}' não existe")
            return False
        
        # Valida provedor de IA
        valid_providers = ["openai", "local"]
        ai_provider = config.get("ai_provider", "")
        if ai_provider not in valid_providers:
            print(f"❌ Provedor de IA inválido: {ai_provider}")
            print(f"   Provedores válidos: {', '.join(valid_providers)}")
            return False
        
        # Valida modelo local
        if ai_provider == "local":
            ai_model = config.get("ai_model", "")
            if not ai_model:
                print("❌ Modelo de IA é obrigatório para provedor local")
                return False
        
        return True 