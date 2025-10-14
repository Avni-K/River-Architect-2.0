import psycopg2
from psycopg2 import Error

try:
    # Connect to PostgreSQL database
    connection = psycopg2.connect(
        host="localhost",          # Your PostgreSQL host (usually localhost)
        port="5432",               # Default PostgreSQL port
        database="river_architect", # Your database name
        user="postgres",           # Your PostgreSQL username
        password="database"   # Your PostgreSQL password
    )
    
    # Create a cursor object
    cursor = connection.cursor()
    
    # Print PostgreSQL connection properties
    print("Connected to PostgreSQL database")
    print(connection.get_dsn_parameters(), "\n")
    
    # Execute a query on the 'condition' table
    cursor.execute("SELECT * FROM condition LIMIT 5;")
    records = cursor.fetchall()
    
    print("Sample records from 'condition' table:")
    for row in records:
        print(row)
    
except (Exception, Error) as error:
    print("Error while connecting to PostgreSQL:", error)
    
finally:
    # Close database connection
    if connection:
        cursor.close()
        connection.close()
        print("\nPostgreSQL connection closed")