from pyflightdata import FlightData
from concurrent.futures import ThreadPoolExecutor, as_completed

class FlightInfo:
    def __init__(self, flight_numbers):
        self.flight_numbers = flight_numbers
        self.f = FlightData()

    def fetch_flight_info(self, flight_number):
        try:
            flight_info = self.f.get_history_by_flight_number(flight_number)
            if flight_info:
                return flight_info
            else:
                return {'flight_number': flight_number, 'status': 'No data found'}
        except Exception as e:
            print(f"Error fetching data for {flight_number}: {e}")
            return {'flight_number': flight_number, 'status': 'Error fetching data'}

    def get_flights_info(self):
        flights_info = {}
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_flight = {executor.submit(self.fetch_flight_info, flight_number): flight_number for flight_number in self.flight_numbers}
            for future in as_completed(future_to_flight):
                flight_data = future.result()
                flight_number = flight_data[0]['identification']['number']['default']
                arriving_date = flight_data[0]['time']['scheduled']['arrival_date']
                arriving_time = flight_data[0]['time']['scheduled']['arrival_time'] 
                flights_info[flight_number] = [arriving_date, arriving_time]
                
        return flights_info

# def main():
#     flight_numbers = ['SK2862', 'LH874', 'SK899', 'SK2870', 'KL1189', 'SK249', 'KL1185', 'SK269', 'SK271', 'SK267', 'DY608', 'KL1187', 'SK257', 'DY618', 'SK255', 'SK2864', 'SK273']  
#     flight_info_obj = FlightInfo(flight_numbers)
#     flights_info = flight_info_obj.get_flights_info()

#     for flight_data in flights_info.items():
#         print(flight_data)  # Process or print the flight data
    
# if __name__ == '__main__':
#     main()
