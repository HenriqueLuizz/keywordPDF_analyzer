# KeywordPDF Analyzer

Análise de documentos PDF com extração de informações usando IA.

## 🚀 Como usar

### 1. Configuração

Crie um arquivo `config.ini` na raiz do projeto:

```ini
[CONFIG]
# Diretórios e arquivos
keywords_list = keywords.txt
pdf_dir = files/
output_path = files/

# Configuração de IA
ai_provider = openai
ai_model = gpt-4o

# Opções de processamento
verbose = true
keep_markdown = false
```

### 2. Preparação

1. **Coloque seus PDFs na pasta `files/`**
2. **Configure suas keywords no arquivo `keywords.txt`**:
   ```
   aumento de capital
   ações ordinárias
   estrutura administrativa
   ```
3. **Configure sua chave da OpenAI** (crie um arquivo `.env`):
   ```
   OPENAI_API_KEY=sua_chave_aqui
   ```

### 3. Execução

```bash
python keyword_analyzer.py
```

## 📋 Fluxo da Aplicação

1. **Configuração**: Carrega `config.ini` ou usa valores padrão
2. **Busca PDFs**: Procura arquivos `.pdf` na pasta `files/`
3. **Conversão**: Converte PDFs para Markdown usando `docling`
4. **Análise IA**: Envia para o modelo LLM configurado
5. **Extração**: Coleta informações obrigatórias:
   - `company`: Nome da empresa
   - `date`: Data do documento
   - `resumo`: Resumo do documento
   - `keyword`: Palavra-chave encontrada
   - `sentence`: Frase com a palavra-chave
6. **Salvamento**: Gera arquivo `resultados.csv` na pasta dos PDFs
7. **Limpeza**: Remove arquivos markdown temporários (configurável)
8. **Resumo**: Exibe estatísticas no console

## ⚙️ Configurações

### config.ini

| Parâmetro | Descrição | Padrão |
|-----------|-----------|--------|
| `keywords_list` | Arquivo com palavras-chave | `keywords.txt` |
| `pdf_dir` | Pasta com arquivos PDF | `files/` |
| `output_path` | Pasta para salvar CSV | `files/` |
| `ai_provider` | Provedor de IA (`openai`/`local`) | `local` |
| `ai_model` | Modelo de IA | `gemma3:4b` |
| `verbose` | Modo verboso | `false` |
| `keep_markdown` | Manter arquivos markdown | `false` |

### Provedores de IA

#### OpenAI
- Configure `OPENAI_API_KEY` no arquivo `.env`
- Modelos suportados: `gpt-4o`, `gpt-4`, `gpt-3.5-turbo`

#### Local (Ollama)
- Instale o [Ollama](https://ollama.ai)
- Modelos suportados: `llama2`, `gemma3:4b`, `mistral`, etc.

## 📊 Saída

O arquivo `resultados.csv` contém:

| Coluna | Descrição |
|--------|-----------|
| `filename` | Nome do arquivo PDF |
| `company` | Nome da empresa identificada |
| `date` | Data do documento |
| `resumo` | Resumo do documento |
| `keyword` | Palavra-chave encontrada |
| `sentence` | Frase com a palavra-chave |

## 🔧 Instalação

```bash
# Clone o repositório
git clone <url-do-repositorio>
cd keywordPDF_analyzer

# Instale as dependências
pip install -r requirements.txt

# Configure o ambiente
cp config.ini.example config.ini
# Edite config.ini conforme necessário
```

## 📝 Exemplo de uso

1. **Preparar arquivos**:
   ```
   files/
   ├── documento1.pdf
   ├── documento2.pdf
   └── documento3.pdf
   
   keywords.txt:
   aumento de capital
   ações ordinárias
   ```

2. **Executar análise**:
   ```bash
   python keyword_analyzer.py
   ```

3. **Resultado**:
   ```
   🚀 Iniciando KeywordPDF Analyzer
   ==================================================
   📁 Encontrados 3 arquivos PDF
   🔄 Convertendo PDFs para Markdown...
   🤖 Analisando documentos com IA...
   ✅ Resultados salvos em: files/resultados.csv
   
   📊 RESUMO DA ANÁLISE
   ==================================================
   📄 Arquivos analisados: 3
   🏢 Empresas identificadas: 3
   📅 Datas extraídas: 3
   🔍 Keywords encontradas: 2
   ==================================================
   ✅ Análise concluída com sucesso!
   ```

## 🛠️ Desenvolvimento

### Estrutura do projeto

```
keywordPDF_analyzer/
├── keyword_analyzer.py      # Script principal
├── config.ini              # Configuração
├── keywords.txt            # Palavras-chave
├── files/                  # PDFs para análise
├── src/
│   ├── __init__.py
│   ├── config_manager.py   # Gerenciador de configuração
│   ├── pdf_processor.py    # Processamento de PDFs
│   ├── ai_analyzer.py      # Análise com IA
│   ├── csv_processor.py    # Processamento CSV
│   ├── ai_connector.py     # Conectores de IA
│   └── local_model.py      # Modelos locais
└── requirements.txt        # Dependências
```

## 📄 Licença

MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.
