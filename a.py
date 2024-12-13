import mysql.connector

config = {
  'user': 'root',
  'password': '12345678',
  'host': 'localhost',
  'database': 'BloodDonation',
  'raise_on_warnings': True
}

cnx = mysql.connector.connect(**config)

cursor = cnx.cursor()

__all__ = ['cursor', 'cnx']