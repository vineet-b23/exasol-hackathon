import os
import pyexasol
from dotenv import load_dotenv

load_dotenv()

def seed():
    conn = pyexasol.connect(
        dsn=os.getenv("EXASOL_HOST"),
        user=os.getenv("EXASOL_USER"),
        password=os.getenv("EXASOL_PASSWORD"),
        autocommit=True
    )
    
    conn.execute("CREATE SCHEMA IF NOT EXISTS MAIN;")
    conn.execute("OPEN SCHEMA MAIN;")

    # Define table structure
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trace_logs (
            log_id INT,
            service_name VARCHAR(100),
            status_code INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Seed initial test rows
    conn.execute("INSERT INTO trace_logs VALUES (1, 'auth-service', 200, CURRENT_TIMESTAMP);")
    conn.execute("INSERT INTO trace_logs VALUES (2, 'payment-service', 500, CURRENT_TIMESTAMP);")
    
    print("Seeding complete!")
    conn.close()

if __name__ == "__main__":
    seed()