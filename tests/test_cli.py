#!/usr/bin/env python3
"""
Script de teste para validar o CLI do KeywordPDF Analyzer
"""

import os
import sys
import subprocess


def test_imports():
    """Testa se todos os módulos podem ser importados"""
    from src.config_manager import ConfigManager
    from src.pdf_processor import PDFProcessor
    from src.openai_analyzer import OpenAIAnalyzer
    from src.csv_processor import CSVProcessor
    from keyword_analyzer import KeywordAnalyzerCLI
    
    # Verifica se as classes foram importadas corretamente
    assert ConfigManager is not None
    assert PDFProcessor is not None
    assert OpenAIAnalyzer is not None
    assert CSVProcessor is not None
    assert KeywordAnalyzerCLI is not None


def test_config_manager():
    """Testa o ConfigManager"""
    from src.config_manager import ConfigManager
    
    config_manager = ConfigManager()
    
    # Testa carregamento de configuração padrão
    config = config_manager.load_config()
    assert isinstance(config, dict)
    
    # Testa carregamento de keywords
    keywords = config_manager.load_keywords("keywords.txt")
    assert isinstance(keywords, list)


def test_pdf_processor():
    """Testa o PDFProcessor"""
    from src.pdf_processor import PDFProcessor
    
    processor = PDFProcessor()
    
    # Verifica se há PDFs para testar
    if not os.path.exists("files"):
        return  # Pula o teste se não houver arquivos
    
    pdf_files = [f for f in os.listdir("files") if f.lower().endswith('.pdf')]
    if not pdf_files:
        return  # Pula o teste se não houver PDFs
    
    # Testa extração de texto
    test_pdf = os.path.join("files", pdf_files[0])
    text = processor.extract_text_from_pdf(test_pdf)
    assert isinstance(text, str)
    assert len(text) > 0


def test_cli_help():
    """Testa se o CLI responde ao comando de ajuda"""
    result = subprocess.run(
        [sys.executable, "keyword_analyzer.py", "--help"],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    assert result.returncode == 0
    assert "KeywordPDF Analyzer" in result.stdout
    assert "--help" in result.stdout


def test_openai_config():
    """Testa configuração da OpenAI"""
    from src.openai_analyzer import OpenAIAnalyzer
    
    analyzer = OpenAIAnalyzer()
    
    # O método deve existir e retornar um booleano
    is_configured = analyzer.is_configured()
    assert isinstance(is_configured, bool) 
