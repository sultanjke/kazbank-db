"""Step 1: check the connection, load credentials from .env, inspect autocommit."""
import os

import psycopg
from dotenv import load_dotenv

load_dotenv()                                  # Task 1.2: read DATABASE_URL from .env
conn_str = os.environ["DATABASE_URL"]

with psycopg.connect(conn_str) as conn:
    row = conn.execute("SELECT version()").fetchone()
    print("Server version:", row[0])            # Task 1.1
    print("autocommit =", conn.autocommit)      # Task 1.3: prints False