from datetime import datetime
from pyflightdata import FlightData
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

class FlightInfo:
    def __init__(self, flight_numbers):
        self.flight_numbers = flight_numbers
        self.f = FlightData()
        
    def fetch_flight_info(self, flight_number):
        try:
            flight_info = self.f.get_history_by_flight_number(flight_number)
            if flight_info:
                logging.info(f"Fetched data for {flight_number}")
                return flight_info
            else:
                logging.warning(f"No data found for {flight_number}")
                return {'flight_number': flight_number, 'status': 'No data found'}
        except Exception as e:
            logging.error(f"Error fetching data for {flight_number}: {e}")
            return {'flight_number': flight_number, 'status': f'Error fetching data: {e}'}
            
    def get_flights_info(self):
        flights_info = {}
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_flight = {executor.submit(self.fetch_flight_info, flight_number): flight_number for flight_number in self.flight_numbers}
            for future in as_completed(future_to_flight):
                flight_data = future.result()
                if isinstance(flight_data, list) and flight_data:
                    flight_number = flight_data[0]['identification']['number']['default']
                    arriving_date = flight_data[0]['time']['scheduled']['arrival_date']
                    arriving_time = flight_data[0]['time']['scheduled']['arrival_time']
                    flights_info[flight_number] = [arriving_date, arriving_time]
                else:
                    logging.warning(f"Invalid data format for flight: {flight_data}")
        
        return flights_info

def main():
    flight_numbers = ['KL1171', 'LH876'] 
    flight_info_obj = FlightInfo(flight_numbers)
    flights_info = flight_info_obj.get_flights_info()

    for flight_data in flights_info.items():
        print(flight_data)  # Process or print the flight data
    
if __name__ == '__main__':
    main()
