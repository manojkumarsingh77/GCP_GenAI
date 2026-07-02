"""
Seed the Cymbal Retail operational database (SQLite).

This simulates the company's "systems of record" (OMS / WMS / CRM) that the
MCP server exposes as tools. Run once before starting the MCP server:

    python setup/seed_database.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "retail.db"


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE customers (
            customer_id   TEXT PRIMARY KEY,
            name          TEXT NOT NULL,
            email         TEXT NOT NULL,
            tier          TEXT NOT NULL DEFAULT 'STANDARD',  -- STANDARD | PLUS
            city          TEXT
        );

        CREATE TABLE orders (
            order_id      TEXT PRIMARY KEY,
            customer_id   TEXT NOT NULL REFERENCES customers(customer_id),
            order_date    TEXT NOT NULL,
            status        TEXT NOT NULL,   -- PROCESSING | SHIPPED | IN_TRANSIT | OUT_FOR_DELIVERY | DELIVERED | DELAYED | RETURN_REQUESTED | REFUNDED
            total_amount  REAL NOT NULL,
            currency      TEXT NOT NULL DEFAULT 'INR',
            payment_method TEXT NOT NULL
        );

        CREATE TABLE order_items (
            order_id      TEXT NOT NULL REFERENCES orders(order_id),
            sku           TEXT NOT NULL,
            product_name  TEXT NOT NULL,
            quantity      INTEGER NOT NULL,
            unit_price    REAL NOT NULL
        );

        CREATE TABLE inventory (
            sku           TEXT PRIMARY KEY,
            product_name  TEXT NOT NULL,
            category      TEXT NOT NULL,
            price         REAL NOT NULL,
            stock_bengaluru INTEGER NOT NULL,
            stock_mumbai    INTEGER NOT NULL,
            stock_delhi     INTEGER NOT NULL
        );

        CREATE TABLE shipments (
            tracking_id   TEXT PRIMARY KEY,
            order_id      TEXT NOT NULL REFERENCES orders(order_id),
            carrier       TEXT NOT NULL,
            status        TEXT NOT NULL,
            last_scan_location TEXT,
            promised_date TEXT,
            last_update   TEXT
        );

        CREATE TABLE returns (
            return_id     TEXT PRIMARY KEY,
            order_id      TEXT NOT NULL REFERENCES orders(order_id),
            reason        TEXT NOT NULL,
            status        TEXT NOT NULL,   -- REQUESTED | APPROVED | PICKED_UP | REFUNDED
            refund_amount REAL,
            created_at    TEXT NOT NULL
        );
        """
    )

    cur.executemany(
        "INSERT INTO customers VALUES (?,?,?,?,?)",
        [
            ("CUST-1001", "Ananya Sharma",  "ananya@example.com",  "PLUS",     "Bengaluru"),
            ("CUST-1002", "Rahul Verma",    "rahul@example.com",   "STANDARD", "Mumbai"),
            ("CUST-1003", "Priya Nair",     "priya@example.com",   "STANDARD", "Kochi"),
            ("CUST-1004", "David Chen",     "david@example.com",   "PLUS",     "Delhi"),
        ],
    )

    cur.executemany(
        "INSERT INTO orders VALUES (?,?,?,?,?,?,?)",
        [
            ("ORD-78001", "CUST-1001", "2026-06-20", "DELIVERED",        24999.0, "INR", "CREDIT_CARD"),
            ("ORD-78002", "CUST-1001", "2026-06-28", "DELAYED",           3499.0, "INR", "UPI"),
            ("ORD-78003", "CUST-1002", "2026-06-25", "IN_TRANSIT",       12499.0, "INR", "CREDIT_CARD"),
            ("ORD-78004", "CUST-1003", "2026-06-15", "DELIVERED",         1899.0, "INR", "COD"),
            ("ORD-78005", "CUST-1004", "2026-06-30", "PROCESSING",       56999.0, "INR", "CREDIT_CARD"),
            ("ORD-78006", "CUST-1002", "2026-05-02", "DELIVERED",         8999.0, "INR", "UPI"),
        ],
    )

    cur.executemany(
        "INSERT INTO order_items VALUES (?,?,?,?,?)",
        [
            ("ORD-78001", "SKU-TV-43",   "Cymbal 43\" 4K Smart TV",          1, 24999.0),
            ("ORD-78002", "SKU-KETL-01", "Cymbal Electric Kettle 1.5L",      1,  1499.0),
            ("ORD-78002", "SKU-TOAST-2", "Cymbal 2-Slice Toaster",           1,  2000.0),
            ("ORD-78003", "SKU-SHOE-RN", "Cymbal RunPro Shoes (Size 9)",     1, 12499.0),
            ("ORD-78004", "SKU-TSHIRT",  "Cymbal Cotton T-Shirt (L, Navy)",  3,   633.0),
            ("ORD-78005", "SKU-LAPTOP",  "Cymbal AeroBook 14 Laptop",        1, 56999.0),
            ("ORD-78006", "SKU-HDPH-BT", "Cymbal BT Headphones ANC",         1,  8999.0),
        ],
    )

    cur.executemany(
        "INSERT INTO inventory VALUES (?,?,?,?,?,?,?)",
        [
            ("SKU-TV-43",   "Cymbal 43\" 4K Smart TV",         "Electronics", 24999.0, 12,  8, 15),
            ("SKU-KETL-01", "Cymbal Electric Kettle 1.5L",     "Appliances",   1499.0, 45, 30,  0),
            ("SKU-TOAST-2", "Cymbal 2-Slice Toaster",          "Appliances",   2000.0,  5,  0,  9),
            ("SKU-SHOE-RN", "Cymbal RunPro Shoes (Size 9)",    "Footwear",    12499.0,  3, 11,  6),
            ("SKU-TSHIRT",  "Cymbal Cotton T-Shirt (L, Navy)", "Apparel",       633.0, 120, 80, 95),
            ("SKU-LAPTOP",  "Cymbal AeroBook 14 Laptop",       "Electronics", 56999.0,  2,  4,  1),
            ("SKU-HDPH-BT", "Cymbal BT Headphones ANC",        "Electronics",  8999.0,  0,  7, 12),
        ],
    )

    cur.executemany(
        "INSERT INTO shipments VALUES (?,?,?,?,?,?,?)",
        [
            ("TRK-90011", "ORD-78001", "BlueDart",  "DELIVERED",        "Bengaluru Hub",  "2026-06-24", "2026-06-24 14:32"),
            ("TRK-90012", "ORD-78002", "Delhivery", "DELAYED",          "Nagpur Hub",     "2026-07-01", "2026-06-29 08:10"),
            ("TRK-90013", "ORD-78003", "BlueDart",  "IN_TRANSIT",       "Pune Hub",       "2026-07-03", "2026-07-01 22:47"),
            ("TRK-90014", "ORD-78004", "IndiaPost", "DELIVERED",        "Kochi GPO",      "2026-06-19", "2026-06-19 11:05"),
            ("TRK-90016", "ORD-78006", "Delhivery", "DELIVERED",        "Mumbai Hub",     "2026-05-06", "2026-05-06 16:20"),
        ],
    )

    conn.commit()
    conn.close()
    print(f"✅ Seeded operational database at: {DB_PATH}")
    print("   Tables: customers, orders, order_items, inventory, shipments, returns")
    print("   Try asking the agent about order ORD-78002 (a DELAYED shipment).")


if __name__ == "__main__":
    main()
