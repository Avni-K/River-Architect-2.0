import psycopg2
from psycopg2 import Error


DB_NAME = "river_architect"
DB_USER = "postgres"
DB_PASSWORD = "database"
DB_HOST = "localhost"
DB_PORT = "5432"


def ensure_database_exists():
    """Create river_architect database if it is missing."""
    admin_conn = psycopg2.connect(
        dbname="postgres",
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )
    admin_conn.autocommit = True
    admin_cur = admin_conn.cursor()
    admin_cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (DB_NAME,))
    exists = admin_cur.fetchone() is not None
    if not exists:
        admin_cur.execute(f'CREATE DATABASE "{DB_NAME}";')
        print(f"Database '{DB_NAME}' created.")
    admin_cur.close()
    admin_conn.close()


def ensure_tables():
    """Create/patch the condition table in river_architect."""
    connection = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )
    cursor = connection.cursor()
    create_table_query = """
    CREATE TABLE IF NOT EXISTS condition (
        condition_name TEXT PRIMARY KEY,
        depth_rasters TEXT,
        velocity_rasters TEXT,
        digital_elevation_model TEXT,
        grain_size_raster TEXT,
        unit TEXT,
        velocity_angle_folder TEXT,
        wse_folder TEXT,
        background_raster TEXT,
        scour_raster TEXT,
        fill_raster TEXT,
        condition_output_path TEXT,
        shear_rasters_folder TEXT,
        shield_stress_rasters_folder TEXT,
        depth_to_water_table_rasters_folder TEXT,
        morphological_unit_rasters_folder TEXT
    );
    """
    cursor.execute(create_table_query)
    cursor.execute("ALTER TABLE condition ADD COLUMN IF NOT EXISTS wse_folder TEXT;")
    cursor.execute("ALTER TABLE condition ADD COLUMN IF NOT EXISTS scour_raster TEXT;")
    cursor.execute("ALTER TABLE condition ADD COLUMN IF NOT EXISTS fill_raster TEXT;")
    cursor.execute("ALTER TABLE condition ADD COLUMN IF NOT EXISTS velocity_angle_folder TEXT;")
    cursor.execute("ALTER TABLE condition ADD COLUMN IF NOT EXISTS background_raster TEXT;")
    cursor.execute("ALTER TABLE condition ADD COLUMN IF NOT EXISTS condition_output_path TEXT;")
    cursor.execute("ALTER TABLE condition ADD COLUMN IF NOT EXISTS shear_rasters_folder TEXT;")
    cursor.execute("ALTER TABLE condition ADD COLUMN IF NOT EXISTS shield_stress_rasters_folder TEXT;")
    cursor.execute("ALTER TABLE condition ADD COLUMN IF NOT EXISTS depth_to_water_table_rasters_folder TEXT;")
    cursor.execute("ALTER TABLE condition ADD COLUMN IF NOT EXISTS morphological_unit_rasters_folder TEXT;")
    connection.commit()
    cursor.close()
    connection.close()
    print("Table 'condition' is ready.")


def main():
    try:
        ensure_database_exists()
        ensure_tables()
    except (Exception, Error) as error:
        print("Error while preparing database:", error)


if __name__ == "__main__":
    main()
