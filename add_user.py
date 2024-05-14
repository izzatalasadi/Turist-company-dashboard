from search_engine import db, create_app, User
from werkzeug.security import generate_password_hash

def create_admin_user(username, password,email, is_admin):
    # Ensure an admin does not already exist
    if User.query.filter_by(username=username).first():
        print('Admin user already exists.')
        return

    # Create a new admin user instance
    admin_user = User(
        username=username,
        password_hash=generate_password_hash(password),
        email=email,
        is_admin=is_admin
    )
    
    # Add the admin user to the database session and commit
    db.session.add(admin_user)
    db.session.commit()

    print(f'user {username} created successfully.')

# Ensure you're running this within an application context
if __name__ == "__main__":
    # 0 for user, 1 for admin
    app = create_app()
    with app.app_context():
        create_admin_user('admin', 'DMCAdmin112!!@','izzat.alasadi@gmail.com',1)