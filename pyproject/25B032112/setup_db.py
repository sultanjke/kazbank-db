"""Step 2: create the KazBank schema and seed data from Python.

Run:  python setup_db.py      (safe to re-run: it drops and recreates the tables)
"""
import os

import psycopg
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.environ["DATABASE_URL"]

DDL = """
DROP TABLE IF EXISTS transactions, accounts, customers;

CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    full_name   TEXT NOT NULL,
    email       TEXT UNIQUE,
    city        TEXT DEFAULT 'Almaty'
);

CREATE TABLE accounts (
    account_id     SERIAL PRIMARY KEY,
    account_number TEXT NOT NULL UNIQUE,
    customer_id    INTEGER NOT NULL REFERENCES customers(customer_id),
    balance        NUMERIC(15,2) NOT NULL DEFAULT 0 CHECK (balance >= 0)
);

CREATE TABLE transactions (
    tx_id      SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(account_id),
    amount     NUMERIC(15,2) NOT NULL CHECK (amount > 0),
    tx_type    TEXT NOT NULL CHECK (tx_type IN ('DEBIT', 'CREDIT')),
    status     TEXT NOT NULL DEFAULT 'COMPLETED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

SEED_CUSTOMERS = [
    ("Arman Bekov", "arman.bekov@mail.kz", "Almaty"),
    ("Zarina Seiit", "zarina.seiit@mail.kz", "Astana"),
    ("Daniyar Nurlan", "daniyar.nurlan@mail.kz", "Shymkent"),
    ("Aigerim Tulegenova", "aigerim.t@mail.kz", "Almaty"),
    ("Nurlan Abenov", "nurlan.abenov@mail.kz", "Karaganda"),
    ("Madina Saparova", "madina.s@mail.kz", "Aktobe"),
    ("Yerlan Kassymov", "yerlan.k@mail.kz", "Almaty"),
    ("Dana Zhumabayeva", "dana.zh@mail.kz", "Astana"),
    ("Timur Ospanov", "timur.o@mail.kz", "Pavlodar"),
    ("Aruzhan Bekmurat", "aruzhan.b@mail.kz", "Atyrau"),
]

# (account_number, customer_id, balance): customers 1-5 get two accounts, 6-10 get one -> 15 accounts
SEED_ACCOUNTS = [
    ("KZ0001", 1, 250000.00), ("KZ0002", 1, 50000.00),
    ("KZ0003", 2, 120000.00), ("KZ0004", 2, 15000.00),
    ("KZ0005", 3, 80000.00),  ("KZ0006", 3, 5000.00),
    ("KZ0007", 4, 300000.00), ("KZ0008", 4, 0.00),
    ("KZ0009", 5, 45000.00),  ("KZ0010", 5, 99000.00),
    ("KZ0011", 6, 150000.00), ("KZ0012", 7, 70000.00),
    ("KZ0013", 8, 20000.00),  ("KZ0014", 9, 500000.00),
    ("KZ0015", 10, 1000.00),
]


def main():
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(DDL)
        # executemany() lives on the cursor (psycopg3 connections have no executemany)
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO customers (full_name, email, city) VALUES (%s, %s, %s)",
                SEED_CUSTOMERS,
            )
            cur.executemany(
                "INSERT INTO accounts (account_number, customer_id, balance) VALUES (%s, %s, %s)",
                SEED_ACCOUNTS,
            )
        conn.commit()

        n_cust = conn.execute("SELECT count(*) FROM customers").fetchone()[0]
        n_acc = conn.execute("SELECT count(*) FROM accounts").fetchone()[0]
        print(f"Seeded {n_cust} customers and {n_acc} accounts")

        # Task 2.3: prove the UNIQUE constraint on account_number works
        try:
            conn.execute(
                "INSERT INTO accounts (account_number, customer_id, balance) VALUES (%s, %s, %s)",
                ("KZ0001", 2, 100),
            )
            conn.commit()
            print("ERROR: duplicate account_number was accepted!")
        except psycopg.errors.UniqueViolation as e:
            conn.rollback()
            print("Duplicate rejected as expected:", e.diag.message_primary)


if __name__ == "__main__":
    main()