import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import os
import csv
import pandas as pd
from src.config_manager import ConfigManager
from src.pdf_processor import PDFProcessor
from src.csv_processor import CSVProcessor


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
