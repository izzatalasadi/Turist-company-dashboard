import pandas as pd 

class ExcelProcessor:
    def __init__(self, file):
        self.file = file
        self.search_strings = [
            "YES Viking Air, Transfer included", 
            "NO Viking Air, Transfer included",
            "Transfer not included"
        ]
    # After df = df.ffill()

    def extract_transportation(self,row):
        # Split the 'Transportation' column on space and take the last part which should be "VAN" or "BUS"
        transportation_parts = str(row['Transportation']).split()
        # Assuming the last word is the mode of transportation and it's always present
        return transportation_parts[-1] if transportation_parts else ''

    def read_and_process_excel(self):
        temp_df = pd.read_excel(self.file)
        bus_row_index = temp_df[temp_df.apply(lambda row: row.astype(str).str.contains('BUS#').any(), axis=1)].index.min()
        
        # Now read the file starting from the found row
        df = pd.read_excel(self.file, skiprows=bus_row_index)
        
        
        df.dropna(how='all', axis=0, inplace=True)
        df.dropna(how='all', axis=1, inplace=True)
        
        df.columns = ["FLIGHT", "TIME", "FROM", "LAST NAME", "FIRST NAME", "BOOKING", "TRANSPORTATION"]
        
        df = df.ffill()
        df['COMMENTS'] = df.apply(self.extract_comments, axis=1)
        #df = df.apply(self.remove_search_strings, axis=1)

        df = df[df['BOOKING'].ne('In total:')]
        df = df[df['LAST NAME'].ne('GA')]
        
        df['STATUS'] = 'Unchecked'  # Add 'STATUS' column with default 'Unchecked'
        df['FLIGHT'] = df['FLIGHT'].astype(str)
        df['FLIGHT'] = df['FLIGHT'].apply(lambda x: x.replace(" ",''))
        df['TRANSPORTATION'] = df['TRANSPORTATION'].str.split().str[-1]
        df['TRANSPORTATION'] = df['TRANSPORTATION'].str.replace('BUSES', 'BUS', regex=False)
        df = df[df['BOOKING'].notna() & (df['BOOKING'] != '')]
        df['TRANSPORTATION'] = df['TRANSPORTATION'].astype(str).replace('guest', 'INDEPENDENT', regex=True)
        df['FLIGHT'] = df['FLIGHT'].astype(str).replace('Transfernotincluded', '', regex=True)
        
        
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

# processor = ExcelProcessor("file.xlsx")
# df = processor.read_and_process_excel()
# print(df.columns)