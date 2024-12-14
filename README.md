# Blood Donation Management System

A Streamlit-based web application for managing blood donations, hospitals, and inventory.

## Prerequisites

- Microsoft SQL Server
- Python 3.7+
- SQL Server Management Studio (SSMS)

## Setup Instructions

### 1. Database Setup

1. Open SQL Server Management Studio (SSMS)
2. Connect to your SQL Server instance
3. Copy the contents of `query.sql`
4. Paste into a new query window in SSMS
5. Execute the query to create the database and tables

### 2. Database Connection Configuration

1. Open `db.py`
2. Modify the following variables according to your SQL Server setup:
   ```python
   server = r'YOUR_SERVER_NAME\SQLEXPRESS'  # Change this to your SQL Server instance name
   ```

### 3. Install Required Packages

1. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

OR

```bash
pip install streamlit pyodbc
```

### 4. Run the Application

1. Start the Streamlit application:
   ```bash
   streamlit run app.py
   // or
   python -m streamlit run app.py
   ```
2. The application should open in your default web browser

## Default Login Credentials

- Username: admin
- Password: admin

## Notes

- Make sure you have the ODBC Driver 17 for SQL Server installed
- Ensure SQL Server is running before starting the application
- If you encounter any connection issues, verify your SQL Server instance name and authentication settings

## Requirements

See `requirements.txt` for a full list of Python dependencies:
- streamlit
- pyodbc

## Support

For any issues or questions, open an issue in the repository.