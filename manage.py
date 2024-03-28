#name_search_engine/manage.py
from operator import or_
from flask import jsonify, render_template, request, send_file, redirect, url_for, flash,jsonify
import pandas as pd
from io import BytesIO
from datetime import datetime
from flask_login import current_user, login_required

from search_engine.models import Guest
from search_engine import create_app, db
from search_engine.config import DevelopmentConfig
import hashlib
from cryptography.fernet import Fernet
from sqlalchemy import or_
import logging
from search_engine.flight_data import FlightInfo
from flask_wtf.csrf import CSRFProtect

logging.basicConfig(filename='app.log', level=logging.INFO)

# Assuming you have a function to load or generate a key for Fernet
def load_key():
    """
    Load the previously generated key
    """
    return open("secret.key", "rb").read()

key = load_key()

@login_required
def encrypt_data(data, key_path="secret.key"):
    # Load the previously generated key
    with open(key_path, "rb") as key_file:
        key = key_file.read()
    fernet = Fernet(key)
    
    encrypted_data = fernet.encrypt(data.encode())
    return encrypted_data

app = create_app(DevelopmentConfig)
app.config['SECRET_KEY'] = 'QjzjsYIw-Po_T8iXr92tyOfgwWdvmWlYLUZM8fg5O68='
csrf = CSRFProtect(app)


@app.route('/', methods=['GET'])
@login_required
def home():
    flight_details = {
        'total_guests': Guest.query.count(),
        'total_checked': Guest.query.filter_by(status='Checked').count(),
        'total_unchecked': Guest.query.filter_by(status='Unchecked').count(),
    }
    # This function now solely renders the home page and handles no file uploads.
    return render_template('index.html',flight_details=flight_details)

@app.route('/dashboard_stats')
def dashboard_stats():
    total_guests = Guest.query.count()
    total_checked = Guest.query.filter_by(status='Checked').count()
    total_unchecked = Guest.query.filter_by(status='Unchecked').count()

    stats = {
        'total_guests': total_guests,
        'total_checked': total_checked,
        'total_unchecked': total_unchecked,
    }

    return jsonify(stats)



@app.route('/search', methods=['POST', 'GET'])
@login_required
def search():
    # Additional details for flights
    search_query = request.form.get('search_query', '').lower()
    flight_filter = request.args.get('flight', None)
    
    guests_query = Guest.query

    if flight_filter:
        guests_query = guests_query.filter(Guest.flight.ilike(f'%{flight_filter}%'))
    
    if search_query:
        guests_query = guests_query.filter(or_(Guest.first_name.ilike(f'%{search_query}%'), Guest.last_name.ilike(f'%{search_query}%')))

    filtered_data = guests_query.all()
    flight_details = {
    'count': guests_query.count(),
    'total_items' : len(filtered_data),
    'total_unchecked' : guests_query.filter_by(status='Unchecked').count(),
    'total_checked' : guests_query.filter_by(status='Checked').count()}
    
    logging.info(f'Flight details: {flight_details}')
    # Get the flights info for flights in the filtered data
    #flights = set(guest.flight for guest in filtered_data if guest.flight !='')
    flights = ['WF429','WF118']
    logging.info(f'Flights: {flights}')
    
    flight_arriving_time = FlightInfo(flights).get_flights_info()
    logging.info(f'Flights arriving time: {flight_arriving_time}')

    logging.info('Start adding the arriving date')
    try:
        for guest in filtered_data:
            if guest.flight in flight_arriving_time:
                # Only update if the flight is found in the flight_arriving_time dictionary
                arriving_info = flight_arriving_time.get(guest.flight, None)
                if arriving_info:
                    guest.arriving_date = arriving_info[0]  # Assuming this is the arriving date
                    guest.arrival_time = arriving_info[1]  # Assuming this is the arrival time
                    db.session.add(guest)
                    
    except Exception as e:
        logging.warn(f'Error: Flight not found {e}')
        
    try:
        db.session.commit()
        logging.info('Flight arriving information updated successfully.')
        
    except Exception as e:
        db.session.rollback()
        logging.error(f'Error: Failed to update flight arriving information: {e}')
        
    logging.info(f"Flight details: {flight_details}")

    # Assign a color to each unique flight in the filtered data
    flight_colors = {flight: '#' + hashlib.md5(flight.encode()).hexdigest()[:6] for flight in flights}
    
    return render_template('search_engine.html', filtered_data=filtered_data, flight_details=flight_details, flight_colors=flight_colors)

@app.route('/update_status', methods=['POST'])
@login_required
def update_status():
    booking_number = request.form.get('booking_number')
    new_status = request.form.get('status')  # 'Checked' or 'Unchecked'

    # Attempt to find an existing guest with the given booking number
    guest = Guest.query.filter_by(booking=booking_number).first()
    
    if guest:
        # If guest found, update status and other relevant fields
        guest.status = new_status
        if new_status == "Checked":
            guest.checked_time = datetime.utcnow()
            guest.checked_by = current_user.username
        else:
            # reset fields
            guest.checked_time = None
            guest.checked_by = None
        logging.info(f"Status for booking number {booking_number} updated to {new_status}.")
        
        try:
            db.session.commit()
            return jsonify({"message": "Status updated successfully!", "category": "success"}), 200
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to update status for booking number {booking_number}: {e}")
            return jsonify({"message": 'Error updating status. Please try again.', "category": 'error'}), 500
    else:
        # If no guest found with the booking number
        logging.warning(f"Booking number {booking_number} not found.")
        return jsonify({"message": "Booking number not found", "category": 'error'}), 404
    
@app.route('/download')
def download_page():
    return render_template('file_management/download_file.html')

@app.route('/save_excel', methods=['POST'])
@login_required
def save_excel():
    try:
        # Query the database for all guests
        guests = Guest.query.all()

        if not guests:
            flash('No data available to save. Please ensure there is data in the database.', 'warning')
            return redirect(url_for('home'))

        # Convert the query result to a list of dictionaries
        data = [{
            'Booking Number': guest.booking,
            'First Name': guest.first_name,
            'Last Name': guest.last_name,
            'Flight': guest.flight,
            'Departure From': guest.departure_from,
            'Arriving Date': guest.arriving_date if guest.arriving_date else '',
            'Arrival Time': guest.arrival_time if guest.arrival_time else '',
            'Transportation': guest.transportation,
            'Status': guest.status,
            'Checked Time': guest.checked_time.strftime('%Y-%m-%d %H:%M:%S') if guest.checked_time else '',
            'Checked By': guest.checked_by,  # You may need to adjust this based on how you store user information
            'Comments': guest.comments
        } for guest in guests]

        # Convert the list of dictionaries to a DataFrame
        df = pd.DataFrame(data)

        # Use a BytesIO buffer to write the DataFrame to an Excel file in memory
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Guests', index=False)

        # Reset the buffer position to the beginning
        excel_buffer.seek(0)

        # Return the Excel file to the client
        return send_file(
            excel_buffer,
            as_attachment=True,
            download_name='guest_data.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        logging.error(f"Error generating Excel file: {e}")
        flash('An error occurred while generating the Excel file. Please try again.', 'danger')
        render_template('file_management/download_file.html')

if __name__ == '__main__':
    #app.run(debug=True, host= '0.0.0.0')
    app.run()
    