# KeywordPDF Analyzer

Uma ferramenta poderosa para análise de documentos PDF com extração de palavras-chave, suporte a OpenAI e conversão para Markdown.

## 🚀 Funcionalidades

- **Análise Tradicional**: Extração de palavras-chave usando regex
- **Análise com OpenAI**: Análise inteligente usando IA
- **Conversão para Markdown**: Conversão de PDFs para formato Markdown
- **Análise Completa**: Combina todos os modos de análise
- **Configuração Automática**: Suporte a arquivo `config.ini` para configurações persistentes
- **Flexibilidade**: Argumentos da linha de comando sobrescrevem configurações do arquivo

## 📋 Pré-requisitos

- Python 3.8+
- Dependências listadas em `requirements.txt`

## 🛠️ Instalação

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd keywordPDF_analyzer
```

2. Crie um ambiente virtual:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure a OpenAI (opcional, apenas para análise com IA):
```bash
export OPENAI_API_KEY="sua-chave-api-aqui"
```

## ⚙️ Configuração

### Configuração Automática (Recomendado)

O sistema suporta configuração automática através do arquivo `config.ini`. Na primeira execução, se o arquivo não existir, ele será criado automaticamente com valores padrão.

#### Exemplo de `config.ini`:

```ini
[CONFIG]
# Diretórios e arquivos
keywords_list = keywords.txt
pdf_dir = files/
output_path = results/

# Modos de operação (true/false)
convert_md = false
openai = false
full_analysis = false
rename = false

# Opções de saída
include_summary = true
context_chars = 30

# Opções de processamento
verbose = false

# Regex patterns (opcional)
regex_date = \n[\w\s]+,\s+(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})\.?
regex_company = ^\s*(.+?)\s*(?:S\.A\.|SA|Companhia|CNPJ|NIRE|–)
```

### Prioridade de Configuração

1. **Linha de comando** (maior prioridade)
2. **config.ini** (prioridade menor)
3. **Valores padrão** (última opção)

## 🎯 Uso

### Uso Simples (com config.ini)

```bash
# Executa com configurações do config.ini
python keyword_analyzer.py
```

### Uso com Argumentos da Linha de Comando

```bash
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
```

### Argumentos Disponíveis

#### Argumentos Principais
- `--dir, -d`: Diretório contendo arquivos PDF (sobrescreve config.ini)
- `--keywords, -k`: Arquivo com lista de palavras-chave (sobrescreve config.ini)
- `--output, -o`: Arquivo de saída (sobrescreve config.ini)

#### Modos de Operação
- `--convert-md`: Converter PDFs para Markdown (sobrescreve config.ini)
- `--openai`: Habilitar análise com OpenAI (sobrescreve config.ini)
- `--full-analysis`: Executar análise completa (sobrescreve config.ini)

#### Opções Adicionais
- `--rename`: Renomear arquivos PDF baseado no conteúdo (sobrescreve config.ini)
- `--config`: Arquivo de configuração personalizado
- `--verbose, -v`: Modo verboso (sobrescreve config.ini)
- `--include-summary`: Incluir coluna resumo no CSV (sobrescreve config.ini)
- `--no-summary`: Excluir coluna resumo do CSV (sobrescreve config.ini)
- `--context-chars`: Número de caracteres de contexto antes/depois das palavras-chave (sobrescreve config.ini)

## 📁 Estrutura de Arquivos

```
keywordPDF_analyzer/
├── keyword_analyzer.py      # CLI principal
├── config.ini              # Configuração automática
├── keywords.txt            # Lista de palavras-chave
├── requirements.txt        # Dependências
├── README.md              # Este arquivo
├── src/                   # Módulos do sistema
│   ├── __init__.py
│   ├── config_manager.py  # Gerenciador de configuração
│   ├── pdf_processor.py   # Processamento de PDFs
│   ├── openai_analyzer.py # Análise com OpenAI
│   └── csv_processor.py   # Processamento de CSV
├── tests/                 # Testes
│   └── test_core.py
├── files/                 # Diretório de entrada (padrão)
└── results/               # Diretório de saída (padrão)
```

## 🔧 Tratamento de Erros

### Configuração Inválida

Quando o `config.ini` contém erros (arquivos inexistentes, valores inválidos, etc.), o sistema:

1. **Mostra os erros** encontrados
2. **Pergunta** se deseja prosseguir com valores padrão
3. **Cria arquivo de exemplo** se necessário

### Exemplo de Interação:

```
⚠️  Problemas encontrados no arquivo de configuração 'config.ini':
   - Arquivo de keywords 'keywords.txt' não existe
   - Diretório de PDFs 'files/' não existe

Deseja prosseguir com valores padrão? (s/N): s
Usando valores padrão...
```

## 🧪 Testes

Execute os testes com:

```bash
# Ative o ambiente virtual primeiro
source .venv/bin/activate

# Execute os testes
pytest tests/
```

## 📊 Saídas

### Análise Tradicional
- Arquivo CSV com colunas: `filename`, `keywords`, `context`, `date`, `company`

### Análise com OpenAI
- Arquivo CSV com colunas: `filename`, `keywords`, `context`, `summary` (opcional), colunas individuais para cada keyword

### Conversão Markdown
- Arquivos `.md` para cada PDF processado

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🆘 Suporte

Para suporte e dúvidas:
1. Verifique a documentação
2. Execute com `--verbose` para mais detalhes
3. Abra uma issue no repositório
