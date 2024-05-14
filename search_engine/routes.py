#TO- do
# change the Excel file if its not will be added to database to PDF
# User emit to notify the system with update for "messages"

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
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file, send_from_directory, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_socketio import emit
from flask_cors import cross_origin
from search_engine.forms import LoginForm, AddUserForm, DeleteUserForm, UpdateProfileForm, SearchForm
from search_engine.models import User, Message, Guest, Activity,Flight
import uuid
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
    
    all_messages = Message.query.filter_by(receiver_id=current_user.id).order_by(Message.timestamp.desc()).all()
    unread_count = Message.query.filter_by(receiver_id=current_user.id, read=False).count()

    # Existing or additional logic for the page
    flight_details = {
        'total_guests': total_guests,
        'total_checked': checked_guests,
        'total_unchecked': total_guests - checked_guests,
    }

    return render_template('index.html', flight_details=flight_details, 
                           total_guests=total_guests, checked_guests=checked_guests, 
                           arrived_guests=arrived_guests, user_checks=user_checks, 
                           checked_percentage=checked_percentage, arrived_percentage=arrived_percentage,
                           messages=all_messages, unread_count=unread_count)


@main_bp.route('/users')
@login_required
def display_users():
    try:
        users = User.query.all()
        return render_template('partials/_top.html', users=users)  # Ensure this conversion is error-free
    except Exception as e:
        logging.error(f"Error fetching users: {e}")
        return jsonify({"error": "Internal server error"}), 500

@main_bp.route('/activities')
@login_required
def activities():
    # Fetch activities from the database ordered by timestamp
    activities = Activity.query.order_by(Activity.timestamp.desc()).all()

    # Calculate total and remaining activities (assuming you track completion)
    total_activities = len(activities)
    remaining_activities = sum(not activity.checked_in for activity in activities)

    return render_template('partials/_activities.html', 
                           activities=activities,
                           total_activities=total_activities, 
                           remaining_activities=remaining_activities)
    
def log_activity(event, description):
    if not current_user.is_authenticated:
        return  # Only log activities for authenticated users

    activity = Activity(
        user_id=current_user.id,
        event=event,
        description=description,
        timestamp=datetime.utcnow()
    )
    try:
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to log activity: {e}",'danger')


@main_bp.route('/api/activities')
@login_required
def api_activities():
    activities = Activity.query.order_by(Activity.timestamp.desc()).all()
    activity_list = [{
        'username': activity.user.username,  # assuming relationship `user` exists
        'event': activity.event,
        'description': activity.description,
        'timestamp': activity.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    } for activity in activities]
    return jsonify(activity_list)

@main_bp.route('/api/messages')
@login_required
def api_messages():
    messages = Message.query.filter_by(recipient_id=current_user.id).order_by(Message.timestamp.desc()).all()
    messages_data = [{
        'sender': message.sender.username,  # assuming a sender relationship
        'body': message.body,
        'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    } for message in messages]
    return jsonify(messages_data)

@main_bp.route('/api/guests')
@login_required
def api_guests():
    if not current_user.is_authenticated:
        return jsonify({'error': 'Unauthorized'}), 401
    
    guests = Guest.query.all()
    guest_list = [{
        'id': guest.id,
        'first_name': guest.first_name,
        'last_name': guest.last_name,
        'booking': guest.booking
    } for guest in guests]
    return jsonify(guest_list)

@main_bp.route('/api/pdfs')
@login_required
def api_pdfs():
    if not current_user.is_authenticated:
        return jsonify({'error': 'Unauthorized'}), 401
    
    directory = os.path.join(current_app.root_path, 'static', 'pdf')
    pdf_files = [f for f in os.listdir(directory) if f.endswith('.pdf')]
    pdf_list = [{'filename': pdf} for pdf in pdf_files]
    return jsonify(pdf_list)

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
            user.update_last_seen()
            log_activity('Login', f'User {current_user.username} logged in successfully')
            
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
            email=form.email.data,  
            mobile=form.mobile.data,
            bio=form.bio.data,
            profile_picture='face1.jpeg',  # Default profile picture
            is_admin=form.is_admin.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        log_activity('Add', f'New User "{user.username}" been added successfully')
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
            activity = Activity(user_id=user.id, event='Delete user', description='User deleted succesfully.')
            db.session.add(activity)
    
            db.session.commit()
            log_activity('Add', f'User "{user.username}" has been deleted successfully')
            flash(f'User "{user.username}" has been deleted.', 'success')
            return redirect(url_for('auth.delete_user'))  
        else:
            flash(f'User "{user}" not found.', 'warning')
    
    return render_template('users_management/delete_user.html', form=form, users=users)

@auth_bp.route('/import_file', methods=['GET', 'POST'])
@login_required
def import_file():
    if request.method == 'POST':
        file_type = request.form.get('file_type')
        file = request.files['file']
        filename = secure_filename(file.filename)
        if file_type == 'excel' and filename.endswith('.xlsx'):
            # Process Excel file
            process_excel(file)
            log_activity('File', f'New Excel file "{filename}" has been added successfully')
            flash('Excel information been added to database', 'success')
        elif file_type == 'pdf' and filename.endswith('.pdf'):
            # Process PDF file
            save_pdf(file)
            flash(f'PDF "{filename}" been saved', 'success')
        else:
            flash('Invalid file type or format. Please select the correct file type and upload an Excel or PDF file.', 'warning')

        return redirect(url_for('auth.import_file'))

    return render_template('file_management/upload_file.html')

def process_excel(file):
    processor = ExcelProcessor(file)  # Adjust as needed
    
    try:
        df = processor.read_and_process_excel()
        logging.info(df)
        for _, row in df.iterrows():
            flight = Flight.query.filter_by(flight_number=str(row['FLIGHT']).strip()).first()
            
            if not flight:
                flight = Flight(
                        flight_number=str(row['FLIGHT']).strip(),
                        departure_from=str(row['FROM']).strip(),
                        arrival_time=str(row.get('TIME', '')).strip()  
                        #arrival_date=str(row.get('ARRIVAL DATE', '')).strip()
                    )
                db.session.add(flight)
                logging.info(f"New flight added: {flight.flight_number}")
                
            existing_guest = Guest.query.filter_by(booking=str(row['BOOKING'])).first()
            if not existing_guest:
                guest = Guest(
                    booking=str(row['BOOKING']),
                    first_name=str(row['FIRST NAME']),
                    last_name=str(row['LAST NAME']),
                    flight_id=flight.id,
                    departure_from=flight.departure_from, # Directly using the flight's departure from
                    arrival_time=flight.arrival_time,  # Directly using the flight's arrival time
                    arriving_date=flight.arrival_date,
                    transportation=str(row['TRANSPORTATION']),
                    status=str(row['STATUS']),
                    comments=str(row['COMMENTS'])
                )
                db.session.add(guest)
                logging.info(f"Added new guest: {guest}")
            else:
                logging.warning(f"Guest with booking {row['BOOKING']} already exists. Skipping.")

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to process file: {e}")

def save_pdf(file):
    # Define the directory where PDFs are stored, relative to the Flask app instance
    directory = os.path.join(current_app.root_path, 'static', 'pdf')
    # Ensure the directory exists
    os.makedirs(directory, exist_ok=True)
    
    # Define the file path
    filename = secure_filename(file.filename)
    filepath = os.path.join(directory, filename)
    
    # Check if a file with the same name already exists
    if os.path.exists(filepath):
        # Create a unique file name by appending a timestamp or UUID
        base, extension = os.path.splitext(filename)
        unique_filename = f"{base}_{uuid.uuid4().hex}{extension}"
        filepath = os.path.join(directory, unique_filename)
        flash(f'File "{filename}" already exists. Saving as "{unique_filename}".', 'warning')
        logging.info(f'File "{filename}" renamed to "{unique_filename}" to avoid overwrite.')
    else:
        flash(f'File "{filename}" has been uploaded successfully.', 'success')
    
    # Save the file to the defined file path
    file.save(filepath)
    logging.info(f'File saved at {filepath}')
    return redirect(url_for('auth.import_file'))

@auth_bp.route('/pdf_viewer')
def pdf_viewer():
    directory = os.path.join(current_app.root_path, 'static', 'pdf')
    # List all files in the directory
    pdf_files = [f for f in os.listdir(directory) if f.endswith('.pdf')]
    pdf_files_urls = {file: url_for('static', filename='pdf/' + file) for file in pdf_files}
    return render_template('partials/_pdf_viewer.html', pdf_files=pdf_files_urls)


@auth_bp.route('/delete_guest_page')
@login_required
def delete_guest_page():
    return render_template('partials/_delete_all_guests.html')

@auth_bp.route('/delete_all_guests', methods=['POST'])
@login_required
def delete_all_guests():
    if not current_user.is_admin:
        flash('You are not authorized to perform this action.', 'danger')
        return redirect(url_for('auth.home'))

    try:
        num_deleted = Guest.query.delete()
        db.session.commit()
        flash(f'Successfully deleted {num_deleted} guests from the database.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to delete guests due to an error.', 'danger')
        logging.error(f'Error deleting all guests: {e}')
    return redirect(url_for('auth.delete_guest_page'))

@auth_bp.route('/delete_pdf', methods=['POST'])
@login_required
def delete_pdf():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    filename = request.form['filename']
    try:
        # Assuming the PDFs are stored in a directory accessible to the app
        directory = os.path.join(current_app.root_path, 'static', 'pdf')
        os.remove(os.path.join(directory, filename))
        return jsonify({'message': 'PDF deleted successfully'}), 200
    except Exception as e:
        current_app.logger.error(f'Failed to delete PDF {filename}: {str(e)}')
        return jsonify({'error': 'Failed to delete PDF'}), 500
    
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
        
    log_activity('Guest', f'"{guest.last_name}, {guest.first_name}" has been added successfully')
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
    
    return render_template('partials/_search_result.html', 
                            query=query,
                            user_results=user_results, 
                            message_results=message_results)


@app_bp.route('/search', methods=['POST', 'GET'])
@cross_origin()
@limiter.limit("30 per minute")
@login_required
def search():
    form = SearchForm()
    if form.validate_on_submit():
        search_query = form.search_query.data.lower()
        flight_filter = request.args.get('flight', None)
    else:
        search_query = request.form.get('search_query', '').lower()
        flight_filter = request.args.get('flight', None)

    guests_query = Guest.query

    if flight_filter:
        guests_query = guests_query.join(Flight).filter(Flight.flight_number.ilike(f'%{flight_filter}%'))

    if search_query:
        guests_query = guests_query.filter(or_(Guest.first_name.ilike(f'%{search_query}%'), Guest.last_name.ilike(f'%{search_query}%')))

    filtered_data = guests_query.all()
    flight_details = {
        'count': guests_query.count(),
        'total_items': len(filtered_data),
        'total_unchecked': guests_query.filter(Guest.status == 'Unchecked').count(),
        'total_checked': guests_query.filter(Guest.status == 'Checked').count()
    }

    # Assign a color to each unique flight in the filtered data
    flights = set(guest.flight for guest in filtered_data if guest.flight)
    flight_colors = {flight.flight_number: '#' + hashlib.md5(flight.flight_number.encode()).hexdigest()[:6] for flight in flights if flight and flight.flight_number}

    return render_template('search_engine.html', form=form, filtered_data=filtered_data, flight_details=flight_details, flight_colors=flight_colors)

@app_bp.route('/update_status', methods=['POST'])
@login_required
def update_status():
    booking_number = request.form.get('booking_number')
    new_status = request.form.get('status')

    guest = Guest.query.filter_by(booking=booking_number).first()
    if guest:
        guest.status = new_status
        if new_status == "Checked":
            guest.checked_time = datetime.utcnow()
            guest.checked_by = current_user.username
        elif new_status == "Unchecked":
            guest.checked_time = None
            guest.checked_by = None

        try:
            db.session.commit()
            flash('Status updated successfully', 'success')
            return jsonify({'message': 'Status updated successfully', 'status': 'success'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e), 'status': 'error'}), 500
    else:
        flash('Booking number not found', 'warning')
        return jsonify({'message': 'Booking number not found', 'status': 'warning'}), 404        
    
@app_bp.route('/download')
def download_page():
    return render_template('file_management/download_file.html')

@app_bp.route('/save_excel', methods=['POST'])
@login_required
def save_excel():
    try:
        logging.info("Accessing save_excel route")
        guests = Guest.query.all()

        if not guests:
            logging.warning("No guests found in database")
            flash('No data available to save. Please ensure there is data in the database.', 'warning')
            return redirect(url_for('app.download_page'))

        data = [{
            # Ensure all attribute names match exactly with your database model
            'Booking Number': guest.booking,
            'First Name': guest.first_name,
            'Last Name': guest.last_name,
            'Flight': guest.flight,
            'Departure From': guest.departure_from,
            'Arriving Date': guest.arriving_date.strftime('%Y-%m-%d') if guest.arriving_date else '',
            'Arrival Time': getattr(guest, 'arrival_time', '').strftime('%H:%M') if getattr(guest, 'arrival_time', None) else '',
            'Transportation': guest.transportation,
            'Status': guest.status,
            'Checked Time': guest.checked_time.strftime('%Y-%m-%d %H:%M:%S') if guest.checked_time else '',
            'Checked By': guest.checked_by if guest.checked_by else '',
            'Comments': guest.comments
            } for guest in guests]

        df = pd.DataFrame(data)
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Guests', index=False)
            
        excel_buffer.seek(0)
        logging.info("Excel file created successfully")
        return send_file(
            excel_buffer,
            as_attachment=True,
            download_name=f'Guests_arrival-{datetime.now().strftime("%Y-%m-%d")}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        #return redirect(url_for('app.download_page'))
    except Exception as e:
        logging.error(f"Error in save_excel: {e}")
        flash('An error occurred while generating the Excel file. Please try again.', 'danger')
        return redirect(url_for('app.download_page'))
    
    
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
        flash('Message been sent.', 'success')
        return redirect(url_for('main.home'))  # Redirect to messages page after sending message
    else:
        flash('Message not been send.', 'warning')
        # Handle other HTTP methods if necessary
        return redirect(url_for('main.home'))  # Redirect to messages page if not a POST request

@app_bp.route('/delete_message/<int:message_id>', methods=['POST'])
@login_required
def delete_message(message_id):
    # Retrieve the message or return a 404 if it doesn't exist
    message = Message.query.get_or_404(message_id)

    # Check if the current user is authorized to delete the message
    if message.sender_id != current_user.id and message.receiver_id != current_user.id:
        # If the user is neither the sender nor the receiver, deny access
        return jsonify({'error': 'Unauthorized access'}), 403

    # Attempt to delete the message
    try:
        db.session.delete(message)
        db.session.commit()
        return jsonify({'message': 'Message deleted successfully'}), 200
    except Exception as e:
        # Handle any exceptions that occur during the delete operation
        db.session.rollback()
        # Log the exception to your logging framework
        # e.g., app.logger.error(f'Error deleting message: {e}')
        return jsonify({'error': 'Failed to delete message, please try again later.'}), 500
    
@app_bp.route('/reply_message/<int:message_id>', methods=['POST'])
@login_required
def reply_message(message_id):
    original_message = Message.query.get_or_404(message_id)
    reply_content = request.form.get('reply_content')
    
    if not reply_content:
        return jsonify({'error': 'Reply cannot be empty'}), 400

    reply_message = Message(
        sender_id=current_user.id,
        receiver_id=original_message.sender_id,  # Note change here from `recipient_id` to `receiver_id`
        content=reply_content
    )
    db.session.add(reply_message)
    db.session.commit()
    return jsonify({'message': 'Reply sent'}), 200

@app_bp.route('/messages')
@login_required
def messages():
    all_messages = Message.query.filter_by(receiver_id=current_user.id).order_by(Message.timestamp.desc()).all()
    unread_count = Message.query.filter_by(receiver_id=current_user.id, read=False).count()
    return render_template('partials/_messages.html', messages=all_messages, unread_count=unread_count)

@app_bp.route('/read_message/<int:message_id>', methods=['POST'])
@login_required
def read_message(message_id):
    message = Message.query.get_or_404(message_id)
    if message.receiver_id == current_user.id:
        message.read = True
        db.session.commit()
        return jsonify({'success': 'Message marked as read'})
    return jsonify({'error': 'Unauthorized'}), 403