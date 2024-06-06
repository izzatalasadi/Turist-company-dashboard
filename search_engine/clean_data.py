import pandas as pd

class ExcelProcessor:
    def __init__(self, file):
        self.file = file
        self.search_strings = [
            "YES Viking Air, Transfer included", 
            "NO Viking Air, Transfer included",
            "Transfer not included"
        ]

    def read_and_process_excel(self):
        df = pd.read_excel(self.file)
        
        # Check if 'TRANSPORTATION' column exists
        if 'TRANSPORTATION' in df.columns or 'Transportation' in df.columns:
            return self._process_with_transportation(df)
        else:
            return self._process_without_transportation()
    
    def _process_with_transportation(self, df):
        bus_row_index = df[df.apply(lambda row: row.astype(str).str.contains('BUS#').any(), axis=1)].index.min()
        
        # Now read the file starting from the found row
        df = df[bus_row_index:]
        
        df.dropna(how='all', inplace=True)
        df.columns = ["TRANSPORTATION"]
        
        df = df.ffill()
        
        return df["TRANSPORTATION"]

    def _process_without_transportation(self):
        
        df = pd.read_excel(self.file)
        # Drop completely empty rows
        df = df.dropna(how='all')

        # Find the first and last non-empty rows
        first_non_empty_row = df.first_valid_index()
        last_non_empty_row = df.last_valid_index()

        # Slice the DataFrame to include only the non-empty rows
        df = df.loc[first_non_empty_row:last_non_empty_row]
        df = df.iloc[1:]
        df.columns = ["invoice",
                      "booking_no",
                      "first_name", 
                      "last_name", 
                      "transfer_type", 
                      "transfer_provided", 
                      "cabin",
                      "arrival_date", 
                      "transfer_time", 
                      "from_type", 
                      "from_location"]
        
        # Create new columns for the processed data
        df["to_city"] = ""
        df["flight"] = ""
        df["org_city"] = ""
        df["ship_name"] = ""

        # Process each row based on the value of "From Type"
        for index, row in df.iterrows():
            from_type = row["from_type"]
            from_location = row["from_location"]
            
            if from_type == "APT":
                tmp_list = from_location.split('-')
                to_location = tmp_list[0]
                flight, org_city = tmp_list[1].split('(Org City:')
                org_city = org_city.rstrip(')')
                
                df.at[index, "to_city"] = str(to_location).strip()
                df.at[index, "flight"] = str(flight).strip()
                df.at[index, "org_city"] = str(org_city).strip()
                df.at[index, "ship_name"] = ""
                
            elif from_type == "SHP":
                to_city, ship_name = from_location.split('-')
                df.at[index, "to_city"] = str(to_city).strip()
                df.at[index, "ship_name"] = ship_name
                df.at[index, "org_city"] = ""
                df.at[index, "flight"] = ""

            elif from_type == "UNK":
                df.at[index, "to_city"] = ""
                df.at[index, "ship_name"] = ""
                df.at[index, "org_city"] = ""
                df.at[index, "flight"] = ""

        # Drop the original "From Location" column
        df.drop(columns=["from_location"], inplace=True)
        
        return df

    def extract_comments(self, row):
        for s in self.search_strings:
            if any(s in str(cell) for cell in row):
                return s
        return ''
    
    def remove_search_strings(self, row):
        for col in row.index:
            if isinstance(row[col], str):
                for s in self.search_strings:
                    if s in row[col]:
                        row[col] = row[col].replace(s, '')  # Remove the string
        return row
    
# def main():
#     file_path = "test.xlsx"
#     processor = ExcelProcessor(file_path)
#     processed_data = processor.read_and_process_excel()
#     print(processed_data)

# if __name__ == "__main__":
#     main()                    