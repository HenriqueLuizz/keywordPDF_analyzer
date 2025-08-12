"""
Processador de PDF - Conversão para Markdown
"""

import os
import tempfile
from typing import List, Optional

from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions
)
from docling.datamodel.settings import settings
from docling.document_converter import DocumentConverter, PdfFormatOption

class PDFProcessor:
    """Processador de arquivos PDF - Conversão para Markdown"""
    
    def __init__(self):
        pass


    def _convert_file(self, pdf_file: str, verbose: bool = False) -> Optional[str]:
        """
        Converte um PDF para Markdown
        """
        
        accelerator_options = AcceleratorOptions(
            num_threads=8, 
            device=AcceleratorDevice.AUTO
        )

        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr=True
        pipeline_options.accelerator_options = accelerator_options
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options.do_cell_matching = True
        

        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options,
                )
            }
        )
        # Enable the profiling to measure the time spent
        settings.debug.profile_pipeline_timings = True

        # Convert the document
        conversion_result = converter.convert(pdf_file)
        doc = conversion_result.document

        # List with total time per document
        doc_conversion_secs = conversion_result.timings["pipeline_total"].times

        md = doc.export_to_markdown()
        # print(md)
        # print(f"Conversion secs: {doc_conversion_secs}")
        return md

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
            return self._convert_file(pdf_path, verbose)

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
