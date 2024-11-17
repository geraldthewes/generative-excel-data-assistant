import os
from excel_preparations import ExcelPreparations
import xlsxwriter
from utils import answer_to_json

def country_code_to_name(code: str) -> str:
    if code == "CH":
        return "Switzerland"
    elif code == "DE":
        return "Germany"
    elif code == "FR":
        return "France"
    elif code == "US":
        return "United States"
    elif code == "ES":
        return "Spain"
    elif code == "global":
        return "Global"
    else:
        return code

def list_files_in_tmp():
    tmp_dir = os.path.join(os.getcwd(), 'tmp')
    if not os.path.exists(tmp_dir):
        return []

    files = os.listdir(tmp_dir)
    return files

def filenames_to_metadata(model, filenames: list, data_frames: dict, info_texts: dict) -> dict:
    metadata_prompt = """As an AI assistant, please extract the metadata from this filename: '{filename}' and this information: '{info_text}'. Also map columns the columns to a list of available options.
     
        ----------------------------------------
        The columns are:
        {columns}.
        Available options are: supplier, material, cost_per_unit_dollar, lead_time_days, price_dollar, units_in_storage, year, month, units_sold, total_sales_dollar, total_sales_euro.
        ----------------------------------------
        
        The output should be in the following format:
        """

    prompt_end = """
        {
            "type": "type of the data. Available options are: sales, inventory, costs_per_unit.",
            "country_code":  "country code. Available options are: CH, DE, FR, US, ES, gloabl.",
            "year_from": "year_from",
            "year_to": "year_to",
            "columns": "Map columns to available options. Example: {'Cost per Unit ($)': 'cost_per_unit_dollar', 'Lead Time (Days)': 'lead_time_days', ...}"
        }

        Remember to only give the json object as output, without any additional text. Strictly avoid anything else than JSON output also exaplanations and other text."""

    metadata = {}
    for filename in filenames:
        columns = data_frames[filename].columns.to_list()
        info_text = info_texts[filename]

        prompt = (
            metadata_prompt.format(
                filename=filename, columns=", ".join(columns),
                info_text=info_text
            )
            + prompt_end
        )
        answer = ""
        for x in model([{"role": "user", "content": prompt}]):
            answer += x

        answer_json = answer_to_json(answer)
        answer_json["columns"] = {v: k for k, v in answer_json["columns"].items()}
        metadata[filename] = answer_json
    return metadata


def get_data(model) -> (list, dict):
    files = list_files_in_tmp()
    excel_preparation = ExcelPreparations()
    data_frames, info_texts = excel_preparation.read_excel(files)
    metadata = filenames_to_metadata(model, files, data_frames, info_texts)
    return files, metadata, data_frames

'''
Using for example "Material Cost_global_2023.xslx", this function returns the suppliers of a given material.
Example prompt: Get suppliers of wood
'''
def get_suppliers_by_material(model, material: str) -> str:
    files, metadata, data_frames = get_data(model)
    
    if not data_frames:
        return "No data available"
    else:
        # use only files with material and supplier columns
        def metadata_filter(filename):
            mt = metadata[filename]
            columns = mt["columns"].keys()
            return "material" in columns and "supplier" in columns
        
        files = list(filter(metadata_filter, files))

        suppliers = ""
        for file in files:
            df = data_frames[file]

            filtered_rows = data_frames[files[0]]["Material"].str.lower()
            result = df[filtered_rows == material.lower()]
        
            if result.shape[0] > 0:
                suppliers += ", ".join(result["Supplier"].to_list())

        if not suppliers:
            return f"No suppliers found. It might be that no relavant excel file was uploaded, or the material '{material}' was not found."
        return suppliers
            
        
def quarter_to_month(quarter: str) -> (int, int):
    if quarter.lower() == "q1":
        return 1, 3
    elif quarter.lower() == "q2":
        return 4, 6
    elif quarter.lower() == "q3":
        return 7, 9
    elif quarter.lower() == "q4":
        return 10, 12
    else:
        return -1, -1
    
'''
Using data from "Material_costs_Elemental Resources_evolution.xlsx", this function compares the average price per unit of a given unit type in two different quarters.
Example prompt: Compare the price per unit of graphene in Q1 2023 and Q2 2023
'''
def compare_price_per_unit_by_quarters(model, unit_type: str, quarter1: str, year1: int, quarter2: str, year2: int) -> str:
    files, metadata, data_frames = get_data(model)

    if not data_frames:
        return "No data available"
    else:
        # use only files with material and supplier columns
        def metadata_filter(filename):
            mt = metadata[filename]

            return mt["type"].lower() == "costs_per_unit"
        
        files = list(filter(metadata_filter, files))

        if len(files) > 1:
            return "Too many data sources available: " + ", ".join(files)
        elif len(files) == 0:
            return "No data source available."

        df = data_frames[files[0]] # take only one resource
        col = list(filter(lambda x: unit_type.lower() in x.lower(), df.columns))[0]
        if not col:
            return "Unit type not found."

        q1_month_from, q1_month_to = quarter_to_month(quarter1)
        q2_month_from, q2_month_to = quarter_to_month(quarter2)

        quarter_filter_q1 = df["Month"].between(q1_month_from, q1_month_to) & (df["Year"] == year1)
        q1 = df[quarter_filter_q1]
        quarter_filter_q2 = df["Month"].between(q2_month_from, q2_month_to) & (df["Year"] == year2)
        q2 = df[quarter_filter_q2]

        avg_q1 = round(q1[col].mean(), 2)
        avg_q2 = round(q2[col].mean(), 2)

        return f"Average price per unit in {quarter1} {year1}: {avg_q1}\nAverage price per unit in {quarter2} {year2}: {avg_q2}"


def excel_test():    
    workbook = xlsxwriter.Workbook('tmp/hello.xlsx')
    worksheet = workbook.add_worksheet()

    worksheet.write('A1', 'Hello world')

    workbook.close()

    return "tmp/hello.xlsx"

'''
Files: "Sales data_CH_2023.xlsx", "Sales data_D_2023.xlsx", etc
Example prompt: How many units of wood have been sold in January 2023?
'''
def get_material_sales(model, material, year, month):
    files, metadata, data_frames = get_data(model)
    
    if not data_frames:
        return "No data available"
    else:
        # use only files with material and supplier columns
        def metadata_filter(filename):
            mt = metadata[filename]
            if str(mt["year_from"]) != str(year):
                return False

            columns = mt["columns"].keys()
            return "material" in columns and "units_sold" in columns
        
        files = list(filter(metadata_filter, files))

        if len(files) == 0:
            return "No data source available."

        number_of_sold_units_txt = ""
        for file in files:
            df = data_frames[file]
            mt = metadata[file]
            columns = mt["columns"]

            material_col = data_frames[file][columns["material"]].str.lower()
            month_col = data_frames[file][columns["month"]].str.lower()
            result = df[(material_col == material.lower()) & (month_col == month.lower())]
        
            if result.shape[0] > 0:
                column = columns["units_sold"]
                country = country_code_to_name(mt["country_code"])
                number_of_sold_units_txt += f"{country}: {result[column].sum()}\n"
        
        return number_of_sold_units_txt
    

