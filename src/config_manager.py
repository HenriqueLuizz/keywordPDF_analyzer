"""
Gerenciador de configuração para o KeywordPDF Analyzer
"""

import os
import re
import configparser
from typing import Dict, Any, Optional


class ConfigManager:
    """Gerencia configurações do sistema"""
    
    def __init__(self, default_config_path: str = "config.ini"):
        self.default_config_path = default_config_path
        self._config_cache = {}
    
    def load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Carrega configuração do arquivo especificado ou usa o padrão
        
        Args:
            config_path: Caminho para o arquivo de configuração
            
        Returns:
            Dicionário com as configurações carregadas
        """
        config_file = config_path or self.default_config_path
        
        # Verifica se já foi carregado
        if config_file in self._config_cache:
            return self._config_cache[config_file]
        
        config = configparser.ConfigParser()
        
        # Se o arquivo não existe, retorna configuração padrão
        if not os.path.isfile(config_file):
            return self._get_default_config()
        
        config.read(config_file)
        
        # Extrai configurações
        config_dict = self._extract_config(config)
        
        # Cache da configuração
        self._config_cache[config_file] = config_dict
        
        return config_dict
    
    def _extract_config(self, config: configparser.ConfigParser) -> Dict[str, Any]:
        """Extrai configurações do objeto ConfigParser"""
        if "CONFIG" not in config:
            return self._get_default_config()
        
        config_section = config["CONFIG"]
        
        # Regex patterns
        regex_date_raw = config_section.get(
            "regex_date", 
            r"\n[\w\s]+,\s+(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})\.?"
        ).strip('"')
        
        regex_company_raw = config_section.get(
            "regex_company", 
            r"^\s*(.+?)\s*(?:S\.A\.|SA|Companhia|CNPJ|NIRE|–)"
        ).strip('"')
        
        return {
            "keywords_list": config_section.get("keywords_list", "keywords.txt"),
            "renamefiles": config_section.get("renamefiles", "0").lower() in ('1', 'true'),
            "pdf_dir": config_section.get("pdf_dir", "files/"),
            "output_path": config_section.get("output_path", "files/"),
            "regex_date": re.compile(regex_date_raw, re.IGNORECASE),
            "regex_company": re.compile(regex_company_raw, re.IGNORECASE | re.MULTILINE),
        }
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Retorna configuração padrão"""
        return {
            "keywords_list": "keywords.txt",
            "renamefiles": False,
            "pdf_dir": "files/",
            "output_path": "files/",
            "regex_date": re.compile(
                r"\n[\w\s]+,\s+(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})\.?", 
                re.IGNORECASE
            ),
            "regex_company": re.compile(
                r"^\s*(.+?)\s*(?:S\.A\.|SA|Companhia|CNPJ|NIRE|–)", 
                re.IGNORECASE | re.MULTILINE
            ),
        }
    
    def create_default_config(self, config_path: str = "config.ini") -> None:
        """
        Cria arquivo de configuração padrão
        
        Args:
            config_path: Caminho onde salvar o arquivo de configuração
        """
        config = configparser.ConfigParser()
        config["CONFIG"] = {
            "keywords_list": "keywords.txt",
            "renamefiles": "False",
            "pdf_dir": "files/",
            "output_path": "files/",
            "regex_date": r"\n[\w\s]+,\s+(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})\.?",
            "regex_company": r"^\s*(.+?)\s*(?:S\.A\.|SA|Companhia|CNPJ|NIRE|–)",
        }
        
        with open(config_path, 'w') as configfile:
            config.write(configfile)
        
        print(f"Arquivo de configuração criado: {config_path}")
    
    def load_keywords(self, keywords_file: str) -> list:
        """
        Carrega lista de palavras-chave do arquivo
        
        Args:
            keywords_file: Caminho para o arquivo de palavras-chave
            
        Returns:
            Lista de palavras-chave
        """
        if not os.path.isfile(keywords_file):
            print(f"Aviso: Arquivo de keywords '{keywords_file}' não encontrado")
            return []
        
        with open(keywords_file, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file.readlines() if line.strip()] 