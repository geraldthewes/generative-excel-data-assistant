import pandas as pd
from typing import List, Optional
import os

class ExcelPreparations:
    def read_excel(self, files):
        data_frames = {}
        info_texts = {}
        for file in files:
            file_path = os.path.join(os.getcwd(), 'tmp', file)
            if not os.path.exists(file_path) or not file_path.endswith(".xlsx"):
                continue
            [header_row, header_col] = self.detect_header_index(file_path)

            # Extract header texts
            if header_row > 0:
                full_df = pd.read_excel(file_path)
                info_texts[file] = ", ".join(filter(lambda x: "Unnamed" not in x, full_df.columns))
                if header_row > 1:
                    for i in range(0, header_row - 1):
                        row = full_df.iloc[i, :]
                        info_texts[file] += ". " + ", ".join(row[row.notna()].tolist())
            else:
                info_texts[file] = "No information"
            
            df = pd.read_excel(file_path, header=header_row)
            df.columns = df.columns.str.strip() # remove leading and trailing whitespaces
            df.columns = df.columns.str.replace("Unnamed.*", "Material", regex=True)
            if header_col > 0:
                df = df.drop(df.columns[:header_col], axis=1)
            data_frames[file] = df
        return data_frames, info_texts

    def detect_header_index(self, file) -> Optional[List[int]]: # returns [header_row, header_col] with df index
        df = pd.read_excel(file, header=None)
        if df is None:
            raise ValueError("File not loaded. Please load the file first using read_excel.")
        
        header_row = None
        header_col = 0

        # Detect the header row
        for i in range(min(10, len(df))):  # Look at the first 10 rows only
            row = df.iloc[i]
            filled_cells = row.notna().sum()

            # Check if the row has more than one filled cell
            if filled_cells > 1:
                # Check if the next row has the same number of filled cells
                if i + 1 < len(df) and df.iloc[i + 1].notna().sum() == filled_cells:
                    # Optionally, check if values are mostly strings, indicating headers
                    if row.apply(lambda x: isinstance(x, str)).sum() > (0.5 * filled_cells):
                        header_row = i
                        break

        # If both row and column are detected, return the header cell position
        if header_row is not None:
            return [header_row, header_col]

        # Fallback: Check the first row and column with multiple filled cells if no header is identified
        if header_row is None:
            for i in range(len(df)):
                if df.iloc[i].notna().sum() > 1:
                    header_row = i
                    break

        # Return the position if either header row or column was detected, otherwise None
        if header_row is not None:
            return [header_row, header_col]
        else:
            return None # No header row or column detected
