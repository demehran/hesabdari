import sqlite3

class Database:
    def __init__(self, db_name="hesabdari.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, phone TEXT, address TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, price REAL DEFAULT 0
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer TEXT, date TEXT, subtotal REAL, tax REAL, total REAL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY, value TEXT
            )
        """)
        self.conn.commit()

    # --- CRUD helpers ---
    def add_customer(self, name, phone, address):
        self.cursor.execute("INSERT INTO customers (name, phone, address) VALUES (?,?,?)", (name, phone, address))
        self.conn.commit()

    def add_product(self, name, price):
        self.cursor.execute("INSERT INTO products (name, price) VALUES (?,?)", (name, price))
        self.conn.commit()

    def list_customers(self, q=None):
        if q:
            self.cursor.execute("SELECT id,name,phone,address FROM customers WHERE name LIKE ? OR phone LIKE ? OR address LIKE ? ORDER BY id DESC",
                                (f"%{q}%", f"%{q}%", f"%{q}%"))
        else:
            self.cursor.execute("SELECT id,name,phone,address FROM customers ORDER BY id DESC")
        return self.cursor.fetchall()

    def list_products(self, q=None):
        if q:
            self.cursor.execute("SELECT id,name,price FROM products WHERE name LIKE ? ORDER BY id DESC", (f"%{q}%",))
        else:
            self.cursor.execute("SELECT id,name,price FROM products ORDER BY id DESC")
        return self.cursor.fetchall()

    def save_invoice_basic(self, customer, date, subtotal, tax, total):
        self.cursor.execute("INSERT INTO invoices (customer,date,subtotal,tax,total) VALUES (?,?,?,?,?)",
                            (customer, date, subtotal, tax, total))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_setting(self, key, default=None):
        self.cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = self.cursor.fetchone()
        return row[0] if row else default

    def set_setting(self, key, value):
        self.cursor.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
        self.conn.commit()

    def wipe_all(self):
        self.cursor.execute("DELETE FROM customers")
        self.cursor.execute("DELETE FROM products")
        self.cursor.execute("DELETE FROM invoices")
        self.conn.commit()

    def close(self):
        self.conn.close()
