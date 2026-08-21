"""
Data Engineer Script: Synthetic Database Generator for TRACE AI Agent
Dependencies: pip install pandas numpy faker
"""

import sqlite3
import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta
import sys

# Configuration
DB_NAME = 'ecommerce_trace.db'
NUM_CUSTOMERS = 15000
NUM_PRODUCTS = 800
NUM_ORDERS = 80000
START_DATE = pd.to_datetime('2023-01-01')
END_DATE = pd.to_datetime('2023-12-31')

# Set seeds for reproducibility
Faker.seed(42)
np.random.seed(42)
random.seed(42)
fake = Faker()

def main():
    print(f"🚀 Starting generation of {DB_NAME}...")

    # ==========================================
    # 1. GENERATE CUSTOMERS
    # ==========================================
    print("⏳ Generating customers table...")
    customers = pd.DataFrame({
        'customer_id': range(1, NUM_CUSTOMERS + 1),
        'name': [fake.name() for _ in range(NUM_CUSTOMERS)],
        'signup_date': [fake.date_between(start_date='-3y', end_date='today') for _ in range(NUM_CUSTOMERS)],
        'region': np.random.choice(['North', 'South', 'East', 'West'], size=NUM_CUSTOMERS),
        'device_type': np.random.choice(['iOS', 'Android', 'Web'], size=NUM_CUSTOMERS, p=[0.4, 0.4, 0.2])
    })

    # ==========================================
    # 2. GENERATE PRODUCTS
    # ==========================================
    print("⏳ Generating products table...")
    categories = ['Electronics', 'Apparel', 'Home', 'Beauty']
    products = pd.DataFrame({
        'product_id': range(1, NUM_PRODUCTS + 1),
        'name': [f"{fake.word().capitalize()} {fake.word().capitalize()}" for _ in range(NUM_PRODUCTS)],
        'category': np.random.choice(categories, size=NUM_PRODUCTS),
        'unit_cost': np.random.uniform(10.0, 300.0, size=NUM_PRODUCTS).round(2)
    })
    # Set price at a standard 40-60% markup initially
    products['unit_price'] = (products['unit_cost'] * np.random.uniform(1.4, 1.6, size=NUM_PRODUCTS)).round(2)

    # ==========================================
    # 3. GENERATE ORDERS (With Anomalies A & B)
    # ==========================================
    print("⏳ Generating orders table...")
    # Pareto distribution for product selection (20% of products get 80% of sales)
    pareto_weights = np.random.pareto(a=1.5, size=NUM_PRODUCTS)
    pareto_weights /= pareto_weights.sum()

    order_dates = [START_DATE + timedelta(days=random.randint(0, 364), hours=random.randint(0, 23)) for _ in range(NUM_ORDERS)]
    
    orders = pd.DataFrame({
        'order_id': range(1, NUM_ORDERS + 1),
        'customer_id': np.random.choice(customers['customer_id'], size=NUM_ORDERS),
        'product_id': np.random.choice(products['product_id'], size=NUM_ORDERS, p=pareto_weights),
        'order_date': sorted(order_dates), # Sort chronologically
        'payment_gateway': np.random.choice(['Stripe', 'PayPal', 'Adyen'], size=NUM_ORDERS, p=[0.5, 0.3, 0.2]),
        'status': np.random.choice(['completed', 'failed', 'cancelled'], size=NUM_ORDERS, p=[0.90, 0.04, 0.06])
    })

    # Merge customer and product data to compute anomalies and financials
    orders = orders.merge(customers[['customer_id', 'device_type', 'region']], on='customer_id')
    orders = orders.merge(products[['product_id', 'category', 'unit_cost', 'unit_price']], on='product_id')

    orders['amount'] = orders['unit_price']
    
    # We include 'cogs' (Cost of Goods Sold) in the orders table to properly track 
    # historical margins, allowing the Q3 margin squeeze to exist chronologically 
    # without overwriting the static 'products' table.
    orders['cogs'] = orders['unit_cost']

    # -------------------------------------------------------------------------
    # 🚨 ANOMALY A: The July Revenue Drop Story
    # For dates between July 1-31, spike order failure rate to 65% ONLY for 
    # payment_gateway = 'Stripe' AND device_type = 'iOS'.
    # -------------------------------------------------------------------------
    july_mask = (orders['order_date'].dt.month == 7)
    stripe_mask = (orders['payment_gateway'] == 'Stripe')
    ios_mask = (orders['device_type'] == 'iOS')
    anomaly_a_mask = july_mask & stripe_mask & ios_mask

    # Apply the 65% failure rate
    random_probs_a = np.random.rand(len(orders))
    orders.loc[anomaly_a_mask & (random_probs_a < 0.65), 'status'] = 'failed'
    orders.loc[anomaly_a_mask & (random_probs_a >= 0.65), 'status'] = 'completed'

    # -------------------------------------------------------------------------
    # 🚨 ANOMALY B: The Q3 Margin Squeeze Story
    # Starting Sept 1st, increase unit_cost (COGS) for 'Electronics' by 40%, 
    # simulating a supplier cost surge while unit_price (amount) stays flat.
    # -------------------------------------------------------------------------
    q3_mask = (orders['order_date'] >= '2023-09-01')
    electronics_mask = (orders['category'] == 'Electronics')
    anomaly_b_mask = q3_mask & electronics_mask

    # Surge the cost incurred for these specific orders by 40%
    orders.loc[anomaly_b_mask, 'cogs'] = (orders.loc[anomaly_b_mask, 'cogs'] * 1.40).round(2)

    # Clean up orders dataframe to match requested schema (plus cogs)
    orders = orders[['order_id', 'customer_id', 'product_id', 'order_date', 'status', 'payment_gateway', 'amount', 'cogs']]

    # ==========================================
    # 4. GENERATE INVENTORY
    # ==========================================
    print("⏳ Generating inventory table...")
    inventory = pd.DataFrame({
        'inventory_id': range(1, NUM_PRODUCTS + 1),
        'warehouse_id': [random.randint(1, 5) for _ in range(NUM_PRODUCTS)],
        'product_id': products['product_id'],
        'stock_level': np.random.randint(50, 1000, size=NUM_PRODUCTS),
        'reorder_point': np.random.randint(20, 100, size=NUM_PRODUCTS),
        'last_restock_date': [fake.date_between(start_date='-60d', end_date='today') for _ in range(NUM_PRODUCTS)]
    })

    # ==========================================
    # 5. GENERATE SHIPMENTS (With Anomaly C)
    # ==========================================
    print("⏳ Generating shipments table...")
    completed_orders = orders[orders['status'] == 'completed'].copy()
    
    shipments = pd.DataFrame({
        'shipment_id': range(1, len(completed_orders) + 1),
        'order_id': completed_orders['order_id'].values,
        'carrier': np.random.choice(['FedEx', 'UPS', 'DHL'], size=len(completed_orders), p=[0.4, 0.4, 0.2]),
        'tracking_status': np.random.choice(['Delivered', 'In Transit', 'Returned'], size=len(completed_orders), p=[0.90, 0.08, 0.02])
    })

    # Merge necessary columns for time/regional logic
    shipments = shipments.merge(completed_orders[['order_id', 'order_date']], on='order_id')
    shipments = shipments.merge(customers[['customer_id', 'region']], left_on=completed_orders['customer_id'].values, right_on='customer_id')

    # Base delivery times (1-3 days standard)
    shipments['estimated_delivery'] = shipments['order_date'] + pd.to_timedelta(np.random.randint(1, 4, size=len(shipments)), unit='d')
    shipments['actual_delivery'] = shipments['estimated_delivery'] + pd.to_timedelta(np.random.randint(-1, 2, size=len(shipments)), unit='d')

    # -------------------------------------------------------------------------
    # 🚨 ANOMALY C: The Regional Logistics Bottleneck Story
    # For orders to the 'West' region in November, set tracking_status = 'Delayed' 
    # for 50% of shipments with carrier = 'FedEx'.
    # -------------------------------------------------------------------------
    nov_mask = (shipments['order_date'].dt.month == 11)
    west_mask = (shipments['region'] == 'West')
    fedex_mask = (shipments['carrier'] == 'FedEx')
    anomaly_c_mask = nov_mask & west_mask & fedex_mask

    random_probs_c = np.random.rand(len(shipments))
    delayed_condition = anomaly_c_mask & (random_probs_c < 0.50)
    
    shipments.loc[delayed_condition, 'tracking_status'] = 'Delayed'
    # Shift actual delivery forward 5-10 days for these delayed shipments
    shipments.loc[delayed_condition, 'actual_delivery'] = shipments.loc[delayed_condition, 'estimated_delivery'] + pd.to_timedelta(np.random.randint(5, 11, size=delayed_condition.sum()), unit='d')

    # Clean up shipments schema
    shipments = shipments[['shipment_id', 'order_id', 'carrier', 'tracking_status', 'estimated_delivery', 'actual_delivery']]

    # ==========================================
    # 6. GENERATE CUSTOMER SUPPORT (With Anomaly C Tickets)
    # ==========================================
    print("⏳ Generating customer support table...")
    # Base tickets: ~3% of all orders generate a random ticket
    base_tickets_mask = np.random.rand(len(orders)) < 0.03
    base_ticket_orders = orders[base_tickets_mask].copy()
    
    # Extract delayed shipments from Anomaly C to generate corresponding tickets
    delayed_shipment_ids = shipments[shipments['tracking_status'] == 'Delayed']['order_id']
    nov_delayed_orders = orders[(orders['order_id'].isin(delayed_shipment_ids)) & (orders['order_date'].dt.month == 11)].copy()
    
    # 85% of those delayed Nov shipments result in a complaint
    anomaly_c_ticket_orders = nov_delayed_orders.sample(frac=0.85, random_state=42)
    
    # Combine baseline tickets and anomaly tickets
    support_orders = pd.concat([base_ticket_orders, anomaly_c_ticket_orders]).drop_duplicates(subset=['order_id'])
    
    issue_types = []
    for _, row in support_orders.iterrows():
        if row['order_id'] in anomaly_c_ticket_orders['order_id'].values:
            issue_types.append('Delivery Delay')
        elif row['status'] == 'failed':
            issue_types.append('Payment Fail')
        else:
            issue_types.append(np.random.choice(['Refund Request', 'Product Defect', 'Delivery Delay']))

    customer_support = pd.DataFrame({
        'ticket_id': range(1, len(support_orders) + 1),
        'customer_id': support_orders['customer_id'].values,
        'order_id': support_orders['order_id'].values,
        'ticket_date': support_orders['order_date'] + pd.to_timedelta(np.random.randint(1, 5, size=len(support_orders)), unit='d'),
        'issue_type': issue_types,
        'resolution_status': np.random.choice(['Open', 'Resolved', 'Escalated'], size=len(support_orders), p=[0.15, 0.75, 0.10])
    })

    # ==========================================
    # EXPORT TO SQLITE
    # ==========================================
    print(f"💾 Saving to SQLite database '{DB_NAME}'...")
    conn = sqlite3.connect(DB_NAME)
    
    # Write tables
    customers.to_sql('customers', conn, index=False, if_exists='replace')
    products.to_sql('products', conn, index=False, if_exists='replace')
    orders.to_sql('orders', conn, index=False, if_exists='replace')
    inventory.to_sql('inventory', conn, index=False, if_exists='replace')
    shipments.to_sql('shipments', conn, index=False, if_exists='replace')
    customer_support.to_sql('customer_support', conn, index=False, if_exists='replace')

    # Verify Counts
    print("\n✅ Generation Complete! Table Row Counts:")
    for table in ['customers', 'products', 'orders', 'inventory', 'shipments', 'customer_support']:
        count = pd.read_sql_query(f"SELECT COUNT(*) FROM {table}", conn).iloc[0,0]
        print(f"   - {table}: {count:,} rows")

    conn.close()
    print("\n🎯 Database is ready for TRACE Agent!")

if __name__ == "__main__":
    main()