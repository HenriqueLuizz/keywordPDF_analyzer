# KeywordPDF Analyzer

KeywordPDF Analyzer is a tool for processing PDF files, extracting relevant information based on keywords, renaming files, and generating reports in CSV format. This tool is ideal for automating document classification and analysis.

## Features

- Extracts text from PDF files.
- Identifies specific keywords within the documents.
- Renames PDF files based on extracted company names and document dates.
- Generates a CSV report with keyword occurrences in each document.

## Installation

Ensure you have Python installed (>= 3.7). Then, install the required dependencies:

```sh
pip install -r requirements.txt
```

## Usage

Run the script with the following command:

```sh
python keywordpdf.py --dir <PDF_DIRECTORY> --keywords <KEYWORDS_FILE> [--rename] [--config <CONFIG_FILE>]
```

### Parameters:

- `--dir`: Directory containing PDF files (e.g., `./documents/files/`).
- `--keywords` or `-k`: File with the list of keywords.
- `--rename` or `-r`: Enables renaming files in the format `COMPANY_YYYYMMDD.pdf`.
- `--config` or `-c`: Specifies the configuration file (e.g., `config.ini`).

### Example:

```sh
python keywordpdf.py --dir ./pdf_files --keywords keywords.txt --rename --config config.ini
```

## Configuration File Example (`config.ini`)

```ini
[CONFIG]
keywords_list = keywords.txt
renamefiles = true
pdf_dir = ./pdf_files
output_path = ./output
regex_date = "\n[\w\s]+, (\d{1,2}) de (\w+) de (\d{4})\."
regex_company = "COMUNICADO AO MERCADO\s*(.+)"
```

## Keywords List File Example (`keywords.txt`)

Each line will be interpreted as a "keyword," even if it consists of more than one word.

Note: Spaces will also be considered as a search character.

```txt
aumento de capital
ações ordinárias
estrutura administrativa
ações
capital
```

## Output

- **Renamed PDFs** (if `--rename` is enabled)
- **CSV report**: A file named `output.csv` containing:

  ```csv
  file_name,keyword1,keyword2,keywordN
  document1.pdf,1,0,1
  document2.pdf,0,1,1
  ```

## License

This project is licensed under the MIT License.
