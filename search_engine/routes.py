import os
import pandas as pd
import hashlib
import logging
from io import BytesIO
from datetime import datetime

from PIL import Image
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file, send_from_directory, current_app
from flask_login import login_user, logout_user, login_required, current_user
#from flask_cors import cross_origin
from search_engine.forms import LoginForm, AddUserForm, DeleteUserForm, UpdateProfileForm, SearchForm
from search_engine.models import User, Message, Guest, Activity, Flight, Transportation
import uuid
from search_engine.extensions import db
from search_engine.clean_data import ExcelProcessor
from search_engine import socketio, limiter
from sqlalchemy.orm import joinedload
from flask_wtf.csrf import validate_csrf
from sqlalchemy import or_

logging.basicConfig(filename='app.log', level=logging.INFO)

# Blueprint Registration
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


# =========== Bp section main ================

@main_bp.route('/', methods=['GET'])
@limiter.limit("10 per minute")
@login_required
def home():
    try:
        logging.debug("Home route accessed")
        
        total_guests = Guest.query.count()
        logging.debug(f"Total guests: {total_guests}")

        checked_guests = Guest.query.filter_by(status='Checked').count()
        logging.debug(f"Checked guests: {checked_guests}")

        arrived_guests = Guest.query.filter_by(status='Arrived').count()
        logging.debug(f"Arrived guests: {arrived_guests}")

        user_checks = Guest.query.filter_by(checked_by=current_user.id).count()
        logging.debug(f"User checks: {user_checks}")

        checked_percentage = (checked_guests / total_guests * 100) if total_guests > 0 else 0
        arrived_percentage = (arrived_guests / total_guests * 100) if total_guests > 0 else 0
        
        all_messages = Message.query.filter_by(receiver_id=current_user.id).order_by(Message.timestamp.desc()).all()
        unread_count = Message.query.filter_by(receiver_id=current_user.id, read=False).count()
        logging.debug(f"Unread messages: {unread_count}")

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
    except Exception as e:
        logging.error(f"Error in home route: {e}")
        return render_template('error.html', error=str(e)), 500
    
@main_bp.route('/users')
@login_required
def display_users():
    try:
        users = User.query.all()
        if current_user in users:
            users.remove(current_user)
        return render_template('partials/_top.html', users=users)
    except Exception as e:
        logging.error(f"Error fetching users: {e}")
        return jsonify({"error": "Internal server error"}), 500

@main_bp.route('/activities')
@login_required
def activities():
    try:
        activities = Activity.query.order_by(Activity.timestamp.desc()).all()
        total_activities = len(activities)
        remaining_activities = sum(not activity.checked_in for activity in activities)

        return render_template('partials/_activities.html', 
                            activities=activities,
                            total_activities=total_activities, 
                            remaining_activities=remaining_activities)
    except Exception as e:
        logging.error(f"Error fetching activities: {e}")
        return jsonify({"error": "Internal server error"}), 500
    
def log_activity(event, description):
    if not current_user.is_authenticated:
        return

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
        flash(f"Failed to log activity: {e}", 'danger')

@main_bp.route('/api/activities')
@login_required
def api_activities():
    try:
        if current_user.is_authenticated:
            activities = Activity.query.order_by(Activity.timestamp.desc()).all()
            activity_list = [{
                'username': activity.user.username,
                'event': activity.event,
                'description': activity.description,
                'timestamp': activity.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            } for activity in activities]
            return jsonify(activity_list)
        else:
            current_app.logger.error("User is not authenticated")
            return jsonify({'error': 'User is not authenticated'}), 401
    except Exception as e:
        current_app.logger.error(f"Error fetching activities: {e}")
        return jsonify({'error': 'Failed to fetch activities'}), 500

@main_bp.route('/api/messages')
@login_required
def api_messages():
    receiver_id = request.args.get('receiver_id')
    if receiver_id is None:
        return jsonify({'error': 'Receiver ID is required'}), 400
    
    messages = Message.query.filter_by(receiver_id=receiver_id).order_by(Message.timestamp.desc()).all()
    messages_data = [{
        'sender': message.sender.username,
        'body': message.content,
        'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    } for message in messages]
    return jsonify(messages_data)

@main_bp.route('/api/guests')
@login_required
def api_guests():
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
        form.mobile.data = current_user.mobile
        form.bio.data = current_user.bio
        
    image_file = url_for('static', filename='images/faces/' + current_user.profile_picture) if current_user.profile_picture else url_for('static', filename='images/faces/face1.jpeg')
    return render_template('auth/profile.html', title='Profile', form=form, image_file=image_file)

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("50 per minute")
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
            flash('Invalid username or password', 'warning')
            return redirect(url_for('auth.login'))
    
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
        try:
            existing_user = User.query.filter((User.username == form.username.data) | (User.email == form.email.data)).first()
            if existing_user:
                flash(f'This username "{existing_user.username}" or email "{existing_user.email}" is already taken. Please choose a different one.', 'danger')
                return redirect(url_for('auth.add_user'))

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
            log_activity('Add', f'New User "{user.username}" added successfully')
            flash(f'User "{user.username}" has been added.', 'success')
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error adding user: {e}")
            flash(f'Error adding user: {str(e)}', 'danger')
            return redirect(url_for('auth.add_user'))

    return render_template('users_management/add_user.html', form=form)

@auth_bp.route('/delete_user', methods=['GET', 'POST'])
@login_required
def delete_user():
    if not current_user.is_admin:
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('main.home'))

    users = User.query.all()
    form = DeleteUserForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            db.session.delete(user)
            db.session.commit()
            log_activity('Delete', f'User "{user.username}" deleted successfully')
            flash(f'User "{user.username}" has been deleted.', 'success')
            return redirect(url_for('auth.delete_user'))
        else:
            flash(f'User "{form.username.data}" not found.', 'warning')
    
    return render_template('users_management/delete_user.html', form=form, users=users)

@auth_bp.route('/import_file', methods=['GET', 'POST'])
@login_required
def import_file():
    if request.method == 'POST':
        file_type = request.form.get('file_type')
        file = request.files['file']
        filename = secure_filename(file.filename)
        if file_type == 'excel' and filename.endswith('.xlsx'):
            process_excel(file)
            log_activity('File', f'New Excel file "{filename}" added successfully')
            flash('Excel information added to database', 'success')
        elif file_type == 'pdf' and filename.endswith('.pdf'):
            save_pdf(file)
            flash(f'PDF "{filename}" saved', 'success')
        else:
            flash('Invalid file type or format. Please select the correct file type and upload an Excel or PDF file.', 'warning')

        return redirect(url_for('auth.import_file'))

    return render_template('file_management/upload_file.html')


def process_excel(file):
    processor = ExcelProcessor(file)
    
    try:
        df = processor.read_and_process_excel()
        
        # Ensure the DataFrame is not empty
        if df.empty:
            logging.warning("No guest data found in the Excel file.")
            flash("No guest data found in the Excel file.", 'warning')
            return

        # First, add all flights to the database
        for _, row in df.iterrows():
            flight_number = row.get('flight', '')
            if flight_number:
                flight = Flight.query.filter_by(flight_number=flight_number).first()
                if not flight:
                    try:
                        flight = Flight(
                            flight_number=flight_number,
                            departure_from=row.get('org_city', ''),
                            arrival_time=row.get('transfer_time', ''),
                            arrival_date=row.get('"arrival_date"', '')
                        )
                        db.session.add(flight)
                        db.session.flush()
                    except Exception as e:
                        logging.error(f"Failed to create flight: {e}")
                        flash(f"Failed to create flight: {e}", 'danger')
                        return

        # Commit all flight additions
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to add flights to the database: {e}")
            flash(f"Failed to add flights to the database: {e}", 'danger')
            return
        
        
        # Then, handle guests and transportations
        for _, row in df.iterrows():
            flight_number = row.get('flight', '')
            if flight_number:
                flight = Flight.query.filter_by(flight_number=flight_number).first()
                flight = Flight.query.filter_by(flight_number=flight_number).first()
            
                existing_guest = Guest.query.filter_by(booking=str(row.get('booking_no', ''))).first()

                if not existing_guest:
                    try:
                        guest = Guest(
                            booking=str(row.get('booking_no', '')),
                            first_name=str(row.get('first_name', '')),
                            last_name=str(row.get('last_name', '')),
                            flight_id=flight.id if flight else None,
                            departure_from=flight.departure_from if flight else None,
                            arrival_time=flight.arrival_time if flight else None,
                            arriving_date = datetime.strptime(str(row.get('arrival_date', '')).split()[0], '%Y-%m-%d').strftime('%d-%m-%y'),
                            cabin = str(row.get('cabin', '')),
                            status=str(row.get('STATUS', '')),
                            comments=str(row.get('COMMENTS', ''))
                        )
                        db.session.add(guest)
                        db.session.flush()
                        guest_id = guest.id
                        
                    except Exception as e:
                        db.session.rollback()
                        logging.error(f"Failed to create guest: {e}")
                        flash(f"Failed to create guest: {e}", 'danger')
                        continue
                else:
                    guest_id = existing_guest.id

                try:
                    # Fetch the transportation related to this guest
                    exist_transportation = Transportation.query.filter_by(guest_id=guest_id).first()
                    if not exist_transportation:
                        # Add transportation record
                        transportation = Transportation(
                            guest_id=guest_id,
                            transport_type=str(row.get('TRANSPORTATION', '')),
                            transport_details=str(row.get('transport_details', ''))  # Adjust based on your Excel structure
                        )
                        db.session.add(transportation)
                except Exception as e:
                    db.session.rollback()
                    logging.error(f"Failed to create transportation record: {e}")
                    flash(f"Failed to create transportation record: {e}", 'danger')
                    continue

        try:
            db.session.commit()
            flash('Excel information added to database', 'success')
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to add guest or transportation records to the database: {e}")
            flash(f"Failed to add guest or transportation records to the database: {e}", 'danger')

    except Exception as e:
        logging.error(f"Failed to process file: {e}")
        flash(f"Failed to process file: {e}", 'danger')
        
def save_pdf(file):
    directory = os.path.join(current_app.root_path, 'static', 'pdf')
    os.makedirs(directory, exist_ok=True)
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(directory, filename)
    
    if os.path.exists(filepath):
        base, extension = os.path.splitext(filename)
        unique_filename = f"{base}_{uuid.uuid4().hex}{extension}"
        filepath = os.path.join(directory, unique_filename)
        flash(f'File "{filename}" already exists. Saving as "{unique_filename}".', 'warning')
    else:
        flash(f'File "{filename}" has been uploaded successfully.', 'success')
    
    file.save(filepath)
    logging.info(f'File saved at {filepath}')
    return redirect(url_for('auth.import_file'))

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
        num_deleted_guests = Guest.query.delete()
        num_deleted_trans = Transportation.query.delete()
        num_deleted_flights = Flight.query.delete()
        db.session.commit()
        flash(f'Successfully deleted {num_deleted_guests} guests, transportation {num_deleted_trans}, and flights {num_deleted_flights} from the database.', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash('Failed to delete data due to an error.', 'danger')
        logging.error(f'Error deleting all guests: {e}')
    
    return redirect(url_for('auth.delete_guest_page'))

@auth_bp.route('/delete_pdf', methods=['POST'])
@login_required
def delete_pdf():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    filename = request.form['filename']
    try:
        directory = os.path.join(current_app.root_path, 'static', 'pdf')
        os.remove(os.path.join(directory, filename))
        flash('PDF deleted successfully.', 'success')
        return jsonify({'message': 'PDF deleted successfully'}), 200
    except Exception as e:
        current_app.logger.error(f'Failed to delete PDF {filename}: {str(e)}')
        return jsonify({'error': 'Failed to delete PDF'}), 500
    
# =========== Bp section app ===========

@app_bp.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest/manifest.json')

@app_bp.route('/get_guest_details/<int:guest_id>', methods=['GET'])
@login_required
def get_guest_details(guest_id):
    guest = Guest.query.get_or_404(guest_id)
    guest_data = {
        'id': guest.id,
        'first_name': guest.first_name,
        'last_name': guest.last_name,
        'booking': guest.booking,
        'departure_from': guest.departure_from,
        'arriving_date': guest.arriving_date,
        'arrival_time': guest.arrival_time,
        'comments': guest.comments,
        'flight_number': guest.flight.flight_number if guest.flight else None,
        'transportations': [transport.to_dict() for transport in guest.transportation]
    }
    return jsonify(guest_data)

@app_bp.route('/get_flights', methods=['GET'])
@login_required
def get_flights():
    flights = Flight.query.all()
    flights_data = [{'id': flight.id, 'flight_number': flight.flight_number} for flight in flights]
    return jsonify(flights_data)

@app_bp.route('/update_guest_details', methods=['POST'])
@login_required
def update_guest_details():
    logging.info("Update guest details route hit")
    id = request.form.get('id')
    logging.info(f"Update guest details id {id}")
    guest = Guest.query.get_or_404(id)
    
    for key in request.form:
        if key == 'flight_number':
            flight_number = request.form[key]
            flight = Flight.query.filter_by(flight_number=flight_number).first()
            if not flight:
                flight = Flight(
                    flight_number=flight_number,
                    departure_from=request.form.get('departure_from', ''),
                    arrival_time=request.form.get('arrival_time', ''),
                    arrival_date=request.form.get('arriving_date', '')
                )
                db.session.add(flight)
                db.session.commit()
            guest.flight_id = flight.id
        else:
            setattr(guest, key, request.form[key])
    
    db.session.commit()
    log_activity('Guest', f'"{guest.last_name}, {guest.first_name}" has been updated successfully')
    flash('Guest details updated successfully', 'success')
    return jsonify({'status': 'success', 'message': f'"{guest.last_name}, {guest.first_name}" has been updated successfully'})

@app_bp.route('/dashboard_stats', methods=['GET'])
@login_required
def dashboard_stats():
    # Retrieve the date parameter if provided
    date_str = request.args.get('date')
    if date_str:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        guests = Guest.query.filter(Guest.date == selected_date).all()
    else:
        guests = Guest.query.all()

    total_guests = len(guests)
    total_checked = sum(1 for guest in guests if guest.status == 'Checked')
    total_unchecked = total_guests - total_checked
    
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
@limiter.limit("30 per minute")
@login_required
def search():
    directory = os.path.join(current_app.root_path, 'static', 'pdf')
    pdf_files = [f for f in os.listdir(directory) if f.endswith('.pdf')]
    pdf_files_urls = {file: url_for('static', filename='pdf/' + file) for file in pdf_files}
    
    form = SearchForm()
    if form.validate_on_submit():
        search_query = form.search_query.data.lower()
    else:
        search_query = request.form.get('search_query', '').lower()

    flight_filter = request.args.get('flight', None)
    arrival_time_filter = request.args.get('arrival_time', None)
    departure_from_filter = request.args.get('departure_from', None)
    transportation_filter = request.args.get('transportation', None)

    guests_query = Guest.query

    if flight_filter:
        guests_query = guests_query.join(Flight).filter(Flight.flight_number.ilike(f'%{flight_filter}%'))

    if arrival_time_filter:
        guests_query = guests_query.join(Flight).filter(Flight.arrival_time.ilike(f'%{arrival_time_filter}%'))

    if departure_from_filter:
        guests_query = guests_query.join(Flight).filter(Flight.departure_from.ilike(f'%{departure_from_filter}%'))
    
    if transportation_filter:
        guests_query = guests_query.join(Transportation).filter(Transportation.transport_type.ilike(f'%{transportation_filter}%'))

    if search_query:
        guests_query = guests_query.join(Flight).filter(
            or_(
                Guest.first_name.ilike(f'%{search_query}%'), 
                Guest.last_name.ilike(f'%{search_query}%'), 
                Flight.flight_number.ilike(f'%{search_query}%'), 
                Guest.departure_from.ilike(f'%{search_query}%')
            )
        )

    filtered_data = guests_query.options(joinedload(Guest.flight)).all()
    total_guests = Guest.query.count()
    total_checked = Guest.query.filter_by(status='Checked').count()
    
    flight_details = {
        'count': total_guests,
        'total_items': len(filtered_data),
        'total_checked': total_checked
    }

    flights = set(guest.flight for guest in filtered_data if guest.flight)
    flight_colors = {flight.flight_number: '#' + hashlib.md5(flight.flight_number.encode()).hexdigest()[:6] for flight in flights if flight and flight.flight_number}
    
    arrival_times = set(flight.arrival_time for flight in flights if flight.arrival_time)
    arrival_time_colors = {arrival_time: '#' + hashlib.md5(arrival_time.encode()).hexdigest()[:6] for arrival_time in arrival_times}
    
    departure_froms = set(flight.departure_from for flight in flights if flight.departure_from)
    departure_from_colors = {departure_from: '#' + hashlib.md5(departure_from.encode()).hexdigest()[:6] for departure_from in departure_froms}
    
    transportations = set()
    for guest in filtered_data:
        for transportation in guest.transportation:
            transportations.add(transportation)
    transportation_colors = {transport.transport_type: '#' + hashlib.md5(transport.transport_type.encode()).hexdigest()[:6] for transport in transportations}

    return render_template('search_engine.html', form=form, 
                            filtered_data=filtered_data,
                            search_query=search_query, 
                            flight_details=flight_details, 
                            flight_colors=flight_colors, 
                            arrival_time_colors=arrival_time_colors, 
                            departure_from_colors=departure_from_colors,
                            transportation_colors=transportation_colors, 
                            pdf_files=pdf_files_urls,
                            total_guests=total_guests, 
                            total_checked=total_checked)
   
@app_bp.route('/update_status', methods=['POST'])
@login_required
def update_status():
    try:
        booking_number = request.form.get('booking_number')
        new_status = request.form.get('status')
        csrf_token = request.form.get('csrf_token')
        
        # Validate CSRF token
        validate_csrf(csrf_token)
        
        logging.info(f"Received request to update status. Booking number: {booking_number}, New status: {new_status}")

        guest = Guest.query.filter_by(booking=booking_number).first()
        if guest:
            guest.status = new_status
            guest_id = guest.id
            
            logging.info(f"Guest ID: {guest_id}")
            
            if new_status == "Checked":
                guest.checked_time = datetime.utcnow()
                guest.checked_by = current_user.id  # Ensure this is the user ID
            elif new_status == "Unchecked":
                guest.checked_time = None
                guest.checked_by = None

            db.session.commit()
            logging.info(f"Successfully updated status for booking number: {booking_number}")
            return jsonify({'status': 'success', 'message': 'Status updated successfully'}), 200
        else:
            logging.warning(f"Booking number not found: {booking_number}")
            return jsonify({'status': 'error', 'message': 'Booking number not found'}), 404
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating status: {e}")
        return jsonify({'status': 'error', 'message': f'Failed to update status: {e}'}), 500
            
@app_bp.route('/download')
@login_required
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

        data = []
        for guest in guests:
            try:
                arriving_date = guest.arriving_date.strftime('%Y-%m-%d') if guest.arriving_date else ''
            except AttributeError:
                arriving_date = guest.arriving_date if isinstance(guest.arriving_date, str) else ''
            
            try:
                arrival_time = guest.arrival_time.strftime('%H:%M') if guest.arrival_time else ''
            except AttributeError:
                arrival_time = guest.arrival_time if isinstance(guest.arrival_time, str) else ''
            
            try:
                checked_time = guest.checked_time.strftime('%Y-%m-%d %H:%M:%S') if guest.checked_time else ''
            except AttributeError:
                checked_time = guest.checked_time if isinstance(guest.checked_time, str) else ''
            
            data.append({
                'Booking Number': guest.booking,
                'First Name': guest.first_name,
                'Last Name': guest.last_name,
                'Flight': guest.flight,
                'Departure From': guest.departure_from,
                'Arriving Date': arriving_date,
                'Arrival Time': arrival_time,
                'Transportation': guest.transportation,
                'Status': guest.status,
                'Checked Time': checked_time,
                'Checked By': guest.checked_by if guest.checked_by else '',
                'Comments': guest.comments
            })

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
    except Exception as e:
        logging.error(f"Error in save_excel: {e}")
        flash('An error occurred while generating the Excel file. Please try again.', 'danger')
        return redirect(url_for('app.download_page'))
    
@app_bp.route('/development-rates')
@limiter.limit("10 per minute")
@login_required
def development_rates():
    return render_template('rates.html', hourly_rate=450)

@app_bp.route('/send_message/<int:user_id>', methods=['POST'])
@login_required
def send_message(user_id):
    if request.method == 'POST':
        content = request.form.get('message_content')
        sender_id = current_user.id
        receiver_id = user_id
        
        message = Message(sender_id=sender_id, receiver_id=receiver_id, content=content, timestamp=datetime.utcnow())
        db.session.add(message)
        db.session.commit()
        
        return jsonify({'message': 'Message sent successfully!'}), 200
    else:
        return jsonify({'error': 'Failed to send message'}), 400

@app_bp.route('/delete_message/<int:message_id>', methods=['POST'])
@login_required
def delete_message(message_id):
    message = Message.query.get_or_404(message_id)
    
    if message.sender_id != current_user.id and message.receiver_id != current_user.id:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    try:
        db.session.delete(message)
        db.session.commit()
        flash('Message deleted successfully.', 'success')
        return jsonify({'message': 'Message deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
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
        receiver_id=original_message.sender_id,
        content=reply_content
    )
    db.session.add(reply_message)
    db.session.commit()
    
    flash('Reply sent', 'success')
    return jsonify({'message': 'Reply sent'}), 200

@app_bp.route('/messages')
@login_required
def messages():
    all_messages = Message.query.filter_by(receiver_id=current_user.id).order_by(Message.timestamp.desc()).all()
    unread_count = Message.query.filter_by(receiver_id=current_user.id, read=False).count()
    return render_template('partials/_messages.html', messages=all_messages, unread_count=unread_count, message_thread=message_thread)

def message_thread(user1_id, user2_id):
    return Message.query.filter(
        ((Message.sender_id == user1_id) & (Message.receiver_id == user2_id)) |
        ((Message.sender_id == user2_id) & (Message.receiver_id == user1_id))
    ).order_by(Message.timestamp).all()
        
@app_bp.route('/protected')
@login_required
def protected_route():
    return "This is a protected route."

@app_bp.route('/read_message/<int:message_id>', methods=['POST'])
@login_required
def read_message(message_id):
    message = Message.query.get_or_404(message_id)
    if message.receiver_id == current_user.id:
        message.read = True
        db.session.commit()
        return jsonify({'success': 'Message marked as read'})
    return jsonify({'error': 'Unauthorized'}), 403
