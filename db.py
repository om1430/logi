# db.py
import sqlite3
from datetime import datetime

DB_PATH = "tms.db"


def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # 1) Party Master
    cur.execute("""
    CREATE TABLE IF NOT EXISTS party_master (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        party_name TEXT UNIQUE,
        address TEXT,
        mobile TEXT,
        gst_no TEXT,
        marka TEXT,
        default_rate_per_kg REAL,
        default_rate_per_parcel REAL
    )
    """)

    # 2) Item / Goods Type (simple)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS item_master (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT UNIQUE,
        description TEXT
    )
    """)

    # 3) Rate Master (route wise, optional party-wise)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS rate_master (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        party_id INTEGER,
        from_city TEXT,
        to_city TEXT,
        rate_type TEXT,          -- 'KG' or 'PARCEL'
        rate REAL,
        FOREIGN KEY(party_id) REFERENCES party_master(id)
    )
    """)

    # 4) Token / Bilty Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token_no INTEGER,
        date_time TEXT,
        party_id INTEGER,
        consignor TEXT,
        consignee TEXT,
        marka TEXT,
        from_city TEXT,
        to_city TEXT,
        weight REAL,
        pkgs INTEGER,
        rate REAL,
        rate_type TEXT,
        amount REAL,
        truck_no TEXT,
        driver_name TEXT,
        driver_mobile TEXT,
        status TEXT,          -- 'PENDING', 'LOADED', 'DELIVERED', 'BILLED'
        challan_id INTEGER,
        bill_id INTEGER,
        FOREIGN KEY(party_id) REFERENCES party_master(id)
    )
    """)

    # 5) Challan Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS challan (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        challan_no INTEGER,
        date TEXT,
        from_city TEXT,
        to_city TEXT,
        truck_no TEXT,
        driver_name TEXT,
        driver_mobile TEXT,
        hire REAL,
        loading_hamali REAL,
        unloading_hamali REAL,
        other_exp REAL,
        balance REAL
    )
    """)

    # 6) Mapping: Challan <-> Tokens
    cur.execute("""
    CREATE TABLE IF NOT EXISTS challan_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        challan_id INTEGER,
        token_id INTEGER,
        FOREIGN KEY(challan_id) REFERENCES challan(id),
        FOREIGN KEY(token_id) REFERENCES tokens(id)
    )
    """)

    # 7) Bill / Invoice table (party-wise)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bill_no INTEGER,
        party_id INTEGER,
        from_date TEXT,
        to_date TEXT,
        subtotal REAL,
        gst_percent REAL,
        gst_amount REAL,
        total REAL,
        created_at TEXT,
        FOREIGN KEY(party_id) REFERENCES party_master(id)
    )
    """)

    # 8) Payments
    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        party_id INTEGER,
        date TEXT,
        amount REAL,
        mode TEXT,
        remark TEXT,
        FOREIGN KEY(party_id) REFERENCES party_master(id)
    )
    """)

    conn.commit()
    conn.close()


def get_next_token_no():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(MAX(token_no), 0) + 1 FROM tokens")
    nxt = cur.fetchone()[0]
    conn.close()
    return nxt


def get_next_challan_no():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(MAX(challan_no), 0) + 1 FROM challan")
    nxt = cur.fetchone()[0]
    conn.close()
    return nxt


def get_next_bill_no():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(MAX(bill_no), 0) + 1 FROM bills")
    nxt = cur.fetchone()[0]
    conn.close()
    return nxt


def get_party_list():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, party_name, marka FROM party_master ORDER BY party_name")
    rows = cur.fetchall()
    conn.close()
    return rows


def compute_party_balance(party_id: int):
    """
    Balance = (Total token amount) - (Total payments)
    Very simple logic for now.
    """
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COALESCE(SUM(amount),0) FROM tokens WHERE party_id=?",
                (party_id,))
    token_total = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE party_id=?",
                (party_id,))
    paid = cur.fetchone()[0]

    conn.close()
    return token_total - paid
