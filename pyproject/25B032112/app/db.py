"""Database access helper. Step 6 replaces this with a ConnectionPool."""
import os

import psycopg
from dotenv import load_dotenv

load_dotenv()


def get_conn():
    return psycopg.connect(os.environ["DATABASE_URL"])