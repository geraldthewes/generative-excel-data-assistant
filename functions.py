import gradio as gr
import xlsxwriter
from data_loader import get_data, ColumnType, MetadataType
from utils import get_currency_conversion_rate
from datetime import datetime
import calendar
import json
import plotly.express as px
import pandas as pd

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

def month_idx_to_name(idx: int) -> str:
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    return months[idx - 1]
    
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

'''
Using for example "Material Inventory_US_2023.xlsx", this function returns the suppliers of a given material in a given year.
Example prompt: Get suppliers of wood in 2023.
'''
def get_suppliers_by_material_and_year(model, material: str, year: int) -> str:
    files, metadata, data_frames = get_data(model)
    
    if not data_frames:
        return "No data available"
    else:
        # use only files with material, supplier columns and matching year
        def metadata_filter(filename):
            mt = metadata[filename]
            columns = mt["columns"].keys()
            return "material" in columns and "supplier" in columns and int(mt[MetadataType.YEAR_FROM]) == int(year) and int(mt[MetadataType.YEAR_TO]) == int(year)
        
        files = list(filter(metadata_filter, files))

        suppliers = ""
        for file in files:
            df = data_frames[file]

            filtered_rows = df["Material"].str.lower()
            result = df[filtered_rows == material.lower()]
        
            if result.shape[0] > 0:
                suppliers += ", ".join(result["Supplier"].to_list())

        if not suppliers:
            return f"No suppliers found. It might be that no relevant excel file was uploaded, or the material '{material}' was not found."
        return suppliers

'''
Using for example "Material Cost_global_2018-2022.xlsx", this function returns the price of a material in a given year and the file it was found in.
Example prompt: Where can I find the cost for wood in the year 2023 and what was it?
'''
def get_material_cost_by_year(model, material: str, year: int) -> str:
    files, metadata, data_frames = get_data(model)

    if not data_frames:
        return "No data available"
    else:
        # use only files with material and price columns
        def metadata_filter(filename):
            mt = metadata[filename]
            columns = mt["columns"].keys()
            return "material" in columns and "cost_per_unit_dollar" in columns and int(mt[MetadataType.YEAR_FROM]) >= int(year) and int(mt[MetadataType.YEAR_TO]) <= int(year)
    
        files = list(filter(metadata_filter, files))

        if len(files) > 1:
            return "Too many data sources available: " + ", ".join(files)
        elif len(files) == 0:
            return "No data source available."

        file = files[0]
        df = data_frames[file]
        filtered_rows = df["Material"].str.lower()
        result = df[filtered_rows == material.lower()]

        if result.shape[0] == 0:
            return f"No cost found for {material} in {year}."

        return f"Cost of {material} in {year}: {result['Cost per Unit ($)'].values[0]} USD found in `{file}`"


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

            columns = mt["columns"].keys()
            return mt["type"].lower() == "costs_per_unit" and "year" in columns and "month" in columns
        
        files = list(filter(metadata_filter, files))

        year1 = int(year1)
        year2 = int(year2)

        if len(files) > 1:
            return "Too many data sources available: " + ", ".join(files)
        elif len(files) == 0:
            return "No data source available."

        file = files[0]
        df = data_frames[file] # take only one resource
        col = list(filter(lambda x: unit_type.lower() in x.lower(), df.columns))[0]
        if not col:
            return "Unit type not found."

        q1_month_from, q1_month_to = quarter_to_month(quarter1)
        q2_month_from, q2_month_to = quarter_to_month(quarter2)

        month_col = metadata[file]["columns"]["month"]
        year_col = metadata[file]["columns"]["year"]
        quarter_filter_q1 = df[month_col].between(q1_month_from, q1_month_to) & (df[year_col] == year1)
        q1 = df[quarter_filter_q1]
        quarter_filter_q2 = df[month_col].between(q2_month_from, q2_month_to) & (df[year_col] == year2)
        q2 = df[quarter_filter_q2]

        if q1.shape[0] == 0 or q2.shape[0] == 0:
            return f"Could not find data from {quarter1} {year1} - {quarter2} {year2}."

        avg_q1 = round(q1[col].mean(), 2)
        avg_q2 = round(q2[col].mean(), 2)

        return f"Average price per unit in {quarter1} {year1}: {avg_q1}\nAverage price per unit in {quarter2} {year2}: {avg_q2}"


'''
Files: "Sales data_CH_2023.xlsx", "Sales data_D_2023.xlsx", etc
Example prompt: How many units of wood have been sold in the first three months of 2023?
'''
def get_material_amount_sold(model, material, year: int, month_from: int, month_to: int, country: str) -> str:
    if not year or not month_from or not month_to:
        return "Please provide a year and a month."
    
    files, metadata, data_frames = get_data(model)
    
    if not data_frames:
        return "No data available"
    else:
        def metadata_filter(filename):
            mt = metadata[filename]
            countries_no_match = country != "global" and mt[MetadataType.COUNTRY_CODE] != "global" and mt[MetadataType.COUNTRY_CODE] != country
            if mt[MetadataType.YEAR_FROM] != year or countries_no_match:
                return False

            columns = mt["columns"].keys()
            return ColumnType.MATERIAL in columns and ColumnType.UNITS_SOLD in columns
        
        files = list(filter(metadata_filter, files))

        year = int(year)
        month_from = int(month_from)
        month_to = int(month_to)

        if len(files) == 0:
            return "No data source available."

        number_of_sold_units_txt = ""
        for file in files:
            df = data_frames[file]
            mt = metadata[file]
            columns = mt["columns"]

            material_col = data_frames[file][columns[ColumnType.MATERIAL]].str.lower()
            month_col = data_frames[file][columns[ColumnType.MONTH]]
            result = df[(material_col == material.lower()) & (month_col.between(month_from, month_to))]
        
            if result.shape[0] > 0:
                unit_column = columns[ColumnType.UNITS_SOLD]
                country = country_code_to_name(mt[MetadataType.COUNTRY_CODE])
                number_of_sold_units_txt += f"{country}: {result[unit_column].sum()}\n"
        
        if not number_of_sold_units_txt:
            return f"No sales found for {material} from {month_from} to {month_to} in {year}."

        number_of_sold_units_txt = f"Number of units of {material} sold from {month_idx_to_name(month_from)} to {month_idx_to_name(month_to)} in {year}:\n" + number_of_sold_units_txt
        return number_of_sold_units_txt

'''
Files: "Sales data_CH_2023.xlsx", "Sales data_D_2023.xlsx", etc
Example prompt: List the sales of wood in 2023 in Swiss Francs
'''
def get_material_sales_per_country_in_currency(model, material: str, year: int, to_currency: str, country: str) -> str:
    allowed_currencies = ["USD", "CHF", "EUR"]
    if to_currency not in allowed_currencies:
        return "Only " + ", ".join(allowed_currencies) + " are allowed"
    
    year = int(year)

    files, metadata, data_frames = get_data(model)
    
    if not data_frames:
        return "No data available"
    else:
        def metadata_filter(filename):
            mt = metadata[filename]
            countries_no_match = country != "global" and mt[MetadataType.COUNTRY_CODE] != "global" and mt[MetadataType.COUNTRY_CODE] != country
            if mt[MetadataType.YEAR_FROM] != year or countries_no_match:
                return False

            columns = mt["columns"].keys()
            return ColumnType.MATERIAL in columns and (ColumnType.UNITS_SOLD in columns)
        
        files = list(filter(metadata_filter, files))

        if len(files) == 0:
            return "No data source available."

        number_of_sold_units_txt = ""
        for file in files:
            df = data_frames[file]
            mt = metadata[file]
            columns = mt["columns"]

            material_col = data_frames[file][columns[ColumnType.MATERIAL]].str.lower()
            result = df[(material_col == material.lower())]

            if result.shape[0] > 0:
                if ColumnType.TOTAL_SALES_DOLLAR in columns:
                    sales_column = columns[ColumnType.TOTAL_SALES_DOLLAR]
                    from_currency = "USD"
                elif ColumnType.TOTAL_SALES_EURO in columns:
                    sales_column = columns[ColumnType.TOTAL_SALES_EURO]
                    from_currency = "EUR"

                rate = get_currency_conversion_rate(from_currency, to_currency)
                total_sales = result[sales_column].multiply(rate).sum().round(2)


                country = country_code_to_name(mt[MetadataType.COUNTRY_CODE])
                number_of_sold_units_txt += f"{country}: {total_sales} {to_currency}\n"
        
        if not number_of_sold_units_txt:
            return f"No sales found for {material} in {year}."

        number_of_sold_units_txt = f"Amount of {material} sold in {year} ({country}):\n" + number_of_sold_units_txt
        return number_of_sold_units_txt   
    
def get_total_sales_per_months_for_country_for_year_for_material_in_currency_dataframe(model, country_code: str, material=None, year: int=2023, month_from: int=1, month_to: int=12, to_currency="USD"):
    month_from = int(month_from)
    month_to = int(month_to)
    year = int(year)

    assert month_from <= month_to, f"Invalid month range. 'month_from' ({month_from}) must be smaller than 'month_to' ({month_to})."
    assert year <= 2023, f"Invalid year: '{year}'."

    files, metadata, data_frames = get_data(model)

    if not data_frames:
        raise FileNotFoundError("No data source available.")

    def sales_filter(filename):
        mt = metadata[filename]
        return mt[MetadataType.TYPE] == "sales"

    files = list(filter(sales_filter, files))

    def country_filter(filename):
        mt = metadata[filename]
        return mt["country_code"] == country_code

    files = list(filter(country_filter, files))

    def year_filter(filename):
        mt = metadata[filename]
        year_from = int(mt["year_from"])
        year_to = int(mt["year_to"]) or (year_from + 1)  # +1 because year_to is exclusive
        year_range = range(year_from, year_to + (1 if year_to == year_from else 0))
        return year in year_range

    files = list(filter(year_filter, files))

    if len(files) == 0:
        raise FileNotFoundError("After filtering for given criteria, no data source was found.")
    
    df = data_frames[files[0]]
    mt = metadata[files[0]]

    if material:
        df = df[df[mt["columns"]["material"]].str.lower() == material.lower()]

    # Dynamically retrieve "Total Sales" column name
    sales_column = next((col for col in mt["columns"].values() if "umsatz" in col.lower() or "sales" in col.lower()), None)
    if not sales_column:
        raise AssertionError("Total Sales column not found in metadata.")

    # Convert the "Month" column to integers
    month_col = mt["columns"]["month"]
    df[month_col] = df[month_col].apply(lambda x: list(calendar.month_name).index(x) if isinstance(x, str) else x)

    # Group by month and sum the sales and units
    grouped_df = df.groupby(mt["columns"]["month"]).agg({
        mt["columns"][ColumnType.UNITS_SOLD]: 'sum',
        sales_column: 'sum',
    }).reset_index()

    # Filter by month range
    grouped_df = grouped_df[(grouped_df[mt["columns"]["month"]] >= month_from) & (grouped_df[mt["columns"]["month"]] <= month_to)]

    # Format the month column for better readability
    grouped_df[mt["columns"]["month"]] = grouped_df[mt["columns"]["month"]].apply(lambda x: calendar.month_abbr[int(x)])
    grouped_df.rename(columns={mt["columns"]["month"]: "Month"}, inplace=True)

    # Convert currency to USD
    columns = mt[MetadataType.COLUMNS]
    if ColumnType.TOTAL_SALES_DOLLAR in columns:
        sales_column = columns[ColumnType.TOTAL_SALES_DOLLAR]
        from_currency = "USD"
    elif ColumnType.TOTAL_SALES_EURO in columns:
        sales_column = columns[ColumnType.TOTAL_SALES_EURO]
        from_currency = "EUR"
    else:
        raise AssertionError("Total Sales column not found in metadata.")

    if from_currency != to_currency:
        rate = get_currency_conversion_rate(from_currency, to_currency)
        grouped_df[sales_column] = (grouped_df[sales_column] * rate).round(2)
        grouped_df.rename(
            columns={sales_column: f"Total Sales ({to_currency})"}, inplace=True
        )

    return grouped_df

'''
Files: "Sales data_CH_2023.xlsx", "Sales data_D_2023.xlsx", etc
Example prompt: Return the total Sales of Switzerland for each month in 2023.
'''
def get_total_sales_per_months_for_country_for_year_for_material_in_currency(
    model,
    country: str,
    material=None,
    year: int = 2023,
    month_from: int = 1,
    month_to: int = 12,
    to_currency="USD",
) -> str:
    grouped_df = get_total_sales_per_months_for_country_for_year_for_material_in_currency_dataframe(
        model, country, material, year, month_from, month_to, to_currency
    )

    material_info = f" for {material}" if material else ""
    result = f"Total amount of units sold and total sales {material_info} in {country_code_to_name(country)} from {calendar.month_name[int(month_from)]} to {calendar.month_name[int(month_to)]} {year}:\n"
    result += f"<pre>{grouped_df.to_string(index=False)}</pre>"

    return result

'''
Files: "Sales data_CH_2023.xlsx", "Sales data_D_2023.xlsx", etc
Example prompt: Show me a plot graphic of both the units sold and the total Sales of the USA from June to October in 2023 in Euro.
'''
def plot_total_sales_per_months_for_country_for_year_for_material_in_currency(
    model,
    country_code: str,
    material=None,
    year: int = 2023,
    month_from: int = 1,
    month_to: int = 12,
    to_currency: str = "USD",
    to_plot: str = "sales",
) -> gr.Plot:

    grouped_df = get_total_sales_per_months_for_country_for_year_for_material_in_currency_dataframe(
        model, country_code, material, year, month_from, month_to, to_currency
    )

    if to_plot == "units":
        y_data = grouped_df.columns[1]
        title_info = "Total Amount of Units sold"
    elif to_plot == "both":
        y_data = [grouped_df.columns[1], grouped_df.columns[2]]
        title_info = "Total Amount of Units sold and Total Sales"
    else:
        y_data = grouped_df.columns[2]
        title_info = "Total Sales"

    material_info = f" for {material}" if material else ""
    fig = px.bar(
        grouped_df,
        x=grouped_df.columns[0],
        y=y_data,
        barmode="group",
        title=f"{title_info} in {country_code_to_name(country_code)} in {year}{material_info}",
    )

    return gr.Plot(fig)


'''
Files: "Sales data_CH_2023.xlsx", "Sales data_D_2023.xlsx", etc
Example prompt: Convert the sales of Switzerland in 2023 to Swiss Francs and add it to the file.
'''
def convert_column_to_currency_and_add_to_file(model, currency_code: str, year: int, country_code: str) -> str:
    allowed_currencies = ["USD", "CHF", "EUR"]
    if currency_code not in allowed_currencies:
        return "Only " + ", ".join(allowed_currencies) + " are allowed!"
    
    year = int(year)

    files, metadata, data_frames = get_data(model)

    if not data_frames:
        return "No data available"
    else:
        def metadata_filter(filename):
            mt = metadata[filename]
            
            # Return False if year or country codes don't match
            if str(mt[MetadataType.YEAR_FROM]) != str(year) or country_code == "global" or mt[MetadataType.COUNTRY_CODE] == "global" or mt[MetadataType.COUNTRY_CODE] != country_code:
                return False

            columns = mt["columns"].keys()
            return ColumnType.TOTAL_SALES_DOLLAR in columns or ColumnType.TOTAL_SALES_EURO in columns
        
        files = list(filter(metadata_filter, files))

        if len(files) == 0:
            return "No data source available."
        
        if len(files) > 1:
            return "Too many data sources available: " + ", ".join(files)

        df = data_frames[files[0]]
        mt = metadata[files[0]]
        columns = mt["columns"]

        if ColumnType.TOTAL_SALES_DOLLAR in columns:
            sales_column = columns[ColumnType.TOTAL_SALES_DOLLAR]
            from_currency = "USD"
        elif ColumnType.TOTAL_SALES_EURO in columns:
            sales_column = columns[ColumnType.TOTAL_SALES_EURO]
            from_currency = "EUR"

        converted_sales_column = f"Total Sales ({currency_code})"
        rate = get_currency_conversion_rate(from_currency, currency_code)
        df[converted_sales_column] = df[sales_column].multiply(rate).round(2)

        with open('tmp/file_mapping.json', 'r') as f:
            file_mapping = json.load(f)

        file_path = file_mapping.get(files[0])
        if not file_path:
            return f"File path for {files[0]} not found in file_mapping.json."

        # Translate month index back to month name
        month_col = columns[ColumnType.MONTH]
        df[month_col] = df[month_col].apply(lambda x: calendar.month_name[int(x)] if isinstance(x, int) else x)

        writer = pd.ExcelWriter(file_path, engine="xlsxwriter")
        df.to_excel(writer, sheet_name="Sales Data", index=False)
        writer.close()

        return f'A column has been added to the file. <a href="gradio_api/file={file_path}">Download here</a> or download it below in the “File” section.'


'''
Files: "Sales data_US_2023.xlsx", etc
Example prompt: For the Sales data of the US in 2023 add a column that indicates the price per unit. 
'''
def convert_column_to_price_per_unit_and_add_file(model, year: int, country_code: str) -> str:
    
    year = int(year)

    files, metadata, data_frames = get_data(model)

    if not data_frames:
        return "No data available"
    else:
        def metadata_filter(filename):
            mt = metadata[filename]
            
            # Return False if year or country codes don't match
            if str(mt[MetadataType.YEAR_FROM]) != str(year) or country_code == "global" or mt[MetadataType.COUNTRY_CODE] == "global" or mt[MetadataType.COUNTRY_CODE] != country_code:
                return False

            columns = mt["columns"].keys()
            return (ColumnType.TOTAL_SALES_DOLLAR in columns or ColumnType.TOTAL_SALES_EURO in columns) and ColumnType.UNITS_SOLD in columns
        
        files = list(filter(metadata_filter, files))

        if len(files) == 0:
            return "No data source available."
        
        if len(files) > 1:
            return "Too many data sources available: " + ", ".join(files)

        df = data_frames[files[0]]
        mt = metadata[files[0]]
        columns = mt["columns"]

        if ColumnType.TOTAL_SALES_DOLLAR in columns:
            sales_column = columns[ColumnType.TOTAL_SALES_DOLLAR]
        elif ColumnType.TOTAL_SALES_EURO in columns:
            sales_column = columns[ColumnType.TOTAL_SALES_EURO]
        else:
            return "Total sales column not found."

        price_per_unit_column = "Price per Unit"
        df[price_per_unit_column] = (df[sales_column] / df[columns[ColumnType.UNITS_SOLD]]).round(2)

        with open('tmp/file_mapping.json', 'r') as f:
            file_mapping = json.load(f)

        file_path = file_mapping.get(files[0])
        if not file_path:
            return f"File path for {files[0]} not found in file_mapping.json."

        writer = pd.ExcelWriter(file_path, engine="xlsxwriter")
        df.to_excel(writer, sheet_name="Sales Data", index=False)
        writer.close()

        return f'A column has been added to the file. <a href="gradio_api/file={file_path}">Download here</a> or download it below in the “File” section.'

'''
Files: Material Cost_global_2023.xlsx
Example prompt: Change the supplier name from "Material Masters Co." to "GenAI for the win"
'''
def change_supplier_name_in_files(model, supplier_name_from: str, supplier_name_to) -> str:
    files, metadata, data_frames = get_data(model)

    if not data_frames:
        return "No data available"
    else:
        def metadata_filter(filename):
            mt = metadata[filename]
            columns = mt["columns"].keys()
            return "supplier" in columns
        
        files = list(filter(metadata_filter, files))

        if len(files) == 0:
            return "No data source available."
        
        download_links = ""
        for file in files:
            df = data_frames[file]
            mt = metadata[file]
            columns = mt["columns"]

            supplier_col = columns["supplier"]
            df[supplier_col] = df[supplier_col].replace(supplier_name_from, supplier_name_to)

            with open('tmp/file_mapping.json', 'r') as f:
                file_mapping = json.load(f)

            file_path = file_mapping.get(file)
            if not file_path:
                return f"File path for {file} not found in file_mapping.json."

            writer = pd.ExcelWriter(file_path, engine="xlsxwriter")
            df.to_excel(writer, sheet_name="Sales Data", index=False)
            writer.close()
            download_links += f'<li><a href="gradio_api/file={file_path}">Download {file}</a><br></li>'

        return f'Supplier name "{supplier_name_from}" has been changed to "{supplier_name_to}" all files. Download them here: <br><ul>{download_links}</ul>'

'''
Files: all
Example prompt: Give me an excel formula with which I can calculate the price per unit in the Sales data for the US in 2022. 
'''
def get_excel_formula(model, country_code: str, year: int, question: str) -> str:
    files, metadata, data_frames = get_data(model)
    print(f"files: {files}")

    if not data_frames:
        return "No data available"
    else:
        def metadata_filter(filename):
            mt = metadata[filename]
            return mt[MetadataType.COUNTRY_CODE] == country_code and str(mt[MetadataType.YEAR_FROM]) == str(year)
        
    files = list(filter(metadata_filter, files))
    print(f"fffffffffiles: {files}")

    if len(files) == 0:
        return "No data source available."
    
    if len(files) > 1:
        return "Too many data sources available: " + ", ".join(files)

    df = pd.read_excel(f"tmp/{files[0]}")
    print(f"df: {df}")

    prompt = f"""As an AI assistant, please provide the Excel formula for the following question:
        {question}
        
        based on this data:
        {df.to_string()}
        """

    answer = ""
    for x in model([{"role": "user", "content": prompt}]):
        answer += x
    return answer    