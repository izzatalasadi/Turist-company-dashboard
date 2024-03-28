from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user,login_required, current_user
from search_engine.forms import LoginForm, AddUserForm, DeleteUserForm
from search_engine.models import User, db
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from search_engine.models import Guest
import logging
from search_engine.clean_data import ExcelProcessor

auth_bp = Blueprint('auth', __name__, template_folder='templates')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))  # Adjust according to your home page route
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('home'))  # Adjust according to your home page route
        else:
            flash('Invalid username or password', 'danger')
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

def init_app(app):
    app.register_blueprint(auth_bp)

@auth_bp.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if not current_user.is_admin:
        flash('You do not have permission to view this page.', 'warning')
        return redirect(url_for('home'))

    form = AddUserForm()
    if form.validate_on_submit():
        # Check if user already exists
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            # Flash message if user exists
            flash(f'This username "{existing_user}" is already taken. Please choose a different one.', 'danger')
            return redirect(url_for('auth.add_user'))

        # If the user does not exist, proceed to add them
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        user.is_admin = form.is_admin.data
        db.session.add(user)
        db.session.commit()
        flash(f'"{user}" has been added.', 'success')
        return redirect(url_for('auth.add_user'))

    return render_template('users_management/add_user.html', form=form)

@auth_bp.route('/delete_user', methods=['GET', 'POST'])
@login_required
def delete_user():
    if not current_user.is_admin:
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('home'))

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
            return redirect(url_for('import_file'))

        file = request.files['file']
        filename = secure_filename(file.filename)
        if not filename.endswith('.xlsx'):
            flash('Invalid file format. Please upload an Excel file.', 'warning')
            return redirect(url_for('import_file'))

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

