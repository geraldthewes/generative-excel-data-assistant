import os
from excel_preparations import ExcelPreparations


def list_files_in_tmp():
    tmp_dir = os.path.join(os.getcwd(), 'tmp')
    if not os.path.exists(tmp_dir):
        return []

    files = os.listdir(tmp_dir)
    return files

def get_data() -> (list, dict):
    files = list_files_in_tmp()
    excel_preparation = ExcelPreparations()
    data_frames = excel_preparation.read_excel(files)
    return files, data_frames

'''
Using for example Sales data_CH_2023.xlsx, this function returns the suppliers of a given material.
'''
def get_suppliers_by_material(material: str) -> str:
    files, data_frames = get_data()
    
    if not data_frames:
        return "No data available"
    else:
        df = data_frames[files[0]]

        filtered_rows = data_frames[files[0]]["Material"].str.lower()
        result = df[filtered_rows == material.lower()]
        
        if result.shape[0] > 0:
            return ", ".join(result["Supplier"].to_list())
        else:
            return "Supplier not found"
        
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
Using data from Material_costs_Elemental Resources_evolution.xlsx, this function compares the average price per unit of a given unit type in two different quarters.
'''
def compare_price_per_unit_by_quarters(unit_type: str, quarter1: str, year1: int, quarter2: str, year2: int) -> str:
    files, data_frames = get_data()

    if not data_frames:
        return "No data available"
    else:
        df = data_frames[files[0]]

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
