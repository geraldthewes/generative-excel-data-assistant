import xlsxwriter
from data_loader import get_data, ColumnType, MetadataType
from utils import get_currency_conversion_rate
from datetime import datetime
import calendar

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
    
def name_to_country_code(name: str) -> str:
    if name.lower() == "switzerland":
        return "CH"
    elif name.lower() == "germany":
        return "DE"
    elif name.lower() == "france":
        return "FR"
    elif name.lower() == "united states":
        return "US"
    elif name.lower() == "spain":
        return "ES"
    elif name.lower() == "global":
        return "global"
    else:
        return name

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
            
        
def quarter_to_month(quarter: str) -> tuple[int, int]:
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


def excel_test():    
    workbook = xlsxwriter.Workbook('tmp/hello.xlsx')
    worksheet = workbook.add_worksheet()

    worksheet.write('A1', 'Hello world')

    workbook.close()

    return "tmp/hello.xlsx"

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
    
def get_total_sales_per_month_dataframe(model, country: str, material=None, year: int=2023, month_from: int=1, month_to: int=12):
    month_from = int(month_from)
    month_to = int(month_to)
    year = int(year)

    assert month_from <= month_to, f"Invalid month range. 'month_from' ({month_from}) must be smaller than 'month_to' ({month_to})."
    assert year <= 2023, f"Invalid year: '{year}'."
    
    files, metadata, data_frames = get_data(model)

    if not data_frames:
        return "No data available."
    
    def country_filter(filename):
        mt = metadata[filename]
        return mt["country_code"] == name_to_country_code(country)
    
    files = list(filter(country_filter, files))

    def year_filter(filename):
        mt = metadata[filename]
        year_from = mt["year_from"]
        year_to = mt["year_to"] or (year_from + 1)  # +1 because year_to is exclusive
        year_range = range(year_from, year_to + (1 if year_to == year_from else 0))
        return year in year_range
    
    files = list(filter(year_filter, files))

    print(f"metadata: {metadata}\n\n")
    print(f"files: {files}\n\n")

    if len(files) == 0:
        return "No data source available."
    
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
    grouped_df = df.groupby(mt["columns"]["month"]).agg(
        Units_Sold=(mt["columns"]["units_sold"], 'sum'),
        Total_Sales=(sales_column, 'sum')
    ).reset_index()

    # Filter by month range
    grouped_df = grouped_df[(grouped_df[mt["columns"]["month"]] >= month_from) & (grouped_df[mt["columns"]["month"]] <= month_to)]

    # Format the month column for better readability
    grouped_df[mt["columns"]["month"]] = grouped_df[mt["columns"]["month"]].apply(lambda x: calendar.month_abbr[int(x)])
    grouped_df.rename(columns={mt["columns"]["month"]: "Month"}, inplace=True)

    return grouped_df

'''
Files: "Sales data_CH_2023.xlsx", "Sales data_D_2023.xlsx", etc
Example prompt: Return the total Sales of Switzerland for each month in 2023.
'''
def get_total_sales_per_month(model, country: str, material=None, year: int=2023, month_from: int=1, month_to: int=12):
    grouped_df = get_total_sales_per_month_dataframe(model, country, material, year, month_from, month_to)
    result = f"Total amount of units sold in {country} from {calendar.month_name[int(month_from)]} to {calendar.month_name[int(month_to)]} {year}:\n"
    result += f"Month, Units Sold, Total Sales\n"

    print(f"grouped_df: {grouped_df}\n\n")
    for row in grouped_df.itertuples():
        result += f"{row.Month}: {row.Units_Sold}, {row.Total_Sales}\n"

    return result
