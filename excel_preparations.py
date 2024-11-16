import pandas as pd
from typing import List, Optional
import os

class ExcelPreparations:
    def read_excel(self, files):
        data_frames = {}
        for file in files:
            file_path = os.path.join(os.getcwd(), 'tmp', file)
            [header_row, header_col] = self.detect_header_index(file_path)
            df = pd.read_excel(file_path, header=header_row + 1)
            df.columns = df.columns.str.strip() # remove leading and trailing whitespaces
            if header_col > 0:
                df = df.drop(df.columns[:header_col], axis=1)
            data_frames[file] = df
        return data_frames

    def detect_header_index(self, file) -> Optional[List[int]]: # returns [header_row, header_col] with df index
        df = pd.read_excel(file)
        if df is None:
            raise ValueError("File not loaded. Please load the file first using read_excel.")
        
        header_row = None
        header_col = None

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

        # Detect the header column if header_row is found
        if header_row is not None:
            for j in range(min(10, len(df.columns))):  # Look at the first 10 columns only
                col = df.iloc[:, j]
                filled_cells = col.notna().sum()

                # Check if the column has more than one filled cell
                if filled_cells > 1:
                    # Check if the next column has the same number of filled cells
                    if j + 1 < len(df.columns) and df.iloc[:, j + 1].notna().sum() == filled_cells:
                        # Check if values are mostly strings, indicating headers
                        if col.apply(lambda x: isinstance(x, str)).sum() > (0.5 * filled_cells):
                            header_col = j
                            break

        # If both row and column are detected, return the header cell position
        if header_row is not None and header_col is not None:
            return [header_row, header_col]

        # Fallback: Check the first row and column with multiple filled cells if no header is identified
        if header_row is None:
            for i in range(len(df)):
                if df.iloc[i].notna().sum() > 1:
                    header_row = i
                    break
        if header_col is None:
            for j in range(len(df.columns)):
                if df.iloc[:, j].notna().sum() > 1:
                    header_col = j
                    break

        # Return the position if either header row or column was detected, otherwise None
        if header_row is not None and header_col is not None:
            return [header_row, header_col]
        else:
            return None  # No header row or column detected
