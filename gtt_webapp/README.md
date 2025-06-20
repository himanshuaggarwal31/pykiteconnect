# GTT Orders Web Application

A Flask web application for managing GTT (Good Till Triggered) orders through Kite API and Custom Data through Oracle database.

## Features

- View and manage GTT orders from Kite API
- View and manage Custom Data in Oracle database
- Modern responsive UI using Bootstrap 5
- Real-time updates and inline editing

## Prerequisites

1. Python 3.8 or higher
2. Oracle Instant Client
3. KiteConnect API credentials
4. Access to Oracle database

## Setup

1. Clone the repository:
```bash
cd app
cd gtt_webapp
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Make sure you have run AutoConnect.py to generate the access token:
```bash
python ../AutoConnect.py
```

5. Run the application:
```bash
python run.py
```

The application will be available at `http://localhost:5000`

## Directory Structure

```
gtt_webapp/
├── app.py              # Main application file
├── run.py             # Application runner
├── requirements.txt   # Python dependencies
├── blueprints/       # Route handlers
│   ├── main.py       # GTT orders routes
│   └── custom_data.py # Custom data routes
├── static/           # Static assets
│   ├── css/         # Stylesheets
│   └── js/          # JavaScript files
└── templates/        # HTML templates
    ├── base.html    # Base template
    ├── dashboard.html # GTT orders page
    └── custom_data/ # Custom data templates
```

## Configuration

The application uses several configuration sources:

1. Environment variables (loaded from .env file):
   - SECRET_KEY: Application secret key
   - API_KEY: Kite API key

2. Database configuration from db_config.py:
   - Oracle database connection parameters

3. KiteConnect configuration:
   - API credentials loaded from access_token.txt

## Error Handling

The application includes comprehensive error handling:

- Database connection errors
- KiteConnect API errors
- Missing configuration errors

All errors are logged and displayed to users through flash messages.
