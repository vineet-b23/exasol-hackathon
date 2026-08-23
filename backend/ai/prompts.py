"""
ai/prompts.py
System prompts and database schemas for the TRACE agent.
"""

SYSTEM_PROMPT = """You are TRACE, a Senior Data Analyst AI agent. 
Your primary objective is to investigate data anomalies, answer complex business questions, and provide actionable insights.

When planning an investigation:
1. Break down the user's query into competing hypotheses.
2. Formulate a rationale for why each hypothesis might explain the issue or answer the question.
3. Write highly optimized, valid SQLite SELECT statements to test each hypothesis.
4. ONLY write `SELECT` statements. Never write `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, or any other data-modifying commands.
5. Use SQLite-compatible date/time functions (e.g., strftime(), DATE(), DATETIME()) when querying timestamps.

When summarizing results:
1. Objectively evaluate the execution results of your queries.
2. Identify the leading hypothesis backed by the strongest evidence.
3. Assign a confidence score (0-100) based on data conclusiveness.
4. Always search for and highlight counter-evidence or confounding variables.
"""

SCHEMA_CONTEXT = """
### DATABASE SCHEMA CONTEXT ###

Table: customers
- customer_id (INTEGER, PRIMARY KEY)
- first_name (VARCHAR)
- last_name (VARCHAR)
- email (VARCHAR)
- signup_date (DATE / TEXT ISO-8601)
- status (VARCHAR) -- e.g., 'active', 'churned', 'suspended'
- country (VARCHAR)

Table: products
- product_id (INTEGER, PRIMARY KEY)
- sku (VARCHAR, UNIQUE)
- name (VARCHAR)
- category (VARCHAR)
- unit_price (REAL)
- launch_date (DATE / TEXT ISO-8601)

Table: orders
- order_id (INTEGER, PRIMARY KEY)
- customer_id (INTEGER, FOREIGN KEY -> customers.customer_id)
- order_date (DATETIME / TEXT ISO-8601)
- total_amount (REAL)
- status (VARCHAR) -- e.g., 'pending', 'completed', 'cancelled', 'refunded'

Table: inventory
- inventory_id (INTEGER, PRIMARY KEY)
- product_id (INTEGER, FOREIGN KEY -> products.product_id)
- warehouse_location (VARCHAR)
- quantity_on_hand (INTEGER)
- last_restocked_date (DATETIME / TEXT ISO-8601)

Table: shipments
- shipment_id (INTEGER, PRIMARY KEY)
- order_id (INTEGER, FOREIGN KEY -> orders.order_id)
- carrier (VARCHAR)
- tracking_number (VARCHAR)
- shipped_date (DATETIME / TEXT ISO-8601)
- estimated_delivery (DATETIME / TEXT ISO-8601)
- actual_delivery (DATETIME / TEXT ISO-8601)
- status (VARCHAR) -- e.g., 'processing', 'in_transit', 'delivered', 'delayed'

Table: customer_support
- ticket_id (INTEGER, PRIMARY KEY)
- customer_id (INTEGER, FOREIGN KEY -> customers.customer_id)
- order_id (INTEGER, FOREIGN KEY -> orders.order_id, NULLABLE)
- issue_type (VARCHAR) -- e.g., 'billing', 'shipping', 'quality', 'general'
- status (VARCHAR) -- e.g., 'open', 'resolved', 'escalated'
- created_at (DATETIME / TEXT ISO-8601)
- resolved_at (DATETIME / TEXT ISO-8601, NULLABLE)
"""