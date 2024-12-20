import os
from excel_preparations import ExcelPreparations
from utils import answer_to_json
import json
from datetime import datetime
import re
import hashlib


class ColumnType():
    SUPPLIER = "supplier"
    MATERIAL = "material"
    COST_PER_UNIT_DOLLAR = "cost_per_unit_dollar"
    LEAD_TIME_DAYS = "lead_time_days"
    PRICE_DOLLAR = "price_dollar"
    UNITS_IN_STORAGE = "units_in_storage"
    YEAR = "year"
    MONTH = "month"
    UNITS_SOLD = "units_sold"
    TOTAL_SALES_DOLLAR = "total_sales_dollar"
    TOTAL_SALES_EURO = "total_sales_euro"

class MetadataType():
    TYPE = "type"
    COUNTRY_CODE = "country_code"
    YEAR_FROM = "year_from"
    YEAR_TO = "year_to"
    COLUMNS = "columns"

all_columns = [attr for attr in dir(ColumnType) if not callable(getattr(ColumnType, attr)) and not attr.startswith("__")]


def list_files_in_tmp():
    tmp_dir = os.path.join(os.getcwd(), 'tmp')
    if not os.path.exists(tmp_dir):
        return []

    files = os.listdir(tmp_dir)
    files = list(filter(lambda x: x.endswith('.xlsx'), files))
    return files

def load_metadata_cache():
    metadata = {}
    cache_files = os.listdir('tmp')
    for filename in cache_files:
        if filename.endswith('.json') and not filename.startswith("file_mapping"):
            parts = filename.split('_', 1)
            if len(parts) != 2 or not re.match('^\d{4}-\d{2}-\d{2}$', parts[0]):
                print(f"Invalid cache file: {filename}")
                continue
            date = parts[0]
            filename = parts[1]
            if date != datetime.now().strftime("%Y-%m-%d"):
                os.remove(f'tmp/{date}_{filename}')
                xlsx_filename = filename.replace(".json", "")
                os.remove(f'tmp/{xlsx_filename}')
                continue
            with open(f'tmp/{date}_{filename}', 'r') as f:
                metadata[filename.split(".json")[0]] = json.load(f)
    return metadata

def extract_metadata(model, filenames: list, data_frames: dict, info_texts: dict) -> dict:
    metadata_prompt = """As an AI assistant, please extract the metadata from this filename: '{filename}' and this information: '{info_text}'. Also map the columns to a list of available options.
     
        ----------------------------------------
        The columns are:
        {columns}.
        Available options are: {all_columns}.
        ----------------------------------------
        
        The output should be in the following format:
        """

    prompt_end = """
        {
            "type": "type of the data. Available options are: sales, inventory, costs_per_unit.",
            "country_code": "country code. Available options are: CH, DE, FR, US, ES, global.",
            "year_from": "The year the data starts from.",
            "year_to": "year_to", If the data is for a single year, year_from and year_to should be the same.
            "columns": "Map columns to available options. Example: {'Cost per Unit ($)': 'cost_per_unit_dollar', 'Lead Time (Days)': 'lead_time_days', ...}"
        }

        Remember to only give the json object as output, without any additional text. Strictly avoid anything else than JSON output also exaplanations and other text."""

    curr_date = datetime.now().strftime("%Y-%m-%d")
    cached_metadata = load_metadata_cache()
    metadata = {}
    for filename in filenames:
        if not filename.endswith('.xlsx'):
            continue
        df_columns = data_frames[filename].columns.to_list()
        info_text = info_texts[filename]

        if filename in cached_metadata:
            if cached_metadata[filename]["checksum"] == hashlib.md5(open(f'tmp/{filename}','rb').read()).hexdigest():
                metadata[filename] = cached_metadata[filename]
                continue
            else:
                print(f"Provided file {filename} is different than cached one.")

        prompt = (
            metadata_prompt.format(
                filename=filename, columns=", ".join(df_columns),
                info_text=info_text,
                all_columns=", ".join(all_columns)
            )
            + prompt_end
        )
        answer = ""
        for x in model([{"role": "user", "content": prompt}]):
            answer += x

        answer_dict = answer_to_json(answer)
        answer_dict["columns"] = {str(v).lower(): k for k, v in answer_dict["columns"].items()} # swap keys and values
        if isinstance(answer_dict["year_from"], str) and answer_dict["year_from"].isdigit(): # year can be "unknown"
            answer_dict["year_from"] = int(answer_dict["year_from"])
        if isinstance(answer_dict["year_to"], str) and answer_dict["year_to"].isdigit():
            answer_dict["year_to"] = int(answer_dict["year_to"])


        metadata[filename] = answer_dict

        answer_dict["checksum"] = hashlib.md5(open(f'tmp/{filename}','rb').read()).hexdigest()
        with open(f"tmp/{curr_date}_{filename}.json", "w") as f:
            json.dump(answer_dict, f)

    return metadata


valid_months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
'''
Preprocess the month column to be an integer between 1 and 12
'''
def preprocess_month_column(row: list) -> int:
    if isinstance(row, str):
        if row not in valid_months:
            print(f"Invalid month (1): {row}")
        idx = valid_months.index(row)
        return idx + 1
    elif isinstance(row, int):
        if row < 1 or row > 12:
            print(f"Invalid month (2): {row}")
        return row
    else:
        print(f"Invalid month (3): {row}")
        return row

column_preprocessing = {
    "month": preprocess_month_column,
    "year": lambda x: int(x)
}
def preprocess_dataframes(data_frames: dict, metadata: dict) -> dict:
    for filename, df in data_frames.items():
        md = metadata[filename]
        columns = md["columns"]
        for (col, df_col) in columns.items():
            if col in column_preprocessing:
                df[df_col] = df[df_col].apply(column_preprocessing[col])
    return data_frames


'''
Get all relevant data for a function call
'''
def get_data(model) -> (list, dict):
    files = list_files_in_tmp()
    excel_preparation = ExcelPreparations()
    data_frames, info_texts = excel_preparation.read_excel(files)
    metadata = extract_metadata(model, files, data_frames, info_texts)
    data_frames = preprocess_dataframes(data_frames, metadata)
    return files, metadata, data_frames