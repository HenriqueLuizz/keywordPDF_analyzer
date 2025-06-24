import sys
import pathlib
import pytest
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from src.openai_analyzer import OpenAIAnalyzer
from src.local_model import LocalModelManager


def test_local_model_download_prompt():
    analyzer = OpenAIAnalyzer(model="llama2")
    with patch("src.local_model.LocalModelManager.model_exists", return_value=False), \
         patch("builtins.input", return_value="n"):
        result = analyzer.extract_info_from_file("text", "context", "q")
        assert "error" in result


def test_local_model_manager():
    manager = LocalModelManager()
    with patch("requests.get") as rg:
        rg.return_value.json.return_value = {"models": [{"name": "llama2"}]}
        assert manager.model_exists("llama2")
        assert manager.list_models() == ["llama2"]
    with patch("requests.get", side_effect=Exception):
        assert manager.list_models() == []
    with patch("subprocess.run") as sr:
        manager.pull_model("llama2")
        sr.assert_called_once()


def test_local_model_download_execution():
    analyzer = OpenAIAnalyzer(model="llama2")
    with patch("src.local_model.LocalModelManager.model_exists", return_value=False), \
         patch("builtins.input", return_value="s"), \
         patch("src.local_model.LocalModelManager.pull_model", return_value=True) as pm, \
         patch("requests.post") as rp:
        rp.return_value.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
        analyzer.extract_info_from_file("text", "ctx", "q")
        pm.assert_called_once()

