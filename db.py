import pyodbc

# Replace these with your own database connection details
server = r'HASSAN\SQLEXPRESS'
database = 'BloodDonation'  # Name of your Northwind database
use_windows_authentication = True  # Set to True to use Windows Authentication
username = 'your_username'  # Specify a username if not using Windows Authentication
password = 'your_password'  # Specify a password if not using Windows Authentication


# Create the connection string based on the authentication method chosen
if use_windows_authentication:
    connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
else:
    connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

# # Establish a connection to the database
connection = pyodbc.connect(connection_string)

# # Create a cursor to interact with the database
cursor = connection.cursor()

__all__ = ['cursor', 'connection']



# select_query = "SELECT * FROM [User]"
# cursor.execute(select_query)
# print("All Employees:")
# for row in cursor.fetchall():
#     print(row)