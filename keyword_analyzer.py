#!/usr/bin/env python3
"""
KeywordPDF Analyzer - CLI Tool
Análise de documentos PDF com extração de palavras-chave e integração com OpenAI
"""

import os
import sys
import argparse
import json
from pathlib import Path
from typing import Optional, List

# Importações locais
from src.pdf_processor import PDFProcessor
from src.openai_analyzer import OpenAIAnalyzer
from src.csv_processor import CSVProcessor
from src.config_manager import ConfigManager


class KeywordAnalyzerCLI:
    """CLI principal para o KeywordPDF Analyzer"""
    
    def __init__(self):
        self.config = ConfigManager()
        self.pdf_processor = PDFProcessor()
        self.openai_analyzer = OpenAIAnalyzer()
        self.csv_processor = CSVProcessor()
    
    def setup_parser(self) -> argparse.ArgumentParser:
        """Configura o parser de argumentos da linha de comando"""
        parser = argparse.ArgumentParser(
            description="KeywordPDF Analyzer - Análise de documentos PDF com extração de palavras-chave",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Exemplos de uso:
  # Modo tradicional (sem OpenAI)
  python keyword_analyzer.py --dir files/ --keywords keywords.txt --output results.csv
  
  # Modo com análise OpenAI
  python keyword_analyzer.py --dir files/ --keywords keywords.txt --openai --output results_enriched.csv
  
  # Modo OpenAI sem coluna resumo
  python keyword_analyzer.py --dir files/ --keywords keywords.txt --openai --no-summary --output results_no_summary.csv
  
  # Modo OpenAI com contexto personalizado
  python keyword_analyzer.py --dir files/ --keywords keywords.txt --openai --context-chars 50 --output results_context.csv
  
  # Converter PDFs para Markdown
  python keyword_analyzer.py --convert-md --dir files/ --output output/
  
  # Análise completa com OpenAI
  python keyword_analyzer.py --full-analysis --dir files/ --keywords keywords.txt --output results/
            """
        )
        
        # Argumentos principais
        parser.add_argument(
            "--dir", "-d",
            type=str,
            help="Diretório contendo arquivos PDF"
        )
        
        parser.add_argument(
            "--keywords", "-k",
            type=str,
            help="Arquivo com lista de palavras-chave"
        )
        
        parser.add_argument(
            "--output", "-o",
            type=str,
            default="results.csv",
            help="Arquivo de saída (padrão: results.csv)"
        )
        
        # Modos de operação
        parser.add_argument(
            "--convert-md",
            action="store_true",
            help="Converter PDFs para Markdown"
        )
        
        parser.add_argument(
            "--openai",
            action="store_true",
            help="Habilitar análise com OpenAI"
        )
        
        parser.add_argument(
            "--full-analysis",
            action="store_true",
            help="Executar análise completa (conversão + OpenAI + keywords)"
        )
        
        # Opções adicionais
        parser.add_argument(
            "--rename",
            action="store_true",
            help="Renomear arquivos PDF baseado no conteúdo"
        )
        
        parser.add_argument(
            "--config",
            type=str,
            help="Arquivo de configuração personalizado"
        )
        
        parser.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Modo verboso"
        )
        
        # Novas opções para controle de saída CSV
        parser.add_argument(
            "--include-summary",
            action="store_true",
            default=True,
            help="Incluir coluna resumo no CSV (padrão: True)"
        )
        
        parser.add_argument(
            "--no-summary",
            action="store_true",
            help="Excluir coluna resumo do CSV"
        )
        
        parser.add_argument(
            "--context-chars",
            type=int,
            default=30,
            help="Número de caracteres de contexto antes/depois das palavras-chave (padrão: 30)"
        )
        
        return parser
    
    def validate_args(self, args) -> bool:
        """Valida os argumentos fornecidos"""
        if not args.dir:
            print("Erro: Diretório de entrada é obrigatório (--dir)")
            return False
        
        if not os.path.isdir(args.dir):
            print(f"Erro: Diretório '{args.dir}' não existe")
            return False
        
        if args.keywords and not os.path.isfile(args.keywords):
            print(f"Erro: Arquivo de keywords '{args.keywords}' não existe")
            return False
        
        if args.config and not os.path.isfile(args.config):
            print(f"Erro: Arquivo de configuração '{args.config}' não existe")
            return False
        
        return True
    
    def run_traditional_analysis(self, args):
        """Executa análise tradicional (sem OpenAI)"""
        print("Executando análise tradicional...")
        
        # Carrega configuração
        config = self.config.load_config(args.config)
        
        # Processa PDFs
        results = self.pdf_processor.process_directory(
            directory=args.dir,
            keywords_file=args.keywords or config.get('keywords_list'),
            rename_files=args.rename or config.get('renamefiles', False),
            verbose=args.verbose
        )
        
        # Salva resultados
        output_path = os.path.join(args.output, "traditional_results.csv")
        
        # Determina se deve incluir resumo baseado nos argumentos
        include_summary = self._determine_include_summary(args)
        
        self.csv_processor.save_results(
            results, 
            output_path,
            include_summary=include_summary,
            context_chars=args.context_chars
        )
        
        print(f"Análise tradicional concluída. Resultados salvos em: {output_path}")
    
    def run_openai_analysis(self, args):
        """Executa análise com OpenAI"""
        print("Executando análise com OpenAI...")
        
        # Verifica se OpenAI está configurada
        if not self.openai_analyzer.is_configured():
            print("Erro: OpenAI não está configurada. Configure a variável OPENAI_API_KEY")
            return
        
        # Carrega configuração
        config = self.config.load_config(args.config)
        
        # Converte PDFs para Markdown se necessário
        md_dir = os.path.join(args.output, "markdown")
        if not os.path.exists(md_dir):
            os.makedirs(md_dir)
        
        self.pdf_processor.convert_to_markdown(
            input_dir=args.dir,
            output_dir=md_dir,
            verbose=args.verbose
        )
        
        # Determina se deve incluir resumo baseado nos argumentos
        include_summary = self._determine_include_summary(args)
        
        # Analisa com OpenAI
        enriched_results = self.openai_analyzer.analyze_documents(
            markdown_dir=md_dir,
            keywords_file=args.keywords or config.get('keywords_list'),
            verbose=args.verbose,
            include_summary=include_summary,
            context_chars=args.context_chars
        )
        
        # Salva resultados
        output_path = os.path.join(args.output, "openai_results.csv")
        self.csv_processor.save_enriched_results(
            enriched_results, 
            output_path,
            include_summary=include_summary
        )
        
        print(f"Análise com OpenAI concluída. Resultados salvos em: {output_path}")
    
    def run_full_analysis(self, args):
        """Executa análise completa"""
        print("Executando análise completa...")
        
        # Cria diretório de saída
        os.makedirs(args.output, exist_ok=True)
        
        # Executa análise tradicional
        self.run_traditional_analysis(args)
        
        # Executa análise com OpenAI
        self.run_openai_analysis(args)
        
        print("Análise completa concluída!")
    
    def run_convert_markdown(self, args):
        """Converte PDFs para Markdown"""
        print("Convertendo PDFs para Markdown...")
        
        self.pdf_processor.convert_to_markdown(
            input_dir=args.dir,
            output_dir=args.output,
            verbose=args.verbose
        )
        
        print(f"Conversão concluída. Arquivos salvos em: {args.output}")
    
    def _determine_include_summary(self, args) -> bool:
        """Determina se deve incluir resumo baseado nos argumentos"""
        # Se --no-summary foi especificado, não incluir resumo
        if args.no_summary:
            return False
        # Se --include-summary foi especificado explicitamente, incluir resumo
        if args.include_summary:
            return True
        # Padrão: incluir resumo
        return True
    
    def run(self):
        """Executa o CLI"""
        parser = self.setup_parser()
        args = parser.parse_args()
        
        # Valida argumentos
        if not self.validate_args(args):
            sys.exit(1)
        
        # Executa comando baseado nos argumentos
        try:
            if args.convert_md:
                self.run_convert_markdown(args)
            elif args.full_analysis:
                self.run_full_analysis(args)
            elif args.openai:
                self.run_openai_analysis(args)
            else:
                # Modo padrão: análise tradicional
                self.run_traditional_analysis(args)
                
        except KeyboardInterrupt:
            print("\nOperação cancelada pelo usuário.")
            sys.exit(1)
        except Exception as e:
            print(f"Erro durante a execução: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)


def main():
    """Função principal"""
    cli = KeywordAnalyzerCLI()
    cli.run()


if __name__ == "__main__":
    main() 