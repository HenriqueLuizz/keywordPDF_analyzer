"""
Processador de CSV - Salvamento de resultados
"""

import os
import pandas as pd
from typing import List, Dict, Any


class CSVProcessor:
    """Processador de arquivos CSV"""
    
    def __init__(self):
        pass
    
    
    def save_single_result_with_keywords(self, result: Dict[str, Any], output_path: str, keywords: List[str], verbose: bool = False) -> None:
        """
        Salva um único resultado no CSV com colunas dinâmicas baseadas nas palavras-chave
        
        Args:
            result: Dicionário com os dados do resultado
            output_path: Caminho para salvar o arquivo
            keywords: Lista de palavras-chave para criar colunas
            verbose: Modo verboso
        """
        # Cria diretório se não existir
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            # Define as colunas baseadas nas palavras-chave
            columns = ['filename', 'company', 'date', 'resumo'] + keywords
            
            # Verifica se o arquivo já existe
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                try:
                    # Lê o CSV existente
                    df = pd.read_csv(output_path)
                    
                    # Garante que todas as colunas existam
                    for col in columns:
                        if col not in df.columns:
                            df[col] = ''
                    
                    # Adiciona nova linha
                    df = pd.concat([df, pd.DataFrame([result])], ignore_index=True)
                except Exception as e:
                    # Se não conseguir ler o CSV existente, cria um novo
                    if verbose:
                        print(f"  ⚠️  Erro ao ler CSV existente, criando novo: {e}")
                    df = pd.DataFrame([result], columns=columns)
            else:
                # Cria novo DataFrame com cabeçalho
                df = pd.DataFrame([result], columns=columns)
            
            # Salva o arquivo
            df.to_csv(output_path, index=False, encoding="utf-8")
            
            if verbose:
                print(f"  💾 Resultado salvo: {result.get('filename', 'N/A')}")
                
        except Exception as e:
            print(f"❌ Erro ao salvar resultado: {e}")
    
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