from __future__ import annotations
import os
import sqlite3
from pathlib import Path
from typing import Optional

try:
    import pyodbc  # type: ignore
except Exception:
    pyodbc = None  # optional

APP_DIR = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "HesabdariApp"
APP_DIR.mkdir(parents=True, exist_ok=True)

USER_DB = APP_DIR / "data.db"
USER_SETTINGS = APP_DIR / "settings.ini"

def ensure_sqlite_schema(db_path: Path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS company (
        id INTEGER PRIMARY KEY CHECK (id=1),
        company_name_fa TEXT,
        company_name_en TEXT,
        company_phone TEXT,
        company_address_fa TEXT,
        company_address_en TEXT,
        vat_percent REAL DEFAULT 9.0,
        currency_symbol TEXT DEFAULT 'ریال'
    )""")
    cur.execute("""INSERT OR IGNORE INTO company (id, company_name_fa, company_name_en, company_phone, company_address_fa, company_address_en)
                   VALUES (1, '', '', '', '', '')""")
    cur.execute("""CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        address TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL DEFAULT 0
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        subtotal REAL NOT NULL,
        discount_sum REAL NOT NULL,
        taxable REAL NOT NULL,
        vat REAL NOT NULL,
        grand_total REAL NOT NULL,
        FOREIGN KEY(customer_id) REFERENCES customers(id)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity REAL NOT NULL,
        unit_price REAL NOT NULL,
        discount_percent REAL NOT NULL,
        tax_percent REAL NOT NULL,
        line_total REAL NOT NULL,
        FOREIGN KEY(invoice_id) REFERENCES invoices(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    )""")
    conn.commit()
    conn.close()

def get_sqlite_conn(db_path: Optional[Path] = None):
    path = db_path or USER_DB
    ensure_sqlite_schema(path)
    return sqlite3.connect(path)

def get_access_conn(connection_string: Optional[str] = None, file_path: Optional[str] = None):
    if pyodbc is None:
        raise RuntimeError("pyodbc is not available. Please use SQLite or install the Access Database Engine.")
    conn_str = None
    if connection_string:
        conn_str = connection_string
    elif file_path:
        conn_str = f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={file_path};'
    if not conn_str:
        raise RuntimeError("Access connection string or file path is required.")
    return pyodbc.connect(conn_str)
