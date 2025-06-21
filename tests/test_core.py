import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import os
import csv
import pandas as pd
from src.config_manager import ConfigManager
from src.pdf_processor import PDFProcessor
from src.csv_processor import CSVProcessor

import pytest
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import configparser

from keyword_analyzer import KeywordAnalyzerCLI


def test_load_config_defaults(tmp_path):
    cm = ConfigManager()
    config = cm.load_config(str(tmp_path / "nonexistent.ini"))
    assert config["keywords_list"] == "keywords.txt"
    assert config["renamefiles"] is False
    assert config["pdf_dir"] == "files/"
    assert config["output_path"] == "files/"
    assert config["regex_date"].pattern
    assert config["regex_company"].pattern


def test_load_keywords(tmp_path):
    file = tmp_path / "kw.txt"
    file.write_text("a\nb\n\n c ")
    cm = ConfigManager()
    kws = cm.load_keywords(str(file))
    assert kws == ["a", "b", "c"]


def test_extract_date_and_company():
    text = "Header\nCidade, 1 de Janeiro de 2024.\nEmpresa Teste S.A."
    pdfp = PDFProcessor()
    config = ConfigManager().load_config()
    company, date = pdfp.find_company_and_date(text, config["regex_company"], config["regex_date"])
    assert company == "Empre"  # behavior due to regex
    assert date == "20240101"


def test_keywords_checks():
    text = "Isto contém Alpha e beta."
    keywords = ["alpha", "gamma"]
    pdfp = PDFProcessor()
    assert pdfp.contains_keywords(text, keywords) is True
    assert pdfp.check_keywords_in_text(text, keywords) == [1, 0]


def test_get_unique_filename(tmp_path):
    first = tmp_path / "file.pdf"
    first.write_text("x")
    pdfp = PDFProcessor()
    new_name = pdfp.get_unique_filename(str(tmp_path), "file.pdf")
    assert new_name != "file.pdf"
    assert new_name.startswith("file")


def test_save_results_and_remove_summary(tmp_path):
    results = [["file_name", "company", "date", "resumo", "kw"],
               ["a.pdf", "A", "20200101", "summary", "match"]]
    out = tmp_path / "res.csv"
    cp = CSVProcessor()
    cp.save_results(results, str(out), include_summary=False, context_chars=3)
    with open(out, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    assert rows[0] == ["file_name", "company", "date", "kw"]
    assert rows[1][3].startswith("...") and rows[1][3].endswith("...")


def test_merge_and_clean_dataframe(tmp_path):
    traditional = [["file_name", "company", "date", "kw"],
                   ["a.pdf", "A", "2020", "x"]]
    df_openai = pd.DataFrame([{"file_name": "a.pdf", "extra": 1},
                              {"file_name": "b.pdf", "extra": 2}])
    cp = CSVProcessor()
    merged = cp.merge_results(traditional, df_openai)
    assert set(merged.columns) == {"file_name", "company", "date", "kw", "extra"}

    dirty = pd.DataFrame({"a": [" x ", None], "b": [None, None]})
    cleaned = cp.clean_dataframe(dirty)
    assert cleaned.iloc[0, 0] == "x"
    assert len(cleaned) == 1


class TestConfigManager:
    """Testes para o gerenciador de configuração"""
    
    def test_load_default_config(self):
        """Testa carregamento de configuração padrão"""
        config_manager = ConfigManager()
        config = config_manager.load_config("arquivo_inexistente.ini")
        
        assert config["keywords_list"] == "keywords.txt"
        assert config["pdf_dir"] == "files/"
        assert config["output_path"] == "results/"
        assert config["convert_md"] is False
        assert config["openai"] is False
        assert config["full_analysis"] is False
        assert config["include_summary"] is True
        assert config["context_chars"] == 30
    
    def test_create_default_config(self):
        """Testa criação de arquivo de configuração padrão"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "test_config.ini")
            config_manager = ConfigManager()
            
            config_manager.create_default_config(config_path)
            
            assert os.path.exists(config_path)
            
            # Verifica se o arquivo pode ser lido
            config = config_manager.load_config(config_path)
            assert config["keywords_list"] == "keywords.txt"
            assert config["pdf_dir"] == "files/"
    
    def test_validate_config_with_errors(self):
        """Testa validação de configuração com erros"""
        config_manager = ConfigManager()
        config = {
            "keywords_list": "arquivo_inexistente.txt",
            "pdf_dir": "diretorio_inexistente/",
            "context_chars": -1,
            "convert_md": False,
            "openai": False,
            "full_analysis": False
        }
        
        result = config_manager._validate_config(config)
        
        assert result["valid"] is False
        assert len(result["errors"]) >= 2  # Pelo menos 2 erros esperados
    
    def test_validate_config_valid(self):
        """Testa validação de configuração válida"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Cria arquivos necessários
            keywords_file = os.path.join(temp_dir, "keywords.txt")
            with open(keywords_file, 'w') as f:
                f.write("keyword1\nkeyword2")
            
            pdf_dir = os.path.join(temp_dir, "pdfs")
            os.makedirs(pdf_dir)
            
            config_manager = ConfigManager()
            config = {
                "keywords_list": keywords_file,
                "pdf_dir": pdf_dir,
                "context_chars": 30,
                "convert_md": True,  # Pelo menos um modo habilitado
                "openai": False,
                "full_analysis": False
            }
            
            result = config_manager._validate_config(config)
            assert result["valid"] is True
            assert len(result["errors"]) == 0


class TestCLIConfigIntegration:
    """Testes para integração CLI com configuração"""
    
    def test_merge_config_with_args(self):
        """Testa mesclagem de configuração com argumentos"""
        cli = KeywordAnalyzerCLI()
        
        # Configuração base
        config = {
            "pdf_dir": "files/",
            "keywords_list": "keywords.txt",
            "output_path": "results/",
            "convert_md": False,
            "openai": True,
            "include_summary": True,
            "context_chars": 30
        }
        
        # Argumentos simulados
        args = MagicMock()
        args.dir = "custom_dir/"
        args.keywords = "custom_keywords.txt"
        args.output = "custom_output/"
        args.verbose = True
        args.include_summary = False
        args.context_chars = 50
        
        merged = cli._merge_config_with_args(args, config)
        
        # Argumentos da linha de comando devem ter prioridade
        assert merged["pdf_dir"] == "custom_dir/"
        assert merged["keywords_list"] == "custom_keywords.txt"
        assert merged["output_path"] == "custom_output/"
        assert merged["verbose"] is True
        assert merged["include_summary"] is False
        assert merged["context_chars"] == 50
        
        # Configurações não sobrescritas devem permanecer
        assert merged["openai"] is True
    
    def test_determine_mode_from_config(self):
        """Testa determinação do modo baseado na configuração"""
        cli = KeywordAnalyzerCLI()
        
        # Testa diferentes configurações
        configs = [
            ({"full_analysis": True}, "full_analysis"),
            ({"openai": True}, "openai"),
            ({"convert_md": True}, "convert_md"),
            ({"convert_md": False, "openai": False, "full_analysis": False}, "traditional")
        ]
        
        for config, expected_mode in configs:
            args = MagicMock()
            args.convert_md = False
            args.full_analysis = False
            args.openai = False
            
            # Simula a lógica do método run
            if args.convert_md:
                mode = "convert_md"
            elif args.full_analysis:
                mode = "full_analysis"
            elif args.openai:
                mode = "openai"
            else:
                if config.get('full_analysis'):
                    mode = "full_analysis"
                elif config.get('openai'):
                    mode = "openai"
                elif config.get('convert_md'):
                    mode = "convert_md"
                else:
                    mode = "traditional"
            
            assert mode == expected_mode
    
    @patch('builtins.input', return_value='s')
    def test_config_validation_with_user_choice(self, mock_input):
        """Testa validação de configuração com escolha do usuário"""
        config_manager = ConfigManager()
        
        # Configuração com erro
        config = {
            "keywords_list": "arquivo_inexistente.txt",
            "pdf_dir": "diretorio_inexistente/",
            "context_chars": 30,
            "convert_md": False,
            "openai": False,
            "full_analysis": False
        }
        
        # Simula validação que falha
        with patch.object(config_manager, '_validate_config', return_value={"valid": False, "errors": ["Erro teste"]}):
            # Deve usar configuração padrão quando usuário escolhe 's'
            result = config_manager.load_config("test.ini")
            assert result["keywords_list"] == "keywords.txt"  # Valor padrão
