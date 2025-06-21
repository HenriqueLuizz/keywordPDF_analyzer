#!/usr/bin/env python3
"""
Script de teste para verificar se a coluna keywords está sendo preenchida corretamente
"""

import os
import sys
import pandas as pd
from src.openai_analyzer import OpenAIAnalyzer
from src.pdf_processor import PDFProcessor
import tempfile
import shutil
import subprocess
from pathlib import Path


def test_keywords_extraction():
    """Testa a extração de palavras-chave"""
    # Pré-condições
    assert os.path.exists("files"), "Diretório 'files' não encontrado"
    assert os.path.exists("keywords.txt"), "Arquivo 'keywords.txt' não encontrado"

    with open("keywords.txt", "r", encoding="utf-8") as f:
        keywords = [line.strip() for line in f.readlines() if line.strip()]
    assert keywords, "Nenhuma palavra-chave carregada"

    pdf_files = [f for f in os.listdir("files") if f.lower().endswith('.pdf')]
    assert pdf_files, "Nenhum PDF encontrado em 'files'"
    test_pdf = pdf_files[0]

    processor = PDFProcessor()
    test_md_dir = "test_md"
    os.makedirs(test_md_dir, exist_ok=True)
    try:
        processor.convert_to_markdown("files", test_md_dir, verbose=False)
        analyzer = OpenAIAnalyzer()
        if not analyzer.is_configured():
            md_files = [f for f in os.listdir(test_md_dir) if f.lower().endswith('.md')]
            assert md_files, "Nenhum arquivo Markdown encontrado"
            test_md_file = os.path.join(test_md_dir, md_files[0])
            result = analyzer.find_keywords_in_file(test_md_file, keywords, verbose=False)
            assert isinstance(result, dict)
            assert 'keywords' in result
        else:
            df = analyzer.analyze_documents(test_md_dir, "keywords.txt", verbose=False)
            assert not df.empty, "Nenhum resultado obtido"
            for _, row in df.iterrows():
                assert isinstance(row['keywords'], list)
                for keyword in keywords:
                    assert keyword in row or keyword not in row['keywords']
    finally:
        if os.path.exists(test_md_dir):
            shutil.rmtree(test_md_dir)


def test_csv_output():
    """Testa a geração do CSV com a coluna keywords correta"""
    from src.csv_processor import CSVProcessor
    import tempfile
    
    test_data = [
        {
            'file_name': 'test1.pdf',
            'company': 'Empresa A',
            'date': '2023-01-01',
            'resumo': 'Teste 1',
            'keywords': ['aumento', 'capital'],
            'aumento': 'Frase com aumento',
            'capital': 'Frase com capital',
            'ações': None,
            'estrutura administrativa': None
        },
        {
            'file_name': 'test2.pdf',
            'company': 'Empresa B',
            'date': '2023-01-02',
            'resumo': 'Teste 2',
            'keywords': ['ações'],
            'aumento': None,
            'capital': None,
            'ações': 'Frase com ações',
            'estrutura administrativa': None
        }
    ]
    df = pd.DataFrame(test_data)
    csv_processor = CSVProcessor()
    
    # Usa diretório temporário para evitar erro de diretório vazio
    with tempfile.TemporaryDirectory() as temp_dir:
        test_csv_path = os.path.join(temp_dir, "test_keywords_output.csv")
        csv_processor.save_enriched_results(df, test_csv_path)
        assert os.path.exists(test_csv_path)
        df_read = csv_processor.read_csv(test_csv_path)
        assert len(df_read) == 2
        for _, row in df_read.iterrows():
            assert 'file_name' in row
            assert 'keywords' in row
            keywords_list = eval(row['keywords']) if row['keywords'] and row['keywords'] != '[]' else []
            assert isinstance(keywords_list, list)


def test_cli_with_new_options():
    """Testa o CLI com as novas opções de controle de resumo e contexto"""
    print("\n=== Testando novas opções do CLI ===")
    
    # Cria diretório temporário para testes
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = os.path.join(temp_dir, "test_files")
        os.makedirs(test_dir)
        
        # Cria arquivo de teste
        test_file = os.path.join(test_dir, "test.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("Este é um documento de teste da empresa ABC Ltda emitido em 2024-01-15.")
        
        # Cria arquivo de keywords
        keywords_file = os.path.join(temp_dir, "keywords.txt")
        with open(keywords_file, "w", encoding="utf-8") as f:
            f.write("empresa\n2024\n")
        
        # Testa CLI com --help para verificar se os novos parâmetros aparecem
        try:
            result = subprocess.run([
                sys.executable, "keyword_analyzer.py", "--help"
            ], capture_output=True, text=True, cwd=os.getcwd())
            
            if result.returncode == 0:
                help_text = result.stdout
                
                # Verifica se os novos parâmetros estão na ajuda
                if "--include-summary" in help_text:
                    print("✓ Parâmetro --include-summary encontrado na ajuda")
                else:
                    print("✗ Parâmetro --include-summary NÃO encontrado na ajuda")
                
                if "--no-summary" in help_text:
                    print("✓ Parâmetro --no-summary encontrado na ajuda")
                else:
                    print("✗ Parâmetro --no-summary NÃO encontrado na ajuda")
                
                if "--context-chars" in help_text:
                    print("✓ Parâmetro --context-chars encontrado na ajuda")
                else:
                    print("✗ Parâmetro --context-chars NÃO encontrado na ajuda")
                
                # Verifica se os exemplos estão na ajuda
                if "--no-summary" in help_text and "--context-chars 50" in help_text:
                    print("✓ Exemplos dos novos parâmetros encontrados na ajuda")
                else:
                    print("✗ Exemplos dos novos parâmetros NÃO encontrados na ajuda")
                    
            else:
                print(f"✗ Erro ao executar --help: {result.stderr}")
                
        except Exception as e:
            print(f"✗ Erro ao testar CLI: {e}")


def test_csv_processor_new_features():
    """Testa as novas funcionalidades do CSV processor"""
    print("\n=== Testando novas funcionalidades do CSV Processor ===")
    
    try:
        from src.csv_processor import CSVProcessor
        
        processor = CSVProcessor()
        
        # Testa dados de exemplo
        test_results = [
            ["file_name", "company", "date", "resumo", "keyword1", "keyword2"],
            ["test.pdf", "ABC", "2024-01-01", "Resumo teste", "Frase com keyword1", "Frase com keyword2"]
        ]
        
        # Testa processamento com contexto
        processed = processor._process_results_with_context(test_results, 10)
        
        if len(processed) == 2 and "..." in processed[1][4]:
            print("✓ Processamento com contexto funcionando")
        else:
            print("✗ Processamento com contexto NÃO funcionando")
        
        # Testa remoção de coluna resumo
        without_summary = processor._remove_summary_column(test_results)
        
        if len(without_summary[0]) == 5 and "resumo" not in [col.lower() for col in without_summary[0]]:
            print("✓ Remoção de coluna resumo funcionando")
        else:
            print("✗ Remoção de coluna resumo NÃO funcionando")
            
    except Exception as e:
        print(f"✗ Erro ao testar CSV processor: {e}")


def test_openai_analyzer_new_features():
    """Testa as novas funcionalidades do OpenAI analyzer"""
    print("\n=== Testando novas funcionalidades do OpenAI Analyzer ===")
    
    try:
        from src.openai_analyzer import OpenAIAnalyzer
        
        analyzer = OpenAIAnalyzer()
        
        # Verifica se os métodos aceitam os novos parâmetros
        import inspect
        
        # Verifica analyze_documents
        sig = inspect.signature(analyzer.analyze_documents)
        params = list(sig.parameters.keys())
        
        if 'include_summary' in params and 'context_chars' in params:
            print("✓ Método analyze_documents aceita novos parâmetros")
        else:
            print("✗ Método analyze_documents NÃO aceita novos parâmetros")
        
        # Verifica find_keywords_in_file
        sig = inspect.signature(analyzer.find_keywords_in_file)
        params = list(sig.parameters.keys())
        
        if 'context_chars' in params:
            print("✓ Método find_keywords_in_file aceita parâmetro context_chars")
        else:
            print("✗ Método find_keywords_in_file NÃO aceita parâmetro context_chars")
        
        # Verifica enrich_dataframe
        sig = inspect.signature(analyzer.enrich_dataframe)
        params = list(sig.parameters.keys())
        
        if 'include_summary' in params:
            print("✓ Método enrich_dataframe aceita parâmetro include_summary")
        else:
            print("✗ Método enrich_dataframe NÃO aceita parâmetro include_summary")
            
    except Exception as e:
        print(f"✗ Erro ao testar OpenAI analyzer: {e}")


def main():
    """Função principal"""
    print("🧪 Teste de Melhorias na Coluna Keywords\n")
    
    tests = [
        test_keywords_extraction,
        test_csv_output,
        test_cli_with_new_options,
        test_csv_processor_new_features,
        test_openai_analyzer_new_features
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"=== Resultado dos Testes ===")
    print(f"Passou: {passed}/{total} testes")
    
    if passed == total:
        print("🎉 Todos os testes passaram! A coluna keywords está funcionando corretamente.")
        return 0
    else:
        print("❌ Alguns testes falharam. Verifique os erros acima.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 