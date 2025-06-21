# KeywordPDF Analyzer

KeywordPDF Analyzer é uma ferramenta para processar arquivos PDF, extrair informações relevantes baseadas em palavras-chave, renomear arquivos e gerar relatórios em formato CSV. Esta ferramenta é ideal para automatizar a classificação e análise de documentos.

## 🚀 Novidades

- **CLI organizado e amigável** com múltiplos modos de operação
- **Análise tradicional** (sem OpenAI) - funcionalidade original
- **Análise com OpenAI** - extração inteligente de informações
- **Conversão para Markdown** usando docling
- **Análise completa** combinando ambos os modos

## ✨ Funcionalidades

### Modo Tradicional (Original)
- Extrai texto de arquivos PDF
- Identifica palavras-chave específicas nos documentos
- Renomeia arquivos PDF baseado em nomes de empresas e datas extraídas
- Gera relatório CSV com ocorrências de palavras-chave em cada documento

### Modo OpenAI (Novo)
- Converte PDFs para Markdown usando docling
- Analisa documentos com IA para extrair informações estruturadas
- Enriquece dados com informações de empresa, data e resumo
- Identifica frases específicas que contêm palavras-chave

## 📦 Instalação

Certifique-se de ter Python instalado (>= 3.7). Em seguida, instale as dependências:

```sh
pip install -r requirements.txt
```

### Configuração da OpenAI (Opcional)

Para usar as funcionalidades de IA, configure sua chave da API OpenAI:

```sh
export OPENAI_API_KEY="sua-chave-api-aqui"
```

Ou crie um arquivo `.env`:
```
OPENAI_API_KEY=sua-chave-api-aqui
```

## 🎯 Uso

### CLI Principal

```sh
python keyword_analyzer.py [OPÇÕES]
```

### Modos de Operação

#### 1. Análise Tradicional (Padrão)
```sh
python keyword_analyzer.py --dir files/ --keywords keywords.txt --output results.csv
```

#### 2. Conversão para Markdown
```sh
python keyword_analyzer.py --convert-md --dir files/ --output output/
```

#### 3. Análise com OpenAI
```sh
python keyword_analyzer.py --openai --dir files/ --keywords keywords.txt --output results/
```

#### 4. Análise Completa
```sh
python keyword_analyzer.py --full-analysis --dir files/ --keywords keywords.txt --output results/
```

### Parâmetros

#### Parâmetros Principais
- `--dir`, `-d`: Diretório contendo arquivos PDF
- `--keywords`, `-k`: Arquivo com lista de palavras-chave
- `--output`, `-o`: Arquivo/diretório de saída (padrão: results.csv)

#### Modos de Operação
- `--convert-md`: Converte PDFs para Markdown
- `--openai`: Habilita análise com OpenAI
- `--full-analysis`: Executa análise completa (conversão + OpenAI + keywords)

#### Opções Adicionais
- `--rename`: Renomeia arquivos PDF baseado no conteúdo
- `--config`: Arquivo de configuração personalizado
- `--verbose`, `-v`: Modo verboso

### Exemplos de Uso

```sh
# Análise básica
python keyword_analyzer.py --dir ./pdf_files --keywords keywords.txt

# Análise com renomeação de arquivos
python keyword_analyzer.py --dir ./pdf_files --keywords keywords.txt --rename

# Conversão para Markdown
python keyword_analyzer.py --convert-md --dir ./pdf_files --output ./markdown_files

# Análise com OpenAI
python keyword_analyzer.py --openai --dir ./pdf_files --keywords keywords.txt --output ./results

# Análise completa com modo verboso
python keyword_analyzer.py --full-analysis --dir ./pdf_files --keywords keywords.txt --output ./results --verbose
```

## ⚙️ Configuração

### Arquivo de Configuração (`config.ini`)

```ini
[CONFIG]
keywords_list = keywords.txt
renamefiles = false
pdf_dir = files/
output_path = files/
regex_date = "\n[\w\s]+, (\d{1,2}) de (\w+) de (\d{4})\."
regex_company = "^\s*(.+?)\s*(?:S\.A\.|SA|Companhia|CNPJ|NIRE|–)"
```

### Arquivo de Palavras-chave (`keywords.txt`)

Cada linha será interpretada como uma "palavra-chave", mesmo que consista em mais de uma palavra.

```txt
aumento de capital
ações ordinárias
estrutura administrativa
ações
capital
```

## 📊 Saída

### Modo Tradicional
- **PDFs renomeados** (se `--rename` estiver habilitado)
- **Relatório CSV**: Arquivo com ocorrências de palavras-chave

### Modo OpenAI
- **Arquivos Markdown**: Conversão dos PDFs
- **Relatório CSV enriquecido**: Com informações extraídas pela IA

### Análise Completa
- **Resultados tradicionais**: `traditional_results.csv`
- **Resultados OpenAI**: `openai_results.csv`
- **Arquivos Markdown**: Na pasta `markdown/`

## 🧪 Testes

Execute os testes para verificar se tudo está funcionando:

```sh
python test_cli.py
```

## 📁 Estrutura do Projeto

```
keywordPDF_analyzer/
├── keyword_analyzer.py      # CLI principal
├── src/                     # Módulos do sistema
│   ├── __init__.py
│   ├── config_manager.py    # Gerenciamento de configuração
│   ├── pdf_processor.py     # Processamento de PDFs
│   ├── openai_analyzer.py   # Análise com OpenAI
│   └── csv_processor.py     # Processamento de CSV
├── files/                   # Arquivos PDF de entrada
├── output/                  # Arquivos de saída
├── config.ini              # Configuração
├── keywords.txt            # Palavras-chave
├── requirements.txt        # Dependências
└── README.md              # Documentação
```

## 🔧 Migração da Versão Anterior

Se você estava usando a versão anterior (`keywordPDF.py`), pode continuar usando:

```sh
python keywordPDF.py --dir files/ --keywords keywords.txt --rename
```

O novo CLI (`keyword_analyzer.py`) oferece funcionalidades adicionais mantendo compatibilidade com o comportamento original.

## 📄 Licença

Este projeto está licenciado sob a Licença MIT.
