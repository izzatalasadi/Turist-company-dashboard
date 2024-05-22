# DMC Dashboard

DMC Dashboard is a web application designed to manage and monitor various activities, guests, and messages. The application provides functionalities such as user management, guest import/export, activity logging, and real-time messaging.

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
- CSRF protection and rate limiting
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
    git clone https://github.com/yourusername/DMC_dashboard.git
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
- **Manage Users**: Admins can add, delete, and update user profiles.
- **Guest Management**: Import guest details from Excel, update statuses, and export to Excel.
- **Messages**: Send and receive real-time messages.
- **Activities**: View logs of various activities performed by users.
- **PDF Management**: Upload, view, and delete PDF documents.

## Contributing
Contributions are welcome! Please follow these steps to contribute:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Create a new Pull Request.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
