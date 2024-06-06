import re
import pandas as pd 

class ExcelProcessor:
    def __init__(self, df):
        self.df = df
        
    def read_and_process_excel(self):
        
        # Drop completely empty rows
        self.df = self.df.dropna(how='all')

        # Find the first and last non-empty rows
        first_non_empty_row = self.df.first_valid_index()
        last_non_empty_row = self.df.last_valid_index()

        # Slice the DataFrame to include only the non-empty rows
        self.df = self.df.loc[first_non_empty_row:last_non_empty_row]
        self.df = self.df.iloc[1:]
        self.df.columns = ["booking_no", "first_name", "last_name", "VA_included", "transfer_type", "transfer_provided", "cabin","transfer_date","transfer_time","from_type","from_location"]
        
        # Create new columns for the processed data
        self.df["to_city"] = ""
        self.df["flight"] = ""
        self.df["org_city"] = ""
        self.df["ship_name"] = ""
        
        # Process each row based on the value of "From Type"
        for index, row in self.df.iterrows():
            from_type = row["from_type"]
            from_location = row["from_location"]
            
            org_city = row["org_city"]
            flight = row["flight"]
            to_location = row["to_city"]
            ship_name = row["ship_name"]
            
            if from_type == "APT":
                tmp_list = from_location.split('-')
                to_location = tmp_list[0]
                flight, org_city = tmp_list[1].split('(Org City:')
                org_city = org_city.rstrip(')')
                
                self.df.at[index, "to_city"] = str(to_location).strip()
                self.df.at[index, "flight"] = str(flight).strip()
                self.df.at[index, "org_city"] = str(org_city).strip()
                self.df.at[index, "ship_name"] = ""
                
            elif from_type == "SHP":
                to_city, ship_name = from_location.split('-')
                self.df.at[index, "to_city"] = str(to_city).strip()
                self.df.at[index, "ship_name"] = ship_name
                self.df.at[index, "org_city"] = ""
                self.df.at[index, "flight"] = ""

            elif from_type == "UNK":
                self.df.at[index, "to_city"] = ""
                self.df.at[index, "ship_name"] = ""
                self.df.at[index, "org_city"] = ""
                self.df.at[index, "flight"] = ""

        # Drop the original "From Location" column and rename "Processed From Location" to "From Location"
        self.df.drop(columns=["from_location"], inplace=True)
        
        return self.df

