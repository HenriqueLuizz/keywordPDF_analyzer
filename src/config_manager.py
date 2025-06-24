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
        
        try:
            config.read(config_file)
            config_dict = self._extract_config(config)
            
            # Valida configuração
            validation_result = self._validate_config(config_dict)
            if not validation_result['valid']:
                print(f"⚠️  Problemas encontrados no arquivo de configuração '{config_file}':")
                for error in validation_result['errors']:
                    print(f"   - {error}")
                
                # Pergunta se deseja prosseguir com valores padrão
                response = input("\nDeseja prosseguir com valores padrão? (s/N): ").strip().lower()
                if response in ['s', 'sim', 'y', 'yes']:
                    print("Usando valores padrão...")
                    config_dict = self._get_default_config()
                else:
                    print("Operação cancelada pelo usuário.")
                    raise ValueError("Configuração inválida")
            
            # Cache da configuração
            self._config_cache[config_file] = config_dict
            return config_dict
            
        except Exception as e:
            print(f"❌ Erro ao carregar configuração: {e}")
            print("Criando arquivo de configuração de exemplo...")
            self.create_default_config(config_file)
            return self._get_default_config()
    
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
            # Diretórios e arquivos
            "keywords_list": config_section.get("keywords_list", "keywords.txt"),
            "pdf_dir": config_section.get("pdf_dir", "files/"),
            "output_path": config_section.get("output_path", "results/"),

            # Modelo LLM
            "model": config_section.get("model", "openai"),
            
            # Modos de operação
            "convert_md": config_section.get("convert_md", "false").lower() in ('1', 'true'),
            "openai": config_section.get("openai", "false").lower() in ('1', 'true'),
            "full_analysis": config_section.get("full_analysis", "false").lower() in ('1', 'true'),
            "rename": config_section.get("rename", "false").lower() in ('1', 'true'),
            
            # Opções de saída
            "include_summary": config_section.get("include_summary", "true").lower() in ('1', 'true'),
            "context_chars": int(config_section.get("context_chars", "30")),
            
            # Opções de processamento
            "verbose": config_section.get("verbose", "false").lower() in ('1', 'true'),
            
            # Regex patterns
            "regex_date": re.compile(regex_date_raw, re.IGNORECASE),
            "regex_company": re.compile(regex_company_raw, re.IGNORECASE | re.MULTILINE),
        }
    
    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Valida configuração e retorna resultado da validação"""
        errors = []
        
        # Valida arquivos e diretórios
        if not os.path.isfile(config.get("keywords_list", "")):
            errors.append(f"Arquivo de keywords '{config.get('keywords_list')}' não existe")
        
        if not os.path.isdir(config.get("pdf_dir", "")):
            errors.append(f"Diretório de PDFs '{config.get('pdf_dir')}' não existe")
        
        # Valida valores numéricos
        context_chars = config.get("context_chars", 30)
        if not isinstance(context_chars, int) or context_chars < 0:
            errors.append("context_chars deve ser um número inteiro positivo")
        
        # Valida que pelo menos um modo está selecionado
        modes = [
            config.get("convert_md", False),
            config.get("openai", False),
            config.get("full_analysis", False)
        ]
        if not any(modes):
            errors.append("Pelo menos um modo de operação deve estar habilitado (convert_md, openai, ou full_analysis)")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Retorna configuração padrão"""
        return {
            # Diretórios e arquivos
            "keywords_list": "keywords.txt",
            "pdf_dir": "files/",
            "output_path": "results/",

            # Modelo LLM
            "model": "openai",
            
            # Modos de operação
            "convert_md": False,
            "openai": False,
            "full_analysis": False,
            "rename": False,
            
            # Opções de saída
            "include_summary": True,
            "context_chars": 30,
            
            # Opções de processamento
            "verbose": False,
            
            # Regex patterns
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
            # Diretórios e arquivos
            "keywords_list": "keywords.txt",
            "pdf_dir": "files/",
            "output_path": "results/",

            # Modelo LLM
            "model": "openai",
            
            # Modos de operação (true/false)
            "convert_md": "false",
            "openai": "false",
            "full_analysis": "false",
            "rename": "false",
            
            # Opções de saída
            "include_summary": "true",
            "context_chars": "30",
            
            # Opções de processamento
            "verbose": "false",
            
            # Regex patterns (opcional)
            "regex_date": r"\n[\w\s]+,\s+(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})\.?",
            "regex_company": r"^\s*(.+?)\s*(?:S\.A\.|SA|Companhia|CNPJ|NIRE|–)",
        }
        
        with open(config_path, 'w') as configfile:
            config.write(configfile)
        
        print(f"✅ Arquivo de configuração criado: {config_path}")
        print("📝 Edite o arquivo para configurar suas preferências e execute novamente.")
    
    def load_keywords(self, keywords_file: str) -> list:
        """
        Carrega lista de palavras-chave do arquivo
        
        Args:
            keywords_file: Caminho para o arquivo de palavras-chave
            
        Returns:
            Lista de palavras-chave
        """
        if not os.path.isfile(keywords_file):
            print(f"⚠️  Arquivo de keywords '{keywords_file}' não encontrado")
            return []
        
        with open(keywords_file, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file.readlines() if line.strip()] 