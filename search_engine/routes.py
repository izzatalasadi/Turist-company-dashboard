import os
import pandas as pd
import hashlib
import logging
from io import BytesIO
from datetime import datetime
from operator import or_
from PIL import Image
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from flask_socketio import emit
from flask_cors import cross_origin
from search_engine.forms import LoginForm, AddUserForm, DeleteUserForm, UpdateProfileForm, SearchForm
from search_engine.models import User, Notification, Message, Guest
from search_engine.extensions import  db
from search_engine.clean_data import ExcelProcessor
from search_engine.flight_data import FlightInfo
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file, send_from_directory
from flask_socketio import join_room, leave_room
from flask_cors import cross_origin
from datetime import datetime
from search_engine import socketio
from search_engine import limiter

logging.basicConfig(filename='app.log', level=logging.INFO)


#Blueprint Registration
auth_bp = Blueprint('auth', __name__, template_folder='templates')
main_bp = Blueprint('main', __name__)
app_bp = Blueprint('app', __name__)


# =============== Socketio ===============

@socketio.on('connect')
def handle_connect():
    logging.info('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    logging.info('Client disconnected')
    
@socketio.on('send_message')
def handle_send_message(message):
    # Save message to the database
    new_message = Message(sender_id=message['sender_id'], receiver_id=message['receiver_id'], content=message['content'])
    db.session.add(new_message)
    db.session.commit()

    # Notify the receiver
    socketio.emit('receive_message', {'content': message['content'], 'sender_id': message['sender_id']}, room=message['receiver_id'])

# To join a room for private messaging
@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    logging.info(f"{username} has joined room {room}")
    
@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    logging.info(f"{username} has left room {room}")

# =========== Bp section main ================

@main_bp.route('/', methods=['GET'])
@cross_origin()  # Apply specific CORS policy
@limiter.limit("10 per minute")  # Apply specific rate limit
@login_required
def home():
    # Assuming you already have some logic here
    # Add logic for guest statistics
    total_guests = Guest.query.count()
    checked_guests = Guest.query.filter_by(status='Checked').count()
    arrived_guests = Guest.query.filter_by(status='Arrived').count()
    user_checks = Guest.query.filter_by(checked_by=current_user.username).count()

    checked_percentage = (checked_guests / total_guests * 100) if total_guests > 0 else 0
    arrived_percentage = (arrived_guests / total_guests * 100) if total_guests > 0 else 0

    # Existing or additional logic for the page
    flight_details = {
        'total_guests': total_guests,
        'total_checked': checked_guests,
        'total_unchecked': total_guests - checked_guests,
    }

    return render_template('index.html', flight_details=flight_details, 
                           total_guests=total_guests, checked_guests=checked_guests, 
                           arrived_guests=arrived_guests, user_checks=user_checks, 
                           checked_percentage=checked_percentage, arrived_percentage=arrived_percentage)


@main_bp.route('/users')
@login_required
def display_users():
    # Query the database for all users
    users = User.query.all()
    return render_template('partials/_top.html', users=users)

# =========== Bp section auth ================

def save_picture(form_picture):
    random_hex = os.urandom(8).hex()
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_filename = random_hex + f_ext
    path = 'search_engine/static/images/faces/'
    picture_path = os.path.join(path, picture_filename)
    
    if not os.path.exists(path):
        os.makedirs(path)
    
    # form_picture is a FileStorage object and can be opened with PIL
    image = Image.open(form_picture)
    image.save(picture_path)

    return picture_filename

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileForm()
    if form.validate_on_submit():
        if form.profile_picture.data:
            picture_file = save_picture(form.profile_picture.data)
            current_user.profile_picture = picture_file
        current_user.username = form.username.data
        current_user.bio = form.bio.data
        current_user.mobile = form.mobile.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('auth.profile'))
    
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.mobile.data =  current_user.mobile
        form.bio.data = current_user.bio
        
        
    # Check if current_user has a profile_picture, if not use default
    image_file = url_for('static', filename='images/faces/' + current_user.profile_picture) if current_user.profile_picture else url_for('static', filename='images/faces/face1.jpg')
    return render_template('auth/profile.html', title='Profile', form=form, image_file=image_file)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))  # Adjust according to your home page route
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('main.home'))  # Adjust according to your home page route
        else:
            flash('Invalid username or password', 'danger')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if not current_user.is_admin:
        flash('You do not have permission to view this page.', 'warning')
        return redirect(url_for('main.home'))

    form = AddUserForm()
    if form.validate_on_submit():
        # Check if user already exists
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            # Flash message if user exists
            flash(f'This username "{existing_user.username}" is already taken. Please choose a different one.', 'danger')
            return redirect(url_for('auth.add_user'))

        # If the user does not exist, proceed to add them
        user = User(
            username=form.username.data,
            email=form.email.data,  # Add email field
            mobile=form.mobile.data,
            bio=form.bio.data,
            profile_picture='face1.jpg',  # Default profile picture
            is_admin=form.is_admin.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'User "{user.username}" has been added.', 'success')
        return redirect(url_for('auth.add_user'))

    return render_template('users_management/add_user.html', form=form)



@auth_bp.route('/delete_user', methods=['GET', 'POST'])
@login_required
def delete_user():
    if not current_user.is_admin:
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('main.home'))

    users = User.query.all()  # Query all users
    form = DeleteUserForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            db.session.delete(user)
            db.session.commit()
            flash(f'User "{user}" has been deleted.', 'success')
            return redirect(url_for('auth.delete_user'))  
        else:
            flash(f'User "{user}" not found.', 'warning')
    
    return render_template('users_management/delete_user.html', form=form, users=users)

@auth_bp.route('/import_file', methods=['GET', 'POST'])
@login_required
def import_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(url_for('auth.import_file'))

        file = request.files['file']
        filename = secure_filename(file.filename)
        if not filename.endswith('.xlsx'):
            flash('Invalid file format. Please upload an Excel file.', 'warning')
            return redirect(url_for('auth.import_file'))

        # Process file
        processor = ExcelProcessor(file)  # Adjust as needed
        try:
            df = processor.read_and_process_excel()
            for _, row in df.iterrows():
                    # Check if booking number already exists in the database
                    existing_guest = Guest.query.filter_by(booking=str(row['BOOKING'])).first()
                    
                    if not existing_guest:
                        # If not, add new guest information to the database
                        guest = Guest(
                            booking=str(row['BOOKING']),
                            first_name=str(row['FIRST NAME']),
                            last_name=str(row['LAST NAME']),
                            flight=str(row['FLIGHT']),
                            departure_from=str(row['FROM']),
                            arriving_date=None,  # You need to replace None with actual arriving_date if applicable
                            arrival_time=None,  # You need to replace None with actual arrival_time if applicable
                            transportation=str(row['TRANSPORTATION']),
                            status=str(row['STATUS']),
                            comments=str(row['COMMENTS'])
                        )
                        db.session.add(guest)
                        logging.info(f"Added new guest: {guest}")
                        
                    else:
                        logging.warning(f"Guest with booking {row['BOOKING']} already exists in the database. Skipping.")
                
                # Commit the changes to the database
            db.session.commit()
            flash('File uploaded and processed successfully.', 'success')
            logging.info("Database updated successfully.")
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to process file: {e}', 'warning')
            logging.error(f'Failed to process file: {e}')
        return redirect(url_for('auth.import_file'))

    # For a GET request, render the upload_file.html template
    return render_template('file_management/upload_file.html')

# =========== Bp section app ===========

@app_bp.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest/manifest.json')

@app_bp.route('/get_guest_details/<int:id>')
@cross_origin()  # Apply specific CORS policy
@login_required
def get_guest_details(id):
    guest = Guest.query.get_or_404(id)
    # Convert the guest object to a dictionary or suitable format for JSON response
    guest_details = {column.name: getattr(guest, column.name) for column in guest.__table__.columns}
    return jsonify(guest_details)

@app_bp.route('/update_guest_details', methods=['POST'])
@cross_origin()
def update_guest_details():
    logging.info("Update guest details route hit")
    id = request.form.get('id')
    logging.info(f"Update guest details id {id}")
    guest = Guest.query.get_or_404(id)
    
    # Update guest details based on form input
    for key in request.form:
        setattr(guest, key, request.form[key])
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Guest details updated successfully!'})

@app_bp.route('/dashboard_stats')
@cross_origin()  # Apply specific CORS policy
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

@app_bp.route('/search-results')
@login_required
def search_results():
    query = request.args.get('query', '')
    user_results = User.query.filter(User.username.like(f'%{query}%')).all()
    message_results = Message.query.filter(Message.content.like(f'%{query}%')).all()
    notification_results = Notification.query.filter(Notification.content.like(f'%{query}%')).all()

    return render_template('partials/_search_result.html', 
                            query=query,
                            user_results=user_results, 
                            message_results=message_results, 
                            notification_results=notification_results)


@app_bp.route('/search', methods=['POST', 'GET'])
@cross_origin()  # Apply specific CORS policy
@limiter.limit("30 per minute")  # Apply specific rate limit
@login_required
def search():
    form = SearchForm()
    if form.validate_on_submit():
        search_query = form.search_query.data.lower()
        flight_filter = request.args.get('flight', None)
        # Continue with your existing search logic
    else:
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
    flights = ['KL1171','LH876']
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
    
    return render_template('search_engine.html',form=form, filtered_data=filtered_data, flight_details=flight_details, flight_colors=flight_colors)


@app_bp.route('/update_status', methods=['POST'])
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
        
        if new_status == "Unchecked":
            # reset fields
            guest.checked_time = None
            guest.checked_by = None
        
        try:
            db.session.commit()
            emit('status_changed', {'booking_number': booking_number, 'new_status': new_status}, broadcast=True)
            logging.info(f"Status for booking number {booking_number} updated to {new_status}.")
            return jsonify({"message": "Status updated successfully!", "category": "success"}), 200
        
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to update status for booking number {booking_number}: {e}")
            return jsonify({"message": 'Error updating status. Please try again.', "category": 'error'}), 500
    else:
        # If no guest found with the booking number
        logging.warning(f"Booking number {booking_number} not found.")
        return jsonify({"message": "Booking number not found", "category": 'error'}), 404
    
@app_bp.route('/download')
def download_page():
    return render_template('file_management/download_file.html')

@app_bp.route('/save_excel', methods=['POST'])
@login_required
def save_excel():
    try:
        # Query the database for all guests
        guests = Guest.query.all()

        if not guests:
            flash('No data available to save. Please ensure there is data in the database.', 'warning')
            return redirect(url_for('main.home'))

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


@app_bp.route('/development-rates')
@cross_origin()  # Apply specific CORS policy
@limiter.limit("10 per minute")  # Apply specific rate limit
def development_rates():
    return render_template('rates.html', hourly_rate=450)


@app_bp.route('/send_message/<int:user_id>', methods=['POST'])
@login_required
def send_message(user_id):
    if request.method == 'POST':
        content = request.form.get('message_content')  # Get the message content from the form
        sender_id = current_user.id  # Get the sender ID from the current user
        receiver_id = user_id  # Receiver ID is the user ID specified in the route
        
        
        # Create a new message object
        message = Message(sender_id=sender_id, receiver_id=receiver_id, content=content, timestamp=datetime.utcnow())

        # Save the message to the database
        db.session.add(message)
        db.session.commit()

        return redirect(url_for('app.messages'))  # Redirect to messages page after sending message
    else:
        # Handle other HTTP methods if necessary
        return redirect(url_for('app.messages'))  # Redirect to messages page if not a POST request
@app_bp.route('/delete_message/<int:message_id>', methods=['POST'])
@login_required
def delete_message(message_id):
    message = Message.query.get_or_404(message_id)
    if message.sender_id == current_user.id:
        db.session.delete(message)
        db.session.commit()
        flash('Message deleted successfully', 'success')
    else:
        flash('You are not authorized to delete this message', 'danger')
    return redirect(url_for('app.messages'))

@app_bp.route('/reply_message/<int:message_id>', methods=['POST'])
@login_required
def reply_message(message_id):
    message = Message.query.get_or_404(message_id)
    content = request.form.get('reply_content')
    if content:
        # Assuming you have a reply template or modal, render it here
        # Return the rendered template or modal as a response
        return render_template('reply_message.html', message=message)
    else:
        flash('Reply content cannot be empty', 'danger')
        return redirect(url_for('app.messages'))

@app_bp.route('/messages')
@login_required
def messages():
    user_messages = Message.query.filter_by(receiver_id=current_user.id).order_by(Message.timestamp.desc()).all()
    return render_template('partials/_messages.html', messages=user_messages)

