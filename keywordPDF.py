import os
import re
import csv
import PyPDF2
import argparse
import configparser
from collections import Counter

# Mapping of months to numbers
MONTHS = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
    "janeiro": "01", "fevereiro": "02", "março": "03", "abril": "04",
    "maio": "05", "junho": "06", "julho": "07", "agosto": "08",
    "setembro": "09", "outubro": "10", "novembro": "11", "dezembro": "12"
}

def load_config_file(config_path, keys=[]):
    """Loads the keyword list from the config.ini file"""
    config = configparser.ConfigParser()
    config.read(config_path)

    regex_date_raw = config["CONFIG"].get("regex_date", r"\n[\w\s]+, (\d{1,2}) de (\w+) de (\d{4})\.").strip('"')
    CONFIG = {
        "keywords_list": config["CONFIG"].get("keywords_list", ""),
        "renamefiles": config["CONFIG"].get("renamefiles", "0").lower() in ('1', 'true'),
        "pdf_dir": config["CONFIG"].get("pdf_dir", ""),
        "output_path": config["CONFIG"].get("output_path", ""),
        "regex_date": re.compile(regex_date_raw, re.IGNORECASE),
        "regex_company": re.compile(config["CONFIG"].get("regex_company", r"COMUNICADO AO MERCADO\s*(.+)").strip('"'), re.IGNORECASE),
    }
    
    return {key: CONFIG[key] for key in keys if key in CONFIG}

def load_keywords(config_path):
    print(config_path)
    with open(config_path, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file.readlines()]

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    return text

def get_unique_filename(directory, base_filename):
    """Generates a unique filename by adding a counter if necessary"""
    name, ext = os.path.splitext(base_filename)
    new_filename = base_filename
    counter = 1

    while os.path.isfile(os.path.join(directory, new_filename)):
        new_filename = f"{name} ({counter}){ext}"
        counter += 1

    return new_filename

# Extract document date
def extract_date(text):
    date_pattern = load_config_file(os.getenv("CONFIG_FILE_APP"), ['regex_date'])['regex_date']
    match = re.search(date_pattern, text)

    if match:
        day, month_text, year = match.groups()
        month = MONTHS.get(month_text.lower())
        if month:
            return f"{year}{month}{int(day):02d}"  # Format YYYYMMDD
    return "00000000"  # Default return if the date is not found

def find_company_and_date(text):
    company_pattern = load_config_file(os.getenv("CONFIG_FILE_APP"), ['regex_company'])['regex_company']
    
    company_match = re.search(company_pattern, text)
    company = company_match.group(1) if company_match else "UNKNOWN" 
    company = company.split('(')[0].strip().replace(' ', '_')
    
    date = extract_date(text)
    
    return company, date

# ----- FIND KEYWORDS
def contains_keywords(text, keywords):
    return any(keyword.lower() in text.lower() for keyword in keywords)

def check_keywords_in_text(text, keywords):
    """Checks the presence of keywords in the PDF text"""
    return [1 if keyword.lower() in text.lower() else 0 for keyword in keywords]

# ------ MAIN PROCESS
def process_pdfs(directory, keywords_file, rename=False, output_csv='output.csv'):
    keywords = load_keywords(keywords_file)
    header = [keyword.replace(',', '-').replace(' ', '_') for keyword in keywords]
    matrix = [["file_name","company","date"] + header]  # Header

    for filename in os.listdir(directory):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(directory, filename)
            text = extract_text_from_pdf(pdf_path)
            company, date = find_company_and_date(text)

            if rename:
                if company != 'UNKNOWN' and date != '00000000':
                    new_filename = get_unique_filename(directory, f"{company}_{date}.pdf") 
                    new_path = os.path.join(directory, new_filename)

                    if not os.path.isfile(new_path):
                        os.rename(pdf_path, new_path)
                        print(f"Renamed: {filename} -> {new_filename}")
                        filename = new_filename
                    else:
                        print('Could not rename file')

            row = [filename, company, date] + check_keywords_in_text(text, keywords)
            matrix.append(row)

            if contains_keywords(text, keywords):
                print("Keyword(s) found")
            else:
                print(f"No keywords found in {filename}, not renamed.")

    output_csv = os.path.join(output_csv, get_unique_filename(output_csv, "output.csv"))
    with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(matrix)

    print(f"Result saved to {output_csv}")

def main():
    parser = argparse.ArgumentParser(description="Rename PDF files based on internal content.")
    parser.add_argument("--dir", type=str, help="Directory containing PDF files. Usage: --dir ./documents/files/")
    parser.add_argument("--keywords", "-k", type=str, help="File with the keyword list. Usage: --keywords keywords.txt")
    parser.add_argument("--rename", "-r", action="store_true", help="Enable renaming to the pattern COMPANY_YYYYMMDD.pdf.")
    parser.add_argument("--config", "-c", type=str, help="Specify the configuration file. Usage: -c config.ini")
    args = parser.parse_args()

    if not args.config and not os.path.isfile('config.ini'):
        directory = args.dir or input("Enter the PDF directory: ")
        keywords_file = args.keywords or input("Enter the keyword file path: ")

        if not os.path.isdir(directory):
            print("Error: Invalid directory.")
            return
        if not os.path.isfile(keywords_file):
            print("Error: Keyword file not found.")
            return
        # When no configuration file is provided we still need to
        # supply the keys expected later in the script. Otherwise
        # KeyError exceptions will be raised when accessing
        # 'keywords_list' or 'renamefiles'.
        config = {
            'keywords_list': keywords_file,
            'renamefiles': args.rename,
            'pdf_dir': directory,
            'output_path': '.'
        }
    else:
        config_file = args.config if args.config else 'config.ini'
        if not os.path.isfile(config_file):
            print(f'Error: Config file not found [{config_file}]')
            return
        
        os.environ['CONFIG_FILE_APP'] = config_file
        config = load_config_file(config_file, ['keywords_list', 'renamefiles', 'pdf_dir', 'output_path'])

    
    need_rename = True if args.rename or config['renamefiles'] else False
    
    process_pdfs(directory=config['pdf_dir'], keywords_file=config['keywords_list'], rename=need_rename, output_csv=config['output_path'])

if __name__ == "__main__":
    main()
