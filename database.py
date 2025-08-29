
import sqlite3

DATABASE_NAME = "./data/hns_price.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            timestamp INTEGER NOT NULL,
            currency TEXT NOT NULL,
            price REAL NOT NULL,
            market_cap REAL,
            total_volume REAL,
            PRIMARY KEY (timestamp, currency)
        )
    """)
    conn.commit()
    conn.close()

def insert_price(conn, timestamp, currency, price, market_cap, total_volume):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO prices (timestamp, currency, price, market_cap, total_volume)
        VALUES (?, ?, ?, ?, ?)
    """, (timestamp, currency, price, market_cap, total_volume))
    conn.commit()

def get_prices(from_timestamp: int = None, to_timestamp: int = None, currency: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM prices"
    filters = []
    params = []

    if from_timestamp:
        filters.append("timestamp >= ?")
        params.append(from_timestamp)
    if to_timestamp:
        filters.append("timestamp <= ?")
        params.append(to_timestamp)
    if currency:
        filters.append("currency = ?")
        params.append(currency)

    if filters:
        query += " WHERE " + " AND ".join(filters)

    query += " ORDER BY timestamp DESC"

    cursor.execute(query, params)
    prices = cursor.fetchall()
    conn.close()
    return [dict(row) for row in prices]


def get_daily_summary_prices(from_timestamp: int, to_timestamp: int, currency: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT * FROM (
            SELECT
                *,
                ROW_NUMBER() OVER(PARTITION BY strftime('%Y-%m-%d', timestamp, 'unixepoch') ORDER BY timestamp DESC) as rn
            FROM prices
            WHERE currency = ? AND timestamp >= ? AND timestamp <= ?
        )
        WHERE rn = 1
        ORDER BY timestamp DESC;
    """
    cursor.execute(query, (currency, from_timestamp, to_timestamp))
    prices = cursor.fetchall()
    conn.close()
    return [dict(row) for row in prices]

def get_latest_timestamp(currency: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(timestamp) as latest_timestamp FROM prices WHERE currency = ?", (currency,))
    result = cursor.fetchone()
    conn.close()
    return result['latest_timestamp'] if result and result['latest_timestamp'] else None

def get_latest_price(currency: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM prices WHERE currency = ? ORDER BY timestamp DESC LIMIT 1", (currency,))
    price = cursor.fetchone()
    conn.close()
    return dict(price) if price else None


def _get_price_by_order(currency: str, since: int = None, order: str = "ASC"):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM prices WHERE currency = ?"
    params = [currency]

    if since:
        query += " AND timestamp >= ?"
        params.append(since)

    query += f" ORDER BY price {order} LIMIT 1"

    cursor.execute(query, params)
    price = cursor.fetchone()
    conn.close()
    return dict(price) if price else None

def get_min_price(currency: str, since: int = None):
    return _get_price_by_order(currency, since, "ASC")

def get_max_price(currency: str, since: int = None):
    return _get_price_by_order(currency, since, "DESC")
