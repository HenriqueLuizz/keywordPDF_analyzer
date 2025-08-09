#!/usr/bin/env python3
"""
KeywordPDF Analyzer - Análise de documentos PDF com IA
"""

import os
import sys
from pathlib import Path

# Importações locais
from src.pdf_processor import PDFProcessor
from src.ai_analyzer import AIAnalyzer
from src.csv_processor import CSVProcessor
from src.config_manager import ConfigManager

# Rich (opcional) para uma saída mais amigável
try:
    from rich.progress import (
        Progress,
        SpinnerColumn,
        BarColumn,
        TextColumn,
        TimeElapsedColumn,
        TimeRemainingColumn,
        MofNCompleteColumn,
    )
    from rich.console import Console
    from rich.table import Table
    _RICH_UI = True
    _RICH_CONSOLE = Console()
except Exception:
    _RICH_UI = False
    _RICH_CONSOLE = None


class KeywordAnalyzer:
    """Analisador principal de documentos PDF"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.pdf_processor = PDFProcessor()
        self.ai_analyzer = AIAnalyzer()
        self.csv_processor = CSVProcessor()
    
    def run(self):
        """Executa o fluxo principal de análise"""
        print("🚀 Iniciando KeywordPDF Analyzer")
        print("=" * 50)
        
        # 1. Carrega configuração
        config = self.config_manager.load_config()
        
        # Valida configuração
        if not self.config_manager.validate_config(config):
            print("❌ Configuração inválida. Verifique o arquivo config.ini")
            sys.exit(1)
        
        # Configura analisador de IA
        ai_provider = config.get('ai_provider', 'local')
        ai_model = config.get('ai_model', 'gemma3:latest')
        self.ai_analyzer.set_provider(ai_provider, ai_model)

        # Verifica se IA está configurada
        if not self.ai_analyzer.is_configured():
            if ai_provider == 'openai':
                print("❌ OpenAI não está configurada. Configure a variável OPENAI_API_KEY")
            else:
                print(f"❌ Modelo local '{ai_model}' não está configurado")
            sys.exit(1)
        
        # Exibe configuração
        print("🔧 Configuração:")
        print(f"   Diretório PDF: {config['pdf_dir']}")
        print(f"   Arquivo keywords: {config['keywords_list']}")
        print(f"   Provedor IA: {ai_provider}")
        print(f"   Modelo IA: {ai_model}")
        print(f"   Verbose: {config['verbose']}")
        print(f"   Manter markdown: {config['keep_markdown']}")
        print()

        # 2. Busca arquivos PDF
        pdf_dir = config['pdf_dir']
        pdf_files = self.pdf_processor.get_pdf_files(pdf_dir)
        
        if not pdf_files:
            print(f"❌ Nenhum arquivo PDF encontrado em '{pdf_dir}'")
            sys.exit(1)
        
        print(f"📁 Encontrados {len(pdf_files)} arquivos PDF")
        print()
        
        # 3. Processa cada PDF individualmente
        print("🔄 Processando arquivos PDF...")
        # output_path = os.path.join(config['output_path'], 'resultados.csv')
        
        # Carrega keywords
        try:
            with open(config['keywords_list'], 'r', encoding='utf-8') as f:
                keywords = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except Exception as e:
            print(f"❌ Erro ao carregar keywords: {e}")
            sys.exit(1)
        
        if not keywords:
            print("❌ Nenhuma palavra-chave encontrada no arquivo")
            sys.exit(1)
        
        processed_count = 0

        # if _RICH_UI and _RICH_CONSOLE is not None:
        progress = Progress(
            SpinnerColumn(style="cyan"),
            TextColumn("{task.description}"),
            TextColumn("[dim]{task.fields[stage]}"),
            BarColumn(bar_width=None),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("•"),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            console=_RICH_CONSOLE,
            transient=False,
        )
        with progress:
            task_id = progress.add_task("🔄 Processando PDFs...", total=len(pdf_files), stage="")

            for i, pdf_filename in enumerate(pdf_files):
                progress.update(task_id, description=f"📄 {os.path.basename(pdf_filename)}", stage="convertendo")
                try:
                    # Converte PDF para Markdown sob demanda
                    pdf_path = os.path.join(pdf_filename)
                    markdown_content = self.pdf_processor.convert_single_pdf_to_markdown(
                        pdf_path,
                        verbose=config['verbose']
                    )

                    if not markdown_content:
                        print(f"  ❌ Erro na conversão de {pdf_filename}")
                        progress.update(task_id, stage="erro")
                        continue

                    # Analisa documento com IA
                    progress.update(task_id, stage="analisando")
                    result = self.ai_analyzer.analyze_document(markdown_content, keywords, config['verbose'])

                    # Prepara dados para o CSV
                    row_data = {
                        'filename': pdf_filename,
                        'company': result.get('company', ''),
                        'date': result.get('date', ''),
                        'resumo': result.get('resumo', ''),
                        'tokens': result.get('tokens', '')
                    }

                    # Adiciona dados para cada palavra-chave
                    for keyword in keywords:
                        if keyword in result and isinstance(result[keyword], list):
                            sentences = result[keyword]
                            row_data[keyword] = ' | '.join(sentences) if sentences else ''
                        else:
                            row_data[keyword] = ''

                    output_path = os.path.join(config['output_path'], os.path.basename(os.path.dirname(pdf_filename)), 'resultados.csv')

                    # Salva resultado no CSV
                    progress.update(task_id, stage="salvando")
                    self.csv_processor.save_single_result_with_keywords(
                        row_data, 
                        output_path, 
                        keywords, 
                        config['verbose']
                    )

                    processed_count += 1

                    if result.get('error'):
                        progress.update(task_id, stage="erro")
                        print(f"  ❌ Erro: {result['error']}")
                    else:
                        progress.update(task_id, stage="análise concluída")

                except Exception as e:
                    if config['verbose']:
                        print(f"  ❌ Erro ao processar arquivo {pdf_filename}: {e}")
                    progress.update(task_id, stage="erro")

                    # Salva linha com erro
                    row_data = {
                        'filename': pdf_filename,
                        'company': '',
                        'date': '',
                        'resumo': ''
                    }

                    # Adiciona colunas vazias para cada palavra-chave
                    for keyword in keywords:
                        row_data[keyword] = ''

                    self.csv_processor.save_single_result_with_keywords(
                        row_data, 
                        output_path, 
                        keywords, 
                        config['verbose']
                    )
                finally:
                    progress.advance(task_id)
        
        if processed_count == 0:
            print("❌ Nenhum arquivo foi processado com sucesso")
            sys.exit(1)
        
        print("✅ Processamento concluído")
        print()
        
        # 4. Exibe resumo
        self._show_summary(pdf_files, config['output_path'], processed_count)


    def _show_summary(self, pdf_files, output_path, processed_count):
        """Exibe resumo da análise"""
        print("📊 RESUMO DA ANÁLISE")
        print("=" * 50)
        print(f"📄 Arquivos encontrados: {len(pdf_files)}")
        print(f"✅ Arquivos processados: {processed_count}")
        # print(f"📁 Arquivos encontrados: {', '.join(pdf_files)}")
        print(f"💾 Arquivo CSV gerado: {output_path}")
        
        # Lê o CSV para estatísticas
        try:
            import pandas as pd
            if os.path.exists(output_path):
                # Recupera todos os arquivos resultados*.csv
                results_files = []
                for root, _, files in os.walk(output_path):
                    for name in files:
                        if name.startswith('resultados') and name.endswith('.csv'):
                            results_files.append(os.path.join(root, name))
                
                print(f"📋 Arquivos encontrados: {results_files}")
                for file in results_files:
                    print('-' * 50)
                    print(f"📋 Lendo arquivo: {file}")
                    df = pd.read_csv(file)
                    print(f"📋 Registros no CSV: {len(df)}")

                    # Estatísticas dos resultados
                    if not df.empty:
                        companies_found = df['company'].str.len() > 0
                        dates_found = df['date'].str.len() > 0
                        
                        tokens_sum = int(df['tokens'].sum())
                        tokens_mean = int(df['tokens'].mean())

                        print(f"🏢 Empresas identificadas: {companies_found.sum()}")
                        print(f"📅 Datas extraídas: {dates_found.sum()}")
                        print(f"⚙️ Tokens utilizados: {tokens_sum}")
                        print(f"⚙️ Média de tokens: {tokens_mean}")

                        # Conta palavras-chave encontradas
                        keyword_columns = [col for col in df.columns if col not in ['filename', 'company', 'date', 'resumo', 'tokens']]
                        for keyword in keyword_columns:
                            keyword_found = df[keyword].str.len() > 0
                            print(f"🔍 '{keyword}' encontrada: {keyword_found.sum()}")
        except Exception as e:
            print(f"⚠️  Erro ao ler estatísticas do CSV: {e}")

        print("=" * 50)
        print("✅ Análise concluída com sucesso!")


def main():
    """Função principal"""
    try:
        analyzer = KeywordAnalyzer()
        analyzer.run()
    except KeyboardInterrupt:
        print("\n❌ Operação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 