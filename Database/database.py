import psycopg2
from psycopg2 import Error

try:
    # Connect to PostgreSQL database
    connection = psycopg2.connect(
          # Your PostgreSQL host (usually localhost)
        port="5432",               # Default PostgreSQL port
        database="river_architect", # Your database name
        user="postgres",           # Your PostgreSQL username
        password="database"   # Your PostgreSQL password
    )
    
    # Create a cursor object
    cursor = connection.cursor()

    # Create condition table if it doesn't exist (do not drop existing table)
    create_table_query = """
    CREATE TABLE IF NOT EXISTS condition (
        condition_name TEXT PRIMARY KEY,
        depth_rasters TEXT,
        velocity_rasters TEXT,
        digital_elevation_model TEXT,
        grain_size_raster TEXT
    );
    """
    cursor.execute(create_table_query)
    connection.commit()
    print("Table 'condition' is ready.")
    
    # Print PostgreSQL connection properties
    print("Connected to PostgreSQL database")
    print(connection.get_dsn_parameters(), "\n")
    
    # Execute a query on the 'condition' table
    cursor.execute("SELECT * FROM condition;")
    records = cursor.fetchall()
    
    # Get column names
    colnames = [desc[0] for desc in cursor.description]
    
    print("\n--- Full 'condition' table ---")
    print(colnames)
    for row in records:
        print(row)
    print("---------------------------------")
    
    
except (Exception, Error) as error:
    print("Error while connecting to PostgreSQL:", error)
    
finally:
    # Close database connection
    if connection:
        cursor.close()
        connection.close()
        print("\nPostgreSQL connection closed")