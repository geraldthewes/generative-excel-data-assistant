import os
from excel_preparations import ExcelPreparations


def list_files_in_tmp():
    tmp_dir = os.path.join(os.getcwd(), 'tmp')
    if not os.path.exists(tmp_dir):
        return []

    files = os.listdir(tmp_dir)
    return files

def get_supplier_by_material(material: str) -> str:
    # Read in your Excel files and prepare the data frame
    files = list_files_in_tmp()  # Assuming this is a function that lists your files
    excel_preparation = ExcelPreparations()  # Assuming this prepares the excel reading process
    data = excel_preparation.read_excel(files)  # Reading the data from the Excel file
    
    if not data:
        return "No data available"
    else:
        header_index = data[files[0]]["header_index"]
        df = data[files[0]]["df"]

        
        # Skip the first two rows (header row is at index [1, 0] as per your example)
        df.columns = df.iloc[header_index[0]]  # Set the correct header
        df = df.drop(index=header_index[0])  # Remove the header row itself
        print(f"Header row: {df.columns}")
        print(f"Data: {df}")
        for _, row in df.iterrows():
            if row['Material'].lower() == material.lower():
                return row['Supplier']
            else:
                continue
        return "Supplier not found"
    