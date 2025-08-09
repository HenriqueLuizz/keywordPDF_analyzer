"""
Processador de PDF - Conversão para Markdown
"""

import os
import tempfile
from typing import List, Optional
from docling.document_converter import DocumentConverter

class PDFProcessor:
    """Processador de arquivos PDF - Conversão para Markdown"""
    
    def __init__(self):
        pass
    
    def convert_single_pdf_to_markdown(
        self, 
        pdf_path: str, 
        verbose: bool = False
    ) -> Optional[str]:
        """
        Converte um único PDF para Markdown sob demanda
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            verbose: Modo verboso
            
        Returns:
            Conteúdo Markdown como string, ou None se falhar
        """
        try:
            converter = DocumentConverter()
            file_converted = converter.convert(pdf_path)
            file_converted = file_converted.document.export_to_markdown()
            return file_converted

        except ImportError:
            print("❌ Erro: docling não está instalado. Execute: pip install docling")
            return None
        except Exception as e:
            # Captura erros internos (ex.: dependências como torch levantando AttributeError)
            print(f"❌ Falha na conversão com docling: {e}")
            return None
        
    
    def get_pdf_files(self, directory: str, recursive: bool = True) -> List[str]:
        """
        Lista todos os arquivos PDF em um diretório, com opção de busca recursiva
        
        Args:
            directory: Diretório para buscar
            recursive: Se True, busca recursivamente em subdiretórios
            
        Returns:
            Lista de nomes de arquivos PDF
        """
        if not os.path.exists(directory):
            return []
        
        pdf_files = []
        if recursive:
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        pdf_files.append(os.path.join(root, file))
        else:
            pdf_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.lower().endswith('.pdf')]

        return pdf_files
