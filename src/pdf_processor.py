"""
Processador de PDFs - Funcionalidades tradicionais
"""

import os
import re
import csv
import PyPDF2
from typing import List, Dict, Any, Tuple
from collections import Counter

from .config_manager import ConfigManager


class PDFProcessor:
    """Processador de arquivos PDF com funcionalidades tradicionais"""
    
    # Mapping de meses para números
    MONTHS = {
        "january": "01", "february": "02", "march": "03", "april": "04",
        "may": "05", "june": "06", "july": "07", "august": "08",
        "september": "09", "october": "10", "november": "11", "december": "12",
        "janeiro": "01", "fevereiro": "02", "março": "03", "abril": "04",
        "maio": "05", "junho": "06", "julho": "07", "agosto": "08",
        "setembro": "09", "outubro": "10", "novembro": "11", "dezembro": "12"
    }
    
    def __init__(self):
        self.config_manager = ConfigManager()
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extrai texto de um arquivo PDF
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            Texto extraído do PDF
        """
        try:
            with open(pdf_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                text = "\n".join(
                    page.extract_text() for page in reader.pages 
                    if page.extract_text()
                )
            return text
        except Exception as e:
            print(f"Erro ao extrair texto do PDF {pdf_path}: {e}")
            return ""
    
    def extract_date(self, text: str, regex_date) -> str:
        """
        Extrai data do texto usando regex
        
        Args:
            text: Texto para extrair a data
            regex_date: Regex compilado para extrair data
            
        Returns:
            Data no formato YYYYMMDD ou "00000000" se não encontrada
        """
        match = re.search(regex_date, text)
        
        if match:
            day, month_text, year = match.groups()
            month = self.MONTHS.get(month_text.lower())
            if month:
                return f"{year}{month}{int(day):02d}"  # Formato YYYYMMDD
        return "00000000"  # Retorno padrão se a data não for encontrada
    
    def find_company_and_date(self, text: str, regex_company, regex_date) -> Tuple[str, str]:
        """
        Encontra empresa e data no texto
        
        Args:
            text: Texto para análise
            regex_company: Regex para extrair empresa
            regex_date: Regex para extrair data
            
        Returns:
            Tupla (empresa, data)
        """
        company_match = re.search(regex_company, text)
        company = company_match.group(1) if company_match else "UNKNOWN"
        company = company.split('(')[0].strip().replace(' ', '_')
        
        date = self.extract_date(text, regex_date)
        
        return company, date
    
    def contains_keywords(self, text: str, keywords: List[str]) -> bool:
        """
        Verifica se o texto contém alguma palavra-chave
        
        Args:
            text: Texto para verificar
            keywords: Lista de palavras-chave
            
        Returns:
            True se contém alguma palavra-chave, False caso contrário
        """
        return any(keyword.lower() in text.lower() for keyword in keywords)
    
    def check_keywords_in_text(self, text: str, keywords: List[str]) -> List[int]:
        """
        Verifica a presença de palavras-chave no texto
        
        Args:
            text: Texto para verificar
            keywords: Lista de palavras-chave
            
        Returns:
            Lista com 1 para cada palavra-chave encontrada, 0 caso contrário
        """
        return [1 if keyword.lower() in text.lower() else 0 for keyword in keywords]
    
    def get_unique_filename(self, directory: str, base_filename: str) -> str:
        """
        Gera um nome de arquivo único adicionando contador se necessário
        
        Args:
            directory: Diretório onde verificar
            base_filename: Nome base do arquivo
            
        Returns:
            Nome de arquivo único
        """
        name, ext = os.path.splitext(base_filename)
        new_filename = base_filename
        counter = 1
        
        while os.path.isfile(os.path.join(directory, new_filename)):
            new_filename = f"{name} ({counter}){ext}"
            counter += 1
        
        return new_filename
    
    def process_directory(
        self, 
        directory: str, 
        keywords_file: str, 
        rename_files: bool = False,
        verbose: bool = False
    ) -> List[List[str]]:
        """
        Processa todos os PDFs em um diretório
        
        Args:
            directory: Diretório com arquivos PDF
            keywords_file: Arquivo com lista de palavras-chave
            rename_files: Se deve renomear arquivos
            verbose: Modo verboso
            
        Returns:
            Lista de resultados (cada linha é uma lista)
        """
        # Carrega configuração
        config = self.config_manager.load_config()
        keywords = self.config_manager.load_keywords(keywords_file)
        
        if not keywords:
            print("Aviso: Nenhuma palavra-chave carregada")
            return []
        
        # Prepara cabeçalho
        header = [keyword.replace(',', '-').replace(' ', '_') for keyword in keywords]
        results = [["file_name", "company", "date"] + header]
        
        # Processa cada PDF
        for filename in os.listdir(directory):
            if not filename.lower().endswith(".pdf"):
                continue
                
            pdf_path = os.path.join(directory, filename)
            
            if verbose:
                print(f"Processando: {filename}")
            
            # Extrai texto
            text = self.extract_text_from_pdf(pdf_path)
            if not text:
                if verbose:
                    print(f"  Aviso: Não foi possível extrair texto de {filename}")
                continue
            
            # Extrai empresa e data
            company, date = self.find_company_and_date(
                text, config['regex_company'], config['regex_date']
            )
            
            # Renomeia arquivo se solicitado
            if rename_files:
                if company != 'UNKNOWN' and date != '00000000':
                    new_filename = self.get_unique_filename(
                        directory, f"{company}_{date}.pdf"
                    )
                    new_path = os.path.join(directory, new_filename)
                    
                    if not os.path.isfile(new_path):
                        os.rename(pdf_path, new_path)
                        if verbose:
                            print(f"  Renomeado: {filename} -> {new_filename}")
                        filename = new_filename
                    else:
                        if verbose:
                            print(f"  Não foi possível renomear {filename}")
            
            # Verifica palavras-chave
            keyword_results = self.check_keywords_in_text(text, keywords)
            row = [filename, company, date] + keyword_results
            results.append(row)
            
            if self.contains_keywords(text, keywords):
                if verbose:
                    print(f"  Palavras-chave encontradas em {filename}")
            else:
                if verbose:
                    print(f"  Nenhuma palavra-chave encontrada em {filename}")
        
        return results
    
    def convert_to_markdown(
        self, 
        input_dir: str, 
        output_dir: str, 
        verbose: bool = False
    ) -> None:
        """
        Converte PDFs para Markdown usando docling
        
        Args:
            input_dir: Diretório com arquivos PDF
            output_dir: Diretório para salvar arquivos Markdown
            verbose: Modo verboso
        """
        try:
            from docling.document_converter import DocumentConverter
        except ImportError:
            print("Erro: docling não está instalado. Execute: pip install docling")
            return
        
        # Cria diretório de saída se não existir
        os.makedirs(output_dir, exist_ok=True)
        
        converter = DocumentConverter()
        
        for filename in os.listdir(input_dir):
            if not filename.lower().endswith(".pdf"):
                continue
                
            pdf_path = os.path.join(input_dir, filename)
            
            if verbose:
                print(f"Convertendo: {filename}")
            
            try:
                # Converte PDF para Markdown
                conv_result = converter.convert(pdf_path)
                
                # Salva arquivo Markdown
                doc_filename = filename.split(".")[0]
                output_path = os.path.join(output_dir, f"{doc_filename}.md")
                
                with open(output_path, "w", encoding="utf-8") as fp:
                    fp.write(conv_result.document.export_to_markdown())
                
                if verbose:
                    print(f"  Salvo: {output_path}")
                    
            except Exception as e:
                print(f"  Erro ao converter {filename}: {e}")
    
    def save_results(self, results: List[List[str]], output_path: str) -> None:
        """
        Salva resultados em arquivo CSV
        
        Args:
            results: Lista de resultados
            output_path: Caminho para salvar o arquivo
        """
        # Cria diretório se não existir
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(results)
        
        print(f"Resultados salvos em: {output_path}") 