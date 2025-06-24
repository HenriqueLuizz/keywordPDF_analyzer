#!/usr/bin/env python3
"""
Teste específico para as novas funcionalidades de controle de resumo e contexto
"""

import os
import tempfile
import pandas as pd
from src.csv_processor import CSVProcessor
from src.openai_analyzer import OpenAIAnalyzer

def test_csv_processor_features():
    """Testa as novas funcionalidades do CSV processor"""
    processor = CSVProcessor()
    test_data = [
        ["file_name", "company", "date", "resumo", "keyword1", "keyword2"],
        ["test1.pdf", "ABC", "2024-01-01", "Resumo teste 1", "Frase com keyword1", "Frase com keyword2"],
        ["test2.pdf", "XYZ", "2024-01-02", "Resumo teste 2", "Outra frase", "Mais contexto"]
    ]
    processed = processor._process_results_with_context(test_data, 10)
    assert len(processed) == 3 and "..." in processed[1][4] and "..." in processed[2][4]
    without_summary = processor._remove_summary_column(test_data)
    assert len(without_summary[0]) == 5 and "resumo" not in [col.lower() for col in without_summary[0]]
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "test_output.csv")
        processor.save_results(test_data, output_path, include_summary=True, context_chars=10)
        assert os.path.exists(output_path)
        output_path_no_summary = os.path.join(temp_dir, "test_output_no_summary.csv")
        processor.save_results(test_data, output_path_no_summary, include_summary=False, context_chars=10)
        assert os.path.exists(output_path_no_summary)

def test_openai_analyzer_features():
    """Testa as novas funcionalidades do OpenAI analyzer"""
    analyzer = OpenAIAnalyzer()
    import inspect
    sig = inspect.signature(analyzer.analyze_documents)
    params = list(sig.parameters.keys())
    assert 'include_summary' in params and 'context_chars' in params
    sig = inspect.signature(analyzer.find_keywords_in_file)
    params = list(sig.parameters.keys())
    assert 'context_chars' in params
    sig = inspect.signature(analyzer.enrich_dataframe)
    params = list(sig.parameters.keys())
    assert 'include_summary' in params
    test_df = pd.DataFrame({
        'file_name': ['test.pdf'],
        'company': [''],
        'date': [''],
        'keywords': [[]]
    })
    try:
        analyzer.enrich_dataframe(test_df, "/tmp", verbose=False, include_summary=True)
    except Exception as e:
        assert False, f"Erro no prompt com resumo: {e}"
    try:
        if 'resumo' in test_df.columns:
            test_df = test_df.drop(columns=['resumo'])
        analyzer.enrich_dataframe(test_df, "/tmp", verbose=False, include_summary=False)
    except Exception as e:
        assert False, f"Erro no prompt sem resumo: {e}"

def test_cli_integration():
    """Testa a integração com o CLI"""
    from keyword_analyzer import KeywordAnalyzerCLI
    cli = KeywordAnalyzerCLI()
    parser = cli.setup_parser()
    test_args = parser.parse_args([
        '--dir', '/tmp',
        '--keywords', '/tmp/keywords.txt',
        '--include-summary',
        '--context-chars', '50',
        '--llm-model', 'llama2'
    ])
    assert test_args.include_summary and test_args.context_chars == 50
    test_args_no_summary = parser.parse_args([
        '--dir', '/tmp',
        '--keywords', '/tmp/keywords.txt',
        '--no-summary',
        '--context-chars', '30'
    ])
    include_summary = cli._determine_include_summary(test_args_no_summary, cli.config.load_config())
    assert not include_summary and test_args_no_summary.context_chars == 30
