"""
setup_db.py - One-time database initialisation helper.
Run ONCE before starting the app for the first time:
    python setup_db.py

This script:
  1. Applies database/schema.sql  (creates tables)
  2. Applies database/seed.sql    (inserts demo data)
  3. Creates hashed user passwords using Werkzeug
"""

import os, sys
from pathlib import Path
from dotenv import load_dotenv
import mysql.connector
from werkzeug.security import generate_password_hash

load_dotenv()

DB_CFG = {
    "host"    : os.getenv("DB_HOST", "localhost"),
    "port"    : int(os.getenv("DB_PORT", 3306)),
    "user"    : os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "bank_screening"),
}

BASE = Path(__file__).parent

USERS = [
    # (username, password, role)
    ("arjun.mehta@demo.bank",  "demo1234",   "customer"),
    ("priya.sharma@demo.bank", "demo1234",   "customer"),
    ("ravi.kumar@demo.bank",   "demo1234",   "customer"),
    ("sunita.patel@demo.bank", "demo1234",   "customer"),
    ("amit.verma@demo.bank",   "demo1234",   "customer"),
    ("officer1",               "officer123", "officer"),
    ("officer2",               "officer123", "officer"),
]

CUSTOMERS = [
    # (name, email, phone)
    ("Arjun Mehta",  "arjun.mehta@demo.bank",  "+91-98001-11001"),
    ("Priya Sharma", "priya.sharma@demo.bank", "+91-98001-11002"),
    ("Ravi Kumar",   "ravi.kumar@demo.bank",   "+91-98001-11003"),
    ("Sunita Patel", "sunita.patel@demo.bank", "+91-98001-11004"),
    ("Amit Verma",   "amit.verma@demo.bank",   "+91-98001-11005"),
]

ACCOUNTS = [
    # (customer_idx [0-based], account_number, balance)
    (0, "ACC1001", 125000.00),
    (1, "ACC1002",  48000.00),
    (2, "ACC1003",  92500.00),
    (3, "ACC1004",  15000.00),
    (4, "ACC1005", 310000.00),
]


def run_sql_file(cursor, path: Path):
    """Execute each statement in a .sql file."""
    sql = path.read_text(encoding="utf-8")
    # Split on semicolons, skip blanks
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    for stmt in statements:
        try:
            cursor.execute(stmt)
        except mysql.connector.Error as e:
            print(f"  ⚠  Skipping: {e}")


def main():
    print("-" * 60)
    print("  CoopBank – Database Setup Script")
    print("-" * 60)

    # -- Connect (create DB if not exists) ---------------------------------
    try:
        cfg_no_db = {k: v for k, v in DB_CFG.items() if k != "database"}
        conn = mysql.connector.connect(**cfg_no_db)
        cur  = conn.cursor()
        print(f"[OK] Connected to MySQL at {DB_CFG['host']}:{DB_CFG['port']}")
    except mysql.connector.Error as e:
        print(f"[ERR] Cannot connect to MySQL: {e}")
        print("  Make sure MySQL is running and credentials in .env are correct.")
        sys.exit(1)

    # Create database
    db_name = DB_CFG["database"]
    cur.execute(
        f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
        f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    cur.execute(f"USE `{db_name}`")
    conn.commit()
    print(f"[OK] Database `{db_name}` ready")

    # -- Create tables ------------------------------------------------------
    schema_path = BASE / "database" / "schema.sql"
    print(f"\n-> Applying schema: {schema_path}")
    run_sql_file(cur, schema_path)
    conn.commit()
    print("[OK] Tables created")

    # -- Insert users with hashed passwords ---------------------------------
    print("\n-> Inserting users with hashed passwords…")
    for username, password, role in USERS:
        pw_hash = generate_password_hash(password)
        try:
            cur.execute(
                "INSERT IGNORE INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                (username, pw_hash, role)
            )
            print(f"  + {username} ({role})")
        except mysql.connector.Error as e:
            print(f"  ⚠  {username}: {e}")
    conn.commit()

    # -- Insert customers ----------------------------------------------------
    print("\n-> Inserting customers…")
    customer_ids = []
    for name, email, phone in CUSTOMERS:
        try:
            cur.execute(
                "INSERT IGNORE INTO customers (name, email, phone) VALUES (%s, %s, %s)",
                (name, email, phone)
            )
            cur.execute("SELECT customer_id FROM customers WHERE email=%s", (email,))
            row = cur.fetchone()
            customer_ids.append(row[0])
            print(f"  + {name} ({email})")
        except mysql.connector.Error as e:
            print(f"  ⚠  {name}: {e}")
    conn.commit()

    # -- Insert accounts -----------------------------------------------------
    print("\n-> Inserting accounts…")
    for cust_idx, acct_no, balance in ACCOUNTS:
        if cust_idx < len(customer_ids):
            try:
                cur.execute(
                    "INSERT IGNORE INTO accounts (customer_id, account_number, balance) VALUES (%s, %s, %s)",
                    (customer_ids[cust_idx], acct_no, balance)
                )
                print(f"  + {acct_no} -> Customer #{customer_ids[cust_idx]} (₹{balance:,.2f})")
            except mysql.connector.Error as e:
                print(f"  ⚠  {acct_no}: {e}")
    conn.commit()

    # -- Run seed SQL (transactions, screening results, audit) --------------
    seed_path = BASE / "database" / "seed.sql"
    print(f"\n-> Applying seed data: {seed_path}")
    # Skip the first 2 lines (CREATE DATABASE / USE) since we already did that
    seed_sql = seed_path.read_text(encoding="utf-8")
    # Skip user/customer/account inserts (already done with hashed pw above)
    # Only run transactions, screening_results, manual_reviews, audit_logs
    sections_to_run = []
    in_section = False
    for line in seed_sql.split("\n"):
        if "-- Historical Transactions" in line or "-- Potentially Suspicious" in line \
           or "-- Screening results" in line or "-- Audit log seed" in line:
            in_section = True
        if in_section:
            sections_to_run.append(line)

    if sections_to_run:
        combined = "\n".join(sections_to_run)
        for stmt in combined.split(";"):
            stmt = stmt.strip()
            if stmt and not stmt.startswith("--") and not stmt.startswith("USE"):
                try:
                    cur.execute(stmt)
                except mysql.connector.Error as e:
                    pass    # Duplicate key / expected on re-run
        conn.commit()
        print("[OK] Seed data applied")

    cur.close()
    conn.close()

    print("\n" + "-" * 60)
    print("  Setup complete! You can now run the application:")
    print()
    print("    python app.py")
    print()
    print("  Demo Credentials:")
    print("  {:<34} {:<14} {}".format("Username", "Password", "Role"))
    print("  " + "-" * 58)
    for u, p, r in USERS:
        print(f"  {u:<34} {p:<14} {r}")
    print("-" * 60)


if __name__ == "__main__":
    main()
