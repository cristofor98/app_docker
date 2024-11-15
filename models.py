import psycopg2
from psycopg2.extras import RealDictCursor
# creates table in postgresql products

def get_db_connection():
    return psycopg2.connect(
        dbname="makeup_db",
        user="postgres",
        password="alexandrina",
        host="localhost",
        port="5432",
        cursor_factory=RealDictCursor
    )


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # Create products table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            title VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            price FLOAT NOT NULL,
            link VARCHAR NOT NULL,
            year VARCHAR,
            gama_de_produse VARCHAR,
            volume VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cur.close()
    conn.close()