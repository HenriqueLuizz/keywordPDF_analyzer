"""
Analisador OpenAI - Funcionalidades de análise com IA
"""

import os
import json
import pandas as pd
import tiktoken
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

from .config_manager import ConfigManager


class OpenAIAnalyzer:
    """Analisador que utiliza OpenAI para processar documentos"""
    
    def __init__(self):
        load_dotenv()
        self.config_manager = ConfigManager()
        
        # Tenta inicializar cliente OpenAI
        try:
            from openai import OpenAI
            self.client = OpenAI()
            self._configured = True
        except ImportError:
            print("Aviso: openai não está instalado. Execute: pip install openai")
            self._configured = False
        except Exception as e:
            print(f"Aviso: OpenAI não configurada: {e}")
            self._configured = False
    
    def is_configured(self) -> bool:
        """Verifica se OpenAI está configurada"""
        return self._configured and os.getenv("OPENAI_API_KEY") is not None
    
    def count_tokens(self, messages: List[Dict[str, str]], model: str = "gpt-4o") -> int:
        """
        Conta tokens em uma lista de mensagens
        
        Args:
            messages: Lista de mensagens
            model: Modelo para contar tokens
            
        Returns:
            Número de tokens
        """
        try:
            encoding = tiktoken.encoding_for_model(model)
            num_tokens = 0
            
            for message in messages:
                # Estimativa conservadora do overhead por mensagem
                num_tokens += 4
                for key, value in message.items():
                    num_tokens += len(encoding.encode(value))
            
            num_tokens += 2  # tokens adicionais do sistema
            return num_tokens
        except Exception as e:
            print(f"Erro ao contar tokens: {e}")
            return 0
    
    def extract_info_from_file(
        self, 
        document_content: str, 
        context_system: str, 
        question: str
    ) -> Dict[str, Any]:
        """
        Extrai informações de um documento usando OpenAI
        
        Args:
            document_content: Conteúdo do documento
            context_system: Contexto do sistema para OpenAI
            question: Pergunta para OpenAI
            
        Returns:
            Resposta da OpenAI ou dicionário com erro
        """
        if not self.is_configured():
            return {"error": "OpenAI não está configurada"}
        
        max_tokens = 16384
        messages = [
            {
                "role": "system",
                "content": context_system
            },
            {
                "role": "user",
                "content": (
                    f"Use os dados a seguir como referência para responder a seguinte pergunta.\n\n"
                    f"Documentos: {document_content}\n\n"
                    f"Pergunta: {question}"
                )
            }
        ]
        
        tokens = self.count_tokens(messages, model="gpt-4o")
        print(f"Tokens: {tokens}")
        
        # Verifica se o número de tokens excede o limite do modelo
        if tokens > 16384:
            print(f"Mensagem muito longa. Número de tokens: {tokens}.")
            return {
                "error": "Mensagem muito longa. Número de tokens excede o limite do modelo."
            }
        
        if tokens * 2 > 16384:
            max_tokens = tokens * 2
        
        # Se o número de tokens estiver dentro do limite, envia a mensagem para a API
        try:
            resposta = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.0,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                max_tokens=max_tokens,
            )
            
            resposta_texto = resposta.choices[0].message.content
            print(resposta_texto)
            
            return resposta_texto
        except Exception as e:
            return {"error": f"Ocorreu um erro: {e}"}
    
    def enrich_dataframe(
        self, 
        df: pd.DataFrame, 
        directory: str,
        verbose: bool = False,
        include_summary: bool = True
    ) -> pd.DataFrame:
        """
        Enriquece DataFrame com informações extraídas via OpenAI
        
        Args:
            df: DataFrame a ser enriquecido
            directory: Diretório com arquivos Markdown
            verbose: Modo verboso
            include_summary: Se deve incluir coluna resumo
            
        Returns:
            DataFrame enriquecido
        """
        # Ajusta o prompt baseado nas opções
        if include_summary:
            context_system = '''
                Você é um assistente especializado em processar documentos.
                Deve ser capaz de extrair as informações de nome da companhia e data que foi emitido o documento fornecidos e um resumo de até 270 caracteres.
                O retorno deve ser um dicionário puro sem formação com apenhas as chaves 'company', 'date' e 'resumo'.
                Exemplo de retorno:
                {
                    "company": "Nome da Companhia",
                    "date": "2023-10-01",
                    "resumo": "Resumo do documento"
                }
                Caso não consiga extrair as informações, retorne um dicionário vazio.
            '''
        else:
            context_system = '''
                Você é um assistente especializado em processar documentos.
                Deve ser capaz de extrair as informações de nome da companhia e data que foi emitido o documento fornecidos.
                O retorno deve ser um dicionário puro sem formação com apenhas as chaves 'company' e 'date'.
                Exemplo de retorno:
                {
                    "company": "Nome da Companhia",
                    "date": "2023-10-01"
                }
                Caso não consiga extrair as informações, retorne um dicionário vazio.
            '''
        
        question = 'Qual o nome da companhia e a data que foi emitido o documento?'
        
        for index, row in df.iterrows():
            file_name = row['file_name'].strip(".pdf") + ".md"
            file_path = os.path.join(directory, file_name)
            
            if verbose:
                print(f"Verificando o arquivo: {file_path}")
            
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as fp:
                    content = fp.read()
                    
                    if verbose:
                        print(f"Processando o arquivo: {file_path}")
                    
                    doc_info = self.extract_info_from_file(
                        document_content=content,
                        context_system=context_system,
                        question=question
                    )
                    
                    try:
                        if isinstance(doc_info, str):
                            doc_info = json.loads(doc_info)
                        
                        if 'error' not in doc_info:
                            df.at[index, 'company'] = doc_info.get('company', '')
                            df.at[index, 'date'] = doc_info.get('date', '')
                            
                            # Adiciona resumo apenas se solicitado
                            if include_summary:
                                df.at[index, 'resumo'] = doc_info.get('resumo', '')
                            
                            if verbose:
                                print(f"Informações extraídas: {doc_info}")
                        else:
                            if verbose:
                                print(f"Erro na extração: {doc_info['error']}")
                            df.at[index, 'company'] = "Erro na extração"
                            df.at[index, 'date'] = "Erro na extração"
                            if include_summary:
                                df.at[index, 'resumo'] = "Erro na extração"
                            
                    except json.JSONDecodeError:
                        if verbose:
                            print(f"Erro ao decodificar resposta: {doc_info}")
                        df.at[index, 'company'] = "Erro na decodificação"
                        df.at[index, 'date'] = "Erro na decodificação"
                        if include_summary:
                            df.at[index, 'resumo'] = "Erro na decodificação"
            else:
                if verbose:
                    print(f"Arquivo {file_path} não encontrado. Pulando para o próximo.")
                df.at[index, 'company'] = "Arquivo não encontrado"
                df.at[index, 'date'] = "Arquivo não encontrado"
                if include_summary:
                    df.at[index, 'resumo'] = "Arquivo não encontrado"
        
        return df
    
    def find_keywords_in_file(
        self, 
        file_path: str, 
        keywords: List[str],
        verbose: bool = False,
        context_chars: int = 30
    ) -> Dict[str, Any]:
        """
        Encontra palavras-chave em um arquivo usando OpenAI
        
        Args:
            file_path: Caminho para o arquivo
            keywords: Lista de palavras-chave
            verbose: Modo verboso
            context_chars: Número de caracteres de contexto para palavras-chave
            
        Returns:
            Dicionário com resultados da análise
        """
        context_system = f'''
            Você é um assistente especializado em processar documentos.
            Deve analisar o documento e identificar quais das palavras-chave fornecidas estão presentes no texto.
            
            IMPORTANTE: Na chave "keywords", retorne APENAS as palavras-chave que foram ENCONTRADAS no documento, não todas as palavras-chave da lista.
            
            Para cada palavra-chave encontrada, extraia as frases do documento que a contém, incluindo aproximadamente {context_chars} caracteres antes e depois da palavra-chave para fornecer contexto.
            Se a palavra-chave aparecer mais de uma vez em frases diferentes, separe as frases com " || ".
            
            O retorno deve ser um dicionário JSON válido com a seguinte estrutura:
            {{
                "keywords": ["palavra1", "palavra2"],
                "palavra1": "Frase que contém palavra1 com contexto",
                "palavra2": "Frase que contém palavra2 com contexto || Outra frase com palavra2 e contexto"
            }}
            
            Exemplo:
            - Se a lista for ["aumento", "capital", "ações"] mas só "aumento" e "capital" forem encontrados:
            {{
                "keywords": ["aumento", "capital"],
                "aumento": "A empresa anunciou um aumento de capital social",
                "capital": "O capital social foi aumentado significativamente"
            }}
            
            Caso nenhuma palavra-chave seja encontrada, retorne:
            {{
                "keywords": []
            }}
            
            Caso ocorra erro, retorne:
            {{
                "error": "Descrição do erro"
            }}
        '''
        
        question = f"Analise o documento e identifique quais das seguintes palavras-chave estão presentes: {keywords}\n\nRetorne apenas as palavras-chave ENCONTRADAS no documento com contexto de aproximadamente {context_chars} caracteres."
        
        with open(file_path, "r", encoding="utf-8") as fp:
            content = fp.read()
            
            if verbose:
                print(f"Processando o arquivo: {file_path}")
            
            doc_info = self.extract_info_from_file(
                document_content=content,
                context_system=context_system,
                question=question
            )
            
            try:
                if isinstance(doc_info, str):
                    # Remove formatação markdown se presente
                    cleaned_response = doc_info.strip()
                    if cleaned_response.startswith('```json'):
                        cleaned_response = cleaned_response[7:]
                    if cleaned_response.endswith('```'):
                        cleaned_response = cleaned_response[:-3]
                    
                    cleaned_response = cleaned_response.strip()
                    
                    if verbose:
                        print(f"Resposta limpa: {cleaned_response[:200]}...")
                    
                    return json.loads(cleaned_response)
                return doc_info
            except json.JSONDecodeError as e:
                if verbose:
                    print(f"Erro ao decodificar JSON: {e}")
                    print(f"Resposta original: {doc_info}")
                return {"error": f"Erro ao decodificar resposta: {e}"}
    
    def analyze_documents(
        self, 
        markdown_dir: str, 
        keywords_file: str,
        verbose: bool = False,
        include_summary: bool = True,
        context_chars: int = 30
    ) -> pd.DataFrame:
        """
        Analisa documentos Markdown com OpenAI
        
        Args:
            markdown_dir: Diretório com arquivos Markdown
            keywords_file: Arquivo com palavras-chave
            verbose: Modo verboso
            include_summary: Se deve incluir coluna resumo
            context_chars: Número de caracteres de contexto para palavras-chave
            
        Returns:
            DataFrame com resultados da análise
        """
        # Carrega palavras-chave
        keywords = self.config_manager.load_keywords(keywords_file)
        
        if not keywords:
            print("Aviso: Nenhuma palavra-chave carregada")
            return pd.DataFrame()
        
        # Cria DataFrame base
        results = []
        
        for filename in os.listdir(markdown_dir):
            if not filename.lower().endswith(".md"):
                continue
            
            file_path = os.path.join(markdown_dir, filename)
            pdf_filename = filename.replace(".md", ".pdf")
            
            if verbose:
                print(f"Analisando: {filename}")
            
            # Encontra palavras-chave
            content_result = self.find_keywords_in_file(
                file_path, 
                keywords, 
                verbose,
                context_chars
            )
            
            row = {
                'file_name': pdf_filename,
                'company': '',
                'date': '',
                'keywords': []
            }
            
            # Adiciona coluna resumo apenas se solicitado
            if include_summary:
                row['resumo'] = ''
            
            # Inicializa todas as colunas de palavras-chave como None
            for keyword in keywords:
                row[keyword] = None
            
            if 'error' in content_result:
                if verbose:
                    print(f"Erro ao processar o arquivo {file_path}: {content_result['error']}")
                # Mantém keywords como lista vazia
            else:
                # Obtém apenas as palavras-chave encontradas
                found_keywords = content_result.get('keywords', [])
                row['keywords'] = found_keywords
                
                if verbose:
                    print(f"  Palavras-chave encontradas: {found_keywords}")
                
                # Adiciona frases encontradas apenas para as palavras-chave que foram encontradas
                for keyword in keywords:
                    if keyword in found_keywords and keyword in content_result:
                        row[keyword] = content_result[keyword]
                        if verbose:
                            print(f"  Frase para '{keyword}': {content_result[keyword][:100]}...")
                    # Se não foi encontrada, mantém como None
            
            results.append(row)
        
        df = pd.DataFrame(results)
        
        # Enriquece com informações de empresa e data (e resumo se solicitado)
        df = self.enrich_dataframe(df, markdown_dir, verbose, include_summary)
        
        return df 