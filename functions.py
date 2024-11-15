import os
from excel_preparations import ExcelPreparations


def list_files_in_tmp():
    tmp_dir = os.path.join(os.getcwd(), 'tmp')
    if not os.path.exists(tmp_dir):
        return []

    files = os.listdir(tmp_dir)
    return files

def get_suppliers_by_material(material: str) -> str:
    # Read in your Excel files and prepare the data frame
    files = list_files_in_tmp()  # Assuming this is a function that lists your files
    excel_preparation = ExcelPreparations()  # Assuming this prepares the excel reading process
    data = excel_preparation.read_excel(files)  # Reading the data from the Excel file
    
    if not data:
        return "No data available"
    else:
        df = data[files[0]]

        filtered_rows = data[files[0]]["Material"].str.lower()
        result = df[filtered_rows == material.lower()]
        
        if result.shape[0] > 0:
            return ", ".join(result["Supplier"].to_list())
        else:
            return "Supplier not found"
    