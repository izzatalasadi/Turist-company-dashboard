# Turist Dashboard

Dashboard is a web application designed to manage and monitor various activities, guests, and messages. The application provides functionalities such as user management, guest import/export, activity logging, and real-time messaging.
<img width="1429" alt="image" src="https://github.com/user-attachments/assets/6e272a70-6fac-4060-a9a3-387b19f21652">

## Table of Contents
- [Features](#features)
- [Getting Started](#getting-started)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Deployment](#deployment)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Features
- User authentication and management
- Real-time messaging with Socket.IO
- Guest import from Excel files and export to Excel
- Activity logging and display
- CSRF protection, user view limitation, permissions and rate limiting
- Check-in system, auto update guest flight time, and easy edit guest details in real time.
- Sort and search with all guest details such: name, flight, arriving time ..etc 
- PDF viewing and management
- Responsive design with Bootstrap

## Getting Started

### Prerequisites
- Python 3.9+
- Flask
- PostgreSQL (for production)
- Redis (for rate limiting)

### Installation
1. Clone the repository:
    ```bash
    git clone https://github.com/izzatalasadi/DMC_dashboard.git
    cd DMC_dashboard
    ```

2. Create a virtual environment and activate it:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

### Configuration
1. Copy the `.env.example` file to `.env` and update it with your configuration settings:
    ```bash
    cp .env.example .env
    ```

2. Update `config.py` with appropriate configurations for development, testing, and production environments.

### Running the Application
1. Initialize the database:
    ```bash
    flask db upgrade
    ```

2. Run the development server:
    ```bash
    flask run
    ```

3. Access the application at `http://127.0.0.1:5000`.

### Testing
1. Run the tests using `pytest`:
    ```bash
    pytest
    ```

### Deployment
To deploy the application on Heroku, follow these steps:

1. Create a new Heroku app:
    ```bash
    heroku create your-app-name
    ```

2. Set up PostgreSQL and Redis on Heroku:
    ```bash
    heroku addons:create heroku-postgresql:hobby-dev
    heroku addons:create heroku-redis:hobby-dev
    ```

3. Push your code to Heroku:
    ```bash
    git push heroku main
    ```

4. Run database migrations on Heroku:
    ```bash
    heroku run flask db upgrade
    ```

## Usage
- **Login**: Users can log in to access the dashboard.
<img width="605" alt="image" src="https://github.com/user-attachments/assets/bf36cba5-6e28-45bf-9371-f1276c41a8c7">

- **Manage Users**: Admins can add, delete, and update user profiles.
**User profile**
<img width="244" alt="image" src="https://github.com/user-attachments/assets/665e5cae-af55-4b80-b43b-3feb1bc57488">
<img width="1424" alt="image" src="https://github.com/user-attachments/assets/fcf3f923-56e7-4342-a7fb-8a84c4426d18">
**Add users**
<img width="1433" alt="image" src="https://github.com/user-attachments/assets/1a8f53d2-7803-4924-93e7-115b45b243d8">
**delete users**
<img width="1438" alt="image" src="https://github.com/user-attachments/assets/205aedc9-9ce7-4a5d-8a12-702ffebfcf63">


- **Guest Management**: Import guest details from Excel, update statuses, and export to Excel.
<img width="266" alt="image" src="https://github.com/user-attachments/assets/743917fd-1516-4c82-8152-b864a25b9c92">
    Import guests to database
    <img width="1423" alt="image" src="https://github.com/user-attachments/assets/6189203e-cb23-478b-9f30-571b2d0c71cc">

    Export guests status to Excel file
    <img width="1425" alt="image" src="https://github.com/user-attachments/assets/9c514df6-0bd0-434f-874a-7f635ea5377c">

    Delete guests data from Database
    <img width="1438" alt="image" src="https://github.com/user-attachments/assets/fe6265b3-4ea9-4e66-b9bf-a5c6c84e14fd">

- **Messages**: Send and receive real-time messages.
<img width="1416" alt="image" src="https://github.com/user-attachments/assets/80fca924-17c9-4afe-8ba3-8897388c89bb">

- **Activities**: View logs of various activities performed by users.
<img width="395" alt="image" src="https://github.com/user-attachments/assets/fa930ac6-cb9b-4be4-83aa-843a12e93cbe">

- **PDF Management**: Upload, view, and delete PDF documents.
<img width="1431" alt="image" src="https://github.com/user-attachments/assets/8a0fe803-2306-4ebc-9f0b-a7e4ff4409d6">

_ **Check-in system**
<img width="1435" alt="Screenshot 2024-08-29 at 12 39 22" src="https://github.com/user-attachments/assets/d75db2f5-fc69-4971-b357-377fcb626070">
<img width="1430" alt="Screenshot 2024-08-29 at 12 44 50" src="https://github.com/user-attachments/assets/a1ba6182-0539-4fe4-8f26-4f6ac23d1b3c">
<img width="1136" alt="Screenshot 2024-08-29 at 12 46 39" src="https://github.com/user-attachments/assets/c4efdaa7-ca2a-4e5c-829a-73b84b110a4d">

## Contributing
Contributions are welcome! Please follow these steps to contribute:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Create a new Pull Request.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
