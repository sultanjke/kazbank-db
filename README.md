# KazBank - Python + PostgreSQL Integration Practice

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-4169E1?logo=postgresql&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-000000?logo=flask&logoColor=white)
![psycopg](https://img.shields.io/badge/psycopg-3-336791)

This repository contains a three-tier Python application that talks to PostgreSQL: a Flask REST API over the
KazBank banking schema (customers, accounts, transactions), built with psycopg3. It covers the full practice,
from the first database connection to an atomic, concurrency-safe money-transfer API with a connection pool.

> **Where the code is:** the project lives in [`pyproject/25B032112/`](pyproject/25B032112/).
> Its own [README](pyproject/25B032112/README.md) has the full run instructions, sample curl commands and test evidence.

---

## Repository structure

```
.
├── README.md                     ← you are here (repository overview)
├── .gitignore                    excludes venv/, .env, __pycache__/
└── python_project/
    └── your_id/                  the project (named after the student ID, as the course requires)
        ├── README.md             setup, endpoints, curl examples, test evidence
        ├── requirements.txt      Python dependencies
        ├── .env.example          template for the database connection string
        ├── check_conn.py         Step 1 – first connection, server version, autocommit check
        ├── setup_db.py           Step 2 – schema creation and seed data
        ├── loadtest.py           Step 6 – concurrent load test of the connection pool
        ├── app/
        │   ├── __init__.py       Flask app factory + /health endpoint
        │   ├── db.py             shared ConnectionPool (min 2, max 8)
        │   ├── errors.py         psycopg3 exceptions → HTTP status codes
        │   └── routes/
        │       ├── customers.py      /customers
        │       ├── accounts.py       /accounts
        │       └── transactions.py   /transactions, /transfer
        └── docs/                 screenshots (deadlock demo, test outputs)
```

## Tech stack

| Layer | Technology |
| --- | --- |
| Database | PostgreSQL 15+ |
| Database driver | psycopg 3 (`psycopg[binary]`) and `psycopg-pool` |
| Web framework | Flask 3 |
| Configuration | python-dotenv (`.env` file, never committed) |

## Quick start

```bash
git clone https://github.com/sultanjke/kazbank-db.git
cd kazbank-db/pyproject/25B032112

python -m venv venv
source venv/bin/activate              # Windows (Git Bash): source venv/Scripts/activate
pip install -r requirements.txt

cp .env.example .env                  # then set your PostgreSQL password in .env
python setup_db.py                    # creates and seeds the kazbank tables
flask --app app run                   # API at http://127.0.0.1:5000
```

You need a PostgreSQL database called `kazbank` first (`psql -U postgres -c "CREATE DATABASE kazbank;"`).
See the [project README](pyproject/25B032112/README.md) for details and test commands.

## Practice steps

| Step | Topic | Implemented in |
| --- | --- | --- |
| 1 | Environment setup: psycopg3, `.env`, first connection | `check_conn.py` |
| 2 | Schema & seed data: DDL from Python, `executemany()`, UNIQUE constraint | `setup_db.py` |
| 3 | CRUD REST API with Flask, parameterised queries | `app/routes/` |
| 4 | Transactions & ACID: atomic transfer, SAVEPOINT, SERIALIZABLE, lock ordering | `app/routes/transactions.py` |
| 5 | Error handling: specific psycopg3 exceptions, retry on serialization failure | `app/errors.py`, `with_retry()` |
| 6 | Connection pooling: `ConnectionPool`, `/health` with pool stats, load test | `app/db.py`, `loadtest.py` |
| 7 | Mini-project: complete KazBank Transaction API | the whole `app/` package |

## API overview

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/customers` | List customers (optional `?city=` filter) |
| POST | `/customers` | Create a customer |
| PUT / DELETE | `/customers/<id>` | Update / delete a customer |
| GET | `/accounts?customer_id=n` | Accounts of one customer |
| POST | `/transactions` | Record a single debit or credit |
| GET | `/transactions?account_id=n` | Transaction history of an account, newest first |
| POST | `/transfer` | Atomic transfer between two accounts |
| GET | `/health` | Database check and connection-pool statistics |

## Key concepts demonstrated

- **Atomicity:** a transfer's debit and credit commit together or not at all.
- **SAVEPOINT:** a failed transfer step is rolled back on its own, and the failure is still logged.
- **SERIALIZABLE isolation** with automatic retry on `SerializationFailure` (SQLSTATE 40001).
- **Deadlock prevention** by always locking account rows in ascending ID order.
- **Error mapping:** duplicate → 409, missing field / failed check → 400, database down → 503.
- **SQL-injection safety:** every query uses `%s` parameters; user input is never formatted into SQL.
- **Connection pooling:** one pool created at startup and shared by all requests.

## Submission

The submitted version is tagged **`v1.0`**. The graded project is in `pyproject/25B032112/`.

## Author

**Sultan Mecheyev** - `25B032112`

---

*This repository is coursework submitted for assessment. Please do not copy or reuse it for your own submission.*
