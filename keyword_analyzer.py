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
from typing import Optional, List, Dict, Any

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
  # Usando config.ini (recomendado)
  python keyword_analyzer.py
  
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
        
        # Argumentos principais (todos opcionais se config.ini estiver presente)
        parser.add_argument(
            "--dir", "-d",
            type=str,
            help="Diretório contendo arquivos PDF (sobrescreve config.ini)"
        )
        
        parser.add_argument(
            "--keywords", "-k",
            type=str,
            help="Arquivo com lista de palavras-chave (sobrescreve config.ini)"
        )
        
        parser.add_argument(
            "--output", "-o",
            type=str,
            help="Arquivo de saída (sobrescreve config.ini)"
        )
        
        # Modos de operação (podem vir do config.ini)
        parser.add_argument(
            "--convert-md",
            action="store_true",
            help="Converter PDFs para Markdown (sobrescreve config.ini)"
        )
        
        parser.add_argument(
            "--openai",
            action="store_true",
            help="Habilitar análise com OpenAI (sobrescreve config.ini)"
        )
        
        parser.add_argument(
            "--full-analysis",
            action="store_true",
            help="Executar análise completa (sobrescreve config.ini)"
        )
        
        # Opções adicionais
        parser.add_argument(
            "--rename",
            action="store_true",
            help="Renomear arquivos PDF baseado no conteúdo (sobrescreve config.ini)"
        )
        
        parser.add_argument(
            "--config",
            type=str,
            help="Arquivo de configuração personalizado"
        )
        
        parser.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Modo verboso (sobrescreve config.ini)"
        )
        
        # Novas opções para controle de saída CSV
        parser.add_argument(
            "--include-summary",
            action="store_true",
            help="Incluir coluna resumo no CSV (sobrescreve config.ini)"
        )
        
        parser.add_argument(
            "--no-summary",
            action="store_true",
            help="Excluir coluna resumo do CSV (sobrescreve config.ini)"
        )
        
        parser.add_argument(
            "--context-chars",
            type=int,
            help="Número de caracteres de contexto antes/depois das palavras-chave (sobrescreve config.ini)"
        )
        
        return parser
    
    def _merge_config_with_args(self, args, config: Dict[str, Any]) -> Dict[str, Any]:
        """Mescla configurações do config.ini com argumentos da linha de comando"""
        merged_config = config.copy()
        
        # Argumentos principais (linha de comando tem prioridade)
        if args.dir:
            merged_config['pdf_dir'] = args.dir
        if args.keywords:
            merged_config['keywords_list'] = args.keywords
        if args.output:
            merged_config['output_path'] = args.output
        
        # Modos de operação (linha de comando tem prioridade)
        if args.convert_md:
            merged_config['convert_md'] = True
        if args.openai:
            merged_config['openai'] = True
        if args.full_analysis:
            merged_config['full_analysis'] = True
        if args.rename:
            merged_config['rename'] = True
        
        # Opções de processamento
        if args.verbose:
            merged_config['verbose'] = True
        
        # Opções de saída
        if args.include_summary:
            merged_config['include_summary'] = True
        if args.no_summary:
            merged_config['include_summary'] = False
        if args.context_chars is not None:
            merged_config['context_chars'] = args.context_chars
        
        return merged_config
    
    def validate_args(self, args, config: Dict[str, Any]) -> bool:
        """Valida os argumentos fornecidos e configuração"""
        # Usa configuração mesclada
        merged_config = self._merge_config_with_args(args, config)
        
        # Valida diretório de entrada
        pdf_dir = merged_config.get('pdf_dir')
        if not pdf_dir:
            print("❌ Erro: Diretório de entrada não especificado (--dir ou pdf_dir no config.ini)")
            return False
        
        if not os.path.isdir(pdf_dir):
            print(f"❌ Erro: Diretório '{pdf_dir}' não existe")
            return False
        
        # Valida arquivo de keywords
        keywords_file = merged_config.get('keywords_list')
        if keywords_file and not os.path.isfile(keywords_file):
            print(f"❌ Erro: Arquivo de keywords '{keywords_file}' não existe")
            return False
        
        # Valida arquivo de configuração personalizado
        if args.config and not os.path.isfile(args.config):
            print(f"❌ Erro: Arquivo de configuração '{args.config}' não existe")
            return False
        
        # Valida que pelo menos um modo está selecionado
        modes = [
            merged_config.get('convert_md', False),
            merged_config.get('openai', False),
            merged_config.get('full_analysis', False)
        ]
        if not any(modes):
            print("❌ Erro: Nenhum modo de operação especificado")
            print("   Use --convert-md, --openai, --full-analysis ou configure no config.ini")
            return False
        
        return True
    
    def run_traditional_analysis(self, args, config: Dict[str, Any]):
        """Executa análise tradicional (sem OpenAI)"""
        print("Executando análise tradicional...")
        
        # Usa configuração mesclada
        merged_config = self._merge_config_with_args(args, config)
        
        # Processa PDFs
        results = self.pdf_processor.process_directory(
            directory=merged_config['pdf_dir'],
            keywords_file=merged_config['keywords_list'],
            rename_files=merged_config['rename'],
            verbose=merged_config['verbose']
        )
        
        # Salva resultados
        output_path = os.path.join(merged_config['output_path'], "traditional_results.csv")
        
        self.csv_processor.save_results(
            results, 
            output_path,
            include_summary=merged_config['include_summary'],
            context_chars=merged_config['context_chars']
        )
        
        print(f"✅ Análise tradicional concluída. Resultados salvos em: {output_path}")
    
    def run_openai_analysis(self, args, config: Dict[str, Any]):
        """Executa análise com OpenAI"""
        print("Executando análise com OpenAI...")
        
        # Verifica se OpenAI está configurada
        if not self.openai_analyzer.is_configured():
            print("❌ Erro: OpenAI não está configurada. Configure a variável OPENAI_API_KEY")
            return
        
        # Usa configuração mesclada
        merged_config = self._merge_config_with_args(args, config)
        
        # Converte PDFs para Markdown se necessário
        md_dir = os.path.join(merged_config['output_path'], "markdown")
        if not os.path.exists(md_dir):
            os.makedirs(md_dir)
        
        self.pdf_processor.convert_to_markdown(
            input_dir=merged_config['pdf_dir'],
            output_dir=md_dir,
            verbose=merged_config['verbose']
        )
        
        # Analisa com OpenAI
        enriched_results = self.openai_analyzer.analyze_documents(
            markdown_dir=md_dir,
            keywords_file=merged_config['keywords_list'],
            verbose=merged_config['verbose'],
            include_summary=merged_config['include_summary'],
            context_chars=merged_config['context_chars']
        )
        
        # Salva resultados
        output_path = os.path.join(merged_config['output_path'], "openai_results.csv")
        self.csv_processor.save_enriched_results(
            enriched_results, 
            output_path,
            include_summary=merged_config['include_summary']
        )
        
        print(f"✅ Análise com OpenAI concluída. Resultados salvos em: {output_path}")
    
    def run_full_analysis(self, args, config: Dict[str, Any]):
        """Executa análise completa"""
        print("Executando análise completa...")
        
        # Usa configuração mesclada
        merged_config = self._merge_config_with_args(args, config)
        
        # Cria diretório de saída
        os.makedirs(merged_config['output_path'], exist_ok=True)
        
        # Executa análise tradicional
        self.run_traditional_analysis(args, config)
        
        # Executa análise com OpenAI
        self.run_openai_analysis(args, config)
        
        print("✅ Análise completa concluída!")
    
    def run_convert_markdown(self, args, config: Dict[str, Any]):
        """Converte PDFs para Markdown"""
        print("Convertendo PDFs para Markdown...")
        
        # Usa configuração mesclada
        merged_config = self._merge_config_with_args(args, config)
        
        self.pdf_processor.convert_to_markdown(
            input_dir=merged_config['pdf_dir'],
            output_dir=merged_config['output_path'],
            verbose=merged_config['verbose']
        )
        
        print(f"✅ Conversão concluída. Arquivos salvos em: {merged_config['output_path']}")
    
    def _determine_include_summary(self, args, config: Dict[str, Any]) -> bool:
        """Determina se deve incluir resumo baseado nos argumentos e configuração"""
        # Usa configuração mesclada
        merged_config = self._merge_config_with_args(args, config)
        
        # Se --no-summary foi especificado, não incluir resumo
        if args.no_summary:
            return False
        # Se --include-summary foi especificado explicitamente, incluir resumo
        if args.include_summary:
            return True
        # Usa valor da configuração
        return merged_config.get('include_summary', True)
    
    def run(self):
        """Executa o CLI"""
        parser = self.setup_parser()
        args = parser.parse_args()
        
        # Carrega configuração
        config = self.config.load_config(args.config)
        
        # Valida argumentos
        if not self.validate_args(args, config):
            sys.exit(1)
        
        # Determina modo de operação
        # Prioridade: linha de comando > config.ini
        if args.convert_md:
            mode = "convert_md"
        elif args.full_analysis:
            mode = "full_analysis"
        elif args.openai:
            mode = "openai"
        else:
            # Usa configuração do config.ini
            if config.get('full_analysis'):
                mode = "full_analysis"
            elif config.get('openai'):
                mode = "openai"
            elif config.get('convert_md'):
                mode = "convert_md"
            else:
                # Modo padrão: análise tradicional
                mode = "traditional"
        
        # Mostra configuração que será usada
        merged_config = self._merge_config_with_args(args, config)
        print(f"🔧 Configuração:")
        print(f"   Diretório: {merged_config['pdf_dir']}")
        print(f"   Keywords: {merged_config['keywords_list']}")
        print(f"   Saída: {merged_config['output_path']}")
        print(f"   Modo: {mode}")
        print(f"   Verbose: {merged_config['verbose']}")
        print()
        
        # Executa comando baseado no modo
        try:
            if mode == "convert_md":
                self.run_convert_markdown(args, config)
            elif mode == "full_analysis":
                self.run_full_analysis(args, config)
            elif mode == "openai":
                self.run_openai_analysis(args, config)
            else:
                # Modo tradicional
                self.run_traditional_analysis(args, config)
                
        except KeyboardInterrupt:
            print("\n❌ Operação cancelada pelo usuário.")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Erro durante a execução: {e}")
            if merged_config['verbose']:
                import traceback
                traceback.print_exc()
            sys.exit(1)


def main():
    """Função principal"""
    cli = KeywordAnalyzerCLI()
    cli.run()


if __name__ == "__main__":
    main() 