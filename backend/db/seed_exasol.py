import os
import random
from datetime import datetime, timedelta
import pyexasol
from dotenv import load_dotenv

load_dotenv()

def generate_ecommerce_data():
    conn = pyexasol.connect(
        dsn=os.getenv("EXASOL_HOST"),
        user=os.getenv("EXASOL_USER"),
        password=os.getenv("EXASOL_PASSWORD"),
        autocommit=True
    )

    print("Setting up MAIN schema...")
    conn.execute("CREATE SCHEMA IF NOT EXISTS MAIN;")
    conn.execute("OPEN SCHEMA MAIN;")

    # Reset tables
    for table in ["PAYMENT_LOGS", "FULFILLMENT_LOGS", "ORDERS", "INVENTORY"]:
        conn.execute(f"DROP TABLE IF EXISTS {table};")

    print("Creating tables...")
    conn.execute("""
        CREATE TABLE ORDERS (
            order_id VARCHAR(50),
            user_id VARCHAR(50),
            category VARCHAR(50),
            device_type VARCHAR(20),
            app_version VARCHAR(20),
            amount DECIMAL(10,2),
            status VARCHAR(20),
            created_at TIMESTAMP
        );
    """)

    conn.execute("""
        CREATE TABLE PAYMENT_LOGS (
            log_id INT,
            order_id VARCHAR(50),
            gateway VARCHAR(30),
            status_code INT,
            error_code VARCHAR(50),
            latency_ms INT,
            created_at TIMESTAMP
        );
    """)

    conn.execute("""
        CREATE TABLE FULFILLMENT_LOGS (
            fulfillment_id VARCHAR(50),
            order_id VARCHAR(50),
            warehouse_id VARCHAR(30),
            carrier VARCHAR(30),
            status VARCHAR(30),
            delay_days INT,
            updated_at TIMESTAMP
        );
    """)

    conn.execute("""
        CREATE TABLE INVENTORY (
            product_id VARCHAR(50),
            product_name VARCHAR(100),
            category VARCHAR(50),
            stock_quantity INT,
            last_updated TIMESTAMP
        );
    """)

    print("Generating synthetic data with anomalies...")

    orders = []
    payment_logs = []
    fulfillment_logs = []
    
    categories = ["Electronics", "Clothing", "Home & Kitchen", "Books"]
    devices = ["iOS", "Android", "Desktop"]
    gateways = ["Stripe", "PayPal", "Adyen"]
    carriers = ["FedEx", "UPS", "DHL"]
    
    base_time = datetime(2026, 8, 1, 10, 0, 0)
    order_id_counter = 1000
    log_id_counter = 5000

    # 1. Baseline Data: ~200 normal orders over 20 days
    for day in range(20):
        current_date = base_time + timedelta(days=day)
        for _ in range(10):
            order_id_counter += 1
            log_id_counter += 1
            oid = f"ORD_{order_id_counter}"
            uid = f"USR_{random.randint(100, 999)}"
            cat = random.choice(categories)
            dev = random.choice(devices)
            app_ver = "v3.2.0"
            amt = round(random.uniform(20.0, 300.0), 2)
            
            orders.append((oid, uid, cat, dev, app_ver, amt, "COMPLETED", current_date.strftime("%Y-%m-%d %H:%M:%S")))
            payment_logs.append((log_id_counter, oid, random.choice(gateways), 200, "SUCCESS", random.randint(120, 350), current_date.strftime("%Y-%m-%d %H:%M:%S")))
            fulfillment_logs.append((f"FUL_{order_id_counter}", oid, "WH-MAIN", random.choice(carriers), "DELIVERED", 0, (current_date + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")))

    # 2. Inject Anomaly 1: Stripe Outage on Aug 15th
    anomaly_date_1 = datetime(2026, 8, 15, 14, 0, 0)
    for _ in range(30):
        order_id_counter += 1
        log_id_counter += 1
        oid = f"ORD_{order_id_counter}"
        uid = f"USR_{random.randint(100, 999)}"
        
        orders.append((oid, uid, "Electronics", "Desktop", "v3.2.0", 199.99, "FAILED", anomaly_date_1.strftime("%Y-%m-%d %H:%M:%S")))
        payment_logs.append((log_id_counter, oid, "Stripe", 504, "GATEWAY_TIMEOUT", random.randint(4000, 8000), anomaly_date_1.strftime("%Y-%m-%d %H:%M:%S")))

    # 3. Inject Anomaly 2: iOS App Crash on v3.2.1 for Electronics on Aug 18th
    anomaly_date_2 = datetime(2026, 8, 18, 9, 0, 0)
    for _ in range(25):
        order_id_counter += 1
        log_id_counter += 1
        oid = f"ORD_{order_id_counter}"
        uid = f"USR_{random.randint(100, 999)}"
        
        orders.append((oid, uid, "Electronics", "iOS", "v3.2.1", 450.00, "FAILED", anomaly_date_2.strftime("%Y-%m-%d %H:%M:%S")))
        payment_logs.append((log_id_counter, oid, "PayPal", 500, "APP_CLIENT_CRASH", 50, anomaly_date_2.strftime("%Y-%m-%d %H:%M:%S")))

    # Insert Data using PyExasol's import_from_iterable
    conn.import_from_iterable(orders, "ORDERS")
    conn.import_from_iterable(payment_logs, "PAYMENT_LOGS")
    conn.import_from_iterable(fulfillment_logs, "FULFILLMENT_LOGS")

    # Insert Inventory Catalog (~20 rows)
    inventory = [
        ("PRD_101", "Wireless Headphones", "Electronics", 15, "2026-08-20 10:00:00"),
        ("PRD_102", "Mechanical Keyboard", "Electronics", 0, "2026-08-20 10:00:00"),
        ("PRD_103", "Ergonomic Chair", "Home & Kitchen", 45, "2026-08-20 10:00:00"),
        ("PRD_104", "Running Shoes", "Clothing", 80, "2026-08-20 10:00:00"),
    ]
    conn.import_from_iterable(inventory, "INVENTORY")

    print("Successfully seeded ~530 rows into Exasol!")
    conn.close()

if __name__ == "__main__":
    generate_ecommerce_data()