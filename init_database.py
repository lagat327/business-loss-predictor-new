import sqlite3

connection = sqlite3.connect("database.db")

cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS businesses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS financial_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER NOT NULL,
    month INTEGER NOT NULL,
    revenue REAL NOT NULL,
    expenses REAL NOT NULL,
    cost_of_goods REAL NOT NULL,
    cash_flow REAL NOT NULL,
    inventory REAL NOT NULL,
    debt REAL NOT NULL,
    transactions INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (business_id) REFERENCES businesses(id)
)
""")

connection.commit()
connection.close()

print("Database tables ready.")
