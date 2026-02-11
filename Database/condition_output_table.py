import psycopg2
from psycopg2 import Error

DB_NAME = "river_architect"
DB_USER = "postgres"
DB_PASSWORD = "database"
DB_HOST = "localhost"
DB_PORT = "5432"


def ensure_condition_output_table():
    """Create condition_output table and link condition_name to condition table."""
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS condition_output (
            condition_name TEXT PRIMARY KEY
                REFERENCES condition(condition_name)
                ON DELETE CASCADE,
            bed_shield_paths TEXT,
            shear_paths TEXT,
            depth_to_wt_paths TEXT,
            morph_unit_paths TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    )
    conn.commit()
    cur.close()
    conn.close()
    print("Table 'condition_output' is ready and linked to condition.condition_name.")


if __name__ == "__main__":
    try:
        ensure_condition_output_table()
    except (Exception, Error) as e:
        print("Error while preparing condition_output table:", e)
