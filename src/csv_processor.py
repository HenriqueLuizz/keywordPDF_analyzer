"""
Processador de CSV - Funcionalidades para manipulação de dados CSV
"""

import os
import csv
import pandas as pd
from typing import List, Dict, Any


class CSVProcessor:
    """Processador de arquivos CSV"""
    
    def __init__(self):
        pass
    
    def read_csv(self, source_file: str) -> pd.DataFrame:
        """
        Lê um arquivo CSV e retorna um DataFrame do pandas
        
        Args:
            source_file: Caminho para o arquivo CSV a ser lido
            
        Returns:
            DataFrame contendo os dados do CSV
        """
        # Verifica se o arquivo existe e é um CSV
        if not os.path.exists(source_file):
            print(f"Arquivo {source_file} não encontrado.")
            return pd.DataFrame()
        
        if not source_file.lower().endswith(".csv"):
            print(f"Arquivo {source_file} não é um CSV válido.")
            return pd.DataFrame()
        
        try:
            with open(source_file, "r", encoding="utf-8") as fp:
                df = pd.read_csv(fp)
                return df
        except Exception as e:
            print(f"Erro ao ler arquivo CSV {source_file}: {e}")
            return pd.DataFrame()
    
    def save_results(self, results: List[List[str]], output_path: str, include_summary: bool = True, context_chars: int = 30) -> None:
        """
        Salva resultados em arquivo CSV
        
        Args:
            results: Lista de resultados (cada linha é uma lista)
            output_path: Caminho para salvar o arquivo
            include_summary: Se deve incluir coluna resumo
            context_chars: Número de caracteres de contexto para palavras-chave
        """
        # Cria diretório se não existir
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Se não há resultados, cria arquivo vazio
        if not results:
            with open(output_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([])
            print(f"Arquivo vazio criado em: {output_path}")
            return
        
        # Processa resultados para aplicar contexto se necessário
        processed_results = self._process_results_with_context(results, context_chars)
        
        # Remove coluna resumo se não deve ser incluída
        if not include_summary and len(processed_results) > 0:
            processed_results = self._remove_summary_column(processed_results)
        
        with open(output_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(processed_results)
        
        print(f"Resultados salvos em: {output_path}")
    
    def save_enriched_results(self, df: pd.DataFrame, output_path: str, include_summary: bool = True) -> None:
        """
        Salva DataFrame enriquecido em arquivo CSV
        
        Args:
            df: DataFrame a ser salvo
            output_path: Caminho para salvar o arquivo
            include_summary: Se deve incluir coluna resumo
        """
        # Cria diretório se não existir
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Remove coluna resumo se não deve ser incluída
        if not include_summary and 'resumo' in df.columns:
            df = df.drop(columns=['resumo'])
        
        try:
            df.to_csv(output_path, index=False, encoding="utf-8")
            print(f"Resultados enriquecidos salvos em: {output_path}")
        except Exception as e:
            print(f"Erro ao salvar resultados: {e}")
    
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
    
    def merge_results(self, traditional_results: List[List[str]], openai_results: pd.DataFrame) -> pd.DataFrame:
        """
        Mescla resultados tradicionais com resultados da OpenAI
        
        Args:
            traditional_results: Resultados da análise tradicional
            openai_results: Resultados da análise com OpenAI
            
        Returns:
            DataFrame mesclado
        """
        if not traditional_results:
            return openai_results
        
        # Converte resultados tradicionais para DataFrame
        traditional_df = pd.DataFrame(traditional_results[1:], columns=traditional_results[0])
        
        # Mescla os DataFrames
        merged_df = pd.merge(
            traditional_df, 
            openai_results, 
            on='file_name', 
            how='outer',
            suffixes=('_traditional', '_openai')
        )
        
        return merged_df
    
    def export_to_json(self, df: pd.DataFrame, output_path: str) -> None:
        """
        Exporta DataFrame para JSON
        
        Args:
            df: DataFrame a ser exportado
            output_path: Caminho para salvar o arquivo JSON
        """
        # Cria diretório se não existir
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            # Converte DataFrame para formato JSON
            json_data = df.to_dict(orient='records')
            
            with open(output_path, 'w', encoding='utf-8') as f:
                import json
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            print(f"Dados exportados para JSON: {output_path}")
        except Exception as e:
            print(f"Erro ao exportar para JSON: {e}")
    
    def validate_csv_structure(self, df: pd.DataFrame, expected_columns: List[str]) -> bool:
        """
        Valida estrutura de um DataFrame CSV
        
        Args:
            df: DataFrame a ser validado
            expected_columns: Lista de colunas esperadas
            
        Returns:
            True se a estrutura é válida, False caso contrário
        """
        missing_columns = set(expected_columns) - set(df.columns)
        
        if missing_columns:
            print(f"Colunas ausentes no CSV: {missing_columns}")
            return False
        
        return True
    
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpa DataFrame removendo linhas vazias e normalizando dados
        
        Args:
            df: DataFrame a ser limpo
            
        Returns:
            DataFrame limpo
        """
        # Remove linhas completamente vazias
        df_cleaned = df.dropna(how='all')
        
        # Remove espaços em branco das colunas de texto
        for col in df_cleaned.select_dtypes(include=['object']).columns:
            df_cleaned[col] = df_cleaned[col].astype(str).str.strip()
        
        return df_cleaned
    
    def _process_results_with_context(self, results: List[List[str]], context_chars: int) -> List[List[str]]:
        """
        Processa resultados aplicando contexto às palavras-chave
        
        Args:
            results: Lista de resultados
            context_chars: Número de caracteres de contexto
            
        Returns:
            Lista de resultados processada
        """
        if not results or len(results) < 2:
            return results
        
        processed_results = [results[0]]  # Mantém cabeçalho
        
        for row in results[1:]:
            processed_row = row.copy()
            
            # Aplica contexto às colunas de palavras-chave (após as primeiras 3 colunas)
            for i in range(3, len(processed_row)):
                if processed_row[i] and processed_row[i] != 'None':
                    # Adiciona contexto se o valor não estiver vazio
                    processed_row[i] = f"...{processed_row[i]}..."
            
            processed_results.append(processed_row)
        
        return processed_results
    
    def _remove_summary_column(self, results: List[List[str]]) -> List[List[str]]:
        """
        Remove a coluna resumo dos resultados
        
        Args:
            results: Lista de resultados
            
        Returns:
            Lista de resultados sem coluna resumo
        """
        if not results:
            return results
        
        # Encontra índice da coluna resumo
        header = results[0]
        summary_index = None
        
        for i, col in enumerate(header):
            if col.lower() in ['resumo', 'summary', 'resume']:
                summary_index = i
                break
        
        if summary_index is None:
            return results
        
        # Remove coluna resumo de todas as linhas
        processed_results = []
        for row in results:
            processed_row = row[:summary_index] + row[summary_index + 1:]
            processed_results.append(processed_row)
        
        return processed_results 